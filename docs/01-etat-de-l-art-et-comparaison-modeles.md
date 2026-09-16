# État de l'art et comparaison des modèles d'IA de perception

*PRI 2026-2027 — Projet 2 : IA embarquée pour la perception des véhicules autonomes en logistique hospitalière*
*Livrable : « État de l'art et comparaison des modèles » — version 1, septembre 2026*

---

## Sommaire

1. [Méthodologie de la comparaison](#1-méthodologie-de-la-comparaison)
2. [F1 — Détection d'objets 2D](#2-f1--détection-dobjets-2d)
3. [F2 — Segmentation de l'espace libre](#3-f2--segmentation-de-lespace-libre)
4. [F3 — Estimation de la distance](#4-f3--estimation-de-la-distance)
5. [F4 — Suivi multi-objets](#5-f4--suivi-multi-objets)
6. [F5 — Fusion, état sémantique et niveau de confiance](#6-f5--fusion-état-sémantique-et-niveau-de-confiance)
7. [Chaîne d'exécution : formats, runtimes et optimisation](#7-chaîne-dexécution--formats-runtimes-et-optimisation)
8. [Option matérielle : accélérateurs pour Raspberry Pi 5](#8-option-matérielle--accélérateurs-pour-raspberry-pi-5)
9. [Grille de décision multicritère](#9-grille-de-décision-multicritère)
10. [Recommandation argumentée](#10-recommandation-argumentée)
11. [Protocole de validation expérimentale](#11-protocole-de-validation-expérimentale)
12. [Sources](#12-sources)

---

## 1. Méthodologie de la comparaison

### 1.1 Principe

Comparer « des modèles d'IA » dans l'absolu n'a pas de sens ici. La comparaison est menée
**brique fonctionnelle par brique fonctionnelle** (F1 à F5, cf. [cadrage §3](00-cadrage-projet.md)),
selon la grille imposée par le cahier des charges :

| Famille (cahier des charges) | Métriques opérationnelles retenues |
|---|---|
| **Performance** — précision, robustesse, complexité | mAP@50-95, mAP@50, **rappel classe « personne »**, dégradation en basse lumière, nombre de paramètres / GFLOPs |
| **Frugalité** — taille, RAM/CPU, énergie | Taille du fichier déployé (Mo), RSS du processus (Mo), puissance moyenne (W) |
| **Embarqué** — temps d'inférence, CPU, temps réel | Latence médiane et p95 sur RPi 5 (ms), % CPU, cadence soutenue (Hz), déterminisme |

Trois critères supplémentaires, non listés explicitement mais **décisifs pour ce projet**,
sont ajoutés et justifiés :

- **Transférabilité** — capacité du modèle à être ré-entraîné sur un petit jeu de données
  hospitalier. Les classes utiles (brancard, chariot de soins, pied à perfusion, porte
  d'ascenseur) sont absentes de COCO : un modèle performant sur COCO mais avide de données en
  ré-entraînement est inutilisable ici.
- **Calibration de la confiance** — le cahier des charges exige explicitement la sortie
  « niveau de confiance / incertitude » (sortie *f*).
- **Maturité de l'outillage embarqué** — existence d'un export ARM CPU testé (NCNN, TFLite,
  ONNX Runtime). Une architecture sans chemin d'export propre coûte des semaines de projet.

### 1.2 Convention de lecture des chiffres

> ⚠️ **Avertissement méthodologique.** Les latences publiées dans la littérature et sur les blogs
> techniques sont **très dispersées** pour un même modèle : selon la résolution d'entrée (320 / 416 /
> 640), le nombre de threads, le format d'export, la version de l'OS (32 vs 64 bits) et surtout le
> refroidissement, un même YOLO nano sur Raspberry Pi 5 est rapporté entre ~80 ms et ~260 ms. Les
> tableaux ci-dessous servent donc à **classer les candidats et à éliminer**, jamais à dimensionner.
> Les valeurs définitives sont produites par le protocole du §11, sur le matériel du projet.

Chaque valeur porte un indicateur de confiance :

| Marque | Signification |
|---|---|
| 📄 | Publiée dans l'article de référence du modèle (benchmark COCO officiel) |
| 🌐 | Rapportée par une source secondaire (documentation d'éditeur, benchmark communautaire) — **ordre de grandeur** |
| 🧮 | Estimée par extrapolation dans ce document — à confirmer par mesure |
| ❓ | Non documentée pour cette configuration — **à mesurer** |

---

## 2. F1 — Détection d'objets 2D

C'est la brique centrale : elle produit les sorties *a* (obstacle / position / distance),
*b* (personne présente) et contribue à *d* (ascenseur disponible).

### 2.1 Les quatre familles architecturales en présence

#### a) Détecteurs mono-étage à ancres, dorsale mobile (2017-2020)

**SSD-MobileNetV2 / SSDLite, EfficientDet-Lite0/1/2.**
Historiquement la référence de l'embarqué. Principe : une dorsale à convolutions séparables en
profondeur (*depthwise separable*) + des têtes de détection sur plusieurs échelles.

- **Ce qui a vieilli** : la précision. EfficientDet-Lite0/1/2 plafonne autour de **23 / 28 / 32 mAP** 🌐
  sur COCO — c'est-à-dire *en dessous* d'un YOLO nano moderne qui atteint ~40 mAP pour une
  empreinte comparable.
- **Ce qui reste** : un outillage TFLite INT8 exceptionnellement mature et une compatibilité
  totale avec les accélérateurs (Coral, NPU de smartphone).
- **Verdict pour ce projet** : **écartés comme candidat principal**. Un écart de 8 à 17 points de
  mAP se paie directement en faux négatifs sur des personnes, ce qui est le risque à ne pas prendre.
  Conservés comme référence basse (*baseline*) dans le protocole expérimental.

#### b) Détecteurs mono-étage sans ancres, ultra-légers

**NanoDet / NanoDet-Plus.**
Conçu dès l'origine pour le mobile : tête FCOS sans ancres, module d'assignation guidée (AGM),
assignateur à étiquettes douces dynamiques (DSLA) et pyramide légère Ghost-PAN.
NanoDet-Plus revendique **+7 mAP** sur COCO par rapport à NanoDet, pour **980 Ko en INT8 /
1,8 Mo en FP16** et ~97 FPS sur smartphone 🌐.

- **Ce qui séduit** : c'est, et de loin, le modèle le plus frugal du tableau — un ordre de grandeur
  sous les YOLO nano en taille de fichier.
- **Ce qui inquiète** : projet communautaire, **peu maintenu depuis 2022**, écosystème
  d'entraînement et d'export moins robuste, très peu de retours de déploiement récents.
- **Verdict** : **candidat de repli sérieux** si et seulement si le budget de latence s'avère
  intenable pour les YOLO nano sur CPU nu. Le risque projet (outillage) est réel mais la frugalité
  est inégalée.

#### c) Détecteurs YOLO modernes (v8 → v11 → 26)

C'est la famille dominante de l'embarqué en 2026. Points clés de l'évolution :

| Version | Année | Apport structurant pour l'embarqué |
|---|---|---|
| YOLOv5n / YOLOv8n | 2020 / 2023 | Sans ancres (v8), export NCNN/TFLite mature, énorme base de retours d'expérience |
| YOLOv10n | 2024 | Introduction de l'entraînement **sans NMS** (double assignation) |
| YOLO11n | 2024 | Meilleur compromis précision/paramètres à empreinte égale ; YOLO11x atteint **54,7 mAP avec 56,9 M paramètres**, contre 54,3 mAP et 76 M paramètres pour RT-DETRv2-x 📄 |
| **YOLO26n** | **janvier 2026** | **Conçu explicitement pour l'edge** : bout-en-bout **sans NMS**, suppression de la *Distribution Focal Loss*, ProgLoss + STAL (petits objets). **2,4 M paramètres, 40,9 mAP COCO** 🌐 ; l'éditeur annonce **jusqu'à +43 % de vitesse d'inférence CPU** 🌐 |

**L'apport le plus important pour ce projet n'est pas le gain de mAP, c'est la suppression du NMS.**
Le *Non-Maximum Suppression* est un post-traitement dont le coût dépend du **nombre de détections**
dans l'image : il est rapide dans un couloir vide, lent dans un hall bondé — exactement le moment
où la perception doit être la plus réactive. Un modèle sans NMS a une **latence déterministe**,
ce qui satisfait directement le critère C4 (latence au 95ᵉ centile) du cadrage. Pour un système
soumis à une exigence de temps réel en présence de personnes, c'est un argument de sécurité,
pas de confort.

#### d) Transformeurs de détection temps réel

**RT-DETR / RT-DETRv2 / RT-DETRv4, D-FINE, RF-DETR.**
Ces architectures ont supprimé le principal défaut des DETR (convergence lente) et dominent
aujourd'hui le haut du classement COCO :

- D-FINE-M : **52,3 mAP** contre 51,5 mAP pour YOLO11-M 📄
- RF-DETR (dorsale DINOv2, Apache 2.0, ICLR 2026) : première famille temps réel à dépasser
  **60 AP sur COCO** 📄 ; la déclinaison **RF-DETR-Nano** est annoncée à **2,3 ms / 67,6 AP50** 📄
  — mais **sur GPU T4**, pas sur CPU ARM.

- **Ce qui séduit** : la meilleure précision absolue, et surtout une **excellente transférabilité**
  (RF-DETR est explicitement conçu pour le *fine-tuning* sur petits jeux de données de domaine, et
  domine le classement RF100-VL d'adaptabilité — précisément notre cas d'usage hospitalier).
- **Ce qui bloque** : l'attention globale est **mal servie par un CPU ARM**. Les gains mesurés sur
  GPU (parallélisme massif, TensorRT) ne se transposent pas ; les opérateurs d'attention sont mal
  optimisés dans NCNN/TFLite, et la quantification INT8 des transformeurs reste délicate. Aucun
  benchmark RPi 5 fiable n'est disponible ❓.
- **Verdict** : **écartés pour l'inférence embarquée sur CPU nu**, mais **retenus comme modèle
  enseignant** pour une distillation de connaissances vers le modèle embarqué, et comme
  **auto-annotateur** du jeu de données hospitalier (§11.2). C'est la bonne façon d'exploiter leur
  précision sans en payer le coût à l'exécution.

### 2.2 Tableau comparatif — référence COCO

Base commune d'évaluation (COCO val2017, 640×640 sauf mention). Ces chiffres **ne dimensionnent pas**
le système ; ils classent les candidats.

| Modèle | Type | Params (M) | mAP@50-95 | Sans NMS | Licence | Confiance |
|---|---|---|---|---|---|---|
| SSD-MobileNetV2 | Ancres, CNN | ~4,3 | ~22 | non | Apache 2.0 | 🌐 |
| EfficientDet-Lite0 | Ancres, CNN | ~3,2 | ~23 | non | Apache 2.0 | 🌐 |
| EfficientDet-Lite2 | Ancres, CNN | ~5,2 | ~32 | non | Apache 2.0 | 🌐 |
| **NanoDet-Plus-m** | Sans ancres, CNN | ~1,2 | ~27 | non | Apache 2.0 | 🌐 |
| YOLOv8n | Sans ancres, CNN | 3,2 | 37,3 | non | AGPL-3.0 | 📄 |
| YOLO11n | Sans ancres, CNN | 2,6 | 39,5 | non | AGPL-3.0 | 📄 |
| **YOLO26n** | Sans ancres, CNN | **2,4** | **40,9** | **oui** | AGPL-3.0 | 🌐 |
| RF-DETR-Nano | Transformeur | ~- | 67,6 **@50** | oui | Apache 2.0 | 📄 |
| D-FINE-M | Transformeur | ~19 | 52,3 | oui | Apache 2.0 | 📄 |
| RT-DETRv2-x | Transformeur | 76 | 54,3 | oui | Apache 2.0 | 📄 |

> 📌 **Point de vigilance licence.** Les modèles Ultralytics (YOLOv8 / YOLO11 / YOLO26) sont sous
> **AGPL-3.0**. Pour un PRI académique publié en dépôt ouvert, c'est compatible. Si le projet devait
> déboucher sur une valorisation industrielle fermée, une licence commerciale serait nécessaire —
> et **RF-DETR / D-FINE / NanoDet (Apache 2.0) deviendraient structurellement préférables**.
> À signaler à l'encadrant : ce n'est pas un détail, c'est un critère de choix à part entière.

### 2.3 Tableau comparatif — comportement rapporté sur Raspberry Pi 5

| Modèle | Format | Résolution | Latence rapportée | Cadence | Verdict vs budget 50 ms | Confiance |
|---|---|---|---|---|---|---|
| YOLOv8n | ONNX, multi-thread | 640 | ~300 ms | ~3,4 FPS | 🔴 | 🌐 |
| YOLOv8n | **NCNN**, multi-thread | 640 | ~258 ms | ~9,0 FPS* | 🔴 | 🌐 |
| YOLO11n | PyTorch | 640 | ~400 ms | ~2,5 FPS | 🔴 | 🌐 |
| YOLO11n | **NCNN** | 640 | **~80 ms** | ~12 FPS | 🟡 | 🌐 |
| YOLO11n | ONNX | 640 | ~147 ms | 6,79 FPS | 🟠 | 🌐 |
| **YOLO26n** | ONNX | 640 | ~128 ms | 7,79 FPS | 🟠 | 🌐 |
| **YOLO26n** | **NCNN** | 640 | ~67 ms | **~15 FPS** | 🟡 | 🌐 |
| YOLO26n | NCNN INT8 | **416** | ~25-35 ms | ~30-40 FPS | 🟢 | 🧮 |
| NanoDet-Plus-m | NCNN INT8 | 416 | ~20-30 ms | ~35-50 FPS | 🟢 | 🧮 |
| RF-DETR-Nano | ONNX | 640 | non documenté | — | — | ❓ |
| YOLOv8s | **Hailo-8L** (AI Kit) | 640 | ~12-40 ms | 25-80 FPS | 🟢 | 🌐 |

\* *Les sources 🌐 sur YOLOv8n NCNN sont contradictoires (9,0 FPS annoncés pour 258 ms de latence
moyenne — incohérence probablement due à un pipeline en parallèle ou à des conditions de mesure
différentes). C'est exactement pourquoi le §11 impose une re-mesure interne.*

### 2.4 Lecture du tableau — les trois enseignements

1. **Le format d'export pèse plus lourd que le choix du modèle.** Passer de PyTorch à NCNN sur
   YOLO11n fait passer la latence de ~400 ms à ~80 ms, soit **un facteur 5**. Aucun changement
   d'architecture dans ce tableau n'offre un tel gain. **Conclusion : l'effort d'optimisation
   (§7) est prioritaire sur l'effort de sélection d'architecture.**
2. **Aucun modèle ne tient le budget de 50 ms en 640×640 sur CPU nu.** Le budget est atteignable
   uniquement en combinant **NCNN + INT8 + réduction de résolution à 416 ou 320**. C'est la
   décision d'ingénierie centrale du projet, et elle doit être validée par la mesure, pas par
   la littérature.
3. **L'écart YOLO26n / YOLO11n (~15 % de vitesse, +1,4 mAP) est réel mais secondaire** face au
   facteur 5 du point 1. YOLO26n est néanmoins préféré pour une raison qualitative :
   le **déterminisme** apporté par l'absence de NMS.

### 2.5 Résolution d'entrée : le levier le plus rentable

Le coût de calcul d'un CNN varie approximativement avec le **carré** de la résolution :

| Résolution | Coût relatif | Latence estimée (base YOLO26n NCNN @640 ≈ 67 ms) | Effet attendu sur la détection |
|---|---|---|---|
| 640×640 | 1,00 | ~67 ms 🌐 | Référence |
| 512×512 | 0,64 | ~43 ms 🧮 | Perte faible sur objets moyens/proches |
| 416×416 | 0,42 | ~28 ms 🧮 | Perte notable sur petits objets lointains |
| 320×320 | 0,25 | ~17 ms 🧮 | Perte forte ; personnes lointaines manquées |

**Argument spécifique au cas d'usage** : dans un couloir hospitalier, les obstacles pertinents
(personne, chariot, brancard) sont **grands dans l'image** parce que proches — c'est la géométrie
d'un couloir de 2 à 3 m de large. La pénalité de la réduction de résolution y est donc bien plus
faible que sur COCO, dont la métrique est dominée par les petits objets. **Ce point doit être
vérifié expérimentalement sur le jeu de données du projet** — c'est l'expérience la plus rentable
à mener en premier (§11.3).

---

## 3. F2 — Segmentation de l'espace libre

Cette brique produit les sorties *c* (couloir dégagé ou obstrué) et *e* (trajectoire libre ou bloquée).

### 3.1 Pourquoi la détection par boîtes ne suffit pas

Un détecteur répond à « qu'y a-t-il et où ? ». Il ne répond pas à « **puis-je passer ?** ».
Trois cas où F1 échoue seul, tous fréquents en milieu hospitalier :

- une **flaque** ou un sol mouillé signalé — pas un objet, mais une zone non navigable ;
- une **marche ou un dénivelé** (seuil de porte, quai de livraison) — invisible en boîte 2D ;
- un obstacle d'une **classe non apprise** — le détecteur ne produit aucune boîte, et le couloir
  est déclaré libre à tort. **C'est le mode de défaillance le plus dangereux du système.**

La segmentation de l'espace libre répond à la question inverse et complémentaire : elle identifie
**le sol navigable** plutôt que les obstacles. Un obstacle inconnu devient alors simplement
« une zone qui n'est pas du sol ». C'est un filet de sécurité par construction.

### 3.2 Candidats

| Modèle | Type | Argument principal | Limite pour RPi 5 |
|---|---|---|---|
| **BiSeNetV2** | CNN deux branches | Architecture conçue pour le temps réel ; ~82,3 % mIoU sur jeux de données de référence 🌐 | Deux branches = deux passes ; coûteux sur CPU |
| **PP-LiteSeg** | CNN encodeur-décodeur léger | Jusqu'à **77,5 % mIoU sur Cityscapes** avec un très bon compromis vitesse 🌐 ; outillage PaddlePaddle mature | Écosystème PaddlePaddle, export ARM moins courant que NCNN |
| **SegFormer-B0** | Transformeur + décodeur MLP | ~83,0 % mIoU, comparable à BiSeNetV2 🌐 ; très bonne robustesse | Même problème d'attention sur CPU ARM que les DETR |
| **YOLO*n-seg** (segmentation d'instances) | Mono-étage | **Mutualise la dorsale avec F1** — une seule inférence pour détection + masques | mAP de masque plus faible qu'un segmenteur dédié |
| **Fusion géométrique LiDAR 2D** | Non appris | **Coût CPU quasi nul**, robuste, déterministe, ne nécessite aucune annotation | 2D seulement : aveugle aux obstacles hors du plan de balayage, et au verre |

### 3.3 Recommandation pour F2

**Ne pas ajouter un second réseau de neurones.** Deux options sont défendables, la seconde est
retenue :

- ❌ **Segmenteur dédié (PP-LiteSeg / SegFormer-B0)** : ajoute 30 à 80 ms de latence 🧮 sur un budget
  déjà tendu, et exige une campagne d'annotation pixel par pixel — la plus coûteuse qui soit.
- ✅ **Variante `-seg` du détecteur retenu, activée uniquement si le budget de latence le permet
  après optimisation**, **complétée par une occupation géométrique issue du LiDAR 2D**.
  Le LiDAR fournit gratuitement une carte d'occupation locale fiable ; le réseau n'a alors à traiter
  que ce que le LiDAR ne voit pas (verre, obstacles bas hors plan, sols mouillés).

C'est le meilleur rapport valeur/coût : le filet de sécurité « obstacle non classifié » est
assuré par un capteur géométrique déterministe, pas par un réseau supplémentaire.

---

## 4. F3 — Estimation de la distance

Le cahier des charges exige « obstacle détecté / **position** / **distance** » : il faut passer
du pixel au mètre.

### 4.1 Comparaison des trois voies

| Approche | Précision métrique | Coût CPU | Robustesse hospitalière | Annotation requise |
|---|---|---|---|---|
| **Profondeur monoculaire apprise** (MiDaS-Small, Depth Anything V2-Small) | Relative, **non métrique** sans calibration | **Élevé** — un second réseau complet | Sensible aux sols réfléchissants | Aucune (pré-entraîné) |
| **Caméra RGB-D / stéréo** | Métrique, ~cm | Faible (calcul déporté dans le capteur) | **Échoue sur le verre et les surfaces brillantes** | Aucune |
| **LiDAR 2D + projection de la boîte** | Métrique, **~6 cm d'erreur moyenne** rapportés 🌐 | **Quasi nul** | Excellente, sauf verre | Aucune |

### 4.2 Ce que dit la littérature sur la profondeur monoculaire embarquée

Les modèles de profondeur monoculaire ont fait des progrès spectaculaires en qualité, mais restent
**hors budget sur CPU ARM** :

- Depth Anything V2-Small : **20,99 ms sur GPU T4** 📄 — soit, par extrapolation des ratios
  observés sur les détecteurs, plusieurs centaines de millisecondes sur RPi 5 🧮.
- MiDaS v2.1-Small a été déployé sur Raspberry Pi 4 (TFLite + OpenCV, C++) 🌐, et PyD-Net atteint
  ~2 Hz sur Raspberry Pi 3 🌐. Les ordres de grandeur sont clairs : **c'est une charge comparable
  à celle du détecteur lui-même**, pour une sortie *relative* qu'il faut ensuite calibrer.

**Conclusion : la profondeur monoculaire apprise est écartée.** Elle doublerait le budget
d'inférence pour fournir une information que le LiDAR donne mieux, en métrique, et gratuitement.

### 4.3 Recommandation pour F3 — fusion géométrique caméra / LiDAR 2D

L'approche retenue est la **fusion par secteur angulaire** (*Angular Sector Fusion*), documentée
dans la littérature récente sur les robots d'intérieur : pour chaque boîte produite par le
détecteur, on projette son secteur angulaire sur le balayage LiDAR et on prend la distance par
percentile bas des retours du secteur.

- Méthode **déterministe, non apprise, à coût CPU négligeable** — elle n'entame pas le budget.
- La littérature rapporte, avec un filtrage de Kalman, une **erreur moyenne de 0,06 m**, avec un
  taux de succès de **95 % sur obstacles statiques** mais seulement **60 % sur obstacles
  dynamiques** 🌐. Ce dernier chiffre est un **avertissement direct pour notre cas d'usage** :
  les personnes en mouvement sont précisément des obstacles dynamiques. D'où l'importance de la
  brique F4 (suivi), qui apporte la cohérence temporelle manquante.
- Contrainte d'installation à retenir : le LiDAR doit être monté **bas** (~16 cm du sol dans les
  travaux cités) pour intercepter les objets usuels d'intérieur (personnes, chaises, plantes,
  pieds de chariot).

**Le sonar conserve un rôle propre et non substituable** : les portes vitrées et les sas, très
présents en milieu hospitalier, sont invisibles à la fois au LiDAR (le faisceau traverse) et à la
caméra (transparence). C'est la justification technique de sa présence dans le parc de capteurs.

---

## 5. F4 — Suivi multi-objets

Le suivi transforme des détections image par image en **objets persistants dotés d'une identité et
d'une vitesse**. Il conditionne les sorties *e* (trajectoire libre ou bloquée — impossible sans
vitesse estimée) et *f* (niveau de confiance — une détection confirmée sur N images est bien plus
fiable qu'une détection isolée).

### 5.1 Comparaison

| Traqueur | Principe | MOTA (MOT17) | IDF1 (MOT17) | Coût CPU | Réidentification apprise |
|---|---|---|---|---|---|
| SORT | Kalman + IoU | ~74 | ~62 | Négligeable | non |
| **ByteTrack** | Association en deux passes, y compris détections à faible score | **80,3** 📄 | **77,3** 📄 | **Négligeable** | **non** |
| OC-SORT | SORT à mise à jour centrée observation | ~78 | ~77 | Négligeable | non |
| **BoT-SORT** | ByteTrack + compensation du mouvement caméra (CMC) + apparence | **80,5** 📄 | **80,2** 📄 | Modéré à élevé (CMC + extracteur ReID) | oui (variante) |
| DeepSORT | Kalman + descripteur d'apparence appris | ~61 | ~62 | **Élevé** (un CNN par piste) | oui |

### 5.2 Analyse et recommandation

**ByteTrack est retenu.** Justification :

1. **Coût CPU négligeable** : purement géométrique (Kalman + IoU), aucun réseau supplémentaire.
   La littérature rapporte un ensemble YOLOv8n + ByteTrack à **plus de 108 FPS** 🌐 — le traqueur
   ne consomme pratiquement rien à côté du détecteur.
2. **Son principe fondateur sert directement notre contrainte de sécurité.** ByteTrack associe
   *aussi* les détections à faible score de confiance, au lieu de les jeter. Une personne
   partiellement occultée par un brancard produit typiquement une détection à faible score :
   ByteTrack la conserve, un traqueur classique la perd. **C'est un gain direct sur le rappel
   « personne »**, notre critère C1.
3. **BoT-SORT est meilleur (+2,9 IDF1) mais pour de mauvaises raisons ici** : son gain vient
   surtout de la compensation du mouvement caméra, conçue pour des séquences filmées à la main
   ou en panoramique. Sur un VA, **l'IMU et l'odométrie fournissent l'ego-motion directement et
   gratuitement** — il est inutile de l'estimer par vision. La variante ReID coûte un CNN par
   piste : rédhibitoire.

> 💡 **Contribution d'ingénierie proposée** : injecter l'ego-motion IMU/odométrie dans la
> prédiction du filtre de Kalman de ByteTrack. On obtient l'essentiel du bénéfice de BoT-SORT
> **à coût nul**, en exploitant des capteurs déjà présents au cahier des charges. C'est un point
> différenciant à mettre en avant dans le rapport final.

---

## 6. F5 — Fusion, état sémantique et niveau de confiance

### 6.1 Sorties d'état sémantique (*c*, *d*, *e*)

Ces sorties ne sont **pas** produites par un réseau de neurones, mais par une **logique de décision
alimentée par F1-F4**. C'est un choix d'architecture délibéré : une règle explicite est auditable,
déterministe et ne demande aucune annotation, là où un classifieur d'état exigerait un jeu de
données dédié pour un gain nul.

| Sortie | Logique proposée |
|---|---|
| *c* — couloir dégagé / obstrué | Aucune piste confirmée dans le corridor de navigation **ET** occupation LiDAR libre sur ≥ X m |
| *d* — ascenseur disponible | Détection « porte d'ascenseur » **+** état (ouverte/fermée) confirmé sur N images **+** absence de personne dans l'ouverture |
| *e* — trajectoire libre / bloquée | Projection des pistes F4 avec leur vitesse sur l'horizon de temps d'arrêt ; test d'intersection avec le corridor |

La sortie *d* mérite une remarque : « ascenseur disponible » n'est **pas** une classe d'objet, c'est
un **état composite**. Le détecteur fournit « porte d'ascenseur » et éventuellement « indicateur
lumineux » ; l'état se déduit ensuite. Confondre les deux conduirait à créer des classes
artificielles (« ascenseur-disponible », « ascenseur-occupé ») très coûteuses à annoter et fragiles.

### 6.2 Le niveau de confiance (sortie *f*) — la vraie difficulté

Le score brut d'un détecteur **n'est pas une probabilité**. Les réseaux modernes sont notoirement
**sur-confiants** : un lot de détections à 0,9 est empiriquement juste à ~70 %. Livrer ce score tel
quel à l'IA de décision serait une faute : la décision ferait confiance à une mesure non calibrée.

**Chaîne de production du niveau de confiance proposée :**

```
score brut du détecteur
   └─► 1. Calibration (Temperature Scaling sur un jeu de validation dédié)
          └─► 2. Agrégation temporelle (âge de la piste, régularité des associations, ByteTrack)
                 └─► 3. Accord inter-capteurs (la boîte est-elle confirmée par le LiDAR ? le sonar ?)
                        └─► 4. Indicateur de conditions (luminosité, flou de mouvement, T° CPU)
                               └─► confiance finale ∈ [0,1], calibrée (ECE ≤ 0,05, critère C9)
```

- **Temperature scaling** : un seul paramètre scalaire appris *après* l'entraînement, coût
  d'inférence strictement nul. C'est le meilleur rapport efficacité/coût de la littérature sur la
  calibration.
- **Vérification par diagramme de fiabilité** et *Expected Calibration Error* — à intégrer au
  protocole expérimental. C'est un livrable à part entière, explicitement demandé par le sujet.
- Les méthodes plus lourdes (MC-Dropout, ensembles profonds) sont **écartées** : elles multiplient
  le coût d'inférence par le nombre de passes, ce qui est incompatible avec le budget.

---

## 7. Chaîne d'exécution : formats, runtimes et optimisation

Le §2.4 l'a établi : **c'est ici que se gagne la faisabilité du projet**, plus que dans le choix
d'architecture.

### 7.1 Comparaison des runtimes d'inférence sur ARM

| Runtime | Points forts | Points faibles | Adapté au projet |
|---|---|---|---|
| **PyTorch** | Référence pour l'entraînement | **Non destiné à l'inférence embarquée** ; ~400 ms sur YOLO11n @640 🌐 | Entraînement seulement |
| **ONNX Runtime** | Universel, très bon support des opérateurs, INT8 dynamique et statique | Moins optimisé que NCNN sur ARM pour les CNN | Oui — référence de portabilité |
| **NCNN** | **Le plus rapide sur CPU ARM** (Tencent, conçu pour le mobile) ; facteur ~5 mesuré vs PyTorch 🌐 | Couverture d'opérateurs plus étroite (problématique pour les transformeurs) | **Oui — cible de déploiement** |
| **TFLite** | Noyaux INT8 ARM optimisés à la main ; écosystème mature ; indispensable pour Coral | Conversion depuis PyTorch indirecte et parfois fragile | Oui — alternative INT8 |
| **OpenVINO** | Excellent sur x86 (≈ ×3,3 en INT8 🌐) | **Cible Intel** — sans objet sur RPi 5 | Non |

### 7.2 Quantification INT8 : pourquoi elle fonctionne précisément sur le Pi 5

C'est un point technique qui mérite d'être explicité dans le rapport, car il est
**spécifique au matériel imposé** :

> Le gain de l'INT8 dépend entièrement de la présence d'une instruction de **produit scalaire**
> dans le jeu d'instructions (ARM *dotprod* / x86 *VNNI*). La littérature de mesure est sans
> ambiguïté : sur **Cortex-A76 (Raspberry Pi 5), qui possède les instructions dot-product, l'INT8
> apporte environ ×2,1** 🌐. Sur un **Cortex-A53 (Raspberry Pi 3), qui ne les possède pas, l'INT8
> est ~1,76× *plus lent*** que le FP32 🌐.

**Conséquence directe** : le choix du Raspberry Pi 5 dans le cahier des charges n'est pas
neutre — c'est la génération à partir de laquelle la stratégie INT8 devient payante.
D'anciens travaux mesurent jusqu'à **×4 en TFLite INT8 sur Raspberry Pi** par rapport au FP32 🌐.
La perte de précision reste faible **à condition que la calibration soit soignée** (jeu de
calibration représentatif : couloirs de jour *et* de nuit, plusieurs sites).

### 7.3 Techniques d'optimisation, classées par rapport gain/effort

| Technique | Gain attendu | Effort | Risque | Priorité |
|---|---|---|---|---|
| **Export NCNN** | **×3 à ×5** 🌐 | Faible | Faible | **1** |
| **Réduction de résolution** (640 → 416) | **×2,4** 🧮 | Très faible | Perte sur petits objets — **à mesurer** | **2** |
| **Quantification INT8** | **×2,1** 🌐 | Moyen (jeu de calibration) | Perte de mAP si calibration bâclée | **3** |
| Élagage structuré (*pruning*) | ×1,2 à ×1,5 | Élevé (ré-entraînement) | Perte de précision | 4 |
| Distillation (RF-DETR → YOLO26n) | +1 à +3 mAP à coût d'inférence nul | Élevé | Aucun à l'exécution | 5 (si le temps le permet) |
| Réduction du nombre de classes | ×1,05 à ×1,1 | Nul (vient du jeu de données) | Aucun | Systématique |

**Gain cumulé estimé** : ×3 (NCNN) × 2,4 (416) × 2,1 (INT8) ≈ **×15** par rapport à la
référence PyTorch @640 🧮. Partant de ~400 ms, cela place la cible autour de **25-30 ms**,
c'est-à-dire **dans le budget de 50 ms**, avec de la marge pour F2-F5.

> ⚠️ Les gains ne se multiplient jamais exactement (saturation mémoire, surcoûts de
> quantification/déquantification). L'estimation ×15 est un **majorant optimiste** ; un
> facteur ×8 à ×10 serait déjà un succès. C'est l'objet de la mesure §11.

---

## 8. Option matérielle : accélérateurs pour Raspberry Pi 5

À traiter comme **plan de repli**, pas comme solution de premier rang — le sujet demande de
démontrer la **frugalité**, et une solution qui n'existe que grâce à un accélérateur à 70 € répond
moins bien à la problématique posée.

| Solution | Puissance de calcul | Performance rapportée | Consommation | Remarque |
|---|---|---|---|---|
| **CPU seul (4× A76)** | — | cf. §2.3 | 7-12 W système | **Cible principale** : c'est la vraie démonstration de frugalité |
| **AI Kit / AI HAT+ (Hailo-8L)** | 13 TOPS | YOLOv8s @640 : **25-35 FPS**, jusqu'à **80 FPS** en PCIe Gen 3 🌐 | 3-4 TOPS/W ; système < 4 W en 320×320 @ 5 FPS 🌐 | Occupe le port PCIe ; nécessite le SDK Hailo et une compilation HEF du modèle |
| Google Coral USB | 4 TOPS | Bon en TFLite INT8 | ~2 W | Contraintes d'opérateurs fortes ; écosystème en perte de vitesse |

**Position recommandée** : mener le projet sur **CPU nu**, et documenter le Hailo-8L comme
**extension mesurée** dans le protocole expérimental. Cela donne deux points de comparaison dans
le rapport final (frugalité maximale vs performance maximale) et transforme un risque en résultat.

---

## 9. Grille de décision multicritère

Pondérations dérivées des critères d'évaluation du cahier des charges (les trois familles y
pèsent à parts comparables), avec une pondération renforcée sur le déterminisme et la
transférabilité, justifiée aux §2.1c et §1.1.

| Critère | Poids | SSD-MobileNetV2 | NanoDet-Plus | YOLOv8n | YOLO11n | **YOLO26n** | RF-DETR-N |
|---|---|---|---|---|---|---|---|
| Précision (mAP, rappel personne) | 20 % | 1 | 2 | 3 | 4 | **4** | **5** |
| Latence sur RPi 5 CPU | 20 % | 4 | **5** | 3 | 4 | **4** | 1 |
| Frugalité (taille, RAM) | 15 % | 4 | **5** | 3 | 4 | **4** | 2 |
| Déterminisme (sans NMS) | 10 % | 1 | 1 | 1 | 1 | **5** | **5** |
| Maturité de l'export ARM | 15 % | **5** | 3 | **5** | **5** | 4 | 1 |
| Transférabilité (petit jeu de données) | 10 % | 2 | 2 | 4 | 4 | **4** | **5** |
| Écosystème & maintenance | 10 % | 3 | 1 | **5** | **5** | 4 | 4 |
| **Score pondéré / 5** | | **2,95** | **3,00** | **3,40** | **3,95** | **4,10** | **3,05** |

*Échelle : 1 = inadapté, 5 = excellent. Le détail du calcul est reproductible à partir du tableau.*

**Lecture des résultats :**

- **YOLO26n arrive en tête (4,10)** grâce au cumul d'un bon niveau sur tous les critères et d'un
  avantage exclusif sur le déterminisme.
- **YOLO11n le suit de près (3,95)** avec un écosystème d'export plus éprouvé — c'est le
  **repli immédiat** si YOLO26 pose des difficultés d'export NCNN, son principal risque
  (modèle récent, janvier 2026).
- **NanoDet-Plus (3,00)** domine sur la frugalité pure ; il reste le repli en cas d'échec du
  budget de latence.
- **RF-DETR-Nano (3,05)** obtient les meilleures notes de précision et de transférabilité mais est
  pénalisé par l'absence de chemin d'export ARM éprouvé. **Son score bas ne reflète pas sa qualité,
  mais son inadéquation à cette cible matérielle précise** — d'où son rôle d'enseignant/annotateur.

> ⚠️ **Ce classement repose partiellement sur des estimations 🌐/🧮.** Il oriente le choix ; il ne
> le clôt pas. Les trois premiers candidats doivent être re-mesurés selon le §11 avant que le
> livrable « choix argumenté du modèle » ne soit figé.

---

## 10. Recommandation argumentée

### 10.1 Architecture de perception proposée

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Raspberry Pi 5 — 4× Cortex-A76                       │
│                                                                          │
│  Caméra ──► Pré-traitement ──► YOLO26n (NCNN INT8, 416×416)              │
│   30 Hz      redim. + norm.     └─► boîtes + classes + scores bruts      │
│                  │                            │                          │
│                  │                            ▼                          │
│  LiDAR 2D ───────┼───────────────►  ByteTrack + ego-motion IMU           │
│   10 Hz          │                  (pistes, vitesses, âge)              │
│                  │                            │                          │
│  Sonar ──────────┤                            ▼                          │
│   10 Hz          │              Fusion par secteur angulaire             │
│                  │              (boîte × balayage LiDAR → distance)      │
│  IMU/Odom ───────┘                            │                          │
│   50 Hz                                       ▼                          │
│                              Calibration + confiance multi-source        │
│                                               │                          │
│                                               ▼                          │
│                         Logique d'état (couloir, ascenseur, trajectoire) │
│                                               │                          │
└───────────────────────────────────────────────┼──────────────────────────┘
                                                ▼
                                   Sortie structurée @ 10 Hz
                                   → IA de décision (hors périmètre)
```

### 10.2 Synthèse des choix

| Brique | Choix retenu | Repli | Argument décisif |
|---|---|---|---|
| **F1** Détection | **YOLO26n**, NCNN INT8, 416×416 | YOLO11n (export plus éprouvé) → NanoDet-Plus (frugalité) | Meilleur score multicritère ; **latence déterministe** grâce à l'absence de NMS |
| **F2** Espace libre | **Occupation LiDAR 2D** + variante `-seg` si le budget le permet | Segmenteur dédié PP-LiteSeg | Évite un second réseau et une campagne d'annotation pixel |
| **F3** Distance | **Fusion par secteur angulaire caméra/LiDAR 2D** | Caméra RGB-D | Métrique, ~6 cm d'erreur, **coût CPU nul** ; la profondeur monoculaire doublerait le budget |
| **F3'** Verre / sas | **Sonar** | — | Seul capteur voyant les surfaces vitrées |
| **F4** Suivi | **ByteTrack + ego-motion IMU** | OC-SORT | Coût nul ; conserve les détections à faible score → **gain de rappel sur « personne »** |
| **F5** Confiance | **Temperature scaling + agrégation temporelle + accord inter-capteurs** | — | Coût d'inférence nul ; répond à la sortie *f* du sujet |
| **Runtime** | **NCNN** (référence ONNX Runtime conservée) | TFLite INT8 | Facteur ~5 mesuré sur ARM |
| **Matériel** | **CPU nu**, Hailo-8L documenté en extension | AI Kit si le budget de latence échoue | La frugalité est un critère d'évaluation du sujet |

### 10.3 Ce qui rend cette architecture cohérente avec la problématique

Le sujet demande une IA **« performante, frugale et apte au déploiement embarqué »**. La logique
suivie tient en une phrase : **un seul réseau de neurones dans la boucle**.

Toutes les autres fonctions (distance, suivi, état, confiance) sont assurées par des méthodes
géométriques ou statistiques à coût quasi nul, qui exploitent des capteurs déjà présents au
cahier des charges. C'est ce qui permet de tenir simultanément les trois familles de critères
d'évaluation — là où un empilement de réseaux spécialisés (détection + segmentation + profondeur)
saturerait le CPU dès la première démonstration.

---

## 11. Protocole de validation expérimentale

Ce qui précède est un état de l'art : il **oriente**, il ne prouve pas. Voici les mesures à
produire pour transformer cette recommandation en « choix argumenté » défendable.

### 11.1 Banc de mesure sur Raspberry Pi 5

**Conditions imposées** (sans quoi la mesure n'est pas reproductible) :

- Raspberry Pi OS 64 bits, dissipateur **actif**, alimentation officielle 27 W
- **10 minutes de chauffe** avant toute mesure ; relevé de `vcgencmd measure_temp` et
  `vcgencmd get_throttled` en continu
- 1 000 images, les 50 premières écartées (préchauffage des caches)
- Report de la **médiane**, du **p95** et du **maximum** — pas seulement de la moyenne
- Wattmètre USB-C en ligne pour la puissance système
- `psutil` pour le RSS et le pourcentage CPU par cœur

**Matrice d'essais** (3 modèles × 3 formats × 3 résolutions = 27 configurations) :

| Axe | Valeurs |
|---|---|
| Modèle | YOLO26n · YOLO11n · NanoDet-Plus-m |
| Format | PyTorch (référence) · ONNX FP32 · NCNN FP16 · NCNN INT8 |
| Résolution | 640 · 416 · 320 |

### 11.2 Jeu de données

- **Collecte terrain** : couloirs, halls d'ascenseur, sas, de jour et de nuit, avec et sans
  circulation. Anonymisation par floutage des visages **à la source** (RGPD, secret médical).
- **Classes proposées** : `personne`, `personne_au_sol`, `chariot`, `brancard`,
  `pied_a_perfusion`, `porte_ascenseur`, `porte`, `obstacle_statique`.
- **Pré-annotation par RF-DETR ou D-FINE** (exécuté hors ligne sur machine de bureau, pas sur le
  Pi), puis correction manuelle. C'est ainsi que la précision des transformeurs est exploitée sans
  en payer le coût embarqué.
- **Jeu de test dédié basse lumière**, séparé, pour mesurer le critère de robustesse.

### 11.3 Expérience prioritaire — la courbe résolution / rappel

**C'est l'expérience à mener en premier**, avant tout entraînement long. Elle conditionne toute
l'architecture.

Tracer, sur le jeu de test hospitalier : **rappel sur la classe « personne » en fonction de la
résolution d'entrée (640 / 512 / 416 / 320)**, croisé avec la distance de l'objet.

- Si le rappel se maintient à 416 (hypothèse du §2.5 : les obstacles sont proches donc grands
  dans l'image en couloir), **la faisabilité du projet sur CPU nu est acquise**.
- S'il s'effondre, il faut arbitrer immédiatement entre : réduire la vitesse du VA, accepter
  5-7 Hz, ou basculer sur l'accélérateur Hailo-8L. **Le savoir en semaine 4 plutôt qu'en
  semaine 20 est la meilleure réduction de risque du projet.**

### 11.4 Mesures de calibration

Diagramme de fiabilité et *Expected Calibration Error* avant / après temperature scaling, sur le
jeu de validation. Cible : **ECE ≤ 0,05** (critère C9 du cadrage).

---

## 12. Sources

**Détection d'objets — architectures et benchmarks**
- [Ultralytics YOLO26 — modèle edge-first, NMS-free](https://www.ultralytics.com/blog/ultralytics-yolo26-the-new-standard-for-edge-first-vision-ai)
- [Ultralytics YOLO26 — documentation du modèle](https://docs.ultralytics.com/models/yolo26)
- [YOLO26: An Analysis of NMS-Free End to End Framework for Real-Time Object Detection (arXiv 2601.12882)](https://arxiv.org/pdf/2601.12882)
- [Ultralytics YOLO Evolution: YOLO26, YOLO11, YOLOv8, YOLOv5 (arXiv 2510.09653)](https://arxiv.org/pdf/2510.09653)
- [YOLO11 vs RT-DETRv2 — comparaison](https://docs.ultralytics.com/compare/yolo11-vs-rtdetr)
- [RT-DETR — DETRs Beat YOLOs on Real-time Object Detection (arXiv 2304.08069)](https://arxiv.org/pdf/2304.08069)
- [RT-DETRv4 (arXiv 2510.25257)](https://arxiv.org/pdf/2510.25257)
- [RF-DETR: Neural Architecture Search for Real-Time Detection Transformers (arXiv 2511.09554)](https://arxiv.org/pdf/2511.09554)
- [RF-DETR Nano / Small / Medium — annonce Roboflow](https://blog.roboflow.com/rf-detr-nano-small-medium/)
- [Best Object Detection Models 2026 — RF-DETR, YOLOv12 & Beyond](https://blog.roboflow.com/best-object-detection-models/)
- [NanoDet-Plus — dépôt de référence](https://github.com/Awaker1/NanoDet-Plus)
- [A Comprehensive Evaluation of Deep Learning Object Detection Models on Heterogeneous Edge Devices (arXiv 2409.16808)](https://arxiv.org/html/2409.16808)
- [Computer Vision Model Leaderboard — Roboflow](https://leaderboard.roboflow.com/)

**Raspberry Pi 5 — mesures et accélération**
- [YOLO on Raspberry Pi — setup & benchmarks (Ultralytics)](https://docs.ultralytics.com/guides/raspberry-pi)
- [RPi YOLO Benchmark — YOLOv8n (NCNN vs ONNX, multi-thread)](https://kadirmertabatay.github.io/rpi-yolo-benchmark/benchmarks/yolov8/yolov8n/)
- [YOLO26 on a Raspberry Pi 5 with the AI Kit — NCNN export & frame-rate benchmarks](https://aegisai.in/yolo26-raspberry-pi-5-ai-kit-hailo-ncnn-benchmarks/)
- [Benchmark on RPi5 and CM4 running YOLOv8s with the RPi AI Kit — Seeed Studio](https://wiki.seeedstudio.com/benchmark_on_rpi5_and_cm4_running_yolov8s_with_rpi_ai_kit/)
- [Testing Raspberry Pi's AI Kit — 13 TOPS (Jeff Geerling)](https://www.jeffgeerling.com/blog/2024/testing-raspberry-pis-ai-kit-13-tops-70/)
- [Computer Vision Applications with YOLO — Edge AI Engineering](https://mjrovai.github.io/EdgeML_Made_Ease_ebook/raspi/object_detection/cv_yolo.html)

**Quantification et runtimes**
- [Is INT8 Portable? A Cross-Platform Measurement Study of Quantized Inference (arXiv 2609.16085)](https://arxiv.org/html/2609.16085)
- [Performance Characterization of using Quantization for DNN Inference (arXiv 2303.05016)](https://arxiv.org/pdf/2303.05016)
- [Accelerating Deep Learning Model Inference on Arm CPUs with Ultra-Low Bit Quantization (arXiv 2207.08820)](https://arxiv.org/pdf/2207.08820)
- [Does Quantization Improve Inference Speed? It Depends](https://par.nsf.gov/servlets/purl/10636811)

**Segmentation et profondeur**
- [PP-LiteSeg: A Superior Real-Time Semantic Segmentation Model (arXiv 2204.02681)](https://arxiv.org/abs/2204.02681)
- [Real-Time Freespace Segmentation on Autonomous Robots (arXiv 1902.00842)](https://arxiv.org/pdf/1902.00842)
- [Depth-guided Free-space Segmentation for a Mobile Robot (arXiv 2311.01966)](https://arxiv.org/html/2311.01966)
- [Enhancing Robustness of Indoor Robotic Navigation with Free-Space Segmentation Models (arXiv 2402.08763)](https://arxiv.org/pdf/2402.08763)
- [MiDaS v2.1-small sur Raspberry Pi (TFLite + OpenCV, C++)](https://github.com/KozhaAkhmet/MiDaS-v2.1-small-cpp)
- [Monocular Depth Estimation — Ultralytics](https://docs.ultralytics.com/tasks/depth)

**Suivi multi-objets**
- [SORT vs ByteTrack vs OC-SORT vs BoT-SORT vs C-BIoU — MOT Benchmark Comparison](https://trackers.roboflow.com/latest/trackers/comparison/)
- [BoT-SORT: Robust Associations Multi-Pedestrian Tracking (arXiv 2206.14651)](https://arxiv.org/pdf/2206.14651)
- [Observation-Centric SORT (arXiv 2203.14360)](https://arxiv.org/pdf/2203.14360)
- [Multi-Object Tracking — DeepSORT, ByteTrack, OC-SORT in production 2026](https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/multi-object-tracking-deepsort-bytetrack-ocsort)
- [IndoorCrowd: A Multi-Scene Dataset for Human Detection, Segmentation, and Tracking (arXiv 2604.02032)](https://arxiv.org/pdf/2604.02032)

**Fusion capteurs et robotique d'intérieur**
- [Lightweight Semantic-Aware Route Planning on Edge Hardware: Monocular Camera–2D LiDAR Fusion (PMC13075264)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13075264/)
- [Fusion of 2D LiDAR and Vision-Based Detection for Collision-Aware Indoor Navigation (Springer)](https://link.springer.com/chapter/10.1007/978-3-032-18474-0_26)
- [A Review of Sensing Technologies for Indoor Autonomous Mobile Robots (PMC10893033)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10893033/)
- [Sensor Data Fusion for a Mobile Robot Using Neural Networks (PMC8749872)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8749872/)
- [LiDAR vs RGB-D Cameras for AMRs — Orbbec](https://www.orbbec.com/blog/how-lidar-and-rgbd-cameras-compare-and-work-together/)

---

*Document de travail — version 1. Les valeurs marquées 🌐 et 🧮 doivent être confirmées par les
mesures du §11 avant la remise du livrable « choix argumenté du modèle ».*
