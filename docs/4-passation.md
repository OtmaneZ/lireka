# 4. Passation

Tout ce qu'il faut pour exploiter le rapport sans dépendre du prestataire : architecture, accès, exploitation courante, contacts et points connus.

État au 06/11/2026.

---

## 1. Architecture

```
Backoffice Lireka (COEX)
   │  synchronisation quotidienne, de 2:00 à 6:30 environ
   ▼
Base analytique PostgreSQL (COEX)  10.111.119.1:5432 / analytics / analytics_views
   │  tunnel WireGuard (réseau COEX)
   ▼
VPS Lireka 20.19.33.4 (Windows Server, Azure, Inforeso)
   ├── Passerelle Power BI « Lireka-Gateway »
   └── Serveur Git : C:\git\lireka.git
   │  actualisation quotidienne à 8:00
   ▼
Service Power BI, espace de travail « LIREKA - Power BI »
   ├── Modèle sémantique Lireka_Profitabilite
   └── Rapport Lireka_Profitabilite
```

---

## 2. Accès

| Ressource | Accès | Gestion |
|---|---|---|
| Espace de travail **LIREKA - Power BI** | Marc Bordier et Emma Henry : Admin | Lireka |
| Compte de service **powerbi-gateway@lireka.com** | Propriétaire de la passerelle et du modèle publié | Lireka, Inforeso |
| VPS (Bureau à distance) | Compte administrateur | Inforeso |
| Dépôt Git `C:\git\lireka.git` | Clés SSH des membres du groupe `lireka-git` (voir le document 3) | Administrateur du VPS |
| Base PostgreSQL (compte `liber_power_bi`, lecture seule) | Identifiants enregistrés dans la passerelle | COEX |
| Tunnel WireGuard | Configuration installée sur le VPS | COEX |
| SharePoint **PowerBI-Lireka** | Documentation et sauvegardes | Lireka |

**Donner accès au rapport à une personne de Lireka** : dans l'espace de travail, *Gérer l'accès*, l'ajouter avec le rôle **Lecteur**. Seuls les Admin de l'espace peuvent le faire. Une personne extérieure à Lireka (COEX par exemple) doit d'abord être invitée dans le tenant Microsoft 365 de Lireka par Inforeso.

**Licences** : chaque personne qui ouvre le rapport ou publie a besoin d'une licence **Power BI Pro**.

Aucun mot de passe n'est écrit dans ce document ni dans le projet.

---

## 3. Exploitation courante

| Quoi | Où | Fréquence |
|---|---|---|
| Vérifier que l'actualisation de 8:00 a réussi | Modèle sémantique > Historique d'actualisation | Chaque matin, ou sur alerte e-mail |
| Vérifier la fraîcheur des données | Carte « Data through » du rapport | À l'ouverture |
| Publier une modification | Voir le document 3 | À chaque évolution |

**Si l'actualisation échoue**, lire le message d'erreur (*Historique d'actualisation* > *Afficher*) :

| Message | Cause probable | Action |
|---|---|---|
| `relation ... does not exist` | Synchronisation COEX en cours ou trop longue | Relancer l'actualisation plus tard. Si cela se répète, prévenir COEX. |
| `Exception while reading from stream` | Connexion à la base interrompue pendant une lecture longue | Relancer l'actualisation. Si cela se répète, prévenir COEX. |
| Passerelle hors ligne, délai dépassé | VPS arrêté, ou service de la passerelle ou tunnel WireGuard arrêté | Faire vérifier le VPS par Inforeso, puis les services « On-premises data gateway » et WireGuard. |
| Erreur d'identifiants sur la source | Mot de passe de `liber_power_bi` changé | Mettre à jour la connexion dans *Gérer les connexions et les passerelles*, avec les identifiants fournis par COEX. |

---

## 4. Contacts

| Rôle | Personne | Pour |
|---|---|---|
| Décision, règles de calcul | Marc Bordier, Président (mbordier@lireka.com) | Validation des définitions |
| Utilisation, évolutions du rapport | Emma Henry, cofondatrice et directrice générale (ehenry@lireka.com) | Pilotage, nouveaux tableaux |
| Données, base analytique, WireGuard | Michal Kašpar, COEX (michal.kaspar@coex.cz) | Contenu et définition des données |
| VPS, comptes Microsoft 365, réseau | Damien Nivon, Inforeso (support@inforeso.fr) | Infrastructure |
| Modèle et rapport Power BI | Otmane Boulahia, ZineInsights (otmane@zineinsight.com) | Suivi offert le premier mois après la recette |

---

## 5. Points à suivre

| Point | Statut |
|---|---|
| **Licence Pro du compte powerbi-gateway@lireka.com** | Essai gratuit jusqu'au 26/12/2026 environ. Sans licence Pro à cette date, l'actualisation s'arrêtera. À attribuer par Inforeso. |
| Accès de Clémence et de Michal Kašpar | À donner dans l'espace de travail (rôle Lecteur). Michal doit d'abord être invité dans le tenant Lireka. |
| Accès Git d'Emma Henry | Procédure envoyée le 30/10/2026. En attente de sa clé publique. |
| Auteurs des livres | COEX prépare la donnée dans la base analytique. Ajout au rapport dès qu'elle sera disponible. |
| Frais de paiement | Disponibles en base (`payment_cost_eur`), non intégrés à la marge brute. À intégrer si Lireka le souhaite. |
| Droits et taxes des commandes DDP | Power BI les déduit de la marge. La marge calculée par COEX (`contribution_profit_eur`) ne semble pas le faire, par exemple sur la commande 20260914-KE-06518B (504,07 € de droits). À confirmer avec COEX. |
| Website B2B : variations sur un an très élevées | L'activité B2B était quasi nulle en 2024 : les pourcentages sont exacts. |

---

## 6. Décisions prises

| Sujet | Décision |
|---|---|
| Frais de port | Comptés une seule fois : ils sont déjà inclus dans le montant de la commande. |
| Chiffre d'affaires | Hors TVA (`order_amount_excl_vat_eur`). |
| Retours et remboursements | Déduits de la marge brute depuis le 27/10/2026, hors commandes annulées. |
| Coûts génériques | Hors marge brute. À 0 depuis le 01/01/2025 selon COEX, colonne retirée des tableaux. |
| Commandes en préparation | Non affichées : la base ne contient que les commandes à l'état final (validé le 29/10/2026). |
| Heure d'actualisation | 8:00, après la fin de la synchronisation COEX (demande de COEX, 29/10/2026). |
