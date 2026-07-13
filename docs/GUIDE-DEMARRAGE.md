# Guide de démarrage — Mission 4 jours

> **Référence contractuelle** : [`../project/devis.md`](../project/devis.md)  
> Ce guide couvre les **4 jours** de la mission.

---

## Jour 1 — Kick-off, accès & données

- [ ] Personnaliser et envoyer l'email de kick-off → `communications/emails/01-kickoff.md`
- [ ] Kick-off Marc Bordier (30–45 min)
- [ ] Obtenir accès Power BI + tous les CSV → `docs/01-cadrage/checklist-acces-donnees.md`
- [ ] Déposer les fichiers dans `data/raw/`
- [ ] Lancer les scripts ETL :

```bash
# Factures (exemple La Poste)
python scripts/etl/etl_factures_transporteur.py \
  --transporteur la-poste \
  --fichier data/raw/transporteurs/la-poste/la-poste_factures_YYYYMM.csv

# Commandes
python scripts/etl/etl_commandes.py \
  --fichier data/raw/commandes/commandes_YYYYMM.csv

# Validation matching
python scripts/validation/validate_data.py --type matching
```

- [ ] Compléter l'inventaire des sources → `docs/01-cadrage/inventaire-sources.md`

---

## Jour 2 — Intégration Power BI

- [ ] Intégrer La Poste, Colis Privé, Chronopost dans Power BI
- [ ] Publier le dataset commandes structuré
- [ ] S'appuyer sur le modèle DHL/FedEx/UPS existant (référence, pas refonte)

---

## Jour 3 — Jointure & dashboards profitabilité

- [ ] Jointure factures ↔ commandes par `numero_suivi`
- [ ] Mesures marge brute (coût transport réel)
- [ ] Dashboard profitabilité — marge brute par **pays** et par **type de commande** *(1 rapport, structure au choix du prestataire)*

---

## Jour 4 — Formation, documentation & clôture

- [ ] Session formation *(si disponibilité équipes Lireka)* → `docs/05-formation/programme-formation.md`
- [ ] Rédiger la documentation du processus → `docs/04-processus/processus-etl-gouvernance.md`
- [ ] Point de clôture avec Marc Bordier
- [ ] Mettre à jour le registre des livrables → `project/livrables.md`

---

## Commandes utiles

```bash
# Tous les transporteurs d'un dossier
python scripts/etl/etl_factures_transporteur.py \
  --transporteur all \
  --dossier data/raw/transporteurs/

# Valider les factures
python scripts/validation/validate_data.py \
  --type factures \
  --fichier data/processed/transporteurs/factures_unifiees.csv

# Valider les commandes
python scripts/validation/validate_data.py \
  --type commandes \
  --fichier data/processed/commandes/commandes_clean.csv
```

---

## Documents clés (périmètre devis)

| Jour | Documents |
|------|-----------|
| J1 | `devis.md`, `checklist-acces-donnees.md`, `inventaire-sources.md` |
| J2 | `schema-unifie-factures.md`, `schema-export-commandes.md` |
| J3 | `mesures-dax.md`, `livrables.md` |
| J4 | `processus-etl-gouvernance.md`, `programme-formation.md` |

---

*Guide ZineInsights — Juillet 2026*
