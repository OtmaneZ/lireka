# Lireka × ZineInsights — Pilotage économique & financier Power BI

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

## Structure du dépôt

```
lireka/
├── project/
│   ├── devis.md                       ← Référence contractuelle (fait foi)
│   ├── planning.md                    ← Planning 4 jours
│   ├── livrables.md
│   ├── raci.md
│   └── risques.md
├── docs/                              ← Documentation projet
├── data/samples/                      ← Échantillons anonymisés uniquement
├── scripts/validation/                ← Audits et contrôles (hors pipeline ETL)
├── powerbi/                           ← Modèle PBIP + doc mesures
├── communications/                    ← Emails & templates client
└── templates/                         ← Schémas CSV cibles
```

Le reste du dépôt (architecture détaillée, sessions formation 2-3, templates mensuels…) est du **matériel de travail** utile mais **hors périmètre contractuel** sauf mention contraire dans le devis.

---

## Démarrage rapide

### Prérequis (à obtenir dès J1)

- Accès Power BI workspace Lireka (Contributor)
- Accès SharePoint à l'entrepôt `Power_BI_Datawarehouse/` (CSV backend + récaps transporteurs)
- Factures CSV : La Poste (Colissimo), Colis Privé, Chronopost
- Export CSV commandes backend (`customer_order.csv`, `package.csv`, etc.)
- Formule marge brute validée côté finance

### Checklist J1

- [ ] Kick-off avec Marc Bordier → `communications/emails/01-kickoff.md`
- [ ] Récupérer accès et données → `docs/01-cadrage/checklist-acces-donnees.md`
- [ ] Vérifier le paramètre `SharePointSiteURL` dans `powerbi/Lireka_Profitabilite.pbip`
- [ ] Premier refresh Power BI Desktop sur les données réelles
- [ ] Compléter l'inventaire des sources → `docs/01-cadrage/inventaire-sources.md`

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

- [**Devis (référence contractuelle)**](project/devis.md)
- [Cahier des charges](docs/01-cadrage/cahier-des-charges.md)
- [Planning 4 jours](project/planning.md)
- [Livrables](project/livrables.md)
- [Guide de démarrage](docs/GUIDE-DEMARRAGE.md)

---

*Dernière mise à jour : 14 juillet 2026 — ZineInsights*
