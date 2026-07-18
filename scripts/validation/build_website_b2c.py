"""Génère la page « Website B2C » (PAGE A) — mockup Finance 20260716.

Rail identique General View · scope page Website B2C · 4 KPI cards ·
tableau pays (_B2C_Country) Top 15 Sales + Rest of the world.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Import helpers partagés avec General View
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_general_view import (  # noqa: E402
    BAND_ROW,
    BORDER,
    CARD_GAP,
    CARD_H,
    CARD_W,
    CARD_Y,
    CARDBG,
    CX,
    CW,
    FOOTER_H,
    FOOTER_Y,
    LOGO_DST,
    LOGO_SRC,
    MESURES,
    NAV_W,
    NAVBG,
    PRIMARY,
    RAIL_FOOTER_BG,
    REPORT,
    SCHEMA,
    SUBTXT,
    col_disp,
    footer,
    image_logo,
    kpi_card,
    lit,
    meas,
    pos,
    prop,
    shape_rect,
    slicer_date_range,
    slicer_dropdown,
    solid_lit,
    solid_measure,
    textbox_static,
    update_report_json,
    date_relative_filter,
)

ROOT = Path(__file__).resolve().parents[2]
GV_PAGE_ID = "7112a69a17fbef2de240"
PAGE_ID = "8f3e2a1b9c4d5e6f7a8b9c0d1e2f3a"
PAGE = REPORT / "definition" / "pages" / PAGE_ID
VIS = PAGE / "visuals"

B2C_CHANNEL = "Website B2C"
TABLE_HDR = "#7EB8DA"  # bleu Lireka clair (header tableau, pas navy)
TABLE_Y = CARD_Y + CARD_H + 14
TABLE_H = 720 - TABLE_Y - 24


def b2c_page_filter() -> dict:
    """Filtre de page — périmètre Website B2C uniquement."""
    return {
        "name": "canalScopeB2C",
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": "dim_type_commande"}},
                "Property": "canal",
            }
        },
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "d", "Entity": "dim_type_commande", "Type": 0}],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": "d"}},
                                        "Property": "canal",
                                    }
                                }
                            ],
                            "Values": [[{"Literal": {"Value": f"'{B2C_CHANNEL}'"}}]],
                        }
                    }
                }
            ],
        },
    }


def page_filters() -> dict:
    return {
        "filters": [
            date_relative_filter("datePage12m"),
            b2c_page_filter(),
        ]
    }


def country_pl_table(name, x, y, w, h, z) -> dict:
    """Tableau P&L par pays — Top 15 Sales + Rest of the world, tri Sales desc."""
    # Noms ASCII (tiret -) — l'em-dash — provoquait Missing_References côté Desktop.
    # B2C Sort Key dans Values (isHidden non supporté par le schéma PBIR) :
    # colonne en fin de table, largeur 0 — sinon Desktop retombe sur le tri alpha Country.
    sort_key = meas("B2C Sort Key", display="\u200b")
    sort_qr = f"{MESURES}.B2C Sort Key"
    columns = [
        col_disp("dim_pays", "nom_pays_en", "Country"),
        meas("B2C Display - Sales", display="Sales (in EUR)"),
        meas("B2C Display - COGS", display="COGS"),
        meas("B2C Display - Product profit", display="Product profit"),
        meas("B2C Display - Returns and refunds", display="Returns and refunds"),
        meas("B2C Display - Inbound freight", display="Inbound freight"),
        meas("B2C Display - Shipping", display="Shipping"),
        meas("B2C Display - Duties and taxes", display="Duties and taxes"),
        meas("B2C Display - Shipping supplies", display="Shipping supplies"),
        meas("B2C Display - Generic costs", display="Generic costs"),
        meas("B2C Display - Gross profit", display="Gross profit"),
        meas("B2C Display - Revenue YoY %", display="Revenue YoY (%)"),
        meas("B2C Display - GP YoY %", display="Gross Profit YoY (%)"),
        meas("B2C Display - GM YoY bps", display="Gross Margin YoY (bps)"),
        sort_key,
    ]

    def cf(queryref: str, color_measure: str) -> dict:
        return {
            "properties": {"fontColor": solid_measure(color_measure)},
            "selector": {"metadata": queryref},
        }

    cost_cols = [
        "B2C Display - COGS",
        "B2C Display - Returns and refunds",
        "B2C Display - Inbound freight",
        "B2C Display - Shipping",
        "B2C Display - Duties and taxes",
        "B2C Display - Shipping supplies",
        "B2C Display - Generic costs",
    ]
    column_formatting = [cf(f"{MESURES}.{c}", "B2C couleur - cout") for c in cost_cols]
    column_formatting += [
        cf(f"{MESURES}.B2C Display - Product profit", "B2C couleur - profit"),
        cf(f"{MESURES}.B2C Display - Gross profit", "B2C couleur - profit"),
        cf(f"{MESURES}.B2C Display - Revenue YoY %", "B2C couleur - Revenue YoY"),
        cf(f"{MESURES}.B2C Display - GP YoY %", "B2C couleur - Gross Profit YoY"),
        cf(f"{MESURES}.B2C Display - GM YoY bps", "B2C couleur - Gross Margin YoY"),
    ]

    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "tableEx",
            "query": {
                "queryState": {"Values": {"projections": columns}},
                "sortDefinition": {
                    "sort": [
                        {
                            "field": sort_key["field"],
                            "direction": "Descending",
                        }
                    ],
                    "isDefaultSort": True,
                },
            },
            "objects": {
                "columnHeaders": [
                    {
                        "properties": {
                            "fontColor": solid_lit("#FFFFFF"),
                            "backColor": solid_lit(TABLE_HDR),
                            "bold": lit("true"),
                            "fontSize": lit("7D"),
                            "wordWrap": lit("true"),
                            "columnAdjustment": lit("'fitToContent'"),
                            "autoSizeColumnWidth": lit("true"),
                        }
                    },
                    {
                        "properties": {
                            "columnWidth": lit("0D"),
                            "autoSizeColumnWidth": lit("false"),
                            "wordWrap": lit("false"),
                        },
                        "selector": {"metadata": sort_qr},
                    },
                ],
                "values": [
                    {
                        "properties": {
                            "fontSize": lit("7D"),
                            "backColorPrimary": solid_lit(CARDBG),
                            "backColorSecondary": solid_lit(BAND_ROW),
                        }
                    },
                    {
                        "properties": {"wordWrap": lit("false")},
                        "selector": {"metadata": sort_qr},
                    },
                ],
                "columnFormatting": column_formatting,
                "total": prop(
                    {
                        "totals": lit("true"),
                        "fontColor": solid_lit(PRIMARY),
                        "bold": lit("true"),
                        "backColor": solid_lit(BAND_ROW),
                    }
                ),
                "grid": prop({"gridVertical": lit("true"), "gridHorizontal": lit("true")}),
            },
            "visualContainerObjects": {
                "background": prop({"show": lit("true"), "color": solid_lit(CARDBG)}),
                "border": prop(
                    {"show": lit("true"), "color": solid_lit(BORDER), "radius": lit("6D")}
                ),
                "dropShadow": prop({"show": lit("false")}),
                "title": prop(
                    {
                        "show": lit("true"),
                        "text": lit("'Revenue and profitability by country'"),
                        "fontSize": lit("11D"),
                        "bold": lit("true"),
                        "fontColor": solid_lit(PRIMARY),
                    }
                ),
                "stylePreset": prop({"name": lit("'None'")}),
            },
        },
    }


def update_pages_json() -> None:
    pages_meta = REPORT / "definition" / "pages" / "pages.json"
    meta = json.loads(pages_meta.read_text(encoding="utf-8"))
    meta["pageOrder"] = [GV_PAGE_ID, PAGE_ID]
    meta["activePageName"] = PAGE_ID
    pages_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    raise SystemExit(
        "SCRIPT OBSOLETE - execution bloquee.\n"
        "1. Reecrit pageOrder sur 2 entrees : supprimerait 6 des 8 pages.\n"
        "2. shutil.rmtree(VIS) inconditionnel.\n"
        "3. Noms de mesures anterieurs au refactor (GV KPI -> KPI Compact).\n"
        "Le rapport se maintient desormais a la main dans Power BI Desktop.\n"
        "Pour reactiver : corriger les 3 points puis retirer ce garde-fou."
    )
    if LOGO_SRC.exists():
        LOGO_DST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LOGO_SRC, LOGO_DST)
    update_report_json()

    visuals: list[tuple[str, dict]] = []

    # Chrome rail (identique General View)
    visuals.append(("b2c_nav_panel", shape_rect("b2c_nav_panel", 0, 0, NAV_W, 720, 100, NAVBG)))
    visuals.append(("b2c_logo", image_logo("b2c_logo", 27, 8, 161, 163, 110)))
    visuals.append(
        (
            "b2c_rail_footer",
            shape_rect("b2c_rail_footer", 6, 608, 208, 106, 120, RAIL_FOOTER_BG, line=True, radius=4),
        )
    )

    # Slicers rail
    visuals.append(("b2c_slicer_date", slicer_date_range("b2c_slicer_date", 6, 198, 208, 100, 300)))
    visuals.append(
        (
            "b2c_slicer_canal",
            slicer_dropdown(
                "b2c_slicer_canal", 6, 310, 208, 66, 310,
                "dim_type_commande", "canal", "Channel",
            ),
        )
    )
    visuals.append(
        (
            "b2c_slicer_langue",
            slicer_dropdown(
                "b2c_slicer_langue", 6, 388, 208, 66, 320,
                "fact_lignes", "langue_livre", "Language",
            ),
        )
    )

    # KPI cards (mêmes mesures GV — scope B2C via filtre page)
    kpi_specs = [
        ("units", "Ordered units", "GV KPI — Ordered units", "GV sous-titre — Unités", "GV couleur — Unités YoY"),
        ("revenue", "Revenue", "GV KPI — Revenue", "GV sous-titre — Revenue", "GV couleur — Revenue YoY"),
        ("gp", "Gross Profit", "GV KPI — Gross Profit", "GV sous-titre — Gross Profit", "GV couleur — Gross Profit YoY"),
        ("gm", "Gross Margin", "GV KPI — Gross Margin", "GV sous-titre — Gross Margin", "GV couleur — Gross Margin YoY"),
    ]
    for i, (key, title, val_m, sub_m, col_m) in enumerate(kpi_specs):
        x = CX + i * (CARD_W + CARD_GAP)
        for folder, data in kpi_card(key, title, val_m, sub_m, col_m, x, card_index=i):
            branded = json.loads(json.dumps(data).replace("gv_", "b2c_"))
            folder_b2c = folder.replace("gv_", "b2c_")
            branded["name"] = folder_b2c
            visuals.append((folder_b2c, branded))

    # Sous-titre tableau
    visuals.append(
        (
            "b2c_table_subtitle",
            textbox_static(
                "b2c_table_subtitle",
                CX,
                TABLE_Y - 2,
                CW,
                14,
                2999,
                "Data by web channel · current year, figures in EUR · YoY variations vs prior year",
                size=8,
                bold=False,
                color=SUBTXT,
            ),
        )
    )

    # Table pays + footer
    visuals.append(
        ("b2c_table_country", country_pl_table("b2c_table_country", CX, TABLE_Y, CW, TABLE_H, 3000))
    )
    visuals.append(("b2c_footer", footer("b2c_footer", CX, FOOTER_Y, CW, FOOTER_H, 4000)))

    if VIS.exists():
        shutil.rmtree(VIS)
    VIS.mkdir(parents=True, exist_ok=True)
    for folder, data in visuals:
        d = VIS / folder
        d.mkdir(exist_ok=True)
        (d / "visual.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": PAGE_ID,
        "displayName": "Website B2C",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": prop({"color": solid_lit("#FFFFFF"), "transparency": lit("0D")}),
        },
        "filterConfig": page_filters(),
    }
    PAGE.mkdir(parents=True, exist_ok=True)
    (PAGE / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")

    update_pages_json()

    print(f"Website B2C (PAGE A) : {len(visuals)} visuels -> {VIS}")


if __name__ == "__main__":
    main()
