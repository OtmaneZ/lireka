#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere la page Loss analysis (prefixe lo_).

Prefixe lo_ : la_ est pris par Librairie Arthaud (d0e1f2a3...),
loss_ par Top loss makers. Aucun em-dash / point median.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi" / "Lireka_Profitabilite.Report"
PAGE_ID = "a1b2c3d405162738495a6b7c8d9e50"
PAGE = REPORT / "definition" / "pages" / PAGE_ID
VIS = PAGE / "visuals"
PAGES_JSON = REPORT / "definition" / "pages" / "pages.json"
SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/"
    "report/definition/visualContainer/2.9.0/schema.json"
)
SCHEMA_PAGE = (
    "https://developer.microsoft.com/json-schemas/fabric/item/"
    "report/definition/page/2.1.0/schema.json"
)
SCHEMA_PAGES = (
    "https://developer.microsoft.com/json-schemas/fabric/item/"
    "report/definition/pagesMetadata/1.1.0/schema.json"
)

PREFIX = "lo"
MESURES = "_Mesures"
PRIMARY = "#1B3A5C"
NAVBG = "#F4F7FB"
CARDBG = "#FFFFFF"
BORDER = "#D0D7E2"
HEADER_BG = "#E8EDF3"
RAIL_FOOTER_BG = "#EBF0F5"
SUBTXT = "#5A6A7A"
BAND_ROW = "#F4F7FB"
BAR_COLOR = "#C0504D"
DATE_DEFAULT_MONTHS = 12


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def solid_lit(hex_color: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_color}'")}}


def col(entity: str, prop: str, active: bool = False, display: str | None = None) -> dict:
    p = {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": prop,
            }
        },
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }
    if active:
        p["active"] = True
    if display:
        p["displayName"] = display
    return p


def meas(prop: str, display: str | None = None) -> dict:
    p = {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": MESURES}},
                "Property": prop,
            }
        },
        "queryRef": f"{MESURES}.{prop}",
        "nativeQueryRef": prop,
    }
    if display:
        p["displayName"] = display
    return p


def pos(x: float, y: float, w: float, h: float, z: int) -> dict:
    return {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}


def prop(props: dict) -> list:
    return [{"properties": props}]


def vco_bare() -> dict:
    return {
        "background": prop({"show": lit("false")}),
        "border": prop({"show": lit("false")}),
        "dropShadow": prop({"show": lit("false")}),
        "title": prop({"show": lit("false")}),
    }


def vco_card_border() -> dict:
    return vco_bare()


def vco_slicer_panel() -> dict:
    return {
        "background": prop({"show": lit("true"), "color": solid_lit(CARDBG)}),
        "border": prop(
            {"show": lit("true"), "color": solid_lit(BORDER), "radius": lit("4D")}
        ),
        "dropShadow": prop({"show": lit("false")}),
        "title": prop({"show": lit("false")}),
    }


def vco_titled(text: str, font: int = 11) -> dict:
    return {
        "background": prop({"show": lit("true"), "color": solid_lit(CARDBG)}),
        "border": prop(
            {"show": lit("true"), "color": solid_lit(BORDER), "radius": lit("6D")}
        ),
        "dropShadow": prop({"show": lit("false")}),
        "title": prop(
            {
                "show": lit("true"),
                "text": lit(f"'{text}'"),
                "fontSize": lit(f"{font}D"),
                "bold": lit("true"),
                "fontColor": solid_lit(PRIMARY),
            }
        ),
    }


def shape_rect(name: str, x, y, w, h, z, fill, line=False, radius=0) -> dict:
    fill_obj = [
        {"properties": {"show": lit("true")}},
        {
            "properties": {"fillColor": solid_lit(fill), "transparency": lit("0D")},
            "selector": {"id": "default"},
        },
    ]
    if line:
        outline_obj = [
            {"properties": {"show": lit("true")}},
            {
                "properties": {
                    "lineColor": solid_lit(BORDER),
                    "weight": lit("1D"),
                    "transparency": lit("0D"),
                },
                "selector": {"id": "default"},
            },
        ]
    else:
        outline_obj = prop({"show": lit("false")})
    general = {"shapeType": lit("'rectangle'")}
    if radius:
        general["roundEdge"] = lit(f"{radius}D")
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "shape",
            "objects": {
                "general": prop(general),
                "fill": fill_obj,
                "outline": outline_obj,
            },
            "visualContainerObjects": vco_bare(),
        },
    }


def textbox_kpi_header(name: str, x, y, w, h, z, text: str, size: int = 9) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": prop(
                    {
                        "paragraphs": [
                            {
                                "textRuns": [
                                    {
                                        "value": text,
                                        "textStyle": {
                                            "fontWeight": "bold",
                                            "fontSize": f"{size}pt",
                                            "color": PRIMARY,
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                )
            },
            "visualContainerObjects": vco_bare(),
        },
    }


def textbox_static(
    name: str, x, y, w, h, z, text: str, size: int = 8, bold: bool = False
) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": prop(
                    {
                        "paragraphs": [
                            {
                                "textRuns": [
                                    {
                                        "value": text,
                                        "textStyle": {
                                            "fontWeight": "bold" if bold else "normal",
                                            "fontSize": f"{size}pt",
                                            "color": PRIMARY,
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                )
            },
            "visualContainerObjects": vco_bare(),
        },
    }


def image_logo(name: str, x, y, w, h, z) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "image",
            "objects": {
                "general": prop(
                    {
                        "imageUrl": {
                            "expr": {
                                "ResourcePackageItem": {
                                    "PackageName": "RegisteredResources",
                                    "PackageType": 1,
                                    "ItemName": "LirekaLogo.png",
                                }
                            }
                        },
                        "imageScalingType": lit("'Fit'"),
                    }
                )
            },
            "visualContainerObjects": vco_bare(),
        },
    }


def _slicer_header(text: str) -> list:
    return prop(
        {
            "show": lit("true"),
            "text": lit(f"'{text}'"),
            "fontColor": solid_lit(PRIMARY),
            "bold": lit("true"),
            "fontSize": lit("9D"),
        }
    )


def date_relative_filter(name: str = "dateDefault12m") -> dict:
    src = "d"
    col_expr = {
        "Column": {
            "Expression": {"SourceRef": {"Source": src}},
            "Property": "date",
        }
    }
    now_plus_one = {"DateAdd": {"Expression": {"Now": {}}, "Amount": 1, "TimeUnit": 0}}
    lower = {
        "DateSpan": {
            "Expression": {
                "DateAdd": {
                    "Expression": now_plus_one,
                    "Amount": -DATE_DEFAULT_MONTHS,
                    "TimeUnit": 2,
                }
            },
            "TimeUnit": 0,
        }
    }
    upper = {"DateSpan": {"Expression": {"Now": {}}, "TimeUnit": 0}}
    return {
        "name": name,
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": "dim_date"}},
                "Property": "date",
            }
        },
        "type": "RelativeDate",
        "filter": {
            "Version": 2,
            "From": [{"Name": src, "Entity": "dim_date", "Type": 0}],
            "Where": [
                {
                    "Condition": {
                        "Between": {
                            "Expression": col_expr,
                            "LowerBound": lower,
                            "UpperBound": upper,
                        }
                    }
                }
            ],
        },
        "howCreated": "User",
    }


def slicer_date_range(name, x, y, w, h, z) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {"Values": {"projections": [col("dim_date", "date", True)]}}
            },
            "objects": {
                "data": prop({"mode": lit("'Between'")}),
                "header": _slicer_header("Date"),
                "items": prop(
                    {"background": solid_lit(CARDBG), "fontColor": solid_lit(PRIMARY)}
                ),
            },
            "visualContainerObjects": vco_slicer_panel(),
        },
        "filterConfig": {"filters": [date_relative_filter()]},
    }


def slicer_dropdown(name, x, y, w, h, z, entity, prop_name, title) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {"projections": [col(entity, prop_name, True)]}
                }
            },
            "objects": {
                "data": prop({"mode": lit("'Dropdown'")}),
                "header": _slicer_header(title),
                "selection": prop(
                    {
                        "singleSelect": lit("false"),
                        "selectAllCheckboxEnabled": lit("true"),
                    }
                ),
                "items": prop(
                    {"background": solid_lit(CARDBG), "fontColor": solid_lit(PRIMARY)}
                ),
            },
            "visualContainerObjects": vco_slicer_panel(),
        },
    }


def kpi_card(
    key: str,
    title: str,
    val_m: str,
    x: int,
    card_index: int,
    display_units: str = "1D",
    label_precision: str | None = None,
) -> list[tuple[str, dict]]:
    card_y, card_w, card_h, card_hdr = 20, 250, 100, 36
    hdr_y = card_y
    val_y = hdr_y + card_hdr + 4
    sub_y = hdr_y + card_h - 24
    body_z = 1000
    title_z = 9000 + card_index
    content_z = 1100 + card_index
    label_props: dict = {
        "labelDisplayUnits": lit(display_units),
        "color": solid_lit(PRIMARY),
        "fontSize": lit("26D"),
        "bold": lit("true"),
    }
    if label_precision is not None:
        label_props["labelPrecision"] = lit(label_precision)
    pfx = f"{PREFIX}_kpi_{key}"
    return [
        (
            pfx,
            shape_rect(pfx, x, hdr_y, card_w, card_h, body_z, CARDBG, line=True, radius=6),
        ),
        (
            f"{pfx}_hdr",
            shape_rect(
                f"{pfx}_hdr",
                x + 1,
                hdr_y + 1,
                card_w - 2,
                card_hdr,
                body_z + 1,
                HEADER_BG,
                line=False,
            ),
        ),
        (
            f"{pfx}_title",
            textbox_kpi_header(
                f"{pfx}_title", x + 1, hdr_y + 1, card_w - 2, card_hdr, title_z, title, 9
            ),
        ),
        (
            f"{pfx}_val",
            {
                "$schema": SCHEMA,
                "name": f"{pfx}_val",
                "position": pos(x + 8, val_y, card_w - 16, 44, content_z),
                "visual": {
                    "visualType": "card",
                    "query": {"queryState": {"Values": {"projections": [meas(val_m)]}}},
                    "objects": {
                        "labels": prop(label_props),
                        "categoryLabels": prop({"show": lit("false")}),
                    },
                    "visualContainerObjects": vco_card_border(),
                },
            },
        ),
        (
            f"{pfx}_py",
            {
                "$schema": SCHEMA,
                "name": f"{pfx}_py",
                "position": pos(x + 8, sub_y, card_w - 16, 22, content_z + 1),
                "visual": {
                    "visualType": "card",
                    "query": {"queryState": {"Values": {"projections": []}}},
                    "objects": {
                        "labels": prop(
                            {"color": solid_lit(SUBTXT), "fontSize": lit("9D")}
                        ),
                        "categoryLabels": prop({"show": lit("false")}),
                    },
                    "visualContainerObjects": vco_card_border(),
                },
            },
        ),
    ]


def blank_exclude_filter(entity: str, column: str, name: str) -> dict:
    """Filtre visuel : exclure les valeurs vides (meme structure Categorical/Not/null)."""
    return {
        "name": name,
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": column,
            }
        },
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "f", "Entity": entity, "Type": 0}],
            "Where": [
                {
                    "Condition": {
                        "Not": {
                            "Expression": {
                                "Comparison": {
                                    "ComparisonKind": 0,
                                    "Left": {
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {"Source": "f"}
                                            },
                                            "Property": column,
                                        }
                                    },
                                    "Right": {"Literal": {"Value": "null"}},
                                }
                            }
                        }
                    }
                }
            ],
        },
        "howCreated": "User",
    }


def bar_chart_poste(name: str, x, y, w, h, z) -> dict:
    """Barres horizontales : structure Category+Y copiee d'un combo, type clusteredBarChart."""
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "clusteredBarChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            col(
                                "fact_commandes",
                                "poste_basculant",
                                True,
                                "Tipping cost",
                            )
                        ]
                    },
                    "Y": {
                        "projections": [
                            meas("Pertes Totales", display="Total losses")
                        ]
                    },
                },
                "sortDefinition": {
                    "sort": [
                        {
                            "field": meas("Pertes Totales")["field"],
                            # Pertes negatives : Ascendant = |perte| decroissante.
                            "direction": "Ascending",
                        }
                    ]
                },
            },
            "objects": {
                "categoryAxis": prop(
                    {
                        "show": lit("true"),
                        "showAxisTitle": lit("false"),
                        "fontSize": lit("8D"),
                        "concatenateLabels": lit("false"),
                    }
                ),
                "valueAxis": prop(
                    {
                        "show": lit("true"),
                        "showAxisTitle": lit("false"),
                        "fontSize": lit("8D"),
                        "labelDisplayUnits": lit("1000D"),
                        "labelPrecision": lit("1L"),
                    }
                ),
                "legend": prop({"show": lit("false")}),
                "labels": prop(
                    {
                        "show": lit("true"),
                        "labelDisplayUnits": lit("1000D"),
                        "labelPrecision": lit("1L"),
                        "fontSize": lit("7D"),
                        "enableBackground": lit("false"),
                    }
                ),
                "dataPoint": [
                    {
                        "properties": {"fill": solid_lit(BAR_COLOR)},
                        "selector": {"metadata": f"{MESURES}.Pertes Totales"},
                    }
                ],
            },
            "visualContainerObjects": vco_titled("What tips an order into loss", 11),
        },
        "filterConfig": {
            "filters": [
                blank_exclude_filter(
                    "fact_commandes", "poste_basculant", "excludeBlankPoste"
                )
            ]
        },
    }


def combo_tranche(name: str, x, y, w, h, z) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "lineStackedColumnComboChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            col(
                                "fact_commandes",
                                "tranche_panier",
                                True,
                                "Basket size",
                            )
                        ]
                    },
                    "Y": {
                        "projections": [
                            meas("Marge Brute", display="Gross profit")
                        ]
                    },
                    "Y2": {
                        "projections": [
                            meas("Taux Marge Brute", display="Gross margin %")
                        ]
                    },
                },
                "sortDefinition": {
                    "sort": [
                        {
                            "field": col(
                                "fact_commandes", "tranche_panier_ordre"
                            )["field"],
                            "direction": "Ascending",
                        }
                    ]
                },
            },
            "objects": {
                "categoryAxis": prop(
                    {
                        "show": lit("true"),
                        "showAxisTitle": lit("false"),
                        "fontSize": lit("8D"),
                        "concatenateLabels": lit("false"),
                    }
                ),
                "valueAxis": prop(
                    {
                        "show": lit("true"),
                        "showAxisTitle": lit("false"),
                        "fontSize": lit("8D"),
                        "labelDisplayUnits": lit("1000D"),
                        "labelPrecision": lit("1L"),
                    }
                ),
                "legend": prop(
                    {
                        "show": lit("true"),
                        "position": lit("'Top'"),
                        "fontSize": lit("8D"),
                        "showTitle": lit("false"),
                    }
                ),
                "lineStyles": prop(
                    {
                        "strokeWidth": lit("2D"),
                        "showMarker": lit("true"),
                        "markerSize": lit("4D"),
                    }
                ),
                "labels": prop(
                    {
                        "show": lit("true"),
                        "labelDisplayUnits": lit("1000D"),
                        "labelPrecision": lit("1L"),
                        "fontSize": lit("7D"),
                        "enableBackground": lit("false"),
                    }
                ),
                "dataPoint": [
                    {
                        "properties": {"fill": solid_lit("#7EB8DA")},
                        "selector": {"metadata": f"{MESURES}.Marge Brute"},
                    },
                    {
                        "properties": {"fill": solid_lit("#0A2540")},
                        "selector": {"metadata": f"{MESURES}.Taux Marge Brute"},
                    },
                ],
            },
            "visualContainerObjects": vco_titled("Gross margin by basket size", 11),
        },
    }


def detail_table(name: str, x, y, w, h, z) -> dict:
    columns = [
        col("fact_commandes", "poste_basculant", display="Tipping cost"),
        col("dim_type_commande", "canal", display="Channel"),
        meas("Nb Commandes Deficitaires", display="Orders"),
        meas("Pertes Totales", display="Total losses"),
        meas("Perte Moyenne", display="Avg loss"),
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
                            "field": meas("Pertes Totales")["field"],
                            "direction": "Ascending",
                        }
                    ]
                },
            },
            "objects": {
                "columnHeaders": prop(
                    {
                        "fontColor": solid_lit("#FFFFFF"),
                        "backColor": solid_lit(PRIMARY),
                        "bold": lit("true"),
                        "fontSize": lit("8D"),
                        "wordWrap": lit("true"),
                        "columnAdjustment": lit("'fitToContent'"),
                        "autoSizeColumnWidth": lit("true"),
                    }
                ),
                "values": prop(
                    {
                        "fontSize": lit("8D"),
                        "backColorPrimary": solid_lit(CARDBG),
                        "backColorSecondary": solid_lit(BAND_ROW),
                    }
                ),
                "total": prop(
                    {
                        "totals": lit("true"),
                        "fontColor": solid_lit(PRIMARY),
                        "bold": lit("true"),
                    }
                ),
                "grid": prop(
                    {"gridVertical": lit("true"), "gridHorizontal": lit("true")}
                ),
            },
            "visualContainerObjects": {
                **vco_titled("Loss drivers by channel", 11),
                "stylePreset": prop({"name": lit("'None'")}),
            },
        },
        "filterConfig": {
            "filters": [
                blank_exclude_filter(
                    "fact_commandes", "poste_basculant", "excludeBlankPosteTable"
                )
            ]
        },
    }


def page_json() -> dict:
    return {
        "$schema": SCHEMA_PAGE,
        "name": PAGE_ID,
        "displayName": "Loss analysis",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": solid_lit("#FFFFFF"),
                        "transparency": lit("0D"),
                    }
                }
            ]
        },
        "filterConfig": {"filters": [date_relative_filter("datePage12m")]},
    }


def write_visual(folder: str, data: dict) -> None:
    d = VIS / folder
    d.mkdir(parents=True, exist_ok=True)
    path = d / "visual.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def update_pages_json() -> None:
    data = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    order = data.get("pageOrder", [])
    if PAGE_ID not in order:
        order.append(PAGE_ID)
    else:
        order = [p for p in order if p != PAGE_ID] + [PAGE_ID]
    data["pageOrder"] = order
    data["activePageName"] = PAGE_ID
    if "$schema" not in data:
        data["$schema"] = SCHEMA_PAGES
    PAGES_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    PAGE.mkdir(parents=True, exist_ok=True)
    VIS.mkdir(parents=True, exist_ok=True)

    (PAGE / "page.json").write_text(
        json.dumps(page_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    visuals: list[tuple[str, dict]] = []
    visuals.append(
        (
            f"{PREFIX}_nav_panel",
            shape_rect(f"{PREFIX}_nav_panel", 0, 0, 220, 720, 100, NAVBG),
        )
    )
    visuals.append(
        (f"{PREFIX}_logo", image_logo(f"{PREFIX}_logo", 27, 8, 161, 163, 110))
    )
    visuals.append(
        (
            f"{PREFIX}_slicer_date",
            slicer_date_range(f"{PREFIX}_slicer_date", 6, 198, 208, 100, 300),
        )
    )
    visuals.append(
        (
            f"{PREFIX}_slicer_canal",
            slicer_dropdown(
                f"{PREFIX}_slicer_canal",
                6,
                310,
                208,
                66,
                301,
                "dim_type_commande",
                "canal",
                "Channel",
            ),
        )
    )
    visuals.append(
        (
            f"{PREFIX}_rail_footer",
            shape_rect(
                f"{PREFIX}_rail_footer", 6, 608, 208, 106, 120, RAIL_FOOTER_BG, line=True
            ),
        )
    )
    visuals.append(
        (
            f"{PREFIX}_footer",
            textbox_static(
                f"{PREFIX}_footer",
                237,
                702,
                1035,
                16,
                4000,
                "7/2026 - CONFIDENTIEL",
                size=8,
                bold=False,
            ),
        )
    )

    cards = [
        ("orders", "Loss-making orders", "Nb Commandes Deficitaires", 237, "1D", None),
        ("share_orders", "Share of orders", "Part Commandes Deficitaires", 498, "1D", None),
        ("losses", "Total losses", "Pertes Totales", 759, "1D", "0L"),
        ("share_gp", "Share of gross profit", "Part Pertes Marge Brute", 1020, "1D", None),
    ]
    for i, (key, title, measure, x, units, prec) in enumerate(cards):
        visuals.extend(
            kpi_card(key, title, measure, x, i, display_units=units, label_precision=prec)
        )

    visuals.append(
        (
            f"{PREFIX}_chart_poste",
            bar_chart_poste(f"{PREFIX}_chart_poste", 237, 124, 512, 198, 2000),
        )
    )
    visuals.append(
        (
            f"{PREFIX}_chart_tranche",
            combo_tranche(f"{PREFIX}_chart_tranche", 760, 124, 512, 198, 2100),
        )
    )
    visuals.append(
        (
            f"{PREFIX}_table_drivers",
            detail_table(f"{PREFIX}_table_drivers", 237, 332, 1035, 364, 3000),
        )
    )

    # Nettoyage dossiers orphelins du prefixe
    if VIS.exists():
        for child in list(VIS.iterdir()):
            if child.is_dir() and child.name.startswith(f"{PREFIX}_"):
                for f in child.glob("*"):
                    f.unlink()
                child.rmdir()

    for folder, data in visuals:
        write_visual(folder, data)

    update_pages_json()
    print(f"Page {PAGE_ID} : {len(visuals)} visuels ecrits (prefixe {PREFIX}_).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
