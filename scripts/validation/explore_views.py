"""Explore analytics_views — lecture seule, résultats bruts."""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "explore_views.txt"

# EXPLAIN ANALYZE full SELECT * can be long on large views.
STATEMENT_TIMEOUT_MS = 1_800_000  # 30 minutes


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_rows(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "(0 rows)\n"
    widths = [len(c) for c in columns]
    str_rows = []
    for row in rows:
        cells = ["" if v is None else str(v) for v in row]
        str_rows.append(cells)
        for i, cell in enumerate(cells):
            widths[i] = max(widths[i], len(cell))
    header = " | ".join(c.ljust(widths[i]) for i, c in enumerate(columns))
    sep = "-+-".join("-" * w for w in widths)
    lines = [header, sep]
    for cells in str_rows:
        lines.append(" | ".join(cells[i].ljust(widths[i]) for i in range(len(columns))))
    lines.append(f"({len(rows)} rows)")
    return "\n".join(lines) + "\n"


def run_sql(cur, lines: list[str], label: str, sql: str) -> None:
    lines.append("-" * 72)
    lines.append(f"SUBQUERY {label}")
    lines.append(f"started_at={now_stamp()}")
    lines.append(sql.strip())
    lines.append("")
    t0 = time.perf_counter()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
        elapsed = time.perf_counter() - t0
        lines.append(f"elapsed_seconds={elapsed:.3f}")
        lines.append(f"finished_at={now_stamp()}")
        lines.append("")
        # Long single-cell text (EXPLAIN / pg_get_viewdef): plain dump
        if len(columns) == 1 and rows and (
            columns[0].lower() in ("query plan", "pg_get_viewdef")
            or (isinstance(rows[0][0], str) and ("\n" in rows[0][0] or len(rows[0][0]) > 200))
        ):
            for row in rows:
                text = "" if row[0] is None else str(row[0])
                lines.extend(text.splitlines() if text else [""])
            lines.append(f"({len(rows)} rows)")
            lines.append("")
        else:
            lines.append(format_rows(columns, rows))
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        lines.append(f"elapsed_seconds={elapsed:.3f}")
        lines.append(f"finished_at={now_stamp()}")
        lines.append(f"ERROR: {exc}")
        lines.append("")


def column_exists(cur, schema: str, table: str, column: str) -> bool:
    cur.execute(
        """
SELECT 1
FROM information_schema.columns
WHERE table_schema = %s AND table_name = %s AND column_name = %s
LIMIT 1;
""",
        (schema, table, column),
    )
    return cur.fetchone() is not None


def main() -> int:
    password = os.environ.get("PGPASSWORD")
    if not password:
        print("ERROR: PGPASSWORD environment variable is not set.", file=sys.stderr)
        return 2

    OUT.parent.mkdir(parents=True, exist_ok=True)

    conn_kwargs = dict(
        host="10.111.119.1",
        port=5432,
        dbname="analytics",
        user="liber_power_bi",
        password=password,
        connect_timeout=30,
    )

    lines: list[str] = []
    lines.append("explore_views.py — analytics_views explore (read-only)")
    lines.append(
        f"host={conn_kwargs['host']} port={conn_kwargs['port']} "
        f"dbname={conn_kwargs['dbname']} user={conn_kwargs['user']}"
    )
    lines.append(f"started_at={now_stamp()}")
    lines.append(f"statement_timeout_ms={STATEMENT_TIMEOUT_MS}")
    lines.append("")

    try:
        t0 = time.perf_counter()
        conn = psycopg2.connect(**conn_kwargs)
        connect_s = time.perf_counter() - t0
        lines.append(f"CONNECT ok in {connect_s:.3f}s")
        lines.append("")
    except Exception as exc:
        lines.append(f"CONNECT FAILED: {exc}")
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(OUT.read_text(encoding="utf-8"))
        print(f"Wrote {OUT}", file=sys.stderr)
        return 1

    # Autocommit so long EXPLAIN ANALYZE does not hold an open transaction unnecessarily.
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")
            cur.execute("SET default_transaction_read_only = on")

            # ---- A ----
            lines.append("=" * 72)
            lines.append("QUERY A — définition de v_orders_overview")
            lines.append("=" * 72)
            lines.append(f"section_started_at={now_stamp()}")
            lines.append("")
            run_sql(
                cur,
                lines,
                "A1_pg_get_viewdef",
                "SELECT pg_get_viewdef('analytics_views.v_orders_overview'::regclass, true);",
            )
            run_sql(
                cur,
                lines,
                "A2_columns",
                """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema='analytics_views' AND table_name='v_orders_overview'
ORDER BY ordinal_position;
""",
            )
            run_sql(
                cur,
                lines,
                "A3_count",
                "SELECT count(*) FROM analytics_views.v_orders_overview;",
            )
            lines.append(f"section_finished_at={now_stamp()}")
            lines.append("")

            # ---- B ----
            lines.append("=" * 72)
            lines.append("QUERY B — coût réel d'un import complet (EXPLAIN ANALYZE)")
            lines.append("=" * 72)
            lines.append(f"section_started_at={now_stamp()}")
            lines.append("")
            run_sql(
                cur,
                lines,
                "B1_customer_order",
                "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM analytics_views.customer_order;",
            )
            # flush intermediate output so a kill mid-B2 still leaves A+B1 on disk
            OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
            run_sql(
                cur,
                lines,
                "B2_customer_order_item",
                "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM analytics_views.customer_order_item;",
            )
            lines.append(f"section_finished_at={now_stamp()}")
            lines.append("")
            OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # ---- C ----
            lines.append("=" * 72)
            lines.append("QUERY C — remplissage des colonnes financières")
            lines.append("=" * 72)
            lines.append(f"section_started_at={now_stamp()}")
            lines.append("")
            needed = [
                "product_cost_eur",
                "inbound_transportation_cost_eur",
                "duties_and_taxes_eur",
            ]
            missing = [
                c for c in needed if not column_exists(cur, "analytics_views", "customer_order", c)
            ]
            if missing:
                lines.append("-" * 72)
                lines.append("SUBQUERY C1_fill_rates")
                lines.append(f"started_at={now_stamp()}")
                for c in missing:
                    lines.append(f"MISSING_COLUMN: {c}")
                lines.append("SKIPPED: column(s) missing — no equivalent guessed")
                lines.append(f"finished_at={now_stamp()}")
                lines.append("")
            else:
                run_sql(
                    cur,
                    lines,
                    "C1_fill_rates",
                    """
SELECT
  count(*) AS total,
  count(product_cost_eur) AS cost_ok,
  count(inbound_transportation_cost_eur) AS inbound_ok,
  count(duties_and_taxes_eur) AS duties_ok
FROM analytics_views.customer_order;
""",
                )
            lines.append(f"section_finished_at={now_stamp()}")
            lines.append("")

            # ---- D ----
            lines.append("=" * 72)
            lines.append("QUERY D — régularité du rafraîchissement")
            lines.append("=" * 72)
            lines.append(f"section_started_at={now_stamp()}")
            lines.append("")
            run_sql(
                cur,
                lines,
                "D1_last_7_days",
                """
SELECT origin_created::date AS d, count(*)
FROM analytics_views.customer_order
WHERE origin_created > now() - interval '7 days'
GROUP BY 1 ORDER BY 1;
""",
            )
            lines.append(f"section_finished_at={now_stamp()}")
            lines.append("")
    finally:
        conn.close()

    lines.append(f"finished_at={now_stamp()}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    print(f"Wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
