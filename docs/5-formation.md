# 5. Formation

Support de la session de prise en main du rapport et du projet Power BI. Durée indicative : 1 h 30.

---

## Objectifs

À la fin de la session, la personne formée sait :
1. ouvrir le rapport dans le Service et dans Power BI Desktop ;
2. lire les indicateurs et utiliser les filtres ;
3. construire ses propres analyses à partir du modèle publié ;
4. récupérer, modifier et publier le projet avec Git.

---

## Déroulé

| Durée | Thème | Contenu | Référence |
|---|---|---|---|
| 10 min | Accès | Ouvrir app.powerbi.com avec son compte Lireka, espace de travail **LIREKA - Power BI**, rapport **Lireka_Profitabilite** | [4-passation.md](4-passation.md) |
| 20 min | Lire le rapport | Tour des 11 pages ; filtre « Period », slicers Date, Channel et Language ; carte « Data through » ; cartes KPI et comparaisons N-1 | [1-guide-du-rapport.md](1-guide-du-rapport.md) |
| 15 min | Comprendre les chiffres | Revenue hors TVA, composition de la marge brute, commandes exclues, répartition par livre quand on filtre la langue, lecture du Profit bridge et de la Loss analysis | [2-donnees-et-calculs.md](2-donnees-et-calculs.md) |
| 20 min | Construire ses analyses | Power BI Desktop > **Obtenir les données > Modèles sémantiques Power BI > Lireka_Profitabilite** ; créer une page, un visuel, un filtre ; combiner avec une autre source | ci-dessous |
| 15 min | Modifier le rapport commun | `git pull`, ouvrir le `.pbip`, modifier, enregistrer, `git add`, `git commit`, `git push`, publier, actualiser | [3-git-et-publication.md](3-git-et-publication.md) |
| 10 min | Exploitation | Vérifier l'actualisation de 8:00, que faire en cas d'échec, qui contacter | [4-passation.md](4-passation.md) |

---

## Exercices

1. **Lire** : sur General View, filtrer « Period » sur l'année civile précédente ; relever le revenu, la marge brute et le taux de marge de chaque canal.
2. **Comprendre** : sur Top loss makers, ouvrir la commande la plus déficitaire d'un canal et identifier le poste de coût qui pèse le plus.
3. **Construire** : dans Power BI Desktop, se connecter au modèle publié et créer un tableau « revenu et marge brute par pays de livraison et par mois ».
4. **Modifier** : sur un poste équipé de Git, changer un titre de visuel, publier, puis vérifier le changement dans le Service.

---

## Construire ses propres analyses : pas à pas

1. Ouvrir Power BI Desktop, connecté avec son compte Lireka.
2. **Accueil > Obtenir les données** (petite flèche) **> Modèles sémantiques Power BI**.
3. Choisir **Lireka_Profitabilite** > **Se connecter**.
4. Toutes les mesures publiées apparaissent dans la table **_Mesures** ; les axes (date, pays, canal, langue) dans les tables `dim_*`.
5. Pour ajouter une autre source (par exemple des données marketing), utiliser l'option de Desktop qui ajoute un modèle local au modèle publié (proposée lors de l'ajout d'une source ; elle doit être autorisée dans les paramètres d'administration Power BI de Lireka). Le fichier garde le lien vers le modèle publié et y ajoute la nouvelle source.

Le fichier ainsi créé est personnel : il ne modifie pas le rapport commun et affiche toujours les données de la dernière actualisation.
