"""Génère les visual.json du rapport L04 (PBIP)."""
from __future__ import annotations

import json
from pathlib import Path

PAGE = Path(__file__).resolve().parents[2] / "powerbi" / "Lireka_Profitabilite.Report" / "definition" / "pages" / "7112a69a17fbef2de240"
VIS = PAGE / "visuals"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"


def col(entity: str, prop: str, active: bool = False) -> dict:
    p = {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
    }
    if active:
        p["active"] = True
    return p


def meas(entity: str, prop: str) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
    }


def title_vco(text: str) -> dict:
    return {
        "background": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F4F7FB'"}}}}},
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#D0D7E2'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "6D"}}},
                }
            }
        ],
        "dropShadow": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
        "title": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{text}'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B3A5C'"}}}}},
                }
            }
        ],
    }


def bar_chart(name: str, x: int, y: int, w: int, h: int, z: int, entity: str, cat: str, measure: str, title: str) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": {
            "visualType": "clusteredBarChart",
            "query": {
                "queryState": {
                    "Category": {"projections": [col(entity, cat, True)]},
                    "Y": {"projections": [meas("_Mesures", measure)]},
                },
                "sortDefinition": {
                    "sort": [{"field": meas("_Mesures", measure), "direction": "Descending"}]
                },
            },
            "objects": {
                "categoryAxis": [
                    {
                        "properties": {
                            "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                        }
                    }
                ],
                "valueAxis": [
                    {
                        "properties": {
                            "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                            "show": {"expr": {"Literal": {"Value": "false"}}},
                        }
                    }
                ],
                "labels": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "labelPrecision": {"expr": {"Literal": {"Value": "0L"}}},
                            "enableValueDataLabel": {"expr": {"Literal": {"Value": "true"}}},
                            "labelDisplayUnits": {"expr": {"Literal": {"Value": "1D"}}},
                        }
                    }
                ],
            },
            "visualContainerObjects": title_vco(title),
        },
    }


def donut(name: str, x: int, y: int, w: int, h: int, z: int, entity: str, cat: str, measure: str, title: str) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": {
            "visualType": "donutChart",
            "query": {
                "queryState": {
                    "Category": {"projections": [col(entity, cat, True)]},
                    "Y": {"projections": [meas("_Mesures", measure)]},
                },
            },
            "objects": {
                "labels": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "labelStyle": {"expr": {"Literal": {"Value": "'Data value, percent of total'"}}},
                            "labelPrecision": {"expr": {"Literal": {"Value": "1L"}}},
                        }
                    }
                ],
            },
            "visualContainerObjects": title_vco(title),
        },
    }


def card(name: str, x: int, y: int, w: int, h: int, z: int, measure: str, title: str) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {"projections": [meas("_Mesures", measure)]},
                },
            },
            "visualContainerObjects": title_vco(title),
        },
    }


def textbox(name: str, x: int, y: int, w: int, h: int, z: int, text: str) -> dict:
    return {
        "$schema": SCHEMA,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontWeight": "bold",
                                                "fontSize": "13pt",
                                                "color": "#DC3545",
                                            },
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                ],
            },
            "visualContainerObjects": {
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFF3CD'"}}}}},
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFC107'"}}}}},
                            "radius": {"expr": {"Literal": {"Value": "6D"}}},
                        }
                    }
                ],
                "dropShadow": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
            },
        },
    }


def main() -> None:
    visuals = [
        ("l04v_transporteur", bar_chart("l04v_transporteur", 20, 20, 610, 320, 1000, "dim_transporteur", "transporteur", "Nb Colis", "Volumes par transporteur")),
        ("l04v_source_cout", donut("l04v_source_cout", 650, 20, 300, 320, 2000, "fact_transport", "source_cout", "Nb Colis", "Répartition coût (source_cout)")),
        ("l04v_taux_ecart", card("l04v_taux_ecart", 970, 20, 290, 150, 3000, "Taux Écart Coût", "Taux écart coût transport")),
        ("l04v_placeholder_marge", textbox("l04v_placeholder_marge", 970, 190, 290, 150, 4000, "Marge Brute — EN ATTENTE VALIDATION MARC")),
        ("l04v_pays", bar_chart("l04v_pays", 20, 360, 610, 340, 5000, "dim_pays", "nom_pays", "Nb Commandes", "Commandes par pays")),
        ("l04v_type_commande", bar_chart("l04v_type_commande", 650, 360, 610, 340, 6000, "dim_type_commande", "type_commande", "Nb Commandes", "Commandes par type")),
    ]

    VIS.mkdir(parents=True, exist_ok=True)
    for folder, data in visuals:
        d = VIS / folder
        d.mkdir(exist_ok=True)
        (d / "visual.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": "7112a69a17fbef2de240",
        "displayName": "1 - Profitabilité (volumes)",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                    }
                }
            ],
        },
    }
    (PAGE / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Créé {len(visuals)} visuels dans {VIS}")


if __name__ == "__main__":
    main()
