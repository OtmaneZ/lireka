# Inventaire des sources de données

> **Mission** : 4 jours — [`../../project/devis.md`](../../project/devis.md)  
> **Statut** : 🟡 En attente de collecte  
> **Dernière mise à jour** : 12 juillet 2026

---

## Instructions

Ce document recense toutes les sources de données nécessaires à la mission.  
Chaque source doit être complétée avec un échantillon dans `data/samples/`.

**Légende statut** : ⬜ Non reçu · 🔄 En analyse · ✅ Validé

---

## 1. Transporteurs — Factures CSV

### 1.1 Existants (référence)

| Transporteur | Statut | Format | Fréquence | Emplacement | Contact Lireka |
|-------------|--------|--------|-----------|-------------|----------------|
| DHL | ✅ Existant | CSV | Mensuel | Power BI existant | *À compléter* |
| FedEx | ✅ Existant | CSV | Mensuel | Power BI existant | *À compléter* |
| UPS | ✅ Existant | CSV | Mensuel | Power BI existant | *À compléter* |

**Actions audit (J1, rapide)** :
- [ ] Obtenir accès lecture aux 3 dashboards existants
- [ ] Identifier le schéma CSV / modèle pour intégrer les 3 nouveaux transporteurs
- [ ] Repérer le champ numéro de suivi et les mesures DAX utiles

### 1.2 À intégrer

| Transporteur | Statut | Format attendu | Fréquence | Échantillon reçu | Notes |
|-------------|--------|---------------|-----------|-----------------|-------|
| La Poste | ⬜ | CSV factures | Mensuel | ⬜ | *Format à analyser* |
| Colis Privé | ⬜ | CSV factures | Mensuel | ⬜ | *Format à analyser* |
| Chronopost | ⬜ | CSV factures | Mensuel | ⬜ | *Format à analyser* |

**Champs attendus par facture (schéma cible)** :

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `numero_facture` | string | ✅ | Identifiant facture transporteur |
| `date_facture` | date | ✅ | Date d'émission |
| `numero_suivi` | string | ✅ | **Clé de liaison** avec commandes |
| `cout_transport` | decimal | ✅ | Montant facturé (HT ou TTC — à harmoniser) |
| `poids` | decimal | ⬜ | Poids du colis (kg) |
| `pays_destination` | string | ⬜ | Pays de livraison |
| `service` | string | ⬜ | Type de service (express, standard…) |
| `devise` | string | ⬜ | EUR par défaut |

---

## 2. Commandes clients — Export backend

| Élément | Détail |
|---------|--------|
| **Source** | Backend Lireka |
| **Format** | CSV |
| **Fréquence** | À définir (quotidien / hebdo / mensuel) |
| **Statut** | ⬜ Non reçu |
| **Contact** | *Référent technique Lireka* |

### Champs attendus (à valider avec Lireka)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `id_commande` | string | ✅ | Identifiant unique commande |
| `date_commande` | datetime | ✅ | Date de la commande |
| `pays_livraison` | string | ✅ | Pays destination |
| `type_commande` | string | ✅ | Type (B2C, B2B, marketplace…) |
| `ca_ht` | decimal | ✅ | Chiffre d'affaires HT |
| `ca_ttc` | decimal | ⬜ | Chiffre d'affaires TTC |
| `cout_achat` | decimal | ✅ | Coût d'achat des livres |
| `cout_transport_estime` | decimal | ✅ | Coût transport estimé (backend) |
| `transporteur` | string | ✅ | Nom du transporteur utilisé |
| `numero_suivi` | string | ✅ | **Clé de liaison** avec factures |
| `nombre_articles` | int | ⬜ | Nombre de livres |
| `poids_total` | decimal | ⬜ | Poids total commande |

### Questions ouvertes (à poser au kick-off)

- [ ] Quel est le nom exact du champ numéro de suivi dans l'export ?
- [ ] Le numéro de suivi est-il renseigné pour 100% des commandes expédiées ?
- [ ] Format du numéro de suivi : identique à celui des factures transporteurs ?
- [ ] Période d'historique disponible ?
- [ ] Volumétrie : combien de commandes par mois ?
- [ ] Le coût transport estimé : quelle est la formule de calcul ?
- [ ] Données Arthaud Grenoble incluses ou séparées ?

---

## 3. Outils & accès

| Outil | Accès nécessaire | Statut | Contact |
|-------|-----------------|--------|---------|
| Power BI Service | Workspace Lireka — Contributor | ⬜ | Réf. technique |
| Power BI Desktop | Licence (ZineInsights) | ✅ | — |
| Claude AI ↔ Power BI | Lecture (audit connexion existante) | ⬜ | Réf. technique |
| Partage fichiers | OneDrive / SharePoint / SFTP | ⬜ | Réf. technique |

---

## 4. Volumétrie estimée

| Source | Volume estimé | Période |
|--------|--------------|---------|
| Commandes | *À compléter* / mois | 1 mois minimum |
| Factures DHL | Existant | Référence modèle |
| Factures FedEx | Existant | Référence modèle |
| Factures UPS | Existant | Référence modèle |
| Factures La Poste | *À compléter* / mois | 1 mois minimum |
| Factures Colis Privé | *À compléter* / mois | 1 mois minimum |
| Factures Chronopost | *À compléter* / mois | 1 mois minimum |

---

## 5. Checklist de collecte (J1)

- [ ] Factures La Poste (1 mois) → `data/raw/transporteurs/la-poste/`
- [ ] Factures Colis Privé (1 mois) → `data/raw/transporteurs/colis-prive/`
- [ ] Factures Chronopost (1 mois) → `data/raw/transporteurs/chronopost/`
- [ ] Export commandes backend (1 mois) → `data/raw/commandes/`
- [ ] Accès Power BI workspace (Contributor)
- [ ] Accès dashboards DHL / FedEx / UPS (référence)
- [ ] Formule marge brute validée (finance)

---

*À compléter au fil de la mission.*
