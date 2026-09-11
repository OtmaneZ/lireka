"""Audit qualité des vues analytics_views (lecture seule) avant migration CSV → PostgreSQL."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent / "audit_qualite_postgres_out"

VIEWS: dict[str, str] = {
    "customer_order": "id",
    "customer_order_item": "id",
    "customer_order_item_group": "id",
    "package": "id",
    "v_orders_overview": "order_id",
}

CSV_TABLES = (
    "customer_order",
    "customer_order_item",
    "customer_order_item_group",
    "package",
)

HIGHLIGHT_MONETARY = (
    "order_amount_eur",
    "gross_profit_eur",
    "gross_margin",
    "product_cost_eur",
)

MARGIN_TOLERANCE = Decimal("0.01")


def json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def connect() -> psycopg2.extensions.connection:
    password = os.environ.get("PGPASSWORD")
    if not password:
        print("ERROR: PGPASSWORD environment variable is not set.", file=sys.stderr)
        raise SystemExit(2)

    conn = psycopg2.connect(
        host="10.111.119.1",
        port=5432,
        dbname="analytics",
        user="liber_power_bi",
        password=password,
        connect_timeout=30,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET default_transaction_read_only = on;")
    return conn


def list_available_views(cur) -> set[str]:
    cur.execute(
        """
        SELECT viewname FROM pg_views WHERE schemaname = 'analytics_views'
        UNION
        SELECT matviewname FROM pg_matviews WHERE schemaname = 'analytics_views'
        """
    )
    return {r[0] for r in cur.fetchall()}


def find_backend_dir() -> Path | None:
    base = ROOT / "Power_BI_Datawarehouse"
    matches = list(base.glob("*/customer_order.csv"))
    if matches:
        return matches[0].parent
    env = os.environ.get("LIREKA_DWH")
    if env:
        p = Path(env) / "Données_Backend"
        if (p / "customer_order.csv").exists():
            return p
    return None


def fetch_columns(cur, view: str) -> list[tuple[str, str]]:
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'analytics_views' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (view,),
    )
    return [(r[0], r[1]) for r in cur.fetchall()]


def audit_nulls(cur, view: str, columns: list[str], total: int) -> list[dict[str, Any]]:
    if total == 0 or not columns:
        return []
    parts = [
        sql.SQL("count(*) FILTER (WHERE {c} IS NULL) AS {a}").format(
            c=sql.Identifier(col), a=sql.Identifier(f"n_{col}")
        )
        for col in columns
    ]
    query = sql.SQL("SELECT {fields}, count(*) AS total FROM analytics_views.{v}").format(
        fields=sql.SQL(", ").join(parts),
        v=sql.Identifier(view),
    )
    cur.execute(query)
    row = cur.fetchone()
    if not row:
        return []
    col_names = [d[0] for d in cur.description]
    values = dict(zip(col_names, row))
    total_rows = int(values.get("total", total))
    results: list[dict[str, Any]] = []
    for col in columns:
        null_count = int(values.get(f"n_{col}", 0))
        pct = round(100.0 * null_count / total_rows, 4) if total_rows else 0.0
        results.append({"column": col, "null_count": null_count, "null_pct": pct, "total_rows": total_rows})
    results.sort(key=lambda x: x["null_pct"], reverse=True)
    return results


def audit_duplicates(cur, view: str, key_col: str) -> dict[str, Any]:
    cur.execute(
        sql.SQL(
            """
            WITH dup AS (
                SELECT {k}, count(*) AS cnt
                FROM analytics_views.{v}
                WHERE {k} IS NOT NULL
                GROUP BY {k}
                HAVING count(*) > 1
            )
            SELECT count(*) AS duplicate_keys,
                   COALESCE(sum(cnt), 0) AS duplicate_rows,
                   COALESCE(sum(cnt) - count(*), 0) AS excess_rows
            FROM dup
            """
        ).format(k=sql.Identifier(key_col), v=sql.Identifier(view))
    )
    duplicate_keys, duplicate_rows, excess_rows = cur.fetchone()

    cur.execute(
        sql.SQL(
            """
            SELECT {k}, count(*) AS cnt
            FROM analytics_views.{v}
            WHERE {k} IS NOT NULL
            GROUP BY {k}
            HAVING count(*) > 1
            ORDER BY cnt DESC, {k}
            LIMIT 10
            """
        ).format(k=sql.Identifier(key_col), v=sql.Identifier(view))
    )
    examples = [{"key": r[0], "count": int(r[1])} for r in cur.fetchall()]
    return {
        "key_column": key_col,
        "duplicate_keys": int(duplicate_keys),
        "duplicate_rows": int(duplicate_rows),
        "excess_rows": int(excess_rows),
        "examples": examples,
    }


def is_monetary_numeric(col_name: str, data_type: str) -> bool:
    numeric_types = {
        "numeric",
        "integer",
        "bigint",
        "smallint",
        "double precision",
        "real",
        "decimal",
    }
    if data_type not in numeric_types:
        return False
    return col_name.endswith("_eur") or col_name.endswith("_local")


def audit_monetary(cur, view: str, columns_meta: list[tuple[str, str]]) -> list[dict[str, Any]]:
    monetary_cols = [c for c, t in columns_meta if is_monetary_numeric(c, t)]
    results: list[dict[str, Any]] = []
    for col in monetary_cols:
        cur.execute(
            sql.SQL(
                """
                SELECT
                    min({c}) AS min_val,
                    max({c}) AS max_val,
                    count(*) FILTER (WHERE {c} < 0) AS negatives,
                    count(*) FILTER (WHERE {c} = 0) AS zeros,
                    count(*) FILTER (WHERE {c} IS NOT NULL) AS non_null
                FROM analytics_views.{v}
                """
            ).format(c=sql.Identifier(col), v=sql.Identifier(view))
        )
        min_val, max_val, negatives, zeros, non_null = cur.fetchone()
        results.append(
            {
                "column": col,
                "min": min_val,
                "max": max_val,
                "negatives": int(negatives),
                "zeros": int(zeros),
                "non_null": int(non_null),
                "highlight": col in HIGHLIGHT_MONETARY,
            }
        )
    return results


def audit_margin_consistency(cur) -> dict[str, Any]:
    cur.execute(
        """
        SELECT count(*) AS total_checked,
               count(*) FILTER (
                   WHERE abs(gross_margin - (gross_profit_eur / order_amount_eur)) > %s
               ) AS ecart_count
        FROM analytics_views.customer_order
        WHERE order_amount_eur IS NOT NULL
          AND order_amount_eur <> 0
          AND gross_profit_eur IS NOT NULL
          AND gross_margin IS NOT NULL
        """,
        (MARGIN_TOLERANCE,),
    )
    total_checked, ecart_count = cur.fetchone()

    cur.execute(
        """
        SELECT id, order_amount_eur, gross_profit_eur, gross_margin,
               gross_profit_eur / order_amount_eur AS margin_calc,
               gross_margin - (gross_profit_eur / order_amount_eur) AS delta
        FROM analytics_views.customer_order
        WHERE order_amount_eur IS NOT NULL
          AND order_amount_eur <> 0
          AND gross_profit_eur IS NOT NULL
          AND gross_margin IS NOT NULL
          AND abs(gross_margin - (gross_profit_eur / order_amount_eur)) > %s
        ORDER BY abs(gross_margin - (gross_profit_eur / order_amount_eur)) DESC
        LIMIT 10
        """,
        (MARGIN_TOLERANCE,),
    )
    examples = [
        {
            "id": r[0],
            "order_amount_eur": r[1],
            "gross_profit_eur": r[2],
            "gross_margin": r[3],
            "margin_calc": r[4],
            "delta": r[5],
        }
        for r in cur.fetchall()
    ]
    return {
        "tolerance": float(MARGIN_TOLERANCE),
        "formula": "gross_margin ≈ gross_profit_eur / order_amount_eur",
        "total_checked": int(total_checked),
        "ecart_count": int(ecart_count),
        "examples": examples,
    }


def audit_orphans(cur) -> list[dict[str, Any]]:
    checks = [
        ("customer_order_item", "order_id", "customer_order", "id"),
        ("package", "order_id", "customer_order", "id"),
        ("customer_order_item_group", "order_id", "customer_order", "id"),
    ]
    results: list[dict[str, Any]] = []
    for child_view, child_col, parent_view, parent_col in checks:
        cur.execute(
            sql.SQL(
                """
                SELECT count(*) FROM analytics_views.{child} c
                WHERE c.{child_col} IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM analytics_views.{parent} p
                      WHERE p.{parent_col} = c.{child_col}
                  )
                """
            ).format(
                child=sql.Identifier(child_view),
                child_col=sql.Identifier(child_col),
                parent=sql.Identifier(parent_view),
                parent_col=sql.Identifier(parent_col),
            )
        )
        orphan_count = int(cur.fetchone()[0])
        cur.execute(
            sql.SQL(
                """
                SELECT c.{child_col}
                FROM analytics_views.{child} c
                WHERE c.{child_col} IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM analytics_views.{parent} p
                      WHERE p.{parent_col} = c.{child_col}
                  )
                GROUP BY c.{child_col}
                ORDER BY c.{child_col}
                LIMIT 10
                """
            ).format(
                child=sql.Identifier(child_view),
                child_col=sql.Identifier(child_col),
                parent=sql.Identifier(parent_view),
                parent_col=sql.Identifier(parent_col),
            )
        )
        examples = [r[0] for r in cur.fetchall()]
        results.append(
            {
                "child": f"{child_view}.{child_col}",
                "parent": f"{parent_view}.{parent_col}",
                "orphan_count": orphan_count,
                "example_order_ids": examples,
            }
        )
    return results


def parse_origin_created(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype(str).str.slice(0, 19), errors="coerce", utc=True)


def read_csv_table(backend: Path, table: str) -> pd.DataFrame | None:
    path = backend / f"{table}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def compare_csv_postgres(
    cur, backend: Path | None, available: set[str] | None = None
) -> dict[str, Any]:
    section: dict[str, Any] = {"backend_dir": str(backend) if backend else None, "tables": {}}

    if backend is None:
        section["error"] = "CSV backend introuvable (Power_BI_Datawarehouse/Données_Backend)"
        return section

    available = available or set(VIEWS.keys())

    for table in CSV_TABLES:
        csv_df = read_csv_table(backend, table)
        if table not in available:
            table_result: dict[str, Any] = {
                "pg_count": None,
                "csv_count": len(csv_df) if csv_df is not None else 0,
                "diff": None,
                "pg_missing": True,
            }
            section["tables"][table] = table_result
            continue
        cur.execute(sql.SQL("SELECT count(*) FROM analytics_views.{v}").format(v=sql.Identifier(table)))
        pg_count = int(cur.fetchone()[0])
        csv_count = len(csv_df) if csv_df is not None else 0
        table_result: dict[str, Any] = {
            "pg_count": pg_count,
            "csv_count": csv_count,
            "diff": pg_count - csv_count,
        }

        if table == "customer_order" and csv_df is not None and "state" in csv_df.columns:
            csv_by_state = csv_df.groupby("state", dropna=False).size().to_dict()
            cur.execute(
                "SELECT state, count(*) FROM analytics_views.customer_order GROUP BY state ORDER BY state"
            )
            pg_by_state = {str(r[0]) if r[0] is not None else "NULL": int(r[1]) for r in cur.fetchall()}
            all_states = sorted(set(csv_by_state) | set(pg_by_state), key=lambda x: str(x))
            by_state = []
            for st in all_states:
                c = int(csv_by_state.get(st, 0))
                p = int(pg_by_state.get(st, 0))
                by_state.append({"state": st, "csv_count": c, "pg_count": p, "diff": p - c})
            table_result["by_state"] = by_state

        section["tables"][table] = table_result

    # v_orders_overview — pas de CSV, volumétrie PG par order_state
    if "v_orders_overview" in available:
        cur.execute(
            "SELECT order_state, count(*) FROM analytics_views.v_orders_overview "
            "GROUP BY order_state ORDER BY order_state"
        )
        section["v_orders_overview_by_order_state"] = [
            {"order_state": str(r[0]) if r[0] is not None else "NULL", "pg_count": int(r[1])}
            for r in cur.fetchall()
        ]
        cur.execute("SELECT count(*) FROM analytics_views.v_orders_overview")
        section["v_orders_overview_total"] = int(cur.fetchone()[0])
    else:
        section["v_orders_overview_by_order_state"] = []
        section["v_orders_overview_total"] = None
        section["v_orders_overview_missing"] = True

    # Sommes monétaires sur période commune (customer_order)
    co_csv = read_csv_table(backend, "customer_order")
    if (
        "customer_order" in available
        and co_csv is not None
        and "origin_created" in co_csv.columns
    ):
        co_csv = co_csv.copy()
        co_csv["origin_created_dt"] = parse_origin_created(co_csv["origin_created"])
        csv_min = co_csv["origin_created_dt"].min()
        csv_max = co_csv["origin_created_dt"].max()

        cur.execute(
            "SELECT min(origin_created), max(origin_created) FROM analytics_views.customer_order"
        )
        pg_min, pg_max = cur.fetchone()

        if pd.notna(csv_min) and pd.notna(csv_max) and pg_min and pg_max:
            common_start = max(csv_min, pd.Timestamp(pg_min))
            common_end = min(csv_max, pd.Timestamp(pg_max))
            mask = (co_csv["origin_created_dt"] >= common_start) & (
                co_csv["origin_created_dt"] <= common_end
            )
            csv_period = co_csv.loc[mask]
            csv_sums = {
                "order_amount_eur": float(csv_period["order_amount_eur"].fillna(0).sum())
                if "order_amount_eur" in csv_period.columns
                else None,
                "gross_profit_eur": float(csv_period["gross_profit_eur"].fillna(0).sum())
                if "gross_profit_eur" in csv_period.columns
                else None,
            }

            cur.execute(
                """
                SELECT
                    COALESCE(sum(order_amount_eur), 0),
                    COALESCE(sum(gross_profit_eur), 0)
                FROM analytics_views.customer_order
                WHERE origin_created >= %s AND origin_created <= %s
                """,
                (common_start, common_end),
            )
            pg_order_sum, pg_gp_sum = cur.fetchone()
            pg_sums = {
                "order_amount_eur": float(pg_order_sum),
                "gross_profit_eur": float(pg_gp_sum),
            }

            section["customer_order_common_period"] = {
                "start": common_start.isoformat(),
                "end": common_end.isoformat(),
                "csv_rows": int(len(csv_period)),
                "pg_rows": None,
                "csv_sums": csv_sums,
                "pg_sums": pg_sums,
                "sum_diff": {
                    "order_amount_eur": pg_sums["order_amount_eur"] - csv_sums["order_amount_eur"],
                    "gross_profit_eur": pg_sums["gross_profit_eur"] - csv_sums["gross_profit_eur"],
                },
            }
            cur.execute(
                """
                SELECT count(*) FROM analytics_views.customer_order
                WHERE origin_created >= %s AND origin_created <= %s
                """,
                (common_start, common_end),
            )
            section["customer_order_common_period"]["pg_rows"] = int(cur.fetchone()[0])

    # v_orders_overview sums on common period with customer_order CSV dates
    if "v_orders_overview" not in available:
        return section
    co_csv = co_csv if co_csv is not None else read_csv_table(backend, "customer_order")
    if co_csv is None or "origin_created" not in co_csv.columns:
        return section
    co_csv = co_csv.copy()
    co_csv["origin_created_dt"] = parse_origin_created(co_csv["origin_created"])
    csv_min = co_csv["origin_created_dt"].min()
    csv_max = co_csv["origin_created_dt"].max()
    cur.execute("SELECT min(ordered_at), max(ordered_at) FROM analytics_views.v_orders_overview")
    vo_min, vo_max = cur.fetchone()
    if vo_min and vo_max and pd.notna(csv_min) and pd.notna(csv_max):
        common_start = max(pd.Timestamp(csv_min), pd.Timestamp(vo_min))
        common_end = min(pd.Timestamp(csv_max), pd.Timestamp(vo_max))
        if common_start <= common_end:
            cur.execute(
                """
                SELECT
                    COALESCE(sum(order_amount_eur), 0),
                    COALESCE(sum(gross_profit_eur), 0),
                    count(*)
                FROM analytics_views.v_orders_overview
                WHERE ordered_at >= %s AND ordered_at <= %s
                """,
                (common_start, common_end),
            )
            vo_order_sum, vo_gp_sum, vo_rows = cur.fetchone()
            mask = (co_csv["origin_created_dt"] >= common_start) & (
                co_csv["origin_created_dt"] <= common_end
            )
            csv_period = co_csv.loc[mask]
            section["v_orders_overview_common_period"] = {
                "start": common_start.isoformat(),
                "end": common_end.isoformat(),
                "pg_rows": int(vo_rows),
                "csv_rows": int(len(csv_period)),
                "pg_sums": {
                    "order_amount_eur": float(vo_order_sum),
                    "gross_profit_eur": float(vo_gp_sum),
                },
                "csv_sums": {
                    "order_amount_eur": float(csv_period["order_amount_eur"].fillna(0).sum())
                    if "order_amount_eur" in csv_period.columns
                    else None,
                    "gross_profit_eur": float(csv_period["gross_profit_eur"].fillna(0).sum())
                    if "gross_profit_eur" in csv_period.columns
                    else None,
                },
            }
            if section["v_orders_overview_common_period"]["csv_sums"]["order_amount_eur"] is not None:
                section["v_orders_overview_common_period"]["sum_diff"] = {
                    "order_amount_eur": section["v_orders_overview_common_period"]["pg_sums"][
                        "order_amount_eur"
                    ]
                    - section["v_orders_overview_common_period"]["csv_sums"]["order_amount_eur"],
                    "gross_profit_eur": section["v_orders_overview_common_period"]["pg_sums"][
                        "gross_profit_eur"
                    ]
                    - section["v_orders_overview_common_period"]["csv_sums"]["gross_profit_eur"],
                }

    return section


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_Aucune donnée_\n"
    str_rows = [["" if c is None else str(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    sep = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    line = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body = [
        "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |"
        for row in str_rows
    ]
    return "\n".join([sep, line] + body) + "\n"


def build_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    meta = report["meta"]
    lines.append("# Audit qualité — analytics_views")
    lines.append("")
    lines.append(f"- **Généré** : {meta['finished_at']}")
    lines.append(f"- **Host** : {meta['host']} / `{meta['dbname']}` / user `{meta['user']}`")
    lines.append(f"- **Durée** : {meta['elapsed_seconds']:.1f}s")
    if meta.get("views_available"):
        lines.append(f"- **Vues disponibles** : {', '.join(meta['views_available'])}")
    if meta.get("views_missing"):
        lines.append(f"- **Vues absentes** : {', '.join(meta['views_missing'])}")
    lines.append("")

    for view, data in report["views"].items():
        lines.append(f"## {view}")
        lines.append("")
        if data.get("status") in ("missing", "error"):
            lines.append(f"_**{data['status'].upper()}** : {data.get('error', '—')}_")
            lines.append("")
            continue
        lines.append(f"**Lignes** : {data['row_count']}")
        lines.append("")

        lines.append("### 1. Taux de NULL par colonne")
        lines.append("")
        null_rows = [
            [r["column"], r["null_count"], f"{r['null_pct']:.2f}%"]
            for r in data["nulls"]
        ]
        lines.append(md_table(["Colonne", "NULL count", "NULL %"], null_rows))

        lines.append("### 2. Doublons (`" + data["duplicates"]["key_column"] + "`)")
        lines.append("")
        dup = data["duplicates"]
        lines.append(
            f"- Clés en double : **{dup['duplicate_keys']}** "
            f"(lignes dupliquées : {dup['duplicate_rows']}, excédent : {dup['excess_rows']})"
        )
        if dup["examples"]:
            lines.append("")
            ex_rows = [[e["key"], e["count"]] for e in dup["examples"]]
            lines.append(md_table(["Clé", "Count"], ex_rows))
        lines.append("")

        if data["monetary"]:
            lines.append("### 3. Colonnes monétaires (*_eur / *_local)")
            lines.append("")
            mon_rows = [
                [
                    ("**" + m["column"] + "**" if m["highlight"] else m["column"]),
                    m["min"],
                    m["max"],
                    m["negatives"],
                    m["zeros"],
                    m["non_null"],
                ]
                for m in data["monetary"]
            ]
            lines.append(
                md_table(["Colonne", "Min", "Max", "Négatifs", "Zéros", "Non-NULL"], mon_rows)
            )

        if view == "customer_order":
            lines.append("### 4. Cohérence marge brute")
            lines.append("")
            mc = data["margin_consistency"]
            lines.append(f"- Formule : `{mc['formula']}` (tolérance {mc['tolerance']})")
            lines.append(
                f"- Lignes vérifiées : {mc['total_checked']} — **écarts** : {mc['ecart_count']}"
            )
            if mc["examples"]:
                lines.append("")
                ex = [
                    [
                        e["id"],
                        e["order_amount_eur"],
                        e["gross_profit_eur"],
                        e["gross_margin"],
                        e["margin_calc"],
                        e["delta"],
                    ]
                    for e in mc["examples"]
                ]
                lines.append(
                    md_table(
                        ["id", "order_amount_eur", "gross_profit_eur", "gross_margin", "calc", "delta"],
                        ex,
                    )
                )
            lines.append("")

    lines.append("## 5. Cohérence référentielle (orphelins)")
    lines.append("")
    for o in report["referential"]:
        if o.get("skipped"):
            lines.append(f"- _{o['skipped']}_")
            continue
        lines.append(
            f"- **{o['child']}** → {o['parent']} : **{o['orphan_count']}** orphelins"
        )
        if o["example_order_ids"]:
            lines.append(f"  - Exemples : {o['example_order_ids']}")
    lines.append("")

    lines.append("## 6. Comparaison CSV vs PostgreSQL")
    lines.append("")
    csv_cmp = report["csv_comparison"]
    if csv_cmp.get("error"):
        lines.append(f"_{csv_cmp['error']}_")
    else:
        lines.append(f"Répertoire CSV : `{csv_cmp['backend_dir']}`")
        lines.append("")
        lines.append("### Volumétrie par table")
        lines.append("")
        vol_rows = [
            [t, d["csv_count"], d.get("pg_count"), d.get("diff")]
            for t, d in csv_cmp["tables"].items()
        ]
        lines.append(md_table(["Table", "CSV", "PG", "Diff (PG-CSV)"], vol_rows))

        co = csv_cmp["tables"].get("customer_order", {})
        if co.get("by_state"):
            lines.append("### customer_order par `state`")
            lines.append("")
            st_rows = [
                [r["state"], r["csv_count"], r["pg_count"], r["diff"]]
                for r in co["by_state"]
            ]
            lines.append(md_table(["state", "CSV", "PG", "Diff"], st_rows))

        lines.append("### v_orders_overview par `order_state` (PG seul)")
        lines.append("")
        vo_rows = [
            [r["order_state"], r["pg_count"]] for r in csv_cmp["v_orders_overview_by_order_state"]
        ]
        lines.append(md_table(["order_state", "PG count"], vo_rows))

        if csv_cmp.get("customer_order_common_period"):
            cp = csv_cmp["customer_order_common_period"]
            lines.append("### Sommes période commune — customer_order")
            lines.append("")
            lines.append(f"Période : {cp['start']} → {cp['end']}")
            lines.append(f"Lignes CSV : {cp['csv_rows']} | PG : {cp['pg_rows']}")
            lines.append("")
            sum_rows = [
                [
                    "order_amount_eur",
                    cp["csv_sums"]["order_amount_eur"],
                    cp["pg_sums"]["order_amount_eur"],
                    cp["sum_diff"]["order_amount_eur"],
                ],
                [
                    "gross_profit_eur",
                    cp["csv_sums"]["gross_profit_eur"],
                    cp["pg_sums"]["gross_profit_eur"],
                    cp["sum_diff"]["gross_profit_eur"],
                ],
            ]
            lines.append(md_table(["Mesure", "CSV", "PG", "Diff (PG-CSV)"], sum_rows))

        if csv_cmp.get("v_orders_overview_common_period"):
            vp = csv_cmp["v_orders_overview_common_period"]
            lines.append("### Sommes période commune — v_orders_overview vs CSV customer_order dates")
            lines.append("")
            lines.append(f"Période : {vp['start']} → {vp['end']}")
            lines.append(f"Lignes PG (v_orders_overview) : {vp['pg_rows']} | CSV customer_order : {vp['csv_rows']}")
            if vp.get("sum_diff"):
                lines.append("")
                sum_rows = [
                    [
                        "order_amount_eur",
                        vp["csv_sums"]["order_amount_eur"],
                        vp["pg_sums"]["order_amount_eur"],
                        vp["sum_diff"]["order_amount_eur"],
                    ],
                    [
                        "gross_profit_eur",
                        vp["csv_sums"]["gross_profit_eur"],
                        vp["pg_sums"]["gross_profit_eur"],
                        vp["sum_diff"]["gross_profit_eur"],
                    ],
                ]
                lines.append(md_table(["Mesure", "CSV co", "PG vo", "Diff"], sum_rows))

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    started = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "meta": {
            "host": "10.111.119.1",
            "dbname": "analytics",
            "user": "liber_power_bi",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": None,
            "elapsed_seconds": None,
            "views_available": [],
            "views_missing": [],
        },
        "views": {},
        "referential": [],
        "csv_comparison": {},
    }

    try:
        conn = connect()
    except SystemExit as exc:
        return int(exc.code)
    except Exception as exc:
        print(f"CONNECT FAILED: {exc}", file=sys.stderr)
        return 1

    try:
        with conn.cursor() as cur:
            available = list_available_views(cur)
            report["meta"]["views_available"] = sorted(available)
            report["meta"]["views_missing"] = sorted(set(VIEWS) - available)

            for view, key_col in VIEWS.items():
                if view not in available:
                    report["views"][view] = {
                        "status": "missing",
                        "error": f"vue analytics_views.{view} introuvable",
                    }
                    continue
                try:
                    view_data: dict[str, Any] = {"status": "ok"}
                    cur.execute(
                        sql.SQL("SELECT count(*) FROM analytics_views.{v}").format(
                            v=sql.Identifier(view)
                        )
                    )
                    row_count = int(cur.fetchone()[0])
                    view_data["row_count"] = row_count

                    columns_meta = fetch_columns(cur, view)
                    col_names = [c for c, _ in columns_meta]
                    view_data["nulls"] = audit_nulls(cur, view, col_names, row_count)
                    view_data["duplicates"] = audit_duplicates(cur, view, key_col)
                    view_data["monetary"] = audit_monetary(cur, view, columns_meta)
                    if view == "customer_order":
                        view_data["margin_consistency"] = audit_margin_consistency(cur)
                    report["views"][view] = view_data
                except Exception as exc:
                    report["views"][view] = {"status": "error", "error": str(exc)}

            if "customer_order" in available:
                report["referential"] = audit_orphans(cur)
            else:
                report["referential"] = [
                    {
                        "child": "—",
                        "parent": "—",
                        "orphan_count": None,
                        "example_order_ids": [],
                        "skipped": "customer_order absente — cohérence référentielle non calculée",
                    }
                ]
            report["csv_comparison"] = compare_csv_postgres(cur, find_backend_dir(), available)
    finally:
        conn.close()

    elapsed = time.perf_counter() - started
    report["meta"]["elapsed_seconds"] = elapsed
    report["meta"]["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    json_path = OUT_DIR / "results.json"
    md_path = OUT_DIR / "results.md"

    json_path.write_text(
        json.dumps(report, indent=2, default=json_default, ensure_ascii=False),
        encoding="utf-8",
    )
    md_path.write_text(build_markdown(report), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
