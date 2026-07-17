"""Pré-check dashboards : grain item×group + couverture FX marketplace."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\Otmane\Documents\lireka\Power_BI_Datawarehouse\Données_Backend")
OUT = Path(__file__).with_name("pre_dashboard_checks_output.json")

MARKETPLACE_PREFIXES = (
    "AMAZON",
    "CULTURA",
    "RAKUTEN",
    "FNAC",
)


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def is_marketplace(series: pd.Series) -> pd.Series:
    u = series.astype(str).str.upper()
    mask = pd.Series(False, index=series.index)
    for p in MARKETPLACE_PREFIXES:
        mask |= u.str.startswith(p)
    return mask


def main() -> None:
    out: dict = {"root": str(ROOT), "files": {}}

    for name in (
        "customer_order.csv",
        "customer_order_item.csv",
        "customer_order_item_group.csv",
    ):
        p = ROOT / name
        st = p.stat()
        out["files"][name] = {
            "bytes": st.st_size,
            "mtime": pd.Timestamp(st.st_mtime, unit="s").isoformat(),
        }

    # ------------------------------------------------------------------
    # 1) Grain item × group
    # ------------------------------------------------------------------
    items = pd.read_csv(
        ROOT / "customer_order_item.csv",
        usecols=["id", "order_id", "item_group_id", "product_cost_eur"],
        dtype={"id": "Int64", "order_id": "Int64", "item_group_id": "Int64"},
        low_memory=False,
    )
    groups = pd.read_csv(
        ROOT / "customer_order_item_group.csv",
        usecols=[
            "id",
            "quantity",
            "list_price_eur",
            "customer_price_per_item_eur",
        ],
        dtype={"id": "Int64"},
        low_memory=False,
    )

    n_items = len(items)
    n_groups = len(groups)
    dup_group_ids = int(groups["id"].duplicated().sum())

    joined = items.merge(
        groups,
        left_on="item_group_id",
        right_on="id",
        how="left",
        suffixes=("", "_grp"),
        validate="m:1",  # raises if group id not unique → fan-out
    )

    orphan_items = int(joined["id_grp"].isna().sum()) if "id_grp" in joined.columns else int(
        joined["quantity"].isna().sum()
    )
    # after merge, group id column from right may be named id_y
    right_id_col = "id_y" if "id_y" in joined.columns else ("id_grp" if "id_grp" in joined.columns else None)
    if right_id_col:
        orphan_items = int(joined[right_id_col].isna().sum())

    price = num(joined["customer_price_per_item_eur"]).fillna(0)
    list_p = num(joined["list_price_eur"]).fillna(0)
    qty_g = num(joined["quantity"]).fillna(0)

    # Double-count trap: SUM(quantity_groupe) without MAX-by-group
    sum_qty_naive = float(qty_g.sum())
    sum_qty_correct = float(
        joined.groupby("item_group_id", dropna=False)["quantity"].max().fillna(0).sum()
    )

    out["grain_item_x_group"] = {
        "n_items": n_items,
        "n_groups": n_groups,
        "dup_group_ids": dup_group_ids,
        "joined_rows": len(joined),
        "orphan_items_no_group": orphan_items,
        "grain_preserved": len(joined) == n_items and dup_group_ids == 0,
        "join_cardinality": "m:1 (item → group) — validated by pandas merge(validate='m:1')",
        "customer_price_per_item_eur_zero_pct": round(100 * float((price == 0).mean()), 3),
        "list_price_eur_zero_pct": round(100 * float((list_p == 0).mean()), 3),
        "trap_SUM_quantity_groupe_naive": sum_qty_naive,
        "control_SUM_MAX_quantity_by_group": sum_qty_correct,
        "note": (
            "Prix groupe dupliqués sur chaque article physique : SUM(customer_price_per_item_eur) "
            "est correct si le champ = prix unitaire ; SUM(quantity_groupe) double-compte "
            "(mesure contrôle utilise MAX par item_group_id)."
        ),
    }

    # ------------------------------------------------------------------
    # CA grain commande — indépendant du join item×group
    # ------------------------------------------------------------------
    co = pd.read_csv(
        ROOT / "customer_order.csv",
        usecols=[
            "id",
            "source",
            "state",
            "order_amount_eur",
            "order_amount_local",
            "shipping_fee_eur",
            "shipping_fee_local",
            "origin_created",
            "destination_country",
        ],
        low_memory=False,
    )
    co["order_amount_eur"] = num(co["order_amount_eur"]).fillna(0)
    co["order_amount_local"] = num(co["order_amount_local"]).fillna(0)
    co["shipping_fee_eur"] = num(co["shipping_fee_eur"]).fillna(0)
    co["shipping_fee_local"] = num(co["shipping_fee_local"]).fillna(0)
    co["origin_created"] = pd.to_datetime(co["origin_created"], errors="coerce", utc=True)
    co["ym"] = co["origin_created"].dt.strftime("%Y-%m")
    co["is_mp"] = is_marketplace(co["source"])

    # Sample: 1 month × 1 country (FR, latest full month with data)
    fr = co[co["destination_country"].astype(str).str.upper() == "FR"].copy()
    month_counts = fr["ym"].value_counts().sort_index()
    sample_month = month_counts.index[-1] if len(month_counts) else None
    sample = fr[fr["ym"] == sample_month] if sample_month else fr.iloc[0:0]

    ca_natif_sample = float(sample["order_amount_eur"].sum())
    ca_natif_total = float(co["order_amount_eur"].sum())
    ca_hors_cancelled = float(co.loc[co["state"].astype(str) != "CANCELLED", "order_amount_eur"].sum())

    # CA ligne (contrôle) vs CA commande — pour montrer que le grain article n'alimente pas Revenue
    ca_ligne = float(price.sum())
    ca_ligne_nonzero = float(price[price > 0].sum())

    out["ca_independence_from_item_group"] = {
        "published_CA_uses": "fact_commandes[ca_ht] / ca_ht_reconstruit — grain commande",
        "SUM_order_amount_eur_total": ca_natif_total,
        "SUM_order_amount_eur_hors_CANCELLED": ca_hors_cancelled,
        "SUM_customer_price_per_item_eur_all_items": ca_ligne,
        "SUM_customer_price_per_item_eur_nonzero_only": ca_ligne_nonzero,
        "ecart_ligne_vs_commande_attendu": "large — prix ligne ~94% à 0 (limite ETF doc)",
        "sample": {
            "country": "FR",
            "month": sample_month,
            "n_orders": int(len(sample)),
            "SUM_order_amount_eur": ca_natif_sample,
            "expected_delta_before_after_item_group_reactivation": 0,
            "rationale": (
                "Réactivation item×group n'écrit pas dans fact_commandes ; "
                "[CA Total HT], [CA HT Net Annulation], [Revenue] inchangés. "
                "Écart attendu avant/après = 0 sur tout échantillon grain commande."
            ),
        },
    }

    # ------------------------------------------------------------------
    # 2) FX marketplace coverage (fresh snapshot)
    # ------------------------------------------------------------------
    def coverage(df: pd.DataFrame) -> dict:
        n = len(df)
        if n == 0:
            return {"n": 0}
        se = df["shipping_fee_eur"] > 0
        sl = df["shipping_fee_local"] > 0
        oe = df["order_amount_eur"] > 0
        ol = df["order_amount_local"] > 0
        return {
            "n": n,
            "shipping_fee_eur_gt0": int(se.sum()),
            "shipping_fee_eur_gt0_pct": round(100 * float(se.mean()), 3),
            "shipping_fee_eur_sum": round(float(df["shipping_fee_eur"].sum()), 2),
            "shipping_fee_local_gt0": int(sl.sum()),
            "shipping_fee_local_gt0_pct": round(100 * float(sl.mean()), 3),
            "order_amount_eur_gt0": int(oe.sum()),
            "order_amount_eur_gt0_pct": round(100 * float(oe.mean()), 3),
            "order_amount_eur_sum": round(float(df["order_amount_eur"].sum()), 2),
            "order_amount_local_gt0": int(ol.sum()),
            "order_amount_local_gt0_pct": round(100 * float(ol.mean()), 3),
        }

    mp = co[co["is_mp"]]
    non_mp = co[~co["is_mp"]]

    by_type = (
        co.assign(type_u=co["source"].astype(str).str.upper())
        .groupby("type_u", dropna=False)
        .apply(coverage, include_groups=False)
        .to_dict()
    )

    # Focus channels
    focus = {}
    for key, df in co.groupby(co["source"].astype(str).str.upper()):
        if any(str(key).startswith(p) for p in MARKETPLACE_PREFIXES):
            focus[str(key)] = coverage(df)

    out["fx_marketplace"] = {
        "snapshot_mtime": out["files"]["customer_order.csv"]["mtime"],
        "n_orders": len(co),
        "marketplace_aggregate": coverage(mp),
        "non_marketplace_aggregate": coverage(non_mp),
        "by_marketplace_channel": focus,
        "by_type_all": by_type,
        "verdict": None,
    }

    mp_ship_eur = out["fx_marketplace"]["marketplace_aggregate"]["shipping_fee_eur_gt0"]
    mp_oa_eur = out["fx_marketplace"]["marketplace_aggregate"]["order_amount_eur_gt0"]
    if mp_ship_eur == 0 and mp_oa_eur == 0:
        out["fx_marketplace"]["verdict"] = (
            "STATU QUO — shipping_fee_eur et order_amount_eur toujours vides (0%) "
            "sur Amazon/Cultura/Rakuten/Fnac. Aucune action modèle ; bloqué côté Michal."
        )
    elif mp_ship_eur == 0:
        out["fx_marketplace"]["verdict"] = (
            "PARTIEL — order_amount_eur a des valeurs marketplace mais shipping_fee_eur "
            "reste à 0%. Vérifier couverture avant de clôturer le shipping."
        )
    else:
        out["fx_marketplace"]["verdict"] = (
            "CORRECTION DÉTECTÉE — shipping_fee_eur > 0 sur marketplace. "
            "Recalculer couverture par canal avant clôture."
        )

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
