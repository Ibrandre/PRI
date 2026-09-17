# État des lieux de l'existant et justification des choix technologiques

*PRI 2026-2027 — Projet 2 : IA embarquée pour la perception des véhicules autonomes en logistique hospitalière*
*Version 1 — septembre 2026*

---

## Préambule — démarche et objet du document

Avant de choisir une technologie, il faut savoir ce que d'autres ont déjà fait du même problème.
Ce document répond à trois questions, dans cet ordre :

1. **Que fait-on aujourd'hui ?** Quels systèmes de logistique hospitalière autonome existent
   réellement, en production comme en recherche, et jusqu'où vont-ils ?
2. **Avec quelles technologies ?** Quels capteurs, quels modèles, quelles architectures logicielles,
   quel matériel de calcul ces systèmes emploient-ils concrètement ?
3. **Qu'est-ce que cela implique pour nous ?** Comment ces observations, croisées avec nos
   contraintes propres, conduisent-elles — de façon traçable — aux technologies retenues ?

La démarche suivie correspond à la méthodologie en cinq étapes identifiée dans la littérature
récente sur le déploiement de réseaux de neurones embarqués : *définition du besoin → sélection
du modèle → optimisation → alignement matériel → déploiement*. Le présent document couvre la
première étape et amorce la deuxième ; l'[état de l'art des modèles](01-etat-de-l-art-et-comparaison-modeles.md)
traite la deuxième et la troisième.

> **Sommaire**
> [1. État des lieux — les systèmes en production](#1-état-des-lieux--les-systèmes-en-production) ·
> [2. État des lieux — la recherche](#2-état-des-lieux--la-recherche-académique) ·
> [3. État des lieux — les projets embarqués bas coût](#3-état-des-lieux--les-projets-embarqués-bas-coût) ·
> [4. Les briques logicielles standard](#4-les-briques-logicielles-standard-du-domaine) ·
> [5. Synthèse technologique](#5-synthèse-technologique-de-lexistant) ·
> [6. Les six enseignements](#6-les-six-enseignements-transversaux) ·
> [7. Positionnement du projet](#7-positionnement-de-notre-projet-dans-ce-paysage) ·
> [8. L'entonnoir de décision](#8-lentonnoir-de-décision) ·
> [9. Traçabilité des choix](#9-traçabilité-des-choix--de-lobservation-à-la-décision) ·
> [10. Écarts et risques](#10-écarts-assumés-avec-lexistant-et-risques-associés) ·
> [11. Sources](#11-sources)

---

## 1. État des lieux — les systèmes en production

La logistique hospitalière autonome n'est pas un domaine émergent : c'est un marché mature, avec
des flottes déployées depuis plus de quinze ans et des centaines de milliers de livraisons
effectuées. Quatre systèmes structurent le paysage.

### 1.1 Aethon TUG (États-Unis, déployé depuis ~2004)

Le vétéran du domaine, présent dans plusieurs centaines d'hôpitaux nord-américains. Transport de
médicaments, de repas, de linge et de prélèvements.

| Aspect | Ce qui est mis en œuvre |
|---|---|
| **Capteurs** | Suite multi-capteurs : **LiDAR**, **ultrasons**, **infrarouge**, et depuis les générations récentes une **caméra de profondeur Intel RealSense D435** |
| **Cœur de la navigation** | **SLAM** — construction et mise à jour continue d'une carte de l'environnement |
| **Apport de la caméra** | Explicitement introduite pour « voir des obstacles que les ultrasons et l'infrarouge ne peuvent pas détecter », par calcul de profondeur |
| **Intégration bâtiment** | Communication avec ascenseurs et portes automatiques |

**Ce qu'il faut en retenir :** la caméra est arrivée **en dernier**, en complément d'une base
télémétrique déjà fonctionnelle. Elle résout un problème résiduel de couverture, elle ne constitue
pas le socle de la perception.

### 1.2 Panasonic HOSPI (Japon, déployé depuis ~2013)

Le système le plus intéressant pour nous, parce que c'est le seul du panel dont la **sécurité est
certifiée** et documentée publiquement.

| Aspect | Ce qui est mis en œuvre |
|---|---|
| **Capteurs** | Multiples capteurs conçus pour détecter des obstacles « de formes et même de hauteurs variées » en intérieur |
| **Navigation** | Carte pré-programmée du bâtiment + reconnaissance de l'environnement par capteurs |
| **Ascenseurs et portes** | **Coordination par le réseau** — le robot appelle l'ascenseur et commande les portes automatiques via une liaison réseau |
| **Infrastructure** | **Aucune modification du bâtiment** : ni fils, ni capteurs encastrés, ni bandes électromagnétiques au sol |
| **Sécurité** | **Certifié ISO 13482**, et première certification sous les nouvelles normes JIS |
| **Supervision** | Remontée de position en continu vers un centre de contrôle |

**Ce qu'il faut en retenir — deux points majeurs :**

1. **La disponibilité de l'ascenseur n'est pas un problème de vision.** Le système industriel de
   référence la résout par une **requête réseau**, qui donne une information exacte, instantanée et
   fiable à 100 %. Aucun modèle de perception ne peut égaler cela.
2. Le refus de modifier l'infrastructure est un choix commercial assumé (coût d'installation), pas
   une contrainte technique. Il valide en revanche l'approche « perception embarquée autonome ».

### 1.3 Relay Robotics (ex-Savioke, États-Unis)

Robots de livraison pour hôtels, bureaux et hôpitaux ; gammes Relay+, Relay2. Positionnement
explicite sur les environnements publics **encombrés**.

| Aspect | Ce qui est mis en œuvre |
|---|---|
| **Navigation** | Autonomie complète en environnement public fréquenté |
| **Ascenseurs** | Le robot **appelle l'ascenseur, sélectionne sa destination, entre et sort seul**. La communication est configurée à l'installation — pas d'intégration lourde du bâtiment |
| **Déploiement** | Argument « Rapid Install » : opérationnel en jours, pas en mois |

**Ce qu'il faut en retenir :** la rapidité de mise en service est un argument commercial de premier
plan. Cela plaide, pour nous aussi, contre toute solution exigeant une longue campagne
d'annotation propre à chaque site.

### 1.4 Diligent Robotics Moxi (États-Unis)

Le plus avancé en perception, parce que c'est le seul à **manipuler** des objets et à interagir
socialement avec le personnel soignant.

| Aspect | Ce qui est mis en œuvre |
|---|---|
| **Capteurs** | Capteurs multiples, caméras, algorithmes d'IA |
| **Fonctions** | Navigation autonome + manipulation dextre + interaction sociale avec le personnel |

**Ce qu'il faut en retenir :** c'est le seul du panel pour lequel l'IA de perception visuelle est
réellement centrale — et c'est précisément parce qu'il doit **saisir des objets** et **comprendre
des personnes**, pas seulement les éviter. Le niveau de perception requis est fonction de la
tâche, pas du prestige technologique.

---

## 2. État des lieux — la recherche académique

### 2.1 ORB — Operating Room Bot (Carnegie Mellon, IEEE CASE 2025)

Le travail académique récent le plus proche de notre domaine : automatisation de la logistique
**au sein même du bloc opératoire**.

| Aspect | Ce qui est mis en œuvre |
|---|---|
| **Plateforme** | Fetch (base mobile + bras 7 axes + préhenseur à ventouse), capteurs multimodaux |
| **Logiciel** | **ROS 2**, architecture modulaire pilotée par **arbres de comportement** (*behavior trees*) |
| **Perception** | Chaîne combinant **YOLOv7 + SAM 2 (Segment Anything) + Grounding DINO** |
| **Planification** | **cuRobo**, optimisation de trajectoire parallélisée **accélérée GPU** |
| **Résultats** | 80 % de succès en récupération de fournitures, 96 % en réapprovisionnement |

**Ce qu'il faut en retenir :** l'état de l'art académique en perception hospitalière empile
**trois grands modèles de vision** et exige un **GPU**. C'est la démonstration, par l'exemple, de
ce que notre projet ne peut pas faire — et donc la mesure exacte de l'écart à franchir. La
comparaison est éclairante : la chaîne d'ORB représente plusieurs centaines de millions de
paramètres, là où notre budget se compte en **quelques millions**.

### 2.2 Ce que disent les revues de synthèse récentes

Trois enseignements convergents ressortent des revues 2025-2026 sur la perception embarquée en
robotique mobile :

- **Le pipeline est unifié et standardisé** : acquisition → perception → localisation et
  cartographie → prédiction → planification → contrôle. Notre projet occupe la case « perception »,
  ce qui confirme la nécessité d'un **contrat d'interface** propre avec l'aval.
- **La méthodologie de déploiement embarqué est stabilisée** en cinq étapes (besoin → sélection →
  optimisation → alignement matériel → déploiement), avec un triptyque d'optimisation récurrent :
  **élagage, quantification, architectures légères**. C'est exactement la démarche du §7 de notre
  état de l'art des modèles — notre approche est donc alignée sur la pratique du domaine.
- **Le multi-tâche à dorsale partagée s'impose sur l'embarqué.** Des travaux récents montrent
  qu'une dorsale unique de type ResNet-18 servant plusieurs têtes offre le meilleur compromis
  charge/représentation pour un robot autonome déployé sur cible contrainte. **C'est la validation
  académique directe de notre principe « un seul réseau dans la boucle ».**

---

## 3. État des lieux — les projets embarqués bas coût

C'est la catégorie la plus comparable à la nôtre : prototypes académiques sur Raspberry Pi. Elle
donne les ordres de grandeur réellement atteints, loin des annonces commerciales.

| Projet | Matériel | Modèle | Performance rapportée | Lecture critique |
|---|---|---|---|---|
| Robot de surveillance autonome | **Raspberry Pi 5** | YOLOv8 | **6-8 FPS** | Cohérent avec nos tableaux (§2.3 de l'état de l'art). **Hors de notre budget de 10 Hz** |
| Navigation en environnement dynamique | Raspberry Pi | YOLOv8 | 90 % de succès de navigation ; précision 87 % (objets mobiles) / 81 % (fixes) | Montre qu'une navigation utile est atteignable avec une perception imparfaite |
| Prototype ADAS embarqué | Raspberry Pi 3 | YOLOv12n personnalisé | Temps réel revendiqué après optimisation | Confirme que **l'optimisation, pas l'architecture, fait la faisabilité** |
| Robot guide | Raspberry Pi 4B | YOLOv10 | 85 % de précision, « 57 FPS », erreur de distance 0,6 m (ultrasons stéréo) | ⚠️ **Chiffre à considérer avec prudence** : 57 FPS sur un Pi 4B est incompatible avec toutes les autres mesures publiées. Résolution très réduite, ou FPS de la boucle et non de l'inférence |

**Ce qu'il faut en retenir — trois points :**

1. **Le régime réellement observé sur Raspberry Pi est de 6 à 8 FPS avec un YOLO non optimisé.**
   C'est notre point de départ honnête, et il est **sous** notre cible.
2. **Aucun de ces travaux ne publie de mesure rigoureuse** : ni p95, ni température, ni
   consommation, ni durée de chauffe. C'est une faiblesse méthodologique générale du domaine —
   et donc un espace où notre projet peut apporter une contribution réelle (§7.3).
3. **Tous s'arrêtent à la détection.** Aucun ne produit de représentation structurée avec niveau
   de confiance calibré — ce que notre cahier des charges demande explicitement.

---

## 4. Les briques logicielles standard du domaine

### 4.1 ROS 2 et Nav2 : la représentation de référence

Quasiment tous les systèmes cités s'appuient sur ROS / ROS 2. La représentation de l'environnement
y est normalisée : la **costmap 2D en couches**.

| Couche | Rôle | Source de données |
|---|---|---|
| *Static layer* | Obstacles connus et permanents (murs) | Carte SLAM pré-établie |
| *Obstacle layer* | Obstacles dynamiques, suivi en **2D** | Scans laser, nuages de points |
| *Voxel layer* | Obstacles suivis en **3D**, puis projetés en 2D pour l'inflation | Nuages de points |
| *Inflation layer* | Marge de sécurité autour des obstacles | Calculée |

**Ce qu'il faut en retenir :** le format de sortie attendu par l'aval est **déjà normalisé**. Notre
« représentation structurée » a tout intérêt à être compatible avec ce modèle en couches plutôt
qu'à inventer un format propriétaire. C'est un argument fort pour le contrat d'interface, et cela
rend le travail réutilisable au-delà du PRI.

### 4.2 Les normes de sécurité — l'enseignement le plus important du document

| Norme | Portée | Exigence clé |
|---|---|---|
| **ISO 3691-4** | Chariots sans conducteur / AMR industriels | **La détection de personnes doit être assurée par un système de niveau de performance PLd (ISO 13849)** : redondance, détection de défaut, surveillance indépendante. Un « test de détection des personnes » est explicitement normalisé |
| **IEC 61496** | Équipements de protection électro-sensibles (ESPE) | Fixe les paramètres d'essai qu'un dispositif doit passer pour réaliser cette fonction. En pratique, seuls les **Type 3** (scanner laser) et **Type 4** qualifient — d'où le recours systématique aux scanners de sécurité (SICK microScan3 et équivalents, SIL 2 / PLd Cat. 3) |
| **ISO 13482** | Robots de service et d'assistance à la personne (norme du HOSPI) | Sécurité des robots serviteurs mobiles ; révision en cours |

> ### ⚠️ Conséquence architecturale majeure
>
> **La fonction de sécurité est réservée à un matériel certifié.** ISO 3691-4 exige un niveau PLd
> pour la détection de personnes, et IEC 61496 réserve en pratique cette fonction aux ESPE de
> **Type 3 (scanner laser) ou Type 4**. Une caméra associée à un réseau de neurones n'entre pas
> dans cette catégorie : elle ne discrimine pas de façon déterministe — c'est le même argument
> qui écarte les capteurs PIR de la certification.
>
> C'est pourquoi la sécurité des personnes sur un AMR repose sur un **scanner laser de sécurité
> certifié**, câblé à l'arrêt d'urgence, et non sur l'IA de perception. L'IA sert à *comprendre*
> la scène (anticiper, ralentir en douceur, choisir un itinéraire, décider qu'un couloir est
> praticable) ; le matériel certifié sert à *garantir l'arrêt*.
>
> **Nuance à ne pas escamoter** : cela ne veut pas dire qu'un modèle appris est à jamais
> incertifiable. Les normes de sécurité fonctionnelle classiques n'ont pas été conçues pour le
> logiciel d'apprentissage, et des cadres d'assurance dédiés existent (**AMLAS**, travaux
> d'adaptation d'ISO 26262). C'est un sujet de recherche actif. L'énoncé exact est donc : *avec
> les dispositifs et la voie de certification d'aujourd'hui, la fonction d'arrêt revient à un
> ESPE certifié.*
>
> **Ceci nuance une formulation de notre document de cadrage.** Nous y écrivions qu'un faux négatif
> sur la classe « personne » est une faute grave, en traitant implicitement l'IA comme l'organe de
> sécurité. La réponse du domaine n'est pas d'exiger un modèle parfait — c'est de **placer l'IA
> derrière une couche de sécurité déterministe**. Le rappel sur la classe « personne » reste notre
> critère de performance prioritaire (qualité du service, fluidité, anticipation), mais il n'est
> plus le dernier rempart. C'est une correction importante : elle rend le projet **défendable**,
> là où prétendre garantir la sécurité des patients avec un YOLO quantifié sur Raspberry Pi
> serait indéfendable devant un jury.

---

## 5. Synthèse technologique de l'existant

Tableau de synthèse — qui utilise quoi, et sur quel matériel de calcul.

| Système | Télémétrie | Vision | Ultrasons | Calcul | Modèles d'IA | Ascenseur |
|---|---|---|---|---|---|---|
| **Aethon TUG** | LiDAR + IR | RealSense D435 (profondeur) | ✅ | Embarqué x86 (non publié) | Non publié ; SLAM au cœur | Réseau |
| **Panasonic HOSPI** | Capteurs multiples multi-hauteurs | non détaillée | ✅ | Embarqué (non publié) | Évitement + carte pré-établie | **Réseau** |
| **Relay Robotics** | LiDAR + profondeur | ✅ | ✅ | Embarqué (non publié) | Navigation sociale | **Réseau** |
| **Diligent Moxi** | LiDAR | Caméras multiples | — | Embarqué haute performance | IA de perception + manipulation | Réseau |
| **ORB (CMU)** | Capteurs multimodaux | ✅ | — | **GPU** | **YOLOv7 + SAM 2 + Grounding DINO** | n/a |
| **Projets RPi académiques** | Souvent aucune | Caméra seule | Parfois | **Raspberry Pi 3/4/5** | YOLOv8 / v10 / v12n | n/a |
| **→ Notre projet** | **LiDAR 2D** | **Caméra** | **Sonar** | **Raspberry Pi 5, CPU nu** | **YOLO26n + ByteTrack** | **Réseau recommandé** |

### Observations issues du tableau

- **La télémétrie est universelle en production ; la vision est un complément.** Aucun système
  déployé ne fonde sa navigation sur la caméra seule.
- **Les ultrasons survivent** dans la quasi-totalité des systèmes commerciaux, malgré leur âge.
  Raison unique et suffisante : **le verre**. Cela confirme leur présence à notre cahier des charges.
- **Le fossé de calcul est béant** entre la recherche (GPU) et les prototypes bas coût (Pi). Notre
  projet se place délibérément du côté contraint — c'est là que réside sa contribution.
- **Personne ne détecte l'ascenseur par vision.** Tous passent par le réseau.

---

## 6. Les six enseignements transversaux

Ce que l'état des lieux nous apprend, et qui oriente directement les choix du §8.

| # | Enseignement | Source de l'observation |
|---|---|---|
| **E1** | **La géométrie d'abord, la sémantique ensuite.** Tous les systèmes en production fondent leur navigation sur la télémétrie (LiDAR + ultrasons) et ajoutent la vision par-dessus, pour ce que la télémétrie ne voit pas | TUG, HOSPI, Relay |
| **E2** | **La sécurité des personnes ne passe pas par l'IA**, mais par un ESPE certifié (IEC 61496 Type 3/4, PLd). L'IA apporte le confort, l'anticipation et la sémantique | ISO 3691-4, IEC 61496, ISO 13482 / HOSPI |
| **E3** | **Ce qui est connu par le réseau ne doit pas être deviné par un capteur.** L'état de l'ascenseur est obtenu par requête, pas par perception | HOSPI, Relay |
| **E4** | **L'empilement de modèles est réservé au GPU.** Sur cible contrainte, la pratique validée est la dorsale unique multi-tâches | ORB vs travaux ResNet-18 embarqués |
| **E5** | **Sur Raspberry Pi, le régime naturel est 6-8 FPS.** Atteindre 10 Hz+ exige une chaîne d'optimisation explicite (quantification, élagage, architectures légères) | Projets RPi académiques ; revues de déploiement embarqué |
| **E6** | **Le format de sortie est déjà normalisé** (costmap en couches ROS 2). Inventer un format propriétaire serait une régression | Nav2 |

---

## 7. Positionnement de notre projet dans ce paysage

### 7.1 Ce que notre projet n'est pas

Dire ce qu'on ne fait pas est aussi structurant que dire ce qu'on fait :

- **Ce n'est pas un concurrent du TUG ou du HOSPI.** Ceux-ci sont des produits complets
  (navigation, flotte, sécurité certifiée, intégration bâtiment). Nous traitons **une brique** :
  la perception.
- **Ce n'est pas un projet de navigation.** La décision et la planification sont explicitement
  hors périmètre (le cahier des charges parle d'« une IA de décision » comme consommateur aval).
- **Ce n'est pas une démonstration de performance maximale.** ORB fait mieux que ce que nous ferons,
  avec un GPU. Reproduire ORB en moins bien n'aurait aucune valeur.

### 7.2 Ce qui rend notre projet spécifique

Le sujet pose une question que **ni les produits ni les travaux académiques cités ne traitent
frontalement** :

> Jusqu'où peut-on descendre en coût et en consommation tout en produisant une représentation
> structurée, fiable et **assortie d'un niveau de confiance**, exploitable par une IA de décision ?

Les industriels ont résolu le problème **en y mettant le matériel nécessaire**. Les académiques
l'ont résolu **en y mettant un GPU**. Les prototypes Raspberry Pi, eux, s'arrêtent à la détection
brute, sans structuration ni quantification de l'incertitude. **La case est vide, et c'est la nôtre.**

### 7.3 Contributions revendiquées

| # | Contribution | Vide qu'elle comble |
|---|---|---|
| **C-1** | **Protocole de mesure rigoureux sur Raspberry Pi 5** : médiane *et* p95, température, throttling, consommation, durée de chauffe documentée | Aucun des travaux RPi recensés ne publie ces éléments (§3) |
| **C-2** | **Sortie à confiance calibrée** (ECE mesuré, temperature scaling) | Aucun prototype embarqué recensé ne quantifie son incertitude |
| **C-3** | **Fusion caméra / LiDAR 2D à coût CPU nul** pour la distance métrique | La littérature RPi utilise soit la vision seule, soit des ultrasons peu précis (0,6 m d'erreur) |
| **C-4** | **Courbe de compromis résolution / rappel** documentée en contexte couloir | Non documenté : les benchmarks publics sont établis sur COCO, dont la statistique d'échelle diffère radicalement |
| **C-5** | **Injection de l'ego-motion IMU dans le suivi** | Les traqueurs embarqués recensés n'exploitent pas l'odométrie déjà disponible |

---

## 8. L'entonnoir de décision

Voici le raisonnement complet qui mène de l'état des lieux aux technologies retenues. Chaque
étape élimine des options pour une raison explicite et opposable.

```
  ÉTAT DES LIEUX : ce qui existe
  ────────────────────────────────────────────────────────────────────────
  Production : LiDAR + ultrasons + vision d'appoint, sécurité certifiée, ascenseur par réseau
  Recherche  : YOLOv7 + SAM2 + Grounding DINO sur GPU
  Bas coût   : YOLO seul sur Raspberry Pi, 6-8 FPS, sans structuration ni confiance
                                     │
                                     ▼
  FILTRE 1 — Le matériel est imposé : Raspberry Pi 5, CPU nu
  ────────────────────────────────────────────────────────────────────────
  ✗ Éliminé : tout ce qui suppose un GPU → SAM 2, Grounding DINO, cuRobo, DETR lourds
  ✗ Éliminé : les caméras de profondeur haut de gamme (hors budget, et aveugles au verre)
  ✓ Retenu  : une classe de modèles « nano », < 5 M paramètres
                                     │
                                     ▼
  FILTRE 2 — E2 : la sécurité relève du matériel certifié, pas de l'IA
  ────────────────────────────────────────────────────────────────────────
  → L'IA n'a pas à être parfaite : elle doit être RÉGULIÈRE et HONNÊTE sur sa confiance
  ✓ Conséquence : le déterminisme de la latence (p95) devient un critère de premier rang
  ✓ Conséquence : la calibration de la confiance devient un livrable, pas un ornement
                                     │
                                     ▼
  FILTRE 3 — E1 : la géométrie d'abord
  ────────────────────────────────────────────────────────────────────────
  ✗ Éliminé : la profondeur monoculaire apprise (MiDaS, Depth Anything)
              → coût d'un second réseau, sortie non métrique, alors que le LiDAR
                donne la distance en métrique pour un coût CPU nul
  ✗ Éliminé : le segmenteur d'espace libre dédié (PP-LiteSeg, SegFormer-B0)
              → +30 à 80 ms et une campagne d'annotation pixel, alors que
                l'occupation LiDAR couvre l'essentiel du besoin
  ✓ Retenu  : LiDAR 2D pour la distance et l'espace libre ; sonar pour le verre
                                     │
                                     ▼
  FILTRE 4 — E3 : ne pas deviner ce qui est connu
  ────────────────────────────────────────────────────────────────────────
  ✗ Éliminé : la classification visuelle de l'état de l'ascenseur comme source primaire
  ✓ Retenu  : interface réseau ascenseur (à arbitrer avec l'encadrant), la vision
              en secours et en vérification de cohérence
                                     │
                                     ▼
  FILTRE 5 — E4 : une seule dorsale dans la boucle
  ────────────────────────────────────────────────────────────────────────
  ✗ Éliminé : tout empilement détection + segmentation + profondeur
  ✓ Retenu  : un détecteur unique ; les autres fonctions en géométrique/statistique
                                     │
                                     ▼
  FILTRE 6 — E5 : 6-8 FPS est le régime naturel, il faut le dépasser
  ────────────────────────────────────────────────────────────────────────
  → L'effort porte sur la CHAÎNE D'EXÉCUTION, pas sur l'architecture
  ✓ Retenu  : NCNN (×3 à ×5 sur ARM) + INT8 (×2,1 grâce au dot-product du Cortex-A76)
              + résolution réduite (×2,4) → objectif ≈ 25-30 ms
                                     │
                                     ▼
  FILTRE 7 — Départage final entre modèles nano (grille §9 de l'état de l'art)
  ────────────────────────────────────────────────────────────────────────
  ✓ YOLO26n (4,10/5) : sans NMS → latence déterministe, exigée par le filtre 2
  ↳ Repli 1 : YOLO11n (3,95/5), export NCNN plus éprouvé
  ↳ Repli 2 : NanoDet-Plus (3,00/5), frugalité extrême si le budget échoue
                                     │
                                     ▼
  FILTRE 8 — E6 : ne pas réinventer le format de sortie
  ────────────────────────────────────────────────────────────────────────
  ✓ Retenu  : sortie structurée alignée sur le modèle en couches de Nav2 / ROS 2
```

---

## 9. Traçabilité des choix — de l'observation à la décision

Tableau de traçabilité complet : chaque technologie retenue renvoie à l'observation de l'existant
qui la justifie. C'est la pièce à présenter en soutenance.

| Choix technologique | Observation de l'existant | Enseignement | Alternative écartée | Motif de l'élimination |
|---|---|---|---|---|
| **YOLO26n** comme détecteur unique | Les prototypes RPi utilisent tous un YOLO nano ; les modèles lourds exigent un GPU | E4, E5 | RF-DETR, D-FINE, SAM 2 | Pas de chemin d'export ARM éprouvé ; conçus pour GPU |
| **Sans NMS** (déterminisme) | ISO 3691-4 impose un comportement prévisible pour les fonctions liées aux personnes | E2 | YOLOv8n / YOLO11n (avec NMS) | Latence variable selon l'encombrement de la scène — au pire moment |
| **NCNN + INT8 + 416 px** | Le régime RPi observé (6-8 FPS) est sous la cible ; les revues embarquées convergent sur quantification + architectures légères | E5 | PyTorch, ONNX FP32 | Facteur ~5 laissé sur la table |
| **LiDAR 2D pour la distance** | TUG, HOSPI, Relay : tous fondés sur la télémétrie | E1 | Profondeur monoculaire apprise | Doublerait le budget d'inférence pour une sortie non métrique |
| **Sonar conservé** | Les ultrasons survivent dans tous les systèmes commerciaux | E1 | Suppression du sonar | Le verre est invisible au LiDAR **et** à la caméra — très présent en milieu hospitalier |
| **Pas de segmenteur dédié** | Aucun système en production n'embarque de segmentation sémantique dense pour l'espace libre | E1, E4 | PP-LiteSeg, SegFormer-B0 | +30-80 ms et annotation pixel par pixel, pour un besoin déjà couvert par le LiDAR |
| **ByteTrack** (géométrique) | Les prototypes RPi s'arrêtent à la détection, sans persistance temporelle | E4, E5 | DeepSORT, BoT-SORT+ReID | Un CNN par piste : rédhibitoire sur CPU |
| **Ego-motion par IMU** | Les systèmes en production disposent tous d'odométrie ; BoT-SORT l'estime par vision faute de mieux | E1 | Compensation visuelle du mouvement (CMC) | Estimer par vision ce qu'un capteur donne gratuitement |
| **Confiance calibrée** (temperature scaling) | Aucun prototype embarqué recensé ne quantifie son incertitude — c'est un vide | E2 | Scores bruts ; MC-Dropout ; ensembles | Scores bruts : non calibrés, donc trompeurs. MC-Dropout/ensembles : coût × N passes |
| **Ascenseur par réseau** | HOSPI et Relay le font ainsi, tous les deux | E3 | Classification visuelle de l'état | Information exacte disponible sans incertitude — la deviner serait une régression |
| **Sortie alignée Nav2** | La costmap en couches est le standard de facto du domaine | E6 | Format propriétaire | Non réutilisable, non interopérable |
| **CPU nu** (Hailo-8L en repli documenté) | Les produits mettent le matériel nécessaire ; la question du sujet est justement la frugalité | — | AI Kit dès le départ | Répondrait à côté de la problématique posée (« frugale ») |

---

## 10. Écarts assumés avec l'existant et risques associés

Tout écart avec une pratique établie doit être justifié et surveillé. Voici les nôtres.

| Écart | Pratique du domaine | Notre choix | Justification | Risque | Parade |
|---|---|---|---|---|---|
| **Pas de SLAM** | Tous les systèmes en production font du SLAM | Perception locale, sans carte globale | Le sujet porte sur la perception, pas sur la localisation | La sortie « couloir dégagé » manque de contexte global | Interface Nav2 : la carte est fournie par l'aval |
| **Calcul très en dessous** | Production : x86 embarqué / GPU | Raspberry Pi 5, CPU nu | **C'est la problématique même du sujet** | Budget de latence non tenu | Repli documenté : Hailo-8L, résolution réduite |
| **Pas de scanner de sécurité certifié** | ISO 3691-4 + IEC 61496 : ESPE Type 3/4 obligatoire | Prototype de recherche, non certifiable | Hors périmètre d'un PRI | Sur-interprétation du niveau de sécurité atteint | **À écrire explicitement dans le rapport final** : le système est un démonstrateur de perception, pas un organe de sécurité |
| **LiDAR 2D et non 3D** | Le haut de gamme passe au 3D | 2D | Coût, budget CPU, disponibilité | Aveugle hors du plan de balayage (obstacles en hauteur, surplombs) | Caméra + sonar couvrent partiellement ; à documenter comme limite connue |
| **Jeu de données propre** | Les industriels disposent d'années de données terrain | Collecte limitée | Contrainte de projet | Faible généralisation à d'autres sites | Pré-annotation par modèle enseignant ; augmentation de données agressive ; limite annoncée |

---

## 11. Sources

**Systèmes en production**
- [Aethon — Intel RealSense dans les robots de livraison autonomes](https://www.intelrealsense.com/autonomous-mobile-robotics/)
- [How TUG Robots Are Revolutionizing Healthcare Logistics — AZoRobotics](https://www.azorobotics.com/Article.aspx?ArticleID=725)
- [Aethon TUG — présentation technique](https://www.roboticgizmos.com/aethon-tug-healthcare-robot/)
- [Panasonic — Autonomous Mobility Robot (technologies clés)](https://news.panasonic.com/global/stories/2019/69861.html)
- [Panasonic HOSPI — certification ISO 13482 et JIS](https://news.panasonic.com/global/topics/5001)
- [Panasonic HOSPI à Changi General Hospital — étude de cas](https://ap.connect.panasonic.com/th/en/case-studies/panasonic-autonomous-delivery-robots-hospi-aid-hospital-operations-changi-general)
- [Hospi — fiche Wikipedia](https://en.wikipedia.org/wiki/Hospi)
- [Relay Robotics — nouvelle gamme pour hôtels et hôpitaux](https://relayrobotics.com/relay-robotics-announces-new-line-of-delivery-robots-for-hotels-and-hospitals/)
- [Relay2 — intégration ascenseur (The Robot Report)](https://www.therobotreport.com/relay2-delivery-robot-offers-2x-payload-new-elevator-integration/)
- [Relay+ — génération suivante (The Robot Report)](https://www.therobotreport.com/relay-is-saviokes-new-generation-of-service-robot/)
- [Diligent Robotics — Moxi](https://www.diligentrobots.com/moxi)

**Recherche académique**
- [ORB: Operating Room Bot — Automating Operating Room Logistics through Mobile Manipulation (arXiv 2509.15600, IEEE CASE 2025)](https://arxiv.org/html/2509.15600)
- [Artificial Intelligence for Autonomous Mobile Robots in IR4.0–IR6.0: A Unified Review](https://doi.org/10.3390/machines14080950)
- [Edge AI in Practice: A Survey and Deployment Framework for Neural Networks on Embedded Systems (MDPI Electronics)](https://www.mdpi.com/2079-9292/14/24/4877)
- [ResNet-18 based multi-task visual inference and adaptive control for an edge-deployed autonomous robot (Frontiers in Robotics and AI, 2025)](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1680285/full)
- [AI-based approaches for improving autonomous mobile robot localization in indoor environments: a comprehensive review](https://www.sciencedirect.com/science/article/pii/S2215098625000321)
- [Deep Learning-Based Multi-Modal Fusion for Robust Robot Perception and Navigation (arXiv 2504.19002)](https://arxiv.org/pdf/2504.19002)
- [Deep Learning Perspective of Scene Understanding in Autonomous Robots (arXiv 2512.14020)](https://arxiv.org/pdf/2512.14020)

**Projets embarqués bas coût**
- [Development of an Autonomous Surveillance and Object Detection Robot using Raspberry Pi 5 and YOLOv8](https://www.academia.edu/144419870/Project_Report_Development_of_of_an_Autonomous_Surveillance_and_Object_Detection_Robot_using_Raspberry_Pi_5_and_YOLOv8)
- [Enabling Autonomous Navigation in Dynamic Environments: Affordance-Based Mobility (Springer)](https://link.springer.com/chapter/10.1007/978-3-032-10667-4_7)
- [Embedded Intelligent ADAS Car Prototype Using Raspberry Pi and YOLOv12n (Springer)](https://link.springer.com/chapter/10.1007/978-3-032-18144-2_10)
- [Design of a Raspberry Pi 4B-Based Guide Robot with YOLO-v10 Integration](https://www.researchgate.net/publication/393581912_Design_of_a_Raspberry_Pi_4B-Based_Guide_Robot_with_YOLO-v10_Integration)
- [Optimizing object detection for autonomous robots: a comparative analysis of YOLO models (Measurement)](https://www.sciencedirect.com/science/article/abs/pii/S0263224125020354)
- [An Embedded Computer Vision Approach to Environment Modeling and Local Path Planning in AMRs](https://www.sciencedirect.com/org/science/article/pii/S1526149225004722)

**Briques logicielles et normes**
- [Nav2 — Costmap 2D, configuration des couches](https://navigation.ros.org/configuration/packages/configuring-costmaps.html)
- [nav2_costmap_2d — vue d'ensemble du paquet ROS](https://index.ros.org/p/nav2_costmap_2d/)
- [Nav2 — filtrage des obstacles induits par le bruit](https://docs.nav2.org/tutorials/docs/filtering_of_noise-induced_obstacles.html)
- [ISO 3691-4:2020 — Chariots sans conducteur et leurs systèmes](https://www.iso.org/standard/70660.html)
- [Safety Laser Scanners for Personnel Presence Detection — IEC 61496 Type 3/4 et PLd](https://industrialmonitordirect.com/blogs/knowledgebase/safety-laser-scanners-for-personnel-presence-detection)
- [SICK — scanners laser de sécurité pour AGV et AMR](https://www.sick.com/us/en/products/safety/safety-laser-scanners/c/g569359)
- [Guidance on the Assurance of Machine Learning in Autonomous Systems — AMLAS (arXiv 2102.01564)](https://arxiv.org/pdf/2102.01564)
- [An Analysis of ISO 26262: Using Machine Learning Safely in Automotive Software (arXiv 1709.02435)](https://arxiv.org/pdf/1709.02435)
- [Mobile Robot Safety Standards: ISO 3691-4 et ANSI/RIA R15.08](https://blog.saphira.ai/mobile-robot-safety-standards-understanding-iso-3691-4-(driverless-industrial-trucks)-and-r15-08-(industrial-mobile-robots)-implementation)
- [ISO 3691-4 : le cadre de responsabilité pour les AGV](https://www.agvnetwork.com/automated-guided-vehicles-technology/standard-3691-4)
- [The Latest in Autonomous Mobile Robots: New Safety Standards (A3 / Automate)](https://www.automate.org/robotics/industry-insights/autonomous-mobile-robot-safety-updates-new-features)

---

*Documents liés : [Cadrage du projet](00-cadrage-projet.md) · [État de l'art et comparaison des modèles](01-etat-de-l-art-et-comparaison-modeles.md)*
