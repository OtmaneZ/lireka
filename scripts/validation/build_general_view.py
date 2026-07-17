"""Génère la page « General View » — version finale native (mockup Finance 20260716).

Grille : 4 KPI · 2 charts côte à côte · table large · footer
Rail #F4F7FB · slicers habillés · bas de rail vide
Charts : CY empilé par canal + ligne PY · couleurs mockup · labels · YoY
Axe : mensuel court EN (dim_date[mois_annee_court_en], ex. Jul 25) — ~12 barres lisibles
Périmètre : 3 canaux e-commerce (filtre de page) — B2C / B2B / Marketplaces
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi" / "Lireka_Profitabilite.Report"
PAGE_ID = "7112a69a17fbef2de240"
PAGE = REPORT / "definition" / "pages" / PAGE_ID
VIS = PAGE / "visuals"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"

LOGO_SRC = (
    ROOT
    / "Power_BI_Datawarehouse"
    / "Dashboards_transporteurs"
    / "UPS Dashboard PowerBI"
    / "03_Documentation"
    / "Logo de la startup Lireka.png"
)
LOGO_DST = REPORT / "StaticResources" / "RegisteredResources" / "LirekaLogo.png"

# Charte
PRIMARY = "#1B3A5C"
NAVBG = "#F4F7FB"
CARDBG = "#FFFFFF"
BORDER = "#D0D7E2"
HEADER_BG = "#E8EDF3"  # bandeau titre KPI + bandes tableau
TITLE_HDR_BG = HEADER_BG  # gris clair validé (pas navy)
TITLE_HDR_FG = PRIMARY  # titre KPI gris foncé / navy
RAIL_FOOTER_BG = "#EBF0F5"
SUBTXT = "#5A6A7A"
GOOD = "#6FA84B"
BAD = "#C0504D"
BAND_ROW = "#F4F7FB"
PY_LINE = "#7F8C99"  # ligne PY — gris ardoise, pour ne pas retomber sur la palette par défaut

# Période par défaut du slicer Date : 12 derniers mois (relative date, glissant).
DATE_DEFAULT_MONTHS = 12

# Layout 1280×720
NAV_W = 220
CX = 237
CW = 1035
CARD_W = 250
CARD_GAP = 11
CARD_Y = 20
CARD_H = 100
CARD_HDR = 36
CHART_Y = 124
CHART_H = 198
CHART_GAP = 11
CHART_W = (CW - CHART_GAP) // 2
TABLE_Y = CHART_Y + CHART_H + 10
TABLE_H = 720 - TABLE_Y - 24
FOOTER_Y = 702
FOOTER_H = 16

MESURES = "_Mesures"

# Périmètre General View : 3 canaux e-commerce (couleurs strictes mockup).
# Librairie Arthaud / Autre exclus via filtre de page (channel_page_filter).
CHANNELS = ["Website B2C", "Website B2B", "Marketplaces"]
CHANNEL_COLORS = {
    "Website B2C": "#7EB8DA",
    "Website B2B": "#0A2540",
    "Marketplaces": "#F79646",
}


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def solid_lit(hex_color: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_color}'")}}


def solid_measure(prop: str) -> dict:
    return {
        "solid": {
            "color": {
                "expr": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Entity": MESURES}},
                        "Property": prop,
                    }
                }
            }
        }
    }


def col(entity: str, prop: str, active: bool = False) -> dict:
    # nativeQueryRef requis : sans lui, une colonne mesure d'un tableEx est
    # silencieusement ignorée (seul l'en-tête du 1er champ apparaît).
    p = {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }
    if active:
        p["active"] = True
    return p


def meas(prop: str, entity: str = MESURES, display: str | None = None) -> dict:
    p = {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }
    if display:
        p["displayName"] = display
    return p


def col_disp(entity: str, prop: str, display: str | None = None, active: bool = False) -> dict:
    p = col(entity, prop, active)
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


def vco_card_border(radius: int = 6) -> dict:
    return {
        "background": prop({"show": lit("false")}),
        "border": prop({"show": lit("false")}),
        "dropShadow": prop({"show": lit("false")}),
        "title": prop({"show": lit("false")}),
    }


def vco_slicer_panel() -> dict:
    return {
        "background": prop({"show": lit("true"), "color": solid_lit(CARDBG)}),
        "border": prop({"show": lit("true"), "color": solid_lit(BORDER), "radius": lit("4D")}),
        "dropShadow": prop({"show": lit("false")}),
        "title": prop({"show": lit("false")}),
    }


def vco_titled(text: str, font: int = 12) -> dict:
    return {
        "background": prop({"show": lit("true"), "color": solid_lit(CARDBG)}),
        "border": prop({"show": lit("true"), "color": solid_lit(BORDER), "radius": lit("6D")}),
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
    """Rectangle plein — visualType « shape » (nouvelles formes, avril 2021+).

    IMPORTANT : les nouvelles formes exigent un état « default » (comme les
    boutons). Sans l'entrée { selector.id = "default" }, le fillColor est ignoré
    et Power BI applique le remplissage BLEU par défaut de la forme.
    """
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
    """Titre KPI — texte gris foncé ; le fond gris est porté par la shape *_hdr."""
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
                                            "color": TITLE_HDR_FG,
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                )
            },
            "visualContainerObjects": {
                "background": prop({"show": lit("false")}),
                "border": prop({"show": lit("false")}),
                "dropShadow": prop({"show": lit("false")}),
                "title": prop({"show": lit("false")}),
            },
        },
    }


def textbox_static(
    name: str, x, y, w, h, z, text: str, size: int = 9, bold: bool = True, color: str = PRIMARY
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
                                            "color": color,
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


def slicer_dropdown(name, x, y, w, h, z, entity, prop_name, title, single=False) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [col(entity, prop_name, True)]}}},
            "objects": {
                "data": prop({"mode": lit("'Dropdown'")}),
                "header": _slicer_header(title),
                "selection": prop(
                    {
                        "singleSelect": lit("true" if single else "false"),
                        "selectAllCheckboxEnabled": lit("false" if single else "true"),
                    }
                ),
                "items": prop(
                    {
                        "background": solid_lit(CARDBG),
                        "fontColor": solid_lit(PRIMARY),
                    }
                ),
            },
            "visualContainerObjects": vco_slicer_panel(),
        },
    }


def date_relative_filter(name: str = "dateDefault12m") -> dict:
    """Filtre relative date — 12 derniers mois glissants (page ou slicer)."""
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


def date_default_selection() -> dict:
    """Sélection initiale du slicer — 12 derniers mois (relative date)."""
    return {"filters": [date_relative_filter()]}


def page_filters() -> dict:
    """Filtres de page — date 12 mois + périmètre 3 canaux.

    Le filtre date DOIT être au niveau page : un filterConfig sur le slicer
    seul ne propage pas aux charts/table à l'ouverture du rapport.
    """
    return {
        "filters": [
            date_relative_filter("datePage12m"),
            channel_page_filter()["filters"][0],
        ]
    }


def slicer_date_range(name, x, y, w, h, z) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [col("dim_date", "date", True)]}}},
            "objects": {
                "data": prop({"mode": lit("'Between'")}),
                "header": _slicer_header("Date"),
                "items": prop(
                    {
                        "background": solid_lit(CARDBG),
                        "fontColor": solid_lit(PRIMARY),
                    }
                ),
            },
            "visualContainerObjects": vco_slicer_panel(),
        },
        "filterConfig": date_default_selection(),
    }


def month_axis() -> dict:
    """Axe mensuel court EN — ~12 points lisibles (Jul 25, Aug 25…)."""
    return col("dim_date", "mois_annee_court_en", True)


def channel_page_filter() -> dict:
    """Filtre de page — restreint le périmètre aux 3 canaux e-commerce.

    Écarte Librairie Arthaud / Autre : légende propre à 3 canaux, plus de gris,
    table = B2C / B2B / Marketplaces + TOTAL cohérent avec les cartes KPI.
    """
    return {
        "filters": [
            {
                "name": "canalScopeGeneralView",
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
                                    "Values": [
                                        [{"Literal": {"Value": f"'{c}'"}}] for c in CHANNELS
                                    ],
                                }
                            }
                        }
                    ],
                },
            }
        ]
    }


def series_color_data_points(entity: str, prop: str, mapping: dict) -> list:
    out = []
    for label, hex_c in mapping.items():
        out.append(
            {
                "properties": {"fill": solid_lit(hex_c)},
                "selector": {
                    "data": [
                        {
                            "scopeId": {
                                "Comparison": {
                                    "ComparisonKind": 0,
                                    "Left": {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Entity": entity}},
                                            "Property": prop,
                                        }
                                    },
                                    "Right": {"Literal": {"Value": f"'{label}'"}},
                                }
                            }
                        }
                    ]
                },
            }
        )
    return out


def combo_by_channel(
    name,
    x,
    y,
    w,
    h,
    z,
    y_measure,
    y_py_measure,
    title,
    show_legend: bool,
) -> dict:
    """Combo CY (colonnes empilées par canal) + PY (ligne), axe = mois."""
    data_points = series_color_data_points("dim_type_commande", "canal", CHANNEL_COLORS)
    data_points.append(
        {
            "properties": {"fill": solid_lit(PY_LINE)},
            "selector": {"metadata": f"{MESURES}.{y_py_measure}"},
        }
    )
    py_line = meas(y_py_measure, display="PY")
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": pos(x, y, w, h, z),
        "visual": {
            "visualType": "lineStackedColumnComboChart",
            "query": {
                "queryState": {
                    "Category": {"projections": [month_axis()]},
                    "Series": {"projections": [col_disp("dim_type_commande", "canal", "Channel")]},
                    "Y": {"projections": [meas(y_measure)]},
                    "Y2": {"projections": [py_line]},
                },
                "sortDefinition": {
                    "sort": [
                        {
                            "field": col("dim_date", "annee_mois")["field"],
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
                        "labelDisplayUnits": lit("1000000D"),
                        "labelPrecision": lit("1L"),
                    }
                ),
                "legend": prop(
                    {
                        "show": lit("true" if show_legend else "false"),
                        "position": lit("'Top'"),
                        "fontSize": lit("8D"),
                        "showTitle": lit("false"),
                    }
                ),
                "lineStyles": prop(
                    {"strokeWidth": lit("2D"), "showMarker": lit("true"), "markerSize": lit("4D")}
                ),
                "labels": prop(
                    {
                        "show": lit("true"),
                        "labelDisplayUnits": lit("1000000D"),
                        "labelPrecision": lit("1L"),
                        "fontSize": lit("7D"),
                        "enableBackground": lit("false"),
                    }
                ),
                "dataPoint": data_points,
            },
            "visualContainerObjects": vco_titled(title, font=11),
        },
    }


def kpi_card(
    key: str,
    title: str,
    val_m: str,
    sub_m: str,
    col_m: str,
    x: int,
    card_index: int,
) -> list[tuple[str, dict]]:
    """Carte KPI : bordure blanche · bandeau gris clair · valeur · PY.

    z-index : corps de carte fixe (1000), contenu (1100+i), titres (9000+i).
    Les titres passent au-dessus de toutes les cartes — évite le rognage quand
    chaque carte incrémentait z et les shapes recouvraient les textbox voisins.
    """
    hdr_y = CARD_Y
    val_y = hdr_y + CARD_HDR + 4
    sub_y = hdr_y + CARD_H - 24
    body_z = 1000
    title_z = 9000 + card_index
    content_z = 1100 + card_index
    label_props: dict = {
        "labelDisplayUnits": lit("1D"),
        "color": solid_lit(PRIMARY),
        "fontSize": lit("26D"),
        "bold": lit("true"),
    }
    return [
        (
            f"gv_kpi_{key}",
            shape_rect(f"gv_kpi_{key}", x, hdr_y, CARD_W, CARD_H, body_z, CARDBG, line=True, radius=6),
        ),
        # Bandeau gris en shape (évite le bleu navy par défaut si le fond textbox est ignoré).
        (
            f"gv_kpi_{key}_hdr",
            shape_rect(
                f"gv_kpi_{key}_hdr",
                x + 1,
                hdr_y + 1,
                CARD_W - 2,
                CARD_HDR,
                body_z + 1,
                TITLE_HDR_BG,
                line=False,
                radius=0,
            ),
        ),
        (
            f"gv_kpi_{key}_title",
            textbox_kpi_header(
                f"gv_kpi_{key}_title", x + 1, hdr_y + 1, CARD_W - 2, CARD_HDR, title_z, title, size=9
            ),
        ),
        (
            f"gv_kpi_{key}_val",
            {
                "$schema": SCHEMA,
                "name": f"gv_kpi_{key}_val",
                "position": pos(x + 8, val_y, CARD_W - 16, 44, content_z),
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
            f"gv_kpi_{key}_py",
            {
                "$schema": SCHEMA,
                "name": f"gv_kpi_{key}_py",
                "position": pos(x + 8, sub_y, CARD_W - 16, 22, content_z + 1),
                "visual": {
                    "visualType": "card",
                    "query": {"queryState": {"Values": {"projections": [meas(sub_m)]}}},
                    "objects": {
                        "labels": prop(
                            {
                                "color": solid_measure(col_m),
                                "fontSize": lit("9D"),
                                "horizontalAlignment": lit("'left'"),
                            }
                        ),
                        "categoryLabels": prop({"show": lit("false")}),
                    },
                    "visualContainerObjects": vco_card_border(),
                },
            },
        ),
    ]


def kpi_table(name, x, y, w, h, z) -> dict:
    # Libellés anglais (V1 Marc) · tri mockup B2C → B2B → MP via dim_type_commande.ordre_gv
    columns = [
        col_disp("dim_type_commande", "canal", "Channel"),
        meas("Nb Commandes", display="Orders"),
        meas("GV Display — Ordered units", display="Ordered units"),
        meas("Unités commandées YoY %", display="Units YoY%"),
        meas("Taux Annulation", display="Cancellation rate"),
        meas("Taux Annulation YoY bps", display="Cancellation rate YoY bps"),
        meas("GV Display — Revenue", display="Revenue"),
        meas("GV Display — YoY€", display="YoY€"),
        meas("Revenu (reconstruit) YoY %", display="YoY%"),
        meas("GV Display — Gross Profit", display="Gross Profit"),
        meas("Marge Brute YoY %", display="Gross Profit YoY%"),
        meas("Taux Marge Brute (revenu reconstruit)", display="Gross Margin"),
        meas("Taux Marge Brute (revenu reconstruit) YoY bps", display="Gross Margin YoY bps"),
    ]

    def cf(queryref: str, color_measure: str | None = None) -> dict:
        props: dict = {}
        if color_measure:
            props["fontColor"] = solid_measure(color_measure)
        return {"properties": props, "selector": {"metadata": queryref}}

    column_formatting = [
        cf(f"{MESURES}.Unités commandées YoY %", "GV couleur — Unités YoY"),
        cf(f"{MESURES}.Taux Annulation YoY bps", "GV couleur — Cancellation YoY"),
        cf(f"{MESURES}.GV Display — YoY€", "GV couleur — Revenue YoY"),
        cf(f"{MESURES}.Revenu (reconstruit) YoY %", "GV couleur — Revenue YoY"),
        cf(f"{MESURES}.Marge Brute YoY %", "GV couleur — Gross Profit YoY"),
        cf(
            f"{MESURES}.Taux Marge Brute (revenu reconstruit) YoY bps",
            "GV couleur — Gross Margin YoY",
        ),
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
                            "field": col("dim_type_commande", "ordre_gv")["field"],
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
                "columnFormatting": column_formatting,
                "total": prop(
                    {"totals": lit("true"), "fontColor": solid_lit(PRIMARY), "bold": lit("true")}
                ),
                "grid": prop({"gridVertical": lit("true"), "gridHorizontal": lit("true")}),
            },
            "visualContainerObjects": {
                **vco_titled(
                    "Units, revenue and profitability by sales channel — KPI summary", font=11
                ),
                # Sans stylePreset None, le preset par défaut écrase les couleurs custom.
                "stylePreset": prop({"name": lit("'None'")}),
            },
        },
    }


def footer(name, x, y, w, h, z) -> dict:
    return textbox_static(name, x, y, w, h, z, "7/2026 · CONFIDENTIEL", size=8, bold=False)


def update_report_json() -> None:
    path = REPORT / "definition" / "report.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for pkg in data["resourcePackages"]:
        if pkg.get("name") == "RegisteredResources":
            items = pkg["items"]
            if not any(i.get("name") == "LirekaLogo.png" for i in items):
                items.append({"name": "LirekaLogo.png", "path": "LirekaLogo.png", "type": "Image"})
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    if LOGO_SRC.exists():
        LOGO_DST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LOGO_SRC, LOGO_DST)
    update_report_json()

    visuals: list[tuple[str, dict]] = []

    # Chrome
    visuals.append(("gv_nav_panel", shape_rect("gv_nav_panel", 0, 0, NAV_W, 720, 100, NAVBG)))
    visuals.append(("gv_logo", image_logo("gv_logo", 27, 8, 161, 163, 110)))
    visuals.append(
        ("gv_rail_footer", shape_rect("gv_rail_footer", 6, 608, 208, 106, 120, RAIL_FOOTER_BG, line=True, radius=4))
    )
    # V1 tout anglais — pas de toggle FR/EN (_ParamLangueUI = V2 bilingue Marc).

    # Slicers rail (habillés)
    visuals.append(("gv_slicer_date", slicer_date_range("gv_slicer_date", 6, 198, 208, 100, 300)))
    visuals.append(
        (
            "gv_slicer_canal",
            slicer_dropdown(
                "gv_slicer_canal", 6, 310, 208, 66, 310,
                "dim_type_commande", "canal", "Channel",
            ),
        )
    )
    visuals.append(
        (
            "gv_slicer_langue",
            slicer_dropdown(
                "gv_slicer_langue", 6, 388, 208, 66, 320,
                "fact_lignes", "langue_livre", "Language",
            ),
        )
    )
    # Note : plus de slicer « Granularité ». L'axe des charts est mensuel court EN
    # (mois_annee_court_en) pour ~12 barres lisibles sur 12 mois glissants.

    # KPI cards — mesures GV KPI avec format compact modèle (€11.2M / 521.6k)
    kpi_specs = [
        ("units", "Ordered units", "GV KPI — Ordered units", "GV sous-titre — Unités", "GV couleur — Unités YoY"),
        ("revenue", "Revenue", "GV KPI — Revenue", "GV sous-titre — Revenue", "GV couleur — Revenue YoY"),
        ("gp", "Gross Profit", "GV KPI — Gross Profit", "GV sous-titre — Gross Profit", "GV couleur — Gross Profit YoY"),
        ("gm", "Gross Margin", "GV KPI — Gross Margin", "GV sous-titre — Gross Margin", "GV couleur — Gross Margin YoY"),
    ]
    for i, (key, title, val_m, sub_m, col_m) in enumerate(kpi_specs):
        x = CX + i * (CARD_W + CARD_GAP)
        visuals.extend(kpi_card(key, title, val_m, sub_m, col_m, x, card_index=i))

    # Charts côte à côte
    visuals.append(
        (
            "gv_chart_revenue",
            combo_by_channel(
                "gv_chart_revenue", CX, CHART_Y, CHART_W, CHART_H, 2000,
                "Revenu (reconstruit)", "Revenu (reconstruit) PY",
                "Revenue by sales channel", show_legend=True,
            ),
        )
    )
    visuals.append(
        (
            "gv_chart_gp",
            combo_by_channel(
                "gv_chart_gp", CX + CHART_W + CHART_GAP, CHART_Y, CHART_W, CHART_H, 2100,
                "Marge Brute", "Marge Brute PY",
                "Gross Profit by sales channel", show_legend=False,
            ),
        )
    )

    # Table + footer
    visuals.append(("gv_table_channel", kpi_table("gv_table_channel", CX, TABLE_Y, CW, TABLE_H, 3000)))
    visuals.append(("gv_footer", footer("gv_footer", CX, FOOTER_Y, CW, FOOTER_H, 4000)))

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
        "displayName": "General View",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": prop({"color": solid_lit("#FFFFFF"), "transparency": lit("0D")}),
        },
        "filterConfig": page_filters(),
    }
    (PAGE / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")

    pages_meta = REPORT / "definition" / "pages" / "pages.json"
    meta = json.loads(pages_meta.read_text(encoding="utf-8"))
    order = [p for p in meta.get("pageOrder", []) if p != PAGE_ID]
    meta["pageOrder"] = [PAGE_ID] + order
    meta["activePageName"] = PAGE_ID
    pages_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"General View (native v2) : {len(visuals)} visuels -> {VIS}")


if __name__ == "__main__":
    main()
