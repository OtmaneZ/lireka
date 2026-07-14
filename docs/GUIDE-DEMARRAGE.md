# Guide de démarrage — Mission 4 jours

> **Référence contractuelle** : [`../project/devis.md`](../project/devis.md)  
> Ce guide couvre les **4 jours** de la mission.

---

## Jour 1 — Kick-off, accès & données

- [ ] Personnaliser et envoyer l'email de kick-off → `communications/emails/01-kickoff.md`
- [ ] Kick-off Marc Bordier (30–45 min)
- [ ] Obtenir accès Power BI + SharePoint (`Power_BI_Datawarehouse/`) → `docs/01-cadrage/checklist-acces-donnees.md`
- [ ] Vérifier que les CSV sont présents sur SharePoint :
  - `Données_Backend/customer_order.csv`, `package.csv`, `customer_order_item_group.csv`
  - Récaps Colissimo et Chronopost dans `Dashboards_transporteurs/`
- [ ] Ouvrir `powerbi/Lireka_Profitabilite.pbip` dans Power BI Desktop
- [ ] Configurer le paramètre **SharePointSiteURL** (*Transformer les données* → *Gérer les paramètres*)
- [ ] Lancer un **refresh** et vérifier l'absence d'erreur sur les requêtes M
- [ ] Compléter l'inventaire des sources → `docs/01-cadrage/inventaire-sources.md`

---

## Jour 2 — Intégration Power BI

- [ ] Intégrer La Poste, Colis Privé, Chronopost dans le modèle (récaps factures via Power Query M)
- [ ] Vérifier le chargement des tables backend (`fact_commandes`, `fact_transport`, `fact_lignes`)
- [ ] S'appuyer sur le modèle DHL/FedEx/UPS existant comme référence (pas de refonte)

---

## Jour 3 — Jointure & dashboards profitabilité

- [ ] Vérifier le rapprochement factures ↔ colis (`rel_factures_colis` via `id_package`)
- [ ] Mesures marge brute provisoire et contrôles qualité
- [ ] Dashboard profitabilité — marge brute par **pays** et par **type de commande** *(1 rapport, structure au choix du prestataire)*

---

## Jour 4 — Formation, documentation & clôture

- [ ] Session formation *(si disponibilité équipes Lireka)* → `docs/05-formation/programme-formation.md`
- [ ] Rédiger la documentation du processus → `docs/04-processus/processus-etl-gouvernance.md`
- [ ] Point de clôture avec Marc Bordier
- [ ] Mettre à jour le registre des livrables → `project/livrables.md`

---

## Refresh du modèle (étapes réelles)

1. Ouvrir `powerbi/Lireka_Profitabilite.pbip` dans Power BI Desktop
2. Vérifier **SharePointSiteURL** (site Lireka contenant `Power_BI_Datawarehouse/`)
3. **Actualiser** le modèle — Power Query M relit les CSV SharePoint et reconstruit les tables
4. Contrôler les volumes clés (`Nb Commandes`, `Nb Colis`, `Nb Colis Facturés`)
5. Après publication : refresh manuel ou planifié dans Power BI Service *(fréquence au choix Lireka)*

Documentation détaillée : [`docs/04-processus/processus-etl-gouvernance.md`](04-processus/processus-etl-gouvernance.md)

---

## Documents clés (périmètre devis)

| Jour | Documents |
|------|-----------|
| J1 | `devis.md`, `checklist-acces-donnees.md`, `inventaire-sources.md` |
| J2 | `modeles-semanticques.md`, `architecture-data.md` |
| J3 | `mesures-dax.md`, `livrables.md` |
| J4 | `processus-etl-gouvernance.md`, `programme-formation.md` |

---

*Guide ZineInsights — Juillet 2026*
