# Registre des risques — Lireka × ZineInsights

> **Mission** : 4 jours — forfait 1 800 € HT  
> **Référence** : [`devis.md`](devis.md)  
> Dernière mise à jour : 12 juillet 2026

---

## Légende

| Probabilité | Impact | Score |
|-------------|--------|-------|
| Faible (1) | Faible (1) | 🟢 Faible |
| Moyenne (2) | Moyen (2) | 🟡 Moyen |
| Élevée (3) | Élevé (3) | 🔴 Élevé |

**Score = Probabilité × Impact**

---

## Risques identifiés

| ID | Risque | Prob. | Impact | Score | Mitigation | Responsable |
|----|--------|-------|--------|-------|------------|-------------|
| R01 | **Données non fournies dès J1** — Bloque toute la mission | 3 | 3 | 🔴 9 | Checklist accès envoyée avant J1, relance immédiate | Lireka |
| R02 | **Formats factures hétérogènes** — ETL plus long que prévu | 3 | 2 | 🔴 6 | Schéma unifié flexible, prioriser l'essentiel (suivi + coût) | ZineInsights |
| R03 | **Taux de matching suivi faible** — Jointure incomplète | 2 | 3 | 🔴 6 | Nettoyage n° suivi, documenter le taux réel atteint | ZineInsights + Lireka |
| R04 | **Accès Power BI insuffisant** | 2 | 3 | 🔴 6 | Demander Contributor dès J1 matin | Lireka |
| R05 | **Formule marge brute non validée** | 2 | 2 | 🟡 4 | Obtenir validation finance avant J3 | Lireka |
| R06 | **Participants formation indisponibles J4** | 2 | 1 | 🟡 2 | Proposer créneau en visio, documenter en remplacement | Lireka |
| R07 | **Extension de périmètre en cours de mission** | 2 | 2 | 🟡 4 | Renvoyer au devis, tout extra = hors forfait | Marc Bordier |
| R08 | **Données personnelles (RGPD)** | 1 | 3 | 🟡 3 | Pseudonymiser avant import si nécessaire | ZineInsights |

---

## Hypothèses de travail

| # | Hypothèse | Validée |
|---|-----------|---------|
| H01 | Factures La Poste, Colis Privé, Chronopost disponibles en CSV | ⬜ |
| H02 | Export commandes backend contient un champ numéro de suivi | ⬜ |
| H03 | Workspace Power BI Lireka accessible en Contributor | ⬜ |
| H04 | Marge brute = CA − coût achat − coût transport réel *(à valider finance)* | ⬜ |
| H05 | Dashboards DHL/FedEx/UPS consultables comme référence de modèle | ⬜ |

---

## Plan d'action immédiat (avant J1)

- [ ] Envoyer email de kick-off à Marc Bordier
- [ ] Transmettre checklist accès et données
- [ ] Obtenir engagement : données livrées **avant J1 10h**
- [ ] Identifier un référent technique et logistique joignable pendant les 4 jours

---

*Revue en clôture J4.*
