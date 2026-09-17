# Note de synthèse

*PRI 2026-2027 · Projet 2 · Encadrement : Moïse DJOKO-KOUAM*
*Note de synthèse — version 1, septembre 2026*

État des lieux de l'existant, comparaison des modèles et choix technologiques.
Le détail complet figure dans le rapport associé (39 p.).

---

## 1. Le problème, reformulé

**Problématique du sujet :** concevoir une IA de perception *performante, frugale et apte au
déploiement embarqué*, qui transforme des informations de perception hétérogènes en une
représentation structurée de l'environnement du véhicule autonome (VA).

**Le point structurant :** le module de perception n'est pas le produit final — son client est
une **IA de décision**, hors périmètre. Le livrable réel est donc un **contrat d'interface** :
un flux de données structurées, horodatées et **assorties d'un niveau de confiance**.

| Sortie attendue | Nature | Produite par |
|---|---|---|
| a — Obstacle détecté / position / distance | Géométrique + classe | Détection + fusion LiDAR |
| b — Personne présente | Classe + comptage | Détection |
| c — Couloir dégagé ou obstrué | État | Occupation LiDAR + suivi |
| d — Ascenseur disponible | État composite | Détection + logique (voir §4, E3) |
| e — Trajectoire libre ou bloquée | État | Suivi + projection des vitesses |
| **f — Niveau de confiance** | Scalaire [0,1] | **Calibration (§6)** |

La sortie **f** est la plus exigeante : le score brut d'un détecteur n'est pas une probabilité.
Les réseaux modernes sont sur-confiants — un lot de détections à 0,9 est empiriquement juste à
environ 70 %. La livrer telle quelle à l'IA de décision serait une faute.

---

## 2. La contrainte qui commande tout : le Raspberry Pi 5

| Caractéristique | Conséquence directe |
|---|---|
| 4 × Arm Cortex-A76 @ 2,4 GHz | **Pas de GPU ni de NPU** : toute l'inférence est sur CPU |
| Instructions NEON **dot-product** | L'INT8 est réellement accéléré (**× 2,1** mesuré sur A76) — contrairement au Cortex-A53 du Pi 3, où l'INT8 est **1,76 × plus lent**. Le choix du Pi 5 n'est donc pas neutre |
| ~7-12 W en charge, throttling sans dissipateur | Le refroidissement fait partie du protocole de mesure |

### Le budget de latence — transformer « temps réel » en un seuil opposable

VA à 1,0 m/s croisant un piéton à 1,4 m/s → rapprochement à 2,4 m/s. Avec une décélération
confortable de 1 m/s² (charge fragile : prélèvements, médicaments) et 0,5 m de marge, la portée
de détection utile est d'environ **4 m**. En visant une boucle à 10 Hz, dont ~45 ms sont
consommés par l'acquisition, le pré-traitement et la fusion :

> ### Budget d'inférence : ≤ 50 ms par image, soutenu, à température stabilisée
> soit 10 Hz de cadence de perception et 10 cm parcourus par cycle.

| Latence d'inférence (Pi 5, 4 threads, à chaud) | Verdict |
|---|---|
| ≤ 50 ms | Confortable — marge pour la fusion et le suivi |
| 50 – 100 ms | Acceptable |
| 100 – 200 ms | Limite — impose de ralentir le VA ou d'ajouter un accélérateur |
| > 200 ms | **Éliminatoire** en environnement partagé avec des piétons |

---

## 3. État des lieux de l'existant

La logistique hospitalière autonome est un marché **mature**, pas un domaine émergent.

| Système | Capteurs | Calcul | IA de perception | Ascenseur |
|---|---|---|---|---|
| **Aethon TUG** (prod. depuis ~2004) | LiDAR + ultrasons + IR, puis caméra de profondeur RealSense | x86 embarqué | SLAM au cœur ; la caméra est arrivée **en dernier**, en complément | Réseau |
| **Panasonic HOSPI** (prod. depuis ~2013) | Capteurs multiples, multi-hauteurs | Embarqué | Évitement + carte pré-établie. **Certifié ISO 13482** | **Réseau** |
| **Relay Robotics** | LiDAR + profondeur + ultrasons | Embarqué | Navigation en environnement public encombré | **Réseau** |
| **Diligent Moxi** | LiDAR + caméras multiples | Embarqué haute perf. | Perception + manipulation + interaction sociale | Réseau |
| **ORB** — Carnegie Mellon, IEEE CASE 2025 | Multimodaux (base Fetch) | **GPU** | **YOLOv7 + SAM 2 + Grounding DINO**, ROS 2, arbres de comportement | — |
| **Prototypes Raspberry Pi** (académiques) | Caméra seule le plus souvent | **Raspberry Pi 3/4/5** | YOLOv8 / v10 / v12n seul — **6 à 8 FPS** | — |

**Les trois régimes sont nets :** l'industrie résout le problème **en y mettant le matériel
nécessaire** ; la recherche **en y mettant un GPU** ; les prototypes bas coût s'arrêtent à la
détection brute, sans structuration ni quantification de l'incertitude.

---

## 4. Quatre enseignements, et ce qu'ils imposent

| | Enseignement | Ce qu'il impose à notre projet |
|---|---|---|
| **E1** | **La géométrie d'abord, la sémantique ensuite.** Aucun système en production ne fonde sa navigation sur la caméra : tous partent de la télémétrie et ajoutent la vision par-dessus | Le LiDAR 2D fournit la distance métrique et l'espace libre pour un **coût CPU nul**. La profondeur monoculaire apprise (MiDaS, Depth Anything) est **écartée** : elle doublerait le budget d'inférence pour une sortie non métrique |
| **E2** | **La sécurité des personnes ne passe pas par l'IA.** ISO 3691-4 exige un niveau **PLd** (ISO 13849) pour la détection de personnes — redondance, détection de défaut. **Aucun réseau de neurones ne peut y prétendre** : il est statistique, pas déterministe | Dans tous les systèmes commerciaux, un **scanner laser certifié** garantit l'arrêt ; l'IA sert à *comprendre* la scène. Notre module est un **démonstrateur de perception, pas un organe de sécurité** — à écrire explicitement. En contrepartie, le **déterminisme de la latence** et l'**honnêteté de la confiance** deviennent des critères de premier rang |
| **E3** | **Ce qui est connu par le réseau ne doit pas être deviné par un capteur.** HOSPI et Relay obtiennent l'état de l'ascenseur par **requête réseau** — exacte, instantanée, fiable à 100 % | La sortie *d* est mal posée comme problème de vision. **Point à arbitrer (§8)** |
| **E4** | **Sur Raspberry Pi, 6-8 FPS est le régime naturel** d'un YOLO non optimisé — soit **sous notre cible**. Les revues convergent sur un triptyque : quantification, élagage, architectures légères | L'effort doit porter sur la **chaîne d'exécution**, pas sur l'architecture du modèle (§5) |

---

## 5. Comparaison des modèles de détection

### 5.1 Les candidats

| Modèle | Type | Params | mAP COCO | Sans NMS | Latence Pi 5 (640 px) | Verdict |
|---|---|---|---|---|---|---|
| SSD-MobileNetV2 / EfficientDet-Lite | CNN à ancres | 3-5 M | 22-32 | non | — | **Écarté** : 8 à 17 points de mAP sous un YOLO nano moderne |
| NanoDet-Plus-m | CNN sans ancres | ~1,2 M | ~27 | non | ~20-30 ms (416, INT8, est.) | **Repli** : le plus frugal (980 Ko en INT8), mais peu maintenu depuis 2022 |
| YOLOv8n | CNN sans ancres | 3,2 M | 37,3 | non | ~258 ms (NCNN) | Écosystème très mûr |
| YOLO11n | CNN sans ancres | 2,6 M | 39,5 | non | **~80 ms** (NCNN) | **Repli n° 1** : export NCNN le plus éprouvé |
| **YOLO26n** (janv. 2026) | CNN sans ancres | **2,4 M** | **40,9** | **oui** | **~67 ms** (NCNN) | **Retenu** |
| RF-DETR-Nano / D-FINE | Transformeur | — | **meilleure précision** | oui | non documentée | **Écarté pour l'embarqué** : conçus pour GPU, attention mal servie par un CPU ARM. **Réutilisés hors ligne** comme modèle enseignant et auto-annotateur |

*Chiffres issus de la littérature, très dispersés selon la résolution, le nombre de threads et le
refroidissement. Ils servent à **classer et éliminer**, pas à dimensionner : la mesure interne
reste à produire (§7).*

### 5.2 Les deux résultats qui décident

**1. Le format d'export pèse plus lourd que le choix du modèle.** Passer de PyTorch à NCNN sur
YOLO11n fait passer la latence de ~400 ms à ~80 ms — **un facteur 5**. Aucun changement
d'architecture du tableau n'offre un tel gain.

| Technique | Gain | Priorité |
|---|---|---|
| Export **NCNN** (runtime ARM de Tencent) | **× 3 à × 5** | 1 |
| Résolution 640 → **416** | **× 2,4** | 2 |
| Quantification **INT8** (dot-product du A76) | **× 2,1** | 3 |
| **Cumul estimé** | **≈ × 15**, soit ~400 ms → **25-30 ms** | — |

**2. YOLO26n est préféré pour une raison qualitative, pas pour son mAP.** Son avantage de
+1,4 point sur YOLO11n est secondaire face au facteur 5 ci-dessus. Ce qui le départage, c'est
l'architecture **sans NMS** : le coût du *Non-Maximum Suppression* dépend du nombre de détections
dans l'image — rapide dans un couloir vide, lent dans un hall bondé, c'est-à-dire **au pire
moment**. Sans NMS, la latence est déterministe. C'est exactement ce qu'exige l'enseignement E2.

---

## 6. Le choix retenu

### Principe directeur : un seul réseau de neurones dans la boucle

Toutes les autres fonctions — distance, suivi, état, confiance — sont assurées par des méthodes
géométriques ou statistiques à coût quasi nul, exploitant des capteurs déjà présents au cahier
des charges. C'est ce qui permet de tenir simultanément les trois familles de critères
(performance, frugalité, embarqué), là où un empilement de réseaux spécialisés saturerait le CPU.

```
   Caméra 30 Hz
        │
        ▼
   YOLO26n  (NCNN INT8, 416×416)              ◄── le seul réseau de neurones
   boîtes + classes + scores bruts
        │
        ▼
   ByteTrack                                  ◄── IMU / odométrie 50 Hz
   pistes, vitesses, âge                          (ego-motion)
        │
        ▼
   Fusion par secteur angulaire               ◄── LiDAR 2D 10 Hz
   boîte × balayage LiDAR → distance              (distance, espace libre)
        │                                     ◄── Sonar 10 Hz
        │                                         (verre, sas)
        ▼
   Calibration + confiance multi-source
        │
        ▼
   Logique d'état  →  sortie structurée @ 10 Hz  →  IA de décision
   couloir · ascenseur · trajectoire                (hors périmètre)
```

| Brique | Choix | Argument décisif |
|---|---|---|
| **Détection** | **YOLO26n**, NCNN INT8, 416×416 | Meilleur score multicritère (4,10/5) ; **latence déterministe** (sans NMS) |
| **Distance** | **Fusion caméra / LiDAR 2D** par secteur angulaire | Métrique, ~6 cm d'erreur rapportés, **coût CPU nul** |
| **Espace libre** | **Occupation LiDAR 2D** | Un obstacle de classe inconnue devient « une zone qui n'est pas du sol » — filet de sécurité par construction, sans second réseau ni annotation pixel |
| **Verre et sas** | **Sonar** | Seul capteur voyant les surfaces vitrées, invisibles au LiDAR **et** à la caméra |
| **Suivi** | **ByteTrack + ego-motion IMU** | Coût nul ; conserve les détections à faible score → **gain de rappel sur « personne »**. L'IMU remplace gratuitement la compensation visuelle de BoT-SORT |
| **Confiance** | **Temperature scaling** + agrégation temporelle + accord inter-capteurs | Coût d'inférence **nul** ; répond à la sortie *f*. MC-Dropout et ensembles écartés (coût × N passes) |
| **Matériel** | **CPU nu** ; AI Kit Hailo-8L documenté en repli mesuré | La frugalité est un critère d'évaluation du sujet — y répondre avec un accélérateur à 70 € serait répondre à côté |

---

## 7. Ce qui reste à prouver

L'état de l'art **oriente**, il ne prouve pas. Trois travaux à mener avant de figer le choix.

**① L'expérience prioritaire — courbe résolution / rappel.** À mener **avant tout entraînement
long** : tracer le rappel sur la classe « personne » en fonction de la résolution d'entrée
(640 / 512 / 416 / 320), croisé avec la distance.

- L'hypothèse à tester : en couloir hospitalier (2-3 m de large), les obstacles pertinents sont
  **proches donc grands dans l'image**. La pénalité de la réduction de résolution devrait y être
  bien plus faible que sur COCO, dont la métrique est dominée par les petits objets.
- Si le rappel tient à 416, **la faisabilité sur CPU nu est acquise**. Sinon, il faut arbitrer
  entre ralentir le VA, accepter 5-7 Hz, ou basculer sur le Hailo-8L. **Le savoir en semaine 4
  plutôt qu'en semaine 20 est la meilleure réduction de risque du projet.**

**② Le banc de mesure sur Pi 5.** 3 modèles × 4 formats × 3 résolutions. Conditions imposées :
10 min de chauffe, dissipateur actif, 1 000 images, report de la **médiane et du p95** (pas de la
seule moyenne), relevé de température, de throttling et de consommation. Aucun des travaux
Raspberry Pi recensés ne publie ces éléments — c'est un espace de contribution réel.

**③ Le jeu de données.** Collecte en couloirs, halls d'ascenseur et sas, de jour **et de nuit**,
avec floutage des visages à la source (RGPD, secret médical). Classes absentes de COCO à annoter :
brancard, chariot de soins, pied à perfusion, porte d'ascenseur, personne au sol.
Pré-annotation par RF-DETR ou D-FINE **hors ligne**, puis correction manuelle.

### Critères de réussite proposés

| Critère | Seuil |
|---|---|
| Rappel classe « personne » @ IoU 0,5 | ≥ 95 % |
| mAP@0,5 toutes classes | ≥ 60 % |
| Latence médiane / p95 sur Pi 5 | ≤ 50 ms / ≤ 100 ms |
| Taille du modèle déployé | ≤ 15 Mo |
| Puissance système | ≤ 8 W moyens |
| Calibration de la confiance (ECE) | ≤ 0,05 |

---

## 8. Points à arbitrer — questions pour la réunion

1. **Périmètre capteurs.** Le GPS est inopérant en intérieur ; le RFID et le BIR relèvent de la
   localisation symbolique, pas de la perception géométrique. Les traite-t-on, ou sont-ils hors
   périmètre ?
2. **Vitesse nominale du VA.** Elle conditionne tout le budget de latence du §2.
3. **LiDAR disponible : 2D ou 3D ?** L'écart de complexité entre les deux est d'un ordre de grandeur.
4. **L'AI Kit (Hailo-8L) est-il autorisé au budget**, ou la démonstration doit-elle rester sur
   CPU nu ? Cela change la réponse de l'état de l'art.
5. **Accès terrain** pour la collecte du jeu de données, et cadre RGPD associé.
6. **Ascenseur : interface réseau accessible ?** (cf. E3) Sinon, la sortie *d* se dégrade en une
   estimation visuelle nettement moins fiable.

> **Point de licence à signaler.** YOLO26 et YOLO11 sont sous **AGPL-3.0** : compatible avec un
> PRI académique publié en dépôt ouvert, mais bloquant en cas de valorisation industrielle
> fermée. Dans ce cas, **RF-DETR, D-FINE et NanoDet (Apache 2.0)** deviendraient structurellement
> préférables. Ce n'est pas un détail : c'est un critère de choix à part entière.

---

## Sources principales

Bibliographie complète (une cinquantaine de références) dans le rapport détaillé.

- **Systèmes en production** — [Aethon TUG / Intel RealSense](https://www.intelrealsense.com/autonomous-mobile-robotics/) · [Panasonic HOSPI, certification ISO 13482](https://news.panasonic.com/global/topics/5001) · [Relay Robotics, intégration ascenseur](https://www.therobotreport.com/relay2-delivery-robot-offers-2x-payload-new-elevator-integration/) · [Diligent Moxi](https://www.diligentrobots.com/moxi)
- **Recherche** — [ORB: Operating Room Bot (arXiv 2509.15600, IEEE CASE 2025)](https://arxiv.org/html/2509.15600) · [Edge AI in Practice: Survey and Deployment Framework (MDPI Electronics)](https://www.mdpi.com/2079-9292/14/24/4877)
- **Modèles** — [Ultralytics YOLO26](https://docs.ultralytics.com/models/yolo26) · [YOLO26: NMS-Free End-to-End Framework (arXiv 2601.12882)](https://arxiv.org/pdf/2601.12882) · [RF-DETR (arXiv 2511.09554)](https://arxiv.org/pdf/2511.09554) · [ByteTrack / BoT-SORT — comparatif MOT](https://trackers.roboflow.com/latest/trackers/comparison/)
- **Embarqué** — [Is INT8 Portable? Cross-Platform Study (arXiv 2609.16085)](https://arxiv.org/html/2609.16085) · [YOLO on Raspberry Pi — benchmarks](https://docs.ultralytics.com/guides/raspberry-pi)
- **Normes et briques** — [ISO 3691-4:2020](https://www.iso.org/standard/70660.html) · [Nav2 — Costmap 2D](https://navigation.ros.org/configuration/packages/configuring-costmaps.html)
