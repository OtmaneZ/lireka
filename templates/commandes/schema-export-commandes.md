# Schéma — Export commandes backend

> Schéma cible pour l'export CSV des commandes clients depuis le backend Lireka.
> **À valider** avec le référent technique Lireka.

## Colonnes

| Colonne | Type | Obligatoire | Description |
|---------|------|-------------|-------------|
| id_commande | string | oui | Identifiant unique commande |
| date_commande | datetime (ISO 8601) | oui | Date et heure de la commande |
| pays_livraison | string (ISO alpha-3) | oui | Pays de livraison |
| type_commande | string | oui | Type de commande (B2C, B2B…) |
| transporteur | string | oui | Transporteur assigné |
| numero_suivi | string | oui | Numéro de suivi (clé de liaison) |
| ca_ht | decimal | oui | Chiffre d'affaires HT |
| cout_achat | decimal | oui | Coût d'achat des livres |
| cout_transport_estime | decimal | oui | Coût transport estimé (backend) |
| nombre_articles | int | non | Nombre de livres |
| poids_total | decimal | non | Poids total en kg |

## Colonnes optionnelles (souhaitables)

| Colonne | Type | Description |
|---------|------|-------------|
| ca_ttc | decimal | Chiffre d'affaires TTC |
| code_promo | string | Code promotionnel utilisé |
| canal_acquisition | string | Canal marketing d'origine |
| filiale | string | Lireka / Arthaud |

## Convention de nommage

```
commandes_{YYYYMMDD}.csv
```

## Exemple

Voir : `data/samples/commandes/commandes_202606.csv`

## Questions ouvertes

- [ ] Nom exact du champ numéro de suivi côté backend ?
- [ ] Données Arthaud incluses ou séparées ?
- [ ] Fréquence d'export possible (quotidien, hebdo) ?
- [ ] Volumétrie mensuelle ?
