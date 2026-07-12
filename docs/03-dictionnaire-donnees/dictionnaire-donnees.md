# Dictionnaire de données — Lireka

> **⚠️ Hors périmètre devis** — Document de travail technique (référence ETL). Le livrable contractuel est la documentation du processus.  
> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> **Dernière mise à jour** : 12 juillet 2026

---

## 1. Factures transporteurs (schéma unifié)

**Table cible** : `fact_factures_transport`  
**Fichier source** : `data/processed/transporteurs/factures_unifiees.csv`

| # | Champ | Type | Obligatoire | Source | Description | Exemple | Règles |
|---|-------|------|-------------|--------|-------------|---------|--------|
| 1 | `id_facture` | VARCHAR(50) | ✅ | Facture | Identifiant unique de la facture | `FAC-2026-001234` | Unique par transporteur |
| 2 | `date_facture` | DATE | ✅ | Facture | Date d'émission de la facture | `2026-06-15` | Format ISO 8601 |
| 3 | `numero_suivi` | VARCHAR(100) | ✅ | Facture | Numéro de suivi du colis | `1Z999AA10123456784` | Nettoyé (TRIM, UPPER) |
| 4 | `transporteur` | VARCHAR(50) | ✅ | Dérivé | Nom du transporteur | `DHL` | Valeurs contrôlées |
| 5 | `cout_transport` | DECIMAL(10,2) | ✅ | Facture | Montant facturé pour le transport | `12.50` | En EUR, ≥ 0 |
| 6 | `poids` | DECIMAL(8,3) | ⬜ | Facture | Poids du colis en kg | `1.250` | > 0 si renseigné |
| 7 | `pays_destination` | VARCHAR(3) | ⬜ | Facture | Code pays ISO 3166-1 alpha-3 | `FRA` | Code ISO valide |
| 8 | `service` | VARCHAR(100) | ⬜ | Facture | Type de service transport | `Express Worldwide` | Libre |
| 9 | `devise` | VARCHAR(3) | ⬜ | Facture | Devise de facturation | `EUR` | Défaut : EUR |
| 10 | `date_import` | DATETIME | ✅ | Système | Date d'import dans le système | `2026-07-10T09:00:00` | Auto-généré |

### Valeurs contrôlées — `transporteur`

| Valeur | Statut |
|--------|--------|
| `DHL` | ✅ Existant |
| `FedEx` | ✅ Existant |
| `UPS` | ✅ Existant |
| `La Poste` | ⬜ À intégrer |
| `Colis Privé` | ⬜ À intégrer |
| `Chronopost` | ⬜ À intégrer |

---

## 2. Commandes clients (schéma backend)

**Table cible** : `fact_commandes`  
**Fichier source** : `data/processed/commandes/commandes_clean.csv`

| # | Champ | Type | Obligatoire | Source | Description | Exemple | Règles |
|---|-------|------|-------------|--------|-------------|---------|--------|
| 1 | `id_commande` | VARCHAR(50) | ✅ | Backend | Identifiant unique commande | `CMD-2026-78901` | Unique |
| 2 | `date_commande` | DATETIME | ✅ | Backend | Date et heure de la commande | `2026-06-10T14:30:00` | |
| 3 | `pays_livraison` | VARCHAR(3) | ✅ | Backend | Pays de livraison (ISO alpha-3) | `DEU` | Code ISO |
| 4 | `type_commande` | VARCHAR(50) | ✅ | Backend | Type de commande | `B2C_standard` | Valeurs contrôlées |
| 5 | `transporteur` | VARCHAR(50) | ✅ | Backend | Transporteur assigné | `DHL` | Valeurs contrôlées |
| 6 | `numero_suivi` | VARCHAR(100) | ✅ | Backend | Numéro de suivi colis | `1Z999AA10123456784` | Clé de liaison |
| 7 | `ca_ht` | DECIMAL(10,2) | ✅ | Backend | Chiffre d'affaires HT | `45.90` | ≥ 0 |
| 8 | `ca_ttc` | DECIMAL(10,2) | ⬜ | Backend | Chiffre d'affaires TTC | `54.32` | ≥ 0 |
| 9 | `cout_achat` | DECIMAL(10,2) | ✅ | Backend | Coût d'achat des livres | `22.00` | ≥ 0 |
| 10 | `cout_transport_estime` | DECIMAL(10,2) | ✅ | Backend | Coût transport estimé | `8.50` | ≥ 0 |
| 11 | `nombre_articles` | INT | ⬜ | Backend | Nombre de livres commandés | `3` | ≥ 1 |
| 12 | `poids_total` | DECIMAL(8,3) | ⬜ | Backend | Poids total en kg | `2.100` | > 0 |
| 13 | `date_import` | DATETIME | ✅ | Système | Date d'import | `2026-07-10T09:00:00` | Auto-généré |

### Valeurs contrôlées — `type_commande`

| Valeur | Description |
|--------|-------------|
| *À compléter avec Lireka* | |

---

## 3. Champs calculés (Power BI)

| # | Champ | Type | Formule | Description |
|---|-------|------|---------|-------------|
| 1 | `cout_transport_reel` | DECIMAL | LOOKUPVALUE depuis fact_factures_transport | Coût réel issu de la facture |
| 2 | `marge_brute` | DECIMAL | `ca_ht - cout_achat - cout_transport_reel` | Marge brute réelle |
| 3 | `taux_marge_brute` | DECIMAL | `marge_brute / ca_ht` | Taux de marge en % |
| 4 | `ecart_cout_transport` | DECIMAL | `cout_transport_reel - cout_transport_estime` | Écart estimé vs réel |
| 5 | `taux_ecart_cout` | DECIMAL | `ecart_cout_transport / cout_transport_estime` | Écart en % |
| 6 | `est_matche` | BOOLEAN | `NOT(ISBLANK(cout_transport_reel))` | Commande liée à une facture |

---

## 4. Tables de dimensions

### dim_date

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `date` | DATE | PK | `2026-06-15` |
| `annee` | INT | Année | `2026` |
| `trimestre` | INT | Trimestre (1-4) | `2` |
| `mois` | INT | Mois (1-12) | `6` |
| `nom_mois` | VARCHAR | Nom du mois | `Juin` |
| `semaine` | INT | Numéro de semaine ISO | `24` |
| `jour_semaine` | VARCHAR | Jour de la semaine | `Lundi` |

### dim_pays

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `code_pays` | VARCHAR(3) | PK — ISO 3166-1 alpha-3 | `FRA` |
| `nom_pays` | VARCHAR | Nom du pays | `France` |
| `zone_geo` | VARCHAR | Zone géographique | `Europe de l'Ouest` |
| `continent` | VARCHAR | Continent | `Europe` |

### dim_transporteur

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `transporteur` | VARCHAR(50) | PK | `DHL` |
| `type_service` | VARCHAR | Express / Standard / Économique | `Express` |
| `actif` | BOOLEAN | Transporteur actif | `TRUE` |

### dim_type_commande

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `type_commande` | VARCHAR(50) | PK | `B2C_standard` |
| `categorie` | VARCHAR | B2C / B2B / Marketplace | `B2C` |
| `libelle` | VARCHAR | Libellé affiché | `Commande standard B2C` |

---

## 5. Mapping par transporteur

> Section à compléter lors de l'analyse de chaque format de facture.

### La Poste

| Champ source (CSV brut) | Champ unifié | Transformation |
|------------------------|-------------|----------------|
| *À compléter* | | |

### Colis Privé

| Champ source (CSV brut) | Champ unifié | Transformation |
|------------------------|-------------|----------------|
| *À compléter* | | |

### Chronopost

| Champ source (CSV brut) | Champ unifié | Transformation |
|------------------------|-------------|----------------|
| *À compléter* | | |

---

## 6. Glossaire

| Terme | Définition |
|-------|-----------|
| **Marge brute** | CA HT − Coût d'achat − Coût transport réel |
| **Coût transport estimé** | Montant calculé par le backend Lireka (tarifs estimés) |
| **Coût transport réel** | Montant facturé par le transporteur |
| **Numéro de suivi** | Identifiant unique du colis, commun entre backend et facture |
| **Taux de matching** | % de commandes ayant un coût transport réel (liées à une facture) |
| **Star schema** | Modèle en étoile : tables de faits au centre, dimensions autour |

---

*Dictionnaire vivant — mis à jour à chaque phase de la mission.*
