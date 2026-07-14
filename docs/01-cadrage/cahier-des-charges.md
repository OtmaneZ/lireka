# Cahier des charges — Pilotage économique & financier Lireka

> **Formule de marge actée** (Slack Marc Bordier, 13/07/2026) — voir [`../../project/perimetre-verrouille.md`](../../project/perimetre-verrouille.md).

> **Version** : 2.0 — Aligné sur le devis  
> **Date** : 12 juillet 2026  
> **Rédacteur** : Otmane Boulahia — ZineInsights  
> **Client** : Marc Bordier — Lireka  
> **Référence contractuelle** : [`../../project/devis.md`](../../project/devis.md)

---

## 1. Contexte

**Lireka** (www.lireka.com) est une librairie en ligne. En 2025, le groupe Lireka + filiale **Arthaud Grenoble** a réalisé **14,4 M€** de chiffre d'affaires.

**Situation actuelle** :
- 3 dashboards Power BI : DHL, FedEx, UPS (factures CSV)
- Coûts transport backend : estimations
- Pas de vision consolidée marge brute réelle avec coûts transport réels

---

## 2. Périmètre de la mission

### 2.1 Inclus ✅ (devis — 4 jours, 1 800 € HT)

1. **Intégration des 3 transporteurs manquants** : La Poste, Colis Privé, Chronopost
2. **Import et structuration** du fichier CSV commandes backend
3. **Jointure factures ↔ commandes** par numéro de suivi
4. **Dashboards de profitabilité** — marge brute par pays, par type de commande
5. **Formation des utilisateurs** — sessions proposées durant la mission, sous réserve de disponibilité des équipes Lireka
6. **Documentation du processus**

### 2.2 Exclus ❌

- Dashboards transporteurs dédiés (un par transporteur) calqués sur DHL/FedEx/UPS
- Dashboards supplémentaires (synthèse direction, écarts transport, marketing…)
- Refonte des dashboards DHL, FedEx, UPS
- Programme formation multi-sessions structuré (3 × 2 h)
- Dictionnaire de données exhaustif, architecture complète, comité de pilotage
- Développement backend, automatisation exports, maintenance post-mission
- Audit ou modification connexion Claude AI

---

## 3. Données & sources

| Source | Format | Rôle |
|--------|--------|------|
| Factures La Poste, Colis Privé, Chronopost | CSV | Intégration transporteurs |
| Export commandes backend | CSV | Profitabilité, jointure |
| Factures DHL, FedEx, UPS | CSV | Existant — référence modèle |

**Clé de liaison** : numéro de suivi (factures transporteurs ↔ export commandes)

---

## 4. Livrables

Voir [`../../project/livrables.md`](../../project/livrables.md)

| Livrable | Format |
|----------|--------|
| 3 transporteurs intégrés dans Power BI | Power BI |
| Dataset commandes structuré | Power BI |
| Jointure par n° de suivi | Power BI |
| Dashboard profitabilité (pays + type commande — 1 rapport, structure au choix du prestataire) | Power BI |
| Formation utilisateurs | Session visio |
| Documentation du processus | Markdown / PDF |

---

## 5. Planning

**Durée** : **4 jours**

Voir [`../../project/planning.md`](../../project/planning.md)

---

## 6. Prérequis côté Lireka (avant J1)

| Prérequis | Responsable |
|-----------|-------------|
| Accès workspace Power BI (Contributor) | Réf. technique |
| Factures CSV La Poste, Colis Privé, Chronopost (1 mois) | Réf. logistique |
| Export CSV commandes (1 mois) | Réf. technique |
| Formule marge brute validée | ✅ Actée Slack 13/07/2026 — `perimetre-verrouille.md` |
| Référent joignable pendant les 4 jours | Marc Bordier |

---

## 7. Conditions & modalités

| Élément | Détail |
|---------|--------|
| Prestataire | Otmane Boulahia — ZineInsights (SASU) |
| Durée | 4 jours |
| Tarif | 450 € HT / jour — forfait **1 800 € HT** |
| Confidentialité | NDA — données Lireka confidentielles |
| Propriété intellectuelle | Livrables cédés à Lireka à la clôture |

---

## 8. Validation

| | Nom | Date | Signature |
|---|-----|------|-----------|
| Client | Marc Bordier — Lireka | | |
| Prestataire | Otmane Boulahia — ZineInsights | | |

---

*Document aligné sur le devis contractuel.*
