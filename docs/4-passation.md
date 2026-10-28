# 4. Passation

Tout ce qu'il faut pour exploiter le rapport sans dépendre du prestataire : accès, architecture, exploitation courante, contacts et points connus.

État au 26/10/2026.

---

## 1. Architecture

```
Backoffice Lireka (COEX)
   │  synchronisation quotidienne à partir de 2:00
   ▼
Base analytique PostgreSQL (COEX)  10.111.119.1:5432 / analytics / analytics_views
   │  tunnel WireGuard (réseau COEX)
   ▼
VPS Lireka 20.19.33.4 (Windows Server, Azure, Inforeso)
   ├── Passerelle Power BI « Lireka-Gateway »
   └── Serveur Git : C:\git\lireka.git
   │  actualisation quotidienne à 6:00
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
| Dépôt Git `C:\git\lireka.git` | Clés SSH des membres du groupe `lireka-git` | voir [3-git-et-publication.md](3-git-et-publication.md) |
| Base PostgreSQL (compte `liber_power_bi`, lecture seule) | Identifiants enregistrés dans la passerelle | COEX |
| Tunnel WireGuard | Configuration installée sur le VPS | COEX |
| SharePoint **PowerBI-Lireka** | Fichiers et sauvegardes | Lireka |

Au 28/10/2026, la migration vers l'espace de travail LIREKA - Power BI est faite : Marc Bordier et Emma Henry voient le rapport, et le modèle apparaît dans Power BI Desktop. L'accès Git SSH depuis l'extérieur reste ouvert (voir [6-recette.md](6-recette.md)).

Licences : chaque personne qui ouvre le rapport ou publie a besoin d'une licence **Power BI Pro**.

Aucun mot de passe n'est écrit dans ce document ni dans le projet.

---

## 3. Exploitation courante

| Quoi | Où | Fréquence |
|---|---|---|
| Vérifier que l'actualisation de 6:00 a réussi | Modèle sémantique > Historique d'actualisation | Chaque matin, ou sur alerte e-mail |
| Vérifier la fraîcheur des données | Carte « Data through … » du rapport | À l'ouverture |
| Publier une modification | voir [3-git-et-publication.md](3-git-et-publication.md) | À chaque évolution |

**Si l'actualisation échoue**, regarder le message d'erreur (*Historique d'actualisation* > *Afficher*) :

| Message | Cause probable | Action |
|---|---|---|
| `relation ... does not exist` | Synchronisation COEX en cours ou trop longue | Relancer l'actualisation plus tard ; si cela se répète, prévenir COEX |
| Passerelle hors ligne, délai dépassé | VPS arrêté, service de la passerelle ou tunnel WireGuard arrêtés | Vérifier le VPS (Inforeso), puis les services « On-premises data gateway » et WireGuard |
| Erreur d'identifiants sur la source | Mot de passe de `liber_power_bi` changé | Mettre à jour la connexion dans *Gérer les connexions et les passerelles* (identifiants fournis par COEX) |

---

## 4. Contacts

| Rôle | Personne | Pour |
|---|---|---|
| Décision, règles de calcul | Marc Bordier, Président (mbordier@lireka.com) | Validation des définitions |
| Utilisation, évolutions du rapport | Emma Henry, cofondatrice et directrice générale (ehenry@lireka.com) | Pilotage, nouveaux tableaux |
| Données, base analytique, WireGuard | Michal Kašpar, COEX (michal.kaspar@coex.cz) | Contenu et définition des données |
| VPS, comptes Microsoft 365, réseau | Damien Nivon, Inforeso (support@inforeso.fr) | Infrastructure |
| Modèle et rapport Power BI | Otmane Boulahia, ZineInsights (otmane@zineinsight.com) | Suivi offert le premier mois |

---

## 5. Points connus

| Point | Statut |
|---|---|
| Tableau de profitabilité du backoffice différent de Power BI | Le backoffice utilise des coûts estimés, Power BI les coûts réels. COEX aligne le backoffice sur les mêmes valeurs (annoncé le 26/10/2026). |
| Définition de la marge brute | Décisions à prendre par Lireka : intégrer ou non les retours et remboursements, les frais de paiement (`payment_cost_eur`) et les coûts génériques ; traitement des commandes au statut PICKED. |
| Droits et taxes des commandes DDP | Power BI les déduit de la marge ; la marge calculée par COEX (`contribution_profit_eur`) ne semble pas le faire (exemple : commande 20260914-KE-06518B, 504,07 € de droits). À confirmer avec COEX. |
| Website B2B : variations N-1 très élevées | Activité B2B quasi nulle en 2024 : les pourcentages sont exacts. |
| Transporteur des colis | Déduit du numéro de suivi. COEX fournit désormais le transporteur réel (`package.carrier`), utilisable dans une prochaine version. |
| Titres et auteurs des livres | Titres disponibles dans `v_book_attributes` ; auteurs annoncés plus tard par COEX. Non encore intégrés. |
| Accès Git depuis l'extérieur | Port 22 à ouvrir dans Azure par Inforeso. |
