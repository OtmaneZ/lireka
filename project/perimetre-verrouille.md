# Périmètre verrouillé — Lireka × ZineInsights

> Ce document fixe le périmètre exact de la mission. Toute demande ou exploration
> au-delà de ce qui est listé ici est HORS PÉRIMÈTRE pour l'instant.

## Source unique du périmètre

1. **`project/devis.md`** — contrat signé (Malt, réf. M2607-3F8JI, accepté par Marc
   Bordier le 10/07/2026). 4 jours, 1 800 € HT. Les 6 livrables du devis, rien de plus,
   rien de moins.
2. **Formule de marge brute** — précisée par Marc Bordier par message Slack le
   13/07/2026 (canal mission Lireka, 16h09), en réponse directe au livrable L04 du
   devis (« Dashboards de profitabilité — marge brute par pays, par type de commande »).
   Cette formule ne constitue PAS un livrable supplémentaire : elle définit le terme
   « marge brute » du devis. Formule :

```
Revenue (incl. shipping revenue if relevant)
- COGS
- Inbound transportation costs
- Outbound transportation costs (DHL, FedEx, La Poste, etc.)
- Duties and Taxes
- Marketplace commission fees (fixed and variable)
- Shipping supplies
```

## Ce qui est dans le périmètre

1. **Intégration des 3 transporteurs manquants** (La Poste, Colis Privé, Chronopost)
2. **Import et structuration** du fichier CSV commandes backend
3. **Jointure factures ↔ commandes** par numéro de suivi
4. **Dashboards de profitabilité** — marge brute par pays, par type de commande
5. **Formation des utilisateurs**
6. **Documentation du processus**

La formule de marge ci-dessus, implémentée dans `_Mesures.tmdl` (mesure `Marge Brute`)
et câblée sur le rapport L04.

## Ce qui n'est PAS dans le périmètre pour l'instant

- Toute exploration au-delà de la formule confirmée (ex. tests de
  `contribution_profit_eur`, isolation poste par poste des returns/generic costs dans
  `scripts/validation/margin_analysis.py`) : ce sont des outils de diagnostic interne
  utilisés pour valider la formule, PAS des livrables. Ils restent dans le repo comme
  scripts de contrôle, mais ne font l'objet d'aucun visuel, mesure exposée, ou
  documentation client au-delà de ce qui sert à vérifier la formule ci-dessus.
- Toute décision non tranchée : statut CANCELLED, périmètre exact du « if relevant » sur
  le shipping revenue, seuil de tolérance sur la résolution de jointure par date,
  niveau d'intégration Colis Privé/Postes Canada. Ces points restent ouverts — voir
  `AUDIT.md` §6 pour les questions formulées à Marc. Aucun développement supplémentaire
  ne doit anticiper leur réponse.
- Tout ce qui n'apparaît ni dans `devis.md` ni dans le message Slack du 13/07 : pas de
  nouveau dashboard, pas de nouvelle mesure, pas de nouvel import de données, sans
  nouvelle instruction explicite de Marc.

## Traçabilité

| Élément | Source | Statut |
|---------|--------|--------|
| Devis (6 livrables) | `project/devis.md`, PDF signé Malt | Contractuel |
| Formule de marge (7 postes) | Slack, Marc Bordier, 13/07/2026 16h09 | Confirmé, actée |
| Tout le reste | Non demandé | Hors périmètre |
