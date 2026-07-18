# Registre des livrables — Lireka × ZineInsights

> **Référence contractuelle** : [`devis.md`](devis.md) — forfait 4 jours, 1 800 € HT.

---

## Légende statuts

| Symbole | Signification |
|---------|---------------|
| ⬜ | Non démarré |
| 🔄 | En cours |
| ✅ | Livré & validé |
| ⏸️ | En attente (dépendance) |

---

## Livrables contractuels (devis)

| ID | Livrable | Jour cible | Statut | Validé par |
|----|----------|------------|--------|------------|
| L01 | Intégration La Poste, Colis Privé, Chronopost dans Power BI | J2 | ⬜ | Marc Bordier |
| L02 | CSV commandes importé et structuré dans Power BI | J2 | ⬜ | Marc Bordier |
| L03 | Jointure factures ↔ commandes par numéro de suivi | J3 | ⬜ | Marc Bordier |
| L04 | Dashboard profitabilité — marge brute par pays et par type de commande *(1 rapport, 2 axes ; mesure `[Marge Brute]` dans `_Mesures.tmdl`)* | J3 | ⬜ | Marc Bordier |
| L05 | Formation utilisateurs *(selon disponibilité)* | J4 | ⬜ | Participants |
| L06 | Documentation du processus | J4 | ⬜ | Marc Bordier |

---

## Hors périmètre devis (ne pas livrer sauf accord écrit)

| Élément | Raison |
|---------|--------|
| 3 dashboards transporteurs dédiés (un par transporteur) | Non mentionné au devis |
| Dashboard synthèse direction | Non mentionné au devis |
| Dashboard écarts coûts transport (rapport séparé) | Non mentionné au devis |
| 3 sessions formation × 2 h | Non mentionné au devis |
| Dictionnaire de données exhaustif | Non mentionné au devis |
| Dossier de clôture / architecture complète | Non mentionné au devis |

> **Postes Canada** : les données colis backend sont **dans le périmètre** du modèle profitabilité (confirmé Marc). Seuls les dashboards transporteurs **dédiés** (un par transporteur) sont hors périmètre — pas l'intégration des données Postes Canada.

---

## Critères d'acceptation

### Transporteurs
- [ ] La Poste, Colis Privé et Chronopost intégrés dans Power BI
- [ ] Postes Canada : colis backend (`package.csv`) intégrés au modèle profitabilité *(dans le périmètre — confirmé Marc ; coût estimé, pas de dashboard dédié)*
- [ ] Données importées depuis CSV sur au moins 1 mois de factures

### Commandes
- [ ] Export backend intégré dans Power BI
- [ ] Schéma documenté dans la documentation du processus

### Jointure
- [ ] Liaison opérationnelle par numéro de suivi
- [ ] Taux de matching documenté (objectif indicatif, non contractuel)

### Profitabilité
- [ ] **Un** dashboard profitabilité livré (nombre de pages/onglets : au choix du prestataire)
- [ ] Marge brute visible par **pays**
- [ ] Marge brute visible par **type de commande**
- [ ] Coût transport réel utilisé (issu des factures jointes)

### Formation
- [ ] Au moins une session proposée durant la mission *(si disponibilité équipes)*

### Documentation
- [ ] Processus d'import et de refresh documenté

---

*Mis à jour le 14 juillet 2026*
