"""Inbound >0 + row counts vue vs CSV. Lecture seule, résultats bruts."""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "check_inbound_and_counts.txt"
TABLES = (
    "customer_order",
    "customer_order_item",
    "customer_order_item_group",
    "package",
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def find_backend_dir() -> Path:
    base = ROOT / "Power_BI_Datawarehouse"
    matches = list(base.glob("*/customer_order.csv"))
    if not matches:
        raise FileNotFoundError(f"customer_order.csv introuvable sous {base}")
    return matches[0].parent


def count_csv_rows(path: Path) -> int:
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    return max(n - 1, 0)


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


def run(cur, lines: list[str], label: str, sql: str) -> list[tuple] | None:
    lines.append("-" * 72)
    lines.append(label)
    lines.append(f"started_at={now_stamp()}")
    lines.append(sql.strip())
    lines.append("")
    t0 = time.perf_counter()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        elapsed = time.perf_counter() - t0
        lines.append(f"elapsed_seconds={elapsed:.3f}")
        lines.append(f"finished_at={now_stamp()}")
        lines.append("")
        lines.append(format_rows(cols, rows))
        return rows
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        lines.append(f"elapsed_seconds={elapsed:.3f}")
        lines.append(f"finished_at={now_stamp()}")
        lines.append(f"ERROR: {exc}")
        lines.append("")
        return None


def main() -> int:
    password = os.environ.get("PGPASSWORD")
    if not password:
        print("ERROR: PGPASSWORD environment variable is not set.", file=sys.stderr)
        return 2

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("check_inbound_and_counts.py — read-only")
    lines.append(f"started_at={now_stamp()}")
    lines.append("")

    conn = psycopg2.connect(
        host="10.111.119.1",
        port=5432,
        dbname="analytics",
        user="liber_power_bi",
        password=password,
        connect_timeout=30,
    )
    conn.autocommit = True
    lines.append("CONNECT ok")
    lines.append("")

    try:
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")

            lines.append("=" * 72)
            lines.append("INVENTORY — analytics_views right now")
            lines.append("=" * 72)
            run(
                cur,
                lines,
                "INV1_pg_views",
                """
SELECT schemaname, viewname AS name, 'view' AS kind
FROM pg_views WHERE schemaname = 'analytics_views'
UNION ALL
SELECT schemaname, matviewname, 'materialized'
FROM pg_matviews WHERE schemaname = 'analytics_views'
ORDER BY 2;
""",
            )
            run(
                cur,
                lines,
                "INV2_find_customer_order",
                """
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_name IN ('customer_order', 'v_orders_overview', 'fact_order')
ORDER BY 1, 2;
""",
            )

            lines.append("=" * 72)
            lines.append("QUERY 1 — inbound > 0 on analytics_views.customer_order")
            lines.append("=" * 72)
            run(
                cur,
                lines,
                "Q1_inbound_pos",
                """
SELECT count(*) FILTER (WHERE inbound_transportation_cost_eur > 0) AS inbound_pos,
       sum(inbound_transportation_cost_eur) AS inbound_sum,
       min(origin_created) FILTER (WHERE inbound_transportation_cost_eur > 0) AS first_date
FROM analytics_views.customer_order;
""",
            )

            # Fallback if view missing: same metrics on dwh.fact_order if accessible
            run(
                cur,
                lines,
                "Q1_fallback_dwh_fact_order",
                """
SELECT count(*) FILTER (WHERE inbound_transportation_cost_eur > 0) AS inbound_pos,
       sum(inbound_transportation_cost_eur) AS inbound_sum,
       min(origin_created) FILTER (WHERE inbound_transportation_cost_eur > 0) AS first_date
FROM dwh.fact_order
WHERE is_final_state;
""",
            )
            run(
                cur,
                lines,
                "Q1b_breakdown_dwh_fact_order_final",
                """
SELECT
  count(*) AS total,
  count(inbound_transportation_cost_eur) AS non_null,
  count(*) FILTER (WHERE inbound_transportation_cost_eur IS NULL) AS is_null,
  count(*) FILTER (WHERE inbound_transportation_cost_eur = 0) AS is_zero,
  count(*) FILTER (WHERE inbound_transportation_cost_eur > 0) AS gt_zero,
  count(*) FILTER (WHERE inbound_transportation_cost_eur < 0) AS lt_zero
FROM dwh.fact_order
WHERE is_final_state;
""",
            )

            lines.append("=" * 72)
            lines.append("QUERY 2 — row counts view vs CSV")
            lines.append("=" * 72)
            backend = find_backend_dir()
            lines.append(f"csv_dir={backend}")
            lines.append("")

            view_rows: dict[str, int | None] = {}
            for table in TABLES:
                sql = f"SELECT count(*) FROM analytics_views.{table};"
                rows = run(cur, lines, f"Q2_view_{table}", sql)
                view_rows[table] = int(rows[0][0]) if rows else None

            run(
                cur,
                lines,
                "Q2b_dwh_is_final_state",
                """
SELECT 'dwh.fact_order total' AS v, count(*) FROM dwh.fact_order
UNION ALL SELECT 'dwh.fact_order is_final_state=true', count(*) FROM dwh.fact_order WHERE is_final_state
UNION ALL SELECT 'dwh.fact_order is_final_state=false', count(*) FROM dwh.fact_order WHERE NOT is_final_state
UNION ALL SELECT 'dwh.fact_order_item total', count(*) FROM dwh.fact_order_item
UNION ALL SELECT 'dwh.fact_order_item is_final_state=true', count(*) FROM dwh.fact_order_item WHERE is_final_state
UNION ALL SELECT 'dwh.fact_order_item is_final_state=false', count(*) FROM dwh.fact_order_item WHERE NOT is_final_state;
""",
            )

            lines.append("-" * 72)
            lines.append("COMPARE view_count vs csv_row_count")
            lines.append("")
            lines.append(
                f"{'table':<28} | {'view_n':>12} | {'csv_n':>12} | {'view_minus_csv':>14} | csv_mtime"
            )
            lines.append("-" * 90)
            for table in TABLES:
                csv_path = backend / f"{table}.csv"
                csv_n = count_csv_rows(csv_path) if csv_path.exists() else None
                view_n = view_rows.get(table)
                delta = (
                    (view_n - csv_n)
                    if (view_n is not None and csv_n is not None)
                    else None
                )
                mtime = (
                    datetime.fromtimestamp(csv_path.stat().st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if csv_path.exists()
                    else "MISSING"
                )
                lines.append(
                    f"{table:<28} | {str(view_n):>12} | {str(csv_n):>12} | "
                    f"{str(delta):>14} | {mtime}"
                )
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
