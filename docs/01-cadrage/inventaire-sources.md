# Inventaire des sources de données

> **Mission** : 4 jours — [`../../project/devis.md`](../../project/devis.md)  
> **Statut** : 🟢 Données reçues et intégrées au modèle PBIP  
> **Dernière mise à jour** : 14 juillet 2026

---

## Instructions

Ce document recense les sources consommées par le modèle `Lireka_Profitabilite.pbip`.  
Les CSV réels sont sur **SharePoint** (`Power_BI_Datawarehouse/`), lus directement  
par Power Query M — pas de pipeline Python intermédiaire.

**Légende statut** : ⬜ Non reçu · 🔄 En analyse · ✅ Intégré au modèle

---

## 1. Transporteurs — Factures CSV

### 1.1 Existants (référence, hors modèle profitabilité)

| Transporteur | Statut | Format | Emplacement | Notes |
|-------------|--------|--------|-------------|-------|
| DHL | ✅ Existant | CSV | `Dashboards_transporteurs/DHL Dashboard PowerBI/` | Référence design |
| FedEx | ✅ Existant | CSV | Entrepôt SharePoint | Référence design |
| UPS | ✅ Existant | CSV | `Dashboards_transporteurs/UPS Dashboard PowerBI/` | Référence design |

### 1.2 Intégrés au modèle profitabilité

| Transporteur | Statut | Fichiers source | Lignes valides (audit 14/07) | Notes |
|-------------|--------|-----------------|------------------------------|-------|
| La Poste (Colissimo) | ✅ Intégré | `COLISSIMO Dashboard PowerBI/2025 & 2026 récap.csv` | 113 075 | `numero_facture` vide (normal) |
| Chronopost | ✅ Intégré | `CHRONOPOST Dashboard PowerBI/2025 + V2 2026` | 3 046 | Factures multi-colis |
| Colis Privé | ✅ Colis backend | `package.csv` (coût estimé) | 516 836 colis | Pas de récap CSV intégré |
| Postes Canada | ✅ Colis backend | `package.csv` (préfixe `Q013…`) | 3 788 colis | Coût estimé ; PDF factures non recoupés |

Chargement : requêtes M dans `stg_factures_transport_resolu` → `fact_factures_transport`.

---

## 2. Commandes clients — Export backend

| Élément | Détail |
|---------|--------|
| **Source** | Backend Lireka |
| **Fichiers** | `customer_order.csv`, `package.csv`, `customer_order_item_group.csv` |
| **Emplacement** | SharePoint `Données_Backend/` |
| **Statut** | ✅ Reçu et intégré |
| **Volumes (audit 14/07)** | 989 234 commandes · 946 483 colis |

### Mapping backend → modèle

| Fichier backend | Colonne clé | Table Power BI |
|-----------------|-------------|----------------|
| `customer_order.csv` | `id` | `fact_commandes[id_commande]` |
| `customer_order.csv` | `destination_country` | `fact_commandes[code_pays]` → `dim_pays` |
| `customer_order.csv` | `source` | `fact_commandes[type_commande]` → `dim_type_commande` |
| `package.csv` | `order_id` | `fact_transport[order_id]` → `fact_commandes` |
| `package.csv` | `tracking_id` | `fact_transport[numero_suivi]` |

Le transporteur sur les colis est **inféré** du numéro de suivi (`fnNormaliserTransporteur`),  
pas présent en colonne dans le backend.

### Points connus (audit 14/07)

- 83 481 commandes `CANCELLED` — décision métier en attente (Marc)
- 162 commandes hors CANCELLED sans colis associé
- Matching facture réel : ~12,7 % des commandes (Colissimo + Chronopost uniquement)

---

## 3. Outils & accès

| Outil | Accès nécessaire | Statut | Notes |
|-------|-----------------|--------|-------|
| Power BI Service | Workspace Lireka — Contributor | 🔄 | À confirmer publication |
| Power BI Desktop | Licence (ZineInsights) | ✅ | Développement `.pbip` |
| SharePoint | `Power_BI_Datawarehouse/` | ✅ | Source unique des CSV |
| Claude AI ↔ Power BI | Lecture (existant) | ⬜ | Hors périmètre mission |

---

## 4. Volumétrie constatée (entrepôt complet)

| Source | Volume | Période couverte |
|--------|--------|------------------|
| Commandes (`customer_order.csv`) | 989 234 | Historique backend complet |
| Colis (`package.csv`) | 946 483 | Historique backend complet |
| Factures Colissimo + Chronopost | 116 121 lignes valides | Récaps 2025–2026 |

---

## 5. Checklist de collecte (J1) — statut

- [x] Récaps Colissimo sur SharePoint
- [x] Récaps Chronopost sur SharePoint
- [x] Export backend (`customer_order.csv`, `package.csv`, etc.)
- [x] Accès entrepôt SharePoint local / distant
- [ ] Accès Power BI workspace (Contributor) — publication
- [ ] Formule marge brute validée (finance / Marc)

---

*Inventaire aligné sur le modèle livré — pas de dépôt `data/raw/` intermédiaire.*
