"""Diagnostic analytics_views: inventaire, kind, volumétrie, fraîcheur."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "check_views.txt"

QUERIES = [
    (
        "1_inventaire_colonnes",
        """
SELECT table_name, ordinal_position, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'analytics_views'
ORDER BY table_name, ordinal_position;
""",
    ),
    (
        "2_vues_simples_ou_materialisees",
        """
SELECT schemaname, viewname AS name, 'view' AS kind
FROM pg_views WHERE schemaname = 'analytics_views'
UNION ALL
SELECT schemaname, matviewname, 'materialized'
FROM pg_matviews WHERE schemaname = 'analytics_views';
""",
    ),
    (
        "3_volumetrie",
        """
SELECT 'customer_order' AS v, count(*) FROM analytics_views.customer_order
UNION ALL SELECT 'customer_order_item', count(*) FROM analytics_views.customer_order_item
UNION ALL SELECT 'customer_order_item_group', count(*) FROM analytics_views.customer_order_item_group
UNION ALL SELECT 'package', count(*) FROM analytics_views.package;
""",
    ),
    (
        "4_fraicheur",
        """
SELECT max(origin_created) FROM analytics_views.customer_order;
""",
    ),
]


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
    lines.append("check_views.py — analytics_views diagnostic")
    lines.append(f"host={conn_kwargs['host']} port={conn_kwargs['port']} dbname={conn_kwargs['dbname']} user={conn_kwargs['user']}")
    lines.append(f"started_at={time.strftime('%Y-%m-%d %H:%M:%S')}")
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

    try:
        with conn.cursor() as cur:
            for name, sql in QUERIES:
                lines.append("=" * 72)
                lines.append(f"QUERY {name}")
                lines.append("=" * 72)
                lines.append(sql.strip())
                lines.append("")
                t0 = time.perf_counter()
                try:
                    cur.execute(sql)
                    rows = cur.fetchall()
                    columns = [d[0] for d in cur.description] if cur.description else []
                    elapsed = time.perf_counter() - t0
                    lines.append(f"elapsed_seconds={elapsed:.3f}")
                    lines.append("")
                    lines.append(format_rows(columns, rows))
                except Exception as exc:
                    elapsed = time.perf_counter() - t0
                    lines.append(f"elapsed_seconds={elapsed:.3f}")
                    lines.append(f"ERROR: {exc}")
                    lines.append("")
                lines.append("")
    finally:
        conn.close()

    lines.append(f"finished_at={time.strftime('%Y-%m-%d %H:%M:%S')}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    print(f"Wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
