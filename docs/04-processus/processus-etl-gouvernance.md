# Documentation du processus — modèle profitabilité Lireka

> **Livrable contractuel** : L06 — Documentation du processus  
> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> **Date** : 14 juillet 2026

Ce document décrit **comment le modèle livré se recharge**, tel qu'implémenté dans  
`powerbi/Lireka_Profitabilite.pbip`. Il ne définit pas de processus récurrent, de SLA  
ni de rôles de gouvernance — ces éléments ne figurent pas au devis.

---

## 1. Objet livré

Le devis prévoit l'intégration des données transporteurs et commandes dans Power BI,  
la jointure factures ↔ commandes, un dashboard de profitabilité et la documentation  
du processus. Concrètement :

| Livrable devis | Implémentation |
|----------------|----------------|
| 3 transporteurs intégrés (La Poste, Colis Privé, Chronopost) | Récaps Colissimo + Chronopost chargés dans `fact_factures_transport` |
| Dataset commandes structuré | `fact_commandes`, `fact_transport`, `fact_lignes` depuis le backend |
| Jointure factures ↔ commandes | Rapprochement facture → colis par `id_package` (résolution par date dans Power Query) |
| Dashboard profitabilité | Rapport `Lireka_Profitabilite.Report` |
| Documentation du processus | Ce fichier |

Les colis **Postes Canada** (préfixe suivi `Q013…`) sont intégrés au modèle via  
`package.csv` ; ils n'ont pas de factures transporteur dans les récaps actuels.

---

## 2. Source des données

Les CSV sont lus **directement depuis SharePoint** (pas de pipeline Python intermédiaire).

**Paramètre Power Query** : `SharePointSiteURL`  
(valeur par défaut : `https://lirekacom.sharepoint.com/sites/Lireka`)

L'arborescence SharePoint doit reproduire l'entrepôt local `Power_BI_Datawarehouse/` :

```
Power_BI_Datawarehouse/
├── Données_Backend/
│   ├── customer_order.csv
│   ├── customer_order_item.csv
│   ├── package.csv
│   └── customer_order_item_group.csv
└── Dashboards_transporteurs/
    ├── COLISSIMO Dashboard PowerBI/   (*.csv récap)
    └── CHRONOPOST Dashboard PowerBI/ (*.csv récap)
```

Les données brutes ne sont **pas versionnées dans Git** (`.gitignore`).

---

## 3. Chargement dans le modèle (Power Query M)

Mode : **Import** (données chargées en mémoire à chaque refresh).

### Backend commandes et colis

| Table Power BI | Fichier(s) source | Rôle |
|----------------|-------------------|------|
| `fact_commandes` | `customer_order.csv` | Commandes (CA, coûts, pays, type) |
| `fact_transport` | `package.csv` | Colis (coût, suivi, transporteur inféré) |
| `fact_lignes` | `customer_order_item.csv` + `customer_order_item_group.csv` | Lignes d'articles (grain : un article physique / `customer_order_item`) |
| `dim_pays`, `dim_type_commande` | dérivées de `customer_order.csv` | Axes d'analyse |
| `dim_date` | générée (calendrier) | Axe temporel |
| `dim_transporteur` | table statique | Référentiel transporteurs |

`customer_order.csv` (~187 Mo) est lu **une seule fois** via la requête partagée  
`stg_customer_order`, puis réutilisée par `fact_commandes`, `dim_pays` et  
`dim_type_commande`. Les coûts Bloc 5 (retours, génériques) passent par  
`stg_couts_bloc5_commande` (agrégation depuis `stg_Commande_Items` /  
`customer_order_item.csv`). `fact_lignes` merge `customer_order_item.csv` et  
`customer_order_item_group.csv` pour le grain article.

### Factures transporteurs (La Poste / Colissimo, Chronopost)

| Table Power BI | Fichiers source |
|----------------|-----------------|
| `fact_factures_transport` | Récaps Colissimo 2025 + 2026, Chronopost 2025 + V2 2026 |

La logique de unification, typage (`;` + décimale virgule) et résolution  
facture → colis par proximité de date est centralisée dans  
`stg_factures_transport_resolu` (`definition/expressions.tmdl`).

Le transporteur sur les colis est **inféré du numéro de suivi**  
(fonction `fnNormaliserTransporteur`) — il n'existe pas de colonne transporteur  
dans les CSV backend.

### Relations principales

- `fact_transport[order_id]` → `fact_commandes[id_commande]` (`rel_transport_commandes`)
- `fact_lignes[order_id]` → `fact_commandes[id_commande]` (`rel_lignes_commandes`)
- `fact_factures_transport[id_package]` → `fact_transport[id_package]` (`rel_factures_colis`)
- `fact_commandes` → `dim_pays`, `dim_type_commande`, `dim_date`
- `fact_transport` → `dim_transporteur`
- Relations directes facture → `dim_transporteur` / `dim_date` : **inactives** (`isActive: false`) ; activables via `USERELATIONSHIP` dans les mesures de contrôle

---

## 4. Refresh du modèle

### En développement (Power BI Desktop)

1. Ouvrir `powerbi/Lireka_Profitabilite.pbip`
2. Vérifier le paramètre **SharePointSiteURL** (*Transformer les données* → *Gérer les paramètres*)
3. Lancer **Actualiser** (refresh) — toutes les requêtes M se réexécutent
4. Contrôler visuellement le rapport profitabilité

Le premier refresh sur le volume complet peut prendre plusieurs minutes  
(`customer_order.csv` + `package.csv` + récaps factures).

### En production (Power BI Service)

Après publication du dataset sur le workspace Lireka :

1. Les **identifiants de la source SharePoint** doivent être configurés dans le Service
2. Un refresh peut être déclenché manuellement (*Actualiser maintenant*) ou planifié  
   dans les paramètres du dataset — **la fréquence relève du choix Lireka**,  
   elle n'est pas fixée par le devis

---

## 5. Points de vigilance connus

- **Marge brute** : mesure de référence `[Marge Brute]` — formule actée Marc Bordier
  (Slack, 13/07/2026 16h09), documentée dans `_Mesures.tmdl`.
  `[Marge Brute (prov.)]` conservée comme contrôle/comparaison historique.
- **Matching factures** : seules les factures Colissimo/Chronopost alimentent le coût
  rapproché (`source_cout = "facture_rapprochee"`). Les colis sans facture mais avec
  coût backend utilisent `source_cout = "backend_seul"` ; sans les deux :
  `source_cout = "aucun"`. Colis Privé et Postes Canada restent en coût estimé backend.
- **Statut CANCELLED** : règle actée (CA=0 et frais de port exclus dans les mesures
  `[CA HT Net Annulation]` / `[Marge Brute]` ; coûts conservés). Les commandes annulées
  restent dans `fact_commandes` — pas de filtre partition.

---

## 6. Fichiers de référence

| Fichier | Contenu |
|---------|---------|
| `powerbi/Lireka_Profitabilite.SemanticModel/definition/expressions.tmdl` | Requêtes M partagées, fonctions SharePoint |
| `powerbi/Lireka_Profitabilite.SemanticModel/definition/relationships.tmdl` | Relations du modèle |
| `powerbi/models/mesures-dax.md` | Référentiel des mesures DAX |

---

*Documentation alignée sur le périmètre contractuel — proposition commerciale juillet 2026.*
