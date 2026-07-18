# Note d'audit — Dashboards transporteurs existants

> **Statut** : 🟡 À réaliser (J1, audit rapide)  
> **Référence** : [`devis.md`](devis.md)  
> **Objectif** : comprendre le modèle existant pour intégrer les 3 nouveaux transporteurs — **pas** créer 3 dashboards dédiés (hors devis).

---

## Objectif (périmètre devis)

Analyser rapidement les dashboards DHL, FedEx, UPS pour :

1. Identifier le schéma CSV / modèle de données utilisé
2. Reprendre le même modèle pour intégrer La Poste, Colis Privé, Chronopost
3. Noter les mesures DAX utiles pour la jointure et la profitabilité

**Durée prévue** : 1 à 2 h (J1)

---

## Grille d'audit rapide

### Par dashboard (DHL, FedEx, UPS)

| Élément | DHL | FedEx | UPS |
|---------|-----|-------|-----|
| Nom du rapport | | | |
| Dataset associé | | | |
| Champs CSV clés | | | |
| Mesure coût transport | | | |
| Champ numéro de suivi | | | |

---

## Synthèse — Schéma unifié cible

| Champ unifié | La Poste | Colis Privé | Chronopost |
|-------------|----------|-------------|------------|
| `numero_facture` | ⬜ | ⬜ | ⬜ |
| `date_facture` | ⬜ | ⬜ | ⬜ |
| `numero_suivi` | ⬜ | ⬜ | ⬜ |
| `cout_transport` | ⬜ | ⬜ | ⬜ |
| `transporteur` | La Poste | Colis Privé | Chronopost |

---

## Hors périmètre

- Reproduction de visuels transporteurs dédiés pour les 3 nouveaux transporteurs
- Audit connexion Claude AI
- Documentation exhaustive des 3 dashboards existants

---

*Audit rapide J1 — ZineInsights*
