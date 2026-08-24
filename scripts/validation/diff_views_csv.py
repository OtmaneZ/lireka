"""Diff colonnes analytics_views (check_views.txt) vs en-têtes CSV Données_Backend."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "out" / "check_views.txt"
OUT = ROOT / "out" / "diff_views_csv.txt"
TABLES = (
    "customer_order",
    "customer_order_item",
    "customer_order_item_group",
    "package",
)


def find_backend_dir() -> Path:
    base = ROOT / "Power_BI_Datawarehouse"
    matches = list(base.glob("*/customer_order.csv"))
    if not matches:
        raise FileNotFoundError(f"customer_order.csv introuvable sous {base}")
    return matches[0].parent


def parse_view_columns(text: str) -> dict[str, list[str]]:
    """Parse QUERY 1 block: table_name | ordinal | column_name | data_type | is_nullable."""
    cols: dict[str, list[str]] = {t: [] for t in TABLES}
    in_q1 = False
    for line in text.splitlines():
        if line.startswith("QUERY 1_"):
            in_q1 = True
            continue
        if in_q1 and line.startswith("QUERY "):
            break
        if not in_q1:
            continue
        if " | " not in line or line.startswith("table_name") or line.startswith("-+-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        table, _, col = parts[0], parts[1], parts[2]
        if table in cols:
            cols[table].append(col)
    return cols


def csv_headers(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return next(csv.reader(fh))


def main() -> int:
    if not CHECK.exists():
        print(f"ERROR: missing {CHECK}", file=sys.stderr)
        return 1

    text = CHECK.read_text(encoding="utf-8")
    if "ERROR:" in text and "permission denied" in text.lower():
        print(text)
        return 1

    view_cols = parse_view_columns(text)
    backend = find_backend_dir()

    lines: list[str] = []
    lines.append("diff_views_csv — colonnes vue vs CSV")
    lines.append(f"source_views={CHECK}")
    lines.append(f"source_csv_dir={backend}")
    lines.append("")

    for table in TABLES:
        csv_path = backend / f"{table}.csv"
        v = view_cols.get(table, [])
        c = csv_headers(csv_path) if csv_path.exists() else []
        both = [x for x in c if x in set(v)]
        only_csv = [x for x in c if x not in set(v)]
        only_view = [x for x in v if x not in set(c)]

        lines.append("=" * 72)
        lines.append(table)
        lines.append("=" * 72)
        lines.append(f"vue_count={len(v)} csv_count={len(c)}")
        lines.append("")
        lines.append(f"presentes_des_deux_cotes ({len(both)}):")
        for x in both:
            lines.append(f"  - {x}")
        lines.append("")
        lines.append(f"uniquement_dans_csv ({len(only_csv)}):")
        for x in only_csv:
            lines.append(f"  - {x}")
        if not only_csv:
            lines.append("  (aucune)")
        lines.append("")
        lines.append(f"uniquement_dans_vue ({len(only_view)}):")
        for x in only_view:
            lines.append(f"  - {x}")
        if not only_view:
            lines.append("  (aucune)")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    print(f"Wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
