# 6. Compte rendu de recette

Recette de la mise en production du rapport Power BI de profitabilité dans l'environnement de Lireka (devis D-2026-004, ligne « Recette » : refresh planifié validé, contrôle de la marge, contrôle des accès, compte rendu de recette).

Rédigé le 26/10/2026. Constats du 28/10/2026 portés dans les sections 1 et 3. Les points encore marqués **À constater** restent ouverts.

---

## Synthèse

| Point de recette | Statut |
|---|---|
| 1. Refresh planifié validé | Fait (28/10/2026) : actualisation de 6:00 réussie dans l'espace LIREKA - Power BI |
| 2. Contrôle de la marge | Fait (voir section 2) ; décisions de définition en attente de Lireka |
| 3. Contrôle des accès | Rapport visible par Marc et Emma, modèle visible dans Desktop (28/10/2026) ; accès Git SSH d'Emma encore à constater |
| 4. Serveur Git et migration du dépôt | Fait : dépôt livré le 26/10/2026 et testé par SSH ; port 22 à ouvrir dans Azure |

---

## 1. Refresh planifié

| Contrôle | Résultat |
|---|---|
| Échecs constatés avant recette | 20/10 et 23/10/2026 à 06:08 : vues `analytics_views` momentanément absentes pendant la synchronisation COEX. Cause corrigée par COEX le 26/10/2026. |
| Avertissements de format à chaque actualisation | Corrigés le 25/10/2026 ; actualisation du 26/10/2026 à 01:44 terminée sans avertissement. |
| Actualisation de 6:00 réussie dans l'espace LIREKA - Power BI | **Fait** (28/10/2026) |

---

## 2. Contrôle de la marge

### Corrections apportées

| Correction | Effet |
|---|---|
| Frais de port comptés une seule fois (ils sont déjà inclus dans le montant de la commande) | Revenu et marge diminués du port compté en double : 3 459 900,71 € sur tout l'historique |
| Chiffre d'affaires hors TVA (`order_amount_excl_vat_eur`, fourni par COEX le 26/10/2026) | Revenu et marge diminués du montant de la TVA |

### Résultat sur l'année 2025 (General View : Website B2C, Website B2B, Marketplaces)

| Canal | Revenue | Gross Profit | Gross Margin | Référence Lireka |
|---|---|---|---|---|
| Website B2C | 5 430 k€ | 1 265 k€ | 23,3 % | 20 % (site) |
| Website B2B | 449 k€ | 107 k€ | 23,8 % | 20 % (site) |
| Marketplaces | 3 381 k€ | 399 k€ | 11,8 % | 10 % |
| **Total** | **9 259 k€** | **1 771 k€** | **19,1 %** | **17 %** |

Évolution de la marge affichée : 27 % (09/10/2026, 12 mois glissants, TVA et port en double inclus), 20,8 % après correction du port, 19,1 % après passage hors TVA.

L'écart restant avec la référence de 17 % correspond à des postes que la formule actuelle n'inclut pas (retours et remboursements, frais de paiement, coûts génériques) : décision de définition à prendre par Lireka.

### Comparaison avec le tableau de profitabilité du backoffice (septembre 2026, tous canaux, avant passage hors TVA)

| Poste | Power BI | Backoffice |
|---|---|---|
| Chiffre d'affaires | 1 212 739 € | 1 205 789 € |
| Coût d'achat | 586 685 € | 604 880 € |
| Transport amont | 18 300 € | 17 985 € |
| Transport sortant | 236 811 € | 251 603 € |
| Droits et taxes | 24 496 € | 24 154 € |
| Commissions marketplace | 103 410 € | 98 366 € |
| Fournitures | 12 619 € | 17 388 € |
| Retours et remboursements | non déduits | 13 877 € |
| Frais de paiement | non déduits | 4 634 € |
| Coûts génériques | non déduits | 7 480 € |
| **Marge brute** | **230 419 €** | **162 449 €** |

Explication (COEX, 26/10/2026) : le backoffice utilise des coûts estimés, la base analytique les coûts réels. COEX aligne le backoffice sur les mêmes valeurs.

### Décisions attendues de Lireka

1. Intégrer ou non dans la marge brute : retours et remboursements, frais de paiement, coûts génériques.
2. Droits et taxes des commandes DDP (exemple 20260914-KE-06518B : 504,07 €).
3. Commandes au statut PICKED : comptées ou non.

---

## 3. Contrôle des accès

| Contrôle | Résultat |
|---|---|
| Marc Bordier voit le rapport dans l'espace LIREKA - Power BI | **Fait** (28/10/2026) |
| Emma Henry voit le rapport dans l'espace LIREKA - Power BI | **Fait** (28/10/2026) |
| Le modèle apparaît dans Power BI Desktop (Obtenir les données > Modèles sémantiques Power BI) | **Fait** (28/10/2026) |
| Accès Git d'Emma Henry par SSH | **À constater** (après ouverture du port 22) |

---

## 4. Serveur Git et dépôt

| Contrôle | Résultat |
|---|---|
| Git for Windows et OpenSSH Server installés sur le VPS | Fait (25/10/2026) |
| Authentification par mot de passe désactivée | Fait, vérifié (`passwordauthentication no`) |
| Dépôt `C:\git\lireka.git` créé, historique protégé | Fait (26/10/2026) |
| Livraison initiale : 365 fichiers, sans données ni identifiants | Fait, commit `9a580b7` |
| Récupération du dépôt par SSH avec clé | Testé sur le VPS : réussi |
