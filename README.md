# Lireka × ZineInsights — Pilotage économique & financier Power BI

> **Formule de marge actée** (Slack Marc Bordier, 13/07/2026) — voir [`project/perimetre-verrouille.md`](project/perimetre-verrouille.md).

> **Prestataire** : Otmane Boulahia — ZineInsights (SASU)  
> **Client** : Lireka — Marc Bordier, Président  
> **Site** : [lireka.com](https://www.lireka.com)  
> **Durée** : **4 jours** — forfait **1 800 € HT**  
> **Statut** : 🟡 Préparation / Onboarding

> **Référence contractuelle** : [`project/devis.md`](project/devis.md) — le devis fait foi sur le périmètre.

---

## Contexte

Lireka est une librairie en ligne expédiant des livres dans le monde entier. En 2025, le groupe (Lireka + filiale Arthaud Grenoble) a réalisé **14,4 M€** de chiffre d'affaires.

Trois tableaux de bord Power BI existent déjà pour les coûts transporteurs **DHL**, **FedEx** et **UPS** (factures CSV). Cette mission de **4 jours** vise à intégrer les transporteurs restants et les commandes, joindre les données par numéro de suivi, et livrer les **dashboards de profitabilité**.

---

## Périmètre contractuel (devis)

| # | Livrable | Statut |
|---|----------|--------|
| 1 | Intégration **La Poste**, **Colis Privé**, **Chronopost** dans Power BI | ⬜ |
| 2 | Import et structuration du **CSV commandes** backend | ⬜ |
| 3 | **Jointure** factures ↔ commandes par numéro de suivi | ⬜ |
| 4 | **Dashboard profitabilité** — marge brute par pays et par type de commande *(1 rapport, 2 axes)* | ⬜ |
| 5 | **Formation** utilisateurs (selon disponibilité équipes Lireka) | ⬜ |
| 6 | **Documentation du processus** | ⬜ |

---

## Calendrier indicatif (4 jours)

- **J1** : kick-off Marc (30–45 min), accès Power BI + SharePoint, réception CSV
- **J2** : intégration La Poste / Colis Privé / Chronopost + commandes backend
- **J3** : jointure par n° de suivi, dashboard profitabilité L04
- **J4** : formation utilisateurs (si dispo équipes), documentation processus L06, clôture
- **Dépendances Lireka** : workspace Contributor, factures CSV (3 transporteurs), export commandes, disponibilité formation J4

---

## Structure du dépôt

```
lireka/
├── project/
│   ├── devis.md                       ← Référence contractuelle (fait foi)
│   ├── perimetre-verrouille.md        ← Devis + formule marge actée
│   └── livrables.md
├── docs/
│   ├── 04-processus/                  ← L06 — documentation processus
│   └── 05-formation/                  ← Formation (session unique)
├── data/samples/                      ← Échantillons anonymisés uniquement
├── scripts/validation/                ← Audits et contrôles (hors pipeline ETL)
└── powerbi/                           ← Modèle PBIP + doc mesures
```

---

## Démarrage rapide

### Prérequis (à obtenir dès J1)

- Accès Power BI workspace Lireka (Contributor)
- Accès SharePoint à l'entrepôt `Power_BI_Datawarehouse/` (CSV backend + récaps transporteurs)
- Factures CSV : La Poste (Colissimo), Colis Privé, Chronopost
- Export CSV commandes backend (`customer_order.csv`, `package.csv`, etc.)
- Formule marge brute : **actée** (Slack Marc, 13/07/2026) — voir [`project/perimetre-verrouille.md`](project/perimetre-verrouille.md)

### Checklist J1

- [ ] Kick-off avec Marc Bordier
- [ ] Récupérer accès Power BI (Contributor) et SharePoint `Power_BI_Datawarehouse/`
- [ ] Vérifier le paramètre `SharePointSiteURL` dans `powerbi/Lireka_Profitabilite.pbip`
- [ ] Premier refresh Power BI Desktop sur les données réelles

---

## Contacts

| Rôle | Nom | Organisation |
|------|-----|--------------|
| Président / Sponsor | Marc Bordier | Lireka |
| Data Analyst / Chef de projet | Otmane Boulahia | ZineInsights |
| — | *À compléter* | Référent technique Lireka |
| — | *À compléter* | Référent logistique Lireka |

---

## Liens utiles

- [**Périmètre verrouillé**](project/perimetre-verrouille.md) — devis + formule marge actée
- [**Devis (référence contractuelle)**](project/devis.md)
- [Livrables](project/livrables.md)
- [Documentation processus L06](docs/04-processus/processus-etl-gouvernance.md)
- [Formation](docs/05-formation/programme-formation.md)

---

*Dernière mise à jour : 15 juillet 2026 — ZineInsights*
