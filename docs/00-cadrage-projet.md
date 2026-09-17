# Cadrage du projet — Analyse des besoins et des contraintes

*PRI 2026-2027 — Projet 2 : IA embarquée pour la perception des véhicules autonomes en logistique hospitalière*

---

## 1. Ce que dit le cahier des charges

### 1.1 Objectif et problématique

| Élément | Énoncé |
|---|---|
| **Objectif** | Transformer des informations de perception hétérogènes de l'environnement en une représentation structurée et exploitable de l'environnement du VA |
| **Problématique** | Comment concevoir une IA de perception performante, frugale et apte au déploiement embarqué ? |
| **Objectif final** | Démontrer la faisabilité d'une IA de perception **locale**, **frugale** et **embarquable**, produisant des données structurées, fiables et exploitables **par une IA de décision** |

Le point structurant, souvent sous-estimé : **le module de perception n'est pas le produit final**.
Son client est une *IA de décision* (hors périmètre de ce projet). Le livrable réel est donc un
**contrat d'interface** — un flux de données structurées, horodatées et accompagnées d'un niveau
de confiance — et non « un détecteur qui marche ».

### 1.2 Position dans l'architecture du VA

Le module de perception assure l'*acquisition, la représentation, la diffusion et la synchronisation*
des informations contextuelles provenant de trois sources :

- **Environnement proche** : caméra, LiDAR, sonar, IMU, odométrie
- **Environnement lointain** : informations d'infrastructure
- **Autres VA**

Parc de capteurs annoncé : **caméra, LiDAR, IMU, moteurs, sonar, BIR, RFID, GPS**.

> ⚠️ **Constat à arbitrer dès le lancement.** Le GPS est inopérant en intérieur hospitalier
> (couloirs, sous-sols, blocs). Le BIR et le RFID relèvent de la **localisation symbolique**
> (identification de zone, de porte, de chariot) et non de la perception géométrique : ils
> alimentent la représentation de l'environnement mais ne passent pas par le réseau de neurones.
> La proposition de périmètre défendue en §3 est donc : **caméra + LiDAR + sonar + IMU/odométrie**
> pour l'IA de perception, RFID/BIR en entrées symboliques fusionnées en aval.

### 1.3 Sorties attendues (« données de suivi »)

Le cahier des charges énumère les sorties suivantes — c'est la spécification de l'interface :

| # | Sortie | Nature | Brique fonctionnelle |
|---|---|---|---|
| a | Obstacle détecté / position / distance | Géométrique + classe | Détection + distance |
| b | Personne présente | Classe + comptage | Détection |
| c | Couloir dégagé ou obstrué | État booléen/ordinal | Espace libre |
| d | Ascenseur disponible | État sémantique | Détection + état |
| e | Trajectoire libre ou bloquée | État booléen | Espace libre + suivi |
| f | Niveau de confiance / incertitude | Scalaire [0,1] | Transverse |

La sortie **(f)** est la plus exigeante et la plus discriminante pour le choix du modèle : elle impose
une **calibration des scores** (un score de 0,8 doit signifier 80 % de justesse empirique), ce qui
n'est vrai pour aucun détecteur sorti de l'entraînement standard. Elle est traitée en détail dans
l'état de l'art (§6 du document de comparaison).

### 1.4 Travail demandé

1. Analyser les besoins et les contraintes
2. **Étudier plusieurs modèles d'IA**
3. **Choisir et justifier le modèle retenu**
4. Constituer / préparer les données
5. Entraîner et optimiser le modèle
6. Implémenter et tester sur **Raspberry Pi 5**

### 1.5 Livrables techniques

- État de l'art et comparaison des modèles ← *couvert par le présent lot*
- Choix argumenté du modèle
- Jeu de données et protocole de préparation
- Modèle entraîné et optimisé
- Implémentation embarquée
- Protocole et résultats expérimentaux

### 1.6 Livrables de gestion de projet (communs à tous les PRI)

Cahier des charges / expression des besoins · objectifs, périmètre et critères de réussite ·
planning et jalons · répartition des rôles · analyse des risques et plan d'actions ·
suivi d'avancement (réunions, comptes rendus, indicateurs) · suivi des ressources
(matériel, logiciels, budget, temps) · gestion des évolutions · rapport final ·
présentation & démonstration.

### 1.7 Critères d'évaluation du système

Trois familles, qui forment directement l'ossature de la grille de décision :

| Famille | Critères |
|---|---|
| **Performance** | Précision · Robustesse · Complexité |
| **Frugalité** | Taille du modèle · RAM / CPU · Énergie |
| **Embarqué** | Temps d'inférence · Utilisation CPU · Temps réel |

---

## 2. Contrainte matérielle : ce que le Raspberry Pi 5 autorise

| Caractéristique | Valeur | Conséquence pour le choix du modèle |
|---|---|---|
| SoC | Broadcom BCM2712 | — |
| CPU | 4 × Arm Cortex-A76 @ 2,4 GHz | **Pas de GPU exploitable** pour l'inférence, pas de NPU intégré |
| SIMD | NEON, **avec instructions dot-product (SDOT/UDOT)** | L'INT8 est réellement accéléré (≈ ×2 mesuré sur A76), contrairement au Cortex-A53 du Pi 3 où l'INT8 *ralentit* |
| RAM | 4 / 8 / 16 Go LPDDR4X | Budget mémoire confortable, ce n'est pas le facteur limitant |
| Extension | PCIe (AI Kit / AI HAT+ Hailo-8L, 13 TOPS) | Voie de secours si le CPU seul ne tient pas le budget |
| Puissance | ~3-4 W au repos, ~7-12 W en charge | Contrainte batterie du VA ; le SoC *throttle* sans dissipation active |

**Deux conséquences directes :**

1. **Toute l'inférence se fait sur 4 cœurs CPU ARM.** Les chiffres de latence publiés sur GPU
   (T4, A100) ou sur Jetson sont **non transposables** — ils servent uniquement à classer les
   modèles entre eux, jamais à dimensionner.
2. **Le refroidissement fait partie du protocole expérimental.** Un Pi 5 sans ventilateur perd
   20 à 40 % de ses performances après quelques minutes de charge continue. Toute mesure de
   latence non accompagnée d'une mesure de température et d'une durée de chauffe est invalide.

---

## 3. Décomposition fonctionnelle proposée

Le sujet « IA de perception » n'est pas monolithique. Pour rendre le choix des modèles traçable,
on le décompose en cinq briques, chacune avec ses propres candidats :

```
   Caméra ──┬─► F1  Détection 2D (obstacles, personnes, portes, ascenseurs)  ──┐
            │                                                                  │
            └─► F2  Espace libre / sol navigable (segmentation)  ──────────────┤
                                                                               │
   LiDAR 2D ───► F3  Distance & géométrie (mise à l'échelle métrique)  ────────┼─► F5  Fusion
                                                                               │      + état
   Sonar ──────► F3' Détection de surfaces non vues (verre, obstacles bas)  ───┤      + confiance
                                                                               │         │
   IMU/Odom ───► F4  Suivi temporel (ego-motion + tracking multi-objets)  ─────┘         ▼
                                                                                    Sortie
   RFID/BIR ───► (localisation symbolique, fusionnée en aval, hors réseau)      structurée
                                                                                (a → f)
```

| Brique | Rôle | Sorties couvertes |
|---|---|---|
| **F1** Détection 2D | Localiser et classer obstacles, personnes, portes, ascenseurs, chariots | a, b, d |
| **F2** Espace libre | Segmenter le sol navigable devant le VA | c, e |
| **F3** Distance | Passer du pixel au mètre (LiDAR 2D, sonar, ou profondeur monoculaire) | a, e |
| **F4** Suivi | Stabiliser les détections dans le temps, estimer les vitesses | b, e, f |
| **F5** Fusion & décision d'état | Produire la sortie structurée + le niveau de confiance | c, d, e, f |

C'est cette décomposition qui structure l'état de l'art : **un modèle est comparé aux autres
candidats de sa brique**, pas à l'ensemble du champ.

---

## 4. Budget temps réel — d'où vient la cible de latence

C'est le calcul qui transforme « temps réel » (exigence qualitative du cahier des charges) en
un seuil chiffré, opposable, utilisable comme critère d'élimination.

**Hypothèses de service** (à valider avec l'encadrant) :

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| Vitesse de croisière du VA en couloir | 1,0 m/s | Vitesse usuelle d'un AMR hospitalier en zone partagée avec des piétons |
| Vitesse d'un piéton croisé de face | 1,4 m/s | Vitesse de marche moyenne |
| Vitesse de rapprochement pire cas | 2,4 m/s | Somme des deux |
| Décélération confortable (charge fragile) | 1,0 m/s² | Un chariot hospitalier peut transporter des prélèvements, des repas, des médicaments |
| Marge de sécurité | 0,5 m | Distance d'arrêt résiduelle |

**Chaîne de latence à budgéter :**

```
acquisition → pré-traitement → inférence → post-traitement → fusion → publication
   ~15 ms        ~10 ms          ???          ~10 ms         ~5 ms      ~5 ms
```

Le budget hors inférence est d'environ **45 ms**. En visant une cadence de **10 Hz** (100 ms par
cycle, cadence standard d'une boucle de perception d'AMR), il reste :

> ### Budget d'inférence cible : ≤ 50 ms par image, soutenu, à température stabilisée
> soit une cadence de perception de 10 Hz et un déplacement de **10 cm par cycle** à 1 m/s.

**Vérification de cohérence** — distance de réaction totale à 2,4 m/s de rapprochement :
latence perception (0,10 s) + latence décision/commande (0,15 s estimé) = 0,25 s → 0,60 m parcourus,
plus la distance d'arrêt (2,4²/(2×1,0) = 2,88 m) et la marge (0,5 m) ≈ **4,0 m de portée de
détection utile**. C'est compatible avec la portée d'une caméra grand angle en couloir éclairé et
avec un LiDAR 2D d'intérieur (8-12 m).

**Seuils de décision retenus pour la comparaison :**

| Niveau | Latence d'inférence (RPi 5, 4 threads, à chaud) | Verdict |
|---|---|---|
| 🟢 Confortable | ≤ 50 ms (≥ 20 Hz) | Marge pour la fusion et le suivi |
| 🟡 Acceptable | 50 – 100 ms (10-20 Hz) | Tenable, sans brique supplémentaire coûteuse |
| 🟠 Limite | 100 – 200 ms (5-10 Hz) | Impose de réduire la vitesse du VA ou d'ajouter un accélérateur |
| 🔴 Éliminatoire | > 200 ms (< 5 Hz) | Incompatible avec un environnement partagé avec des piétons |

---

## 5. Contraintes spécifiques au milieu hospitalier

Ces contraintes sont **discriminantes** : elles écartent des modèles qui seraient excellents sur COCO.

| Contrainte | Impact technique | Conséquence sur le choix |
|---|---|---|
| **Sols réfléchissants** (linoléum ciré, carrelage) | Reflets interprétés comme des obstacles ; faux positifs de segmentation | Favorise une segmentation de l'espace libre *validée* par le LiDAR plutôt que purement visuelle |
| **Surfaces vitrées** (portes de service, sas) | Invisibles au LiDAR *et* à la caméra | Rend le **sonar non optionnel** — c'est sa justification principale |
| **Éclairage hétérogène** (couloirs, néons, veilleuses de nuit) | Chute de performance en basse lumière | Impose une augmentation de données photométrique agressive et un jeu de test nocturne dédié |
| **Encombrement mobile** (brancards, chariots, perfusions, déambulateurs) | Classes absentes de COCO | Impose un **jeu de données propre** ; écarte tout modèle non ré-entraînable facilement |
| **Personnes en position non debout** (patient au sol, brancard) | La classe « person » COCO est biaisée vers le piéton debout | Impose une collecte incluant ces cas ; critère de robustesse |
| **Sécurité des personnes (ISO 3691-4 / ISO 13482)** | Un faux négatif sur « personne » dégrade fortement le service ; un faux positif est seulement une gêne | **Le rappel (recall) sur la classe « personne » prime sur la précision** — asymétrie à inscrire dans la fonction de coût et dans le protocole de test. ⚠️ **Voir [§4.2 de l'état des lieux](02-etat-des-lieux-et-justification-des-choix.md#42-les-normes-de-sécurité--lenseignement-le-plus-important-du-document)** : ISO 3691-4 impose que la détection de personnes soit assurée par un ESPE certifié IEC 61496 Type 3 ou 4 (scanner laser de sécurité, SIL 2 / PLd Cat. 3) — ce qu'une caméra associée à un réseau de neurones n'est pas. La **sécurité** revient donc au scanner certifié, et l'IA à la **compréhension** de la scène. Notre module est un démonstrateur de perception, **pas un organe de sécurité** |
| **Confidentialité (RGPD, secret médical)** | Interdiction de faire transiter des images de patients | Confirme et *justifie* l'exigence de traitement **100 % local** du cahier des charges ; impose une politique de stockage du jeu de données |

---

## 6. Critères de réussite proposés (mesurables)

Proposition à faire valider en réunion de lancement — elle transforme les critères qualitatifs
du cahier des charges en seuils vérifiables.

| # | Critère | Seuil | Méthode de vérification |
|---|---|---|---|
| C1 | Rappel sur la classe « personne » | ≥ 95 % @ IoU 0,5, sur le jeu de test hospitalier | Évaluation hors ligne |
| C2 | mAP@0,5 toutes classes | ≥ 60 % sur le jeu de test propre | Évaluation hors ligne |
| C3 | Latence d'inférence médiane | ≤ 50 ms sur RPi 5, 4 threads | Mesure sur 1 000 images, après 10 min de chauffe |
| C4 | Latence au 95ᵉ centile | ≤ 100 ms | Même mesure (garantit le déterminisme) |
| C5 | Empreinte mémoire du processus | ≤ 1 Go RSS | `psutil` / `/proc` pendant la boucle |
| C6 | Taille du modèle déployé | ≤ 15 Mo | Fichier sur disque |
| C7 | Puissance système en fonctionnement | ≤ 8 W moyens | Wattmètre USB-C en ligne |
| C8 | Stabilité thermique | Pas de throttling sur 30 min | `vcgencmd get_throttled` |
| C9 | Calibration de la confiance | ECE ≤ 0,05 | Diagramme de fiabilité |
| C10 | Disponibilité de la sortie structurée | 10 Hz soutenus, sans trou > 300 ms | Horodatage du flux de sortie |

---

## 7. Risques identifiés (extrait — à reprendre dans le plan de gestion des risques)

| Risque | Gravité | Probabilité | Parade |
|---|---|---|---|
| Le jeu de données hospitalier ne peut pas être collecté (accès, RGPD) | Élevée | Moyenne | Démarrer sur données publiques d'intérieur + collecte dans les couloirs de l'école comme substitut ; anonymisation par floutage à la source |
| Le CPU seul ne tient pas le budget de 50 ms | Élevée | Moyenne | Réduction de résolution (640 → 416 → 320), INT8, puis **repli sur AI Kit Hailo-8L** |
| Throttling thermique en démonstration | Moyenne | Élevée | Dissipateur actif obligatoire dès la phase de mesure |
| Modèle excellent sur COCO mais médiocre sur les classes hospitalières | Élevée | Élevée | Critère de **transférabilité** intégré à la grille de comparaison (§7 du document d'état de l'art) |
| Dérive de périmètre vers l'IA de décision | Moyenne | Moyenne | Contrat d'interface figé tôt ; la décision est hors périmètre |
| Capteurs (LiDAR, sonar) indisponibles ou livrés tard | Moyenne | Moyenne | Architecture en briques : F1 seule est démontrable sans LiDAR |

---

## 8. Ce qui reste à arbitrer avec l'encadrant

1. **Périmètre capteurs** : GPS et RFID/BIR sont-ils réellement à traiter, ou hors périmètre en intérieur ? (§1.2)
2. **Vitesse nominale du VA** — elle conditionne tout le budget de latence. (§4)
3. **Modèle de LiDAR disponible** : 2D (type RPLIDAR) ou 3D ? L'écart de complexité entre les deux est d'un ordre de grandeur.
4. **Accès terrain** pour la collecte du jeu de données, et cadre RGPD associé.
5. **L'AI Kit (Hailo-8L) est-il autorisé** au budget, ou la démonstration doit-elle rester sur CPU nu ? (Cela change la réponse de l'état de l'art.)
6. **Format du contrat d'interface** avec l'IA de décision : ROS 2 ? JSON sur MQTT ? Cadence fixe ou événementielle ?

---

*Suite : [État de l'art et comparaison des modèles](01-etat-de-l-art-et-comparaison-modeles.md) · [État des lieux de l'existant et justification des choix](02-etat-des-lieux-et-justification-des-choix.md)*
