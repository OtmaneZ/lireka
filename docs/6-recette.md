# 6. Compte rendu de recette

Recette de la mise en production du rapport Power BI de profitabilité dans l'environnement de Lireka (devis D-2026-004). La ligne « Recette » du devis comprend : actualisation planifiée validée, contrôle de la marge, contrôle des accès, compte rendu de recette.

Version finale du 06/11/2026.

---

## Synthèse

| Point de recette | Statut |
|---|---|
| 1. Actualisation planifiée | **Validée.** Actualisation quotidienne à 8:00 dans l'espace LIREKA - Power BI. |
| 2. Contrôle de la marge | **Validé par Lireka le 03/11/2026**, par comparaison avec les comptes du troisième trimestre. |
| 3. Contrôle des accès | **Validé** pour Marc Bordier, Emma Henry et le compte de la passerelle. Accès de Clémence et de Michal Kašpar à donner par Lireka. |
| 4. Serveur Git et migration du dépôt | **Fait.** Dépôt en place sur le VPS, accessible de l'extérieur par clé SSH depuis le 28/10/2026. |

---

## 1. Actualisation planifiée

| Contrôle | Résultat |
|---|---|
| Actualisation planifiée réussie dans l'espace LIREKA - Power BI | Fait, depuis le 28/10/2026 |
| Heure d'actualisation | 8:00 depuis le 29/10/2026, à la demande de COEX, dont la synchronisation se termine vers 6:30 |
| Échecs des 20/10 et 23/10/2026 | Synchronisation COEX anormalement longue. Corrigé par COEX le 26/10/2026. |
| Échec du 01/11/2026 | Connexion interrompue pendant la lecture des titres des livres. Corrigé le 03/11/2026 par la vue légère `v_book_titles`. |
| Actualisations des 02/11 et 03/11/2026 | Réussies, en 19 à 22 minutes |

---

## 2. Contrôle de la marge

### Corrections apportées pendant la recette

| Correction | Effet |
|---|---|
| Frais de port comptés une seule fois | Ils étaient comptés en double, alors qu'ils sont déjà inclus dans le montant de la commande. |
| Chiffre d'affaires hors TVA (`order_amount_excl_vat_eur`, fourni par COEX le 26/10/2026) | Revenu et marge calculés hors TVA. |
| Retours et remboursements déduits de la marge brute (27/10/2026) | Remboursements, rétrofacturations et remplacements, hors commandes annulées. |
| Coûts génériques hors marge brute | À 0 depuis le 01/01/2025 selon COEX ; colonne retirée des tableaux. |

### Alignement avec le backoffice

Le 02/11/2026, COEX a aligné le tableau de profitabilité du backoffice sur les mêmes sources que Power BI : coûts réels, factures transporteurs, annulations déduites. COEX confirme que c'est aussi vrai au niveau de chaque commande.

### Validation par Lireka

Le 03/11/2026, Marc Bordier a comparé chaque poste de revenu et de coût de Power BI et du backoffice avec les comptes du troisième trimestre préparés par l'expert-comptable.

| Poste | Écart avec la comptabilité |
|---|---|
| Chiffre d'affaires | 1,1 % |
| Coût d'achat | 7 %, factures fournisseurs de septembre pas encore toutes comptabilisées |
| Transport sortant | 0,4 % |
| Droits et taxes | 1,7 % |
| Commissions marketplace | 4 % |

Conclusion de Lireka : les données de Power BI et du backoffice sont fiables, et le rapport Finance peut être utilisé.

---

## 3. Contrôle des accès

| Contrôle | Résultat |
|---|---|
| Marc Bordier, Admin de l'espace LIREKA - Power BI, voit le rapport | Fait (28/10/2026) |
| Emma Henry, Admin de l'espace LIREKA - Power BI, voit le rapport | Fait (28/10/2026) |
| Le modèle apparaît dans Power BI Desktop (Obtenir les données > Modèles sémantiques Power BI) | Fait (28/10/2026) |
| Le compte powerbi-gateway@lireka.com porte la passerelle et le modèle | Fait. Licence Pro à attribuer avant le 26/12/2026 environ. |
| Accès de Clémence et de Michal Kašpar | À donner par un Admin de l'espace (rôle Lecteur). Michal doit d'abord être invité dans le tenant Lireka. |
| Accès Git d'Emma Henry | Procédure envoyée le 30/10/2026, en attente de sa clé publique |

---

## 4. Serveur Git et dépôt

| Contrôle | Résultat |
|---|---|
| Git for Windows et OpenSSH Server installés sur le VPS | Fait (25/10/2026) |
| Authentification par mot de passe désactivée | Fait et vérifié |
| Dépôt `C:\git\lireka.git` créé, historique protégé | Fait (26/10/2026) |
| Livraison du projet, sans données ni identifiants | Fait (26/10/2026) |
| Port 22 ouvert dans Azure par Inforeso | Fait (28/10/2026) |
| Récupération du dépôt par SSH avec clé, depuis un poste extérieur | Testé : réussi |
