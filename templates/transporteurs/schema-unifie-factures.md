# Schéma unifié — Factures transporteurs

> Ce fichier définit le schéma cible pour toutes les factures transporteurs.
> Chaque transporteur est mappé vers ce schéma via son script ETL dédié.

## Colonnes

| Colonne | Type | Obligatoire | Description |
|---------|------|-------------|-------------|
| numero_facture | string | oui | Identifiant unique de la facture |
| date_facture | date (YYYY-MM-DD) | oui | Date d'émission |
| numero_suivi | string | oui | Numéro de suivi colis (clé de liaison) |
| cout_transport | decimal | oui | Montant facturé en EUR |
| poids | decimal | non | Poids en kg |
| pays_destination | string (ISO alpha-3) | non | Pays de livraison |
| service | string | non | Type de service |
| devise | string | non | Devise (défaut: EUR) |

## Transporteurs supportés

- DHL (existant)
- FedEx (existant)
- UPS (existant)
- La Poste
- Colis Privé
- Chronopost

## Convention de nommage

```
{transporteur}_factures_{YYYYMM}.csv
```

## Exemple

Voir : `data/samples/transporteurs/la-poste/la-poste_factures_202606.csv`
