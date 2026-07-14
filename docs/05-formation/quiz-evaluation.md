# Quiz d'évaluation — Autonomie Power BI

> **⚠️ Hors périmètre devis** — Support optionnel. Non requis pour la clôture du forfait 4 jours.

> **Durée** : 10 minutes  
> **Seuil d'autonomie** : ≥ 8/10 (80%)

---

## Questions

### Q1. Où consulte-t-on les dashboards Lireka en lecture seule ?

- [ ] A) Power BI Desktop
- [ ] B) Power BI Service (navigateur)
- [ ] C) Excel
- [ ] D) PowerPoint

<details>
<summary>Réponse</summary>
B) Power BI Service — c'est l'interface web pour consulter et partager les rapports.
</details>

---

### Q2. Comment filtrer un rapport sur un pays spécifique ?

- [ ] A) Modifier le dataset
- [ ] B) Utiliser un Slicer ou cliquer sur un visuel
- [ ] C) Supprimer les autres pays du CSV
- [ ] D) Envoyer un email au data analyst

<details>
<summary>Réponse</summary>
B) Utiliser un Slicer ou cliquer sur un élément d'un visuel (cross-filter).
</details>

---

### Q3. Quelle est la formule de la marge brute réelle chez Lireka ?

- [ ] A) CA TTC − Coût transport estimé
- [ ] B) CA HT − Coût achat − Coût transport réel
- [ ] C) CA HT − Coût transport estimé
- [ ] D) CA TTC − Coût achat

<details>
<summary>Réponse</summary>
B) Réponse simplifiée à des fins pédagogiques (session bases).

**Formule complète actée (7 postes)** — Slack Marc Bordier, 13/07/2026 :
Revenue (incl. shipping revenue if relevant) − COGS − inbound transport − outbound transport − duties & taxes − marketplace commissions − shipping supplies.
Voir [`project/perimetre-verrouille.md`](../../project/perimetre-verrouille.md).
</details>

---

### Q4. Quel champ relie les commandes aux factures transporteurs ?

- [ ] A) id_commande
- [ ] B) numero_facture
- [ ] C) numero_suivi
- [ ] D) pays_livraison

<details>
<summary>Réponse</summary>
C) Le numéro de suivi — présent à la fois dans l'export commandes et les factures transporteurs.
</details>

---

### Q5. Combien de transporteurs sont intégrés dans Power BI Lireka ?

- [ ] A) 3 (DHL, FedEx, UPS)
- [ ] B) 4
- [ ] C) 6 (DHL, FedEx, UPS, La Poste, Colis Privé, Chronopost)
- [ ] D) 7 (DHL, FedEx, UPS, La Poste, Colis Privé, Chronopost, Postes Canada)

<details>
<summary>Réponse</summary>
D) 7 transporteurs (dont Postes Canada), + une modalité `INCONNU` pour les colis dont le transporteur n'a pas pu être identifié à partir du numéro de suivi.
</details>

---

### Q6. Quel outil utilise-t-on pour CRÉER un nouveau rapport ?

- [ ] A) Power BI Service
- [ ] B) Power BI Desktop
- [ ] C) Power Automate
- [ ] D) Claude AI

<details>
<summary>Réponse</summary>
B) Power BI Desktop — le logiciel local pour créer et modifier les rapports.
</details>

---

### Q7. Où publier un rapport de test pour ne pas impacter la production ?

- [ ] A) Workspace "Lireka - Transport"
- [ ] B) Workspace "Lireka - Profitabilité"
- [ ] C) Workspace "Lireka - Formation"
- [ ] D) Sur son PC uniquement

<details>
<summary>Réponse</summary>
C) Le workspace "Formation" est le bac à sable pour s'exercer.
</details>

---

### Q8. Que signifie un "écart coût transport" positif ?

- [ ] A) Le transport a coûté moins cher que prévu
- [ ] B) Le transport a coûté plus cher que l'estimation backend
- [ ] C) Le transporteur a remboursé Lireka
- [ ] D) Le numéro de suivi est incorrect

<details>
<summary>Réponse</summary>
B) Un écart positif = coût réel > coût estimé → le transport a coûté plus cher que prévu.
</details>

---

### Q9. Quel visuel est le plus adapté pour afficher un KPI unique (ex: marge brute totale) ?

- [ ] A) Tableau
- [ ] B) Graphique en barres
- [ ] C) Carte (Card)
- [ ] D) Carte géographique

<details>
<summary>Réponse</summary>
C) La Carte (Card) affiche une seule valeur en grand — idéal pour les KPIs.
</details>

---

### Q10. Comment remettre tous les filtres à zéro dans un rapport ?

- [ ] A) Fermer et rouvrir le navigateur
- [ ] B) Cliquer sur le bouton "Reset" (Réinitialiser les filtres)
- [ ] C) Supprimer le rapport
- [ ] D) Contacter le support

<details>
<summary>Réponse</summary>
B) Le bouton Reset en haut du rapport remet tous les slicers et filtres à leur état initial.
</details>

---

## Grille de notation

| Score | Niveau | Recommandation |
|-------|--------|----------------|
| 10/10 | ⭐ Expert | Totalement autonome |
| 8-9/10 | ✅ Autonome | Peut créer ses propres dashboards |
| 6-7/10 | 🟡 Intermédiaire | Accompagnement ponctuel suffisant |
| < 6/10 | 🔴 Débutant | Session de rattrapage recommandée |

---

## Fiche résultat

| Participant | Date | Score | Niveau | Signature |
|------------|------|-------|--------|-----------|
| | | /10 | | |
| | | /10 | | |
| | | /10 | | |

---

*Quiz ZineInsights — Juillet 2026*
