# PRI 2026-2027 — Projet 2 : IA embarquée pour la perception des véhicules autonomes en logistique hospitalière

**Encadrement :** Moïse DJOKO-KOUAM
**Mots clés :** Intelligence artificielle, Perception, Fusion, Suivi, Embarqué

## Problématique

> Comment concevoir une IA de perception performante, frugale et apte au déploiement embarqué ?

Transformer des informations de perception hétérogènes de l'environnement en une
représentation structurée et exploitable de l'environnement du véhicule autonome (VA),
exécutable localement sur **Raspberry Pi 5**.

## État du dépôt

| Document | Contenu | Livrable PRI couvert |
|---|---|---|
| [`docs/00-cadrage-projet.md`](docs/00-cadrage-projet.md) | Synthèse du cahier des charges, analyse des besoins et contraintes, décomposition fonctionnelle, budget temps réel | *Analyser les besoins et les contraintes* |
| [`docs/01-etat-de-l-art-et-comparaison-modeles.md`](docs/01-etat-de-l-art-et-comparaison-modeles.md) | État de l'art par brique fonctionnelle, tableaux comparatifs COCO et Raspberry Pi 5, grille multicritère pondérée, recommandation argumentée | *État de l'art et comparaison des modèles* + *Choix argumenté du modèle* |
| [`docs/02-etat-des-lieux-et-justification-des-choix.md`](docs/02-etat-des-lieux-et-justification-des-choix.md) | État des lieux des projets existants (industriels, recherche, prototypes bas coût), technologies employées, enseignements transversaux, entonnoir de décision et traçabilité des choix | *État de l'art* + *Choix argumenté du modèle* |
| [`docs/03-synthese.md`](docs/03-synthese.md) | Note de synthèse : l'essentiel des trois documents en 6 pages, pour présentation à l'encadrant | — |

## PDF

Deux documents sont générés à partir des Markdown de `docs/` :

| Fichier | Profil | Pages | Usage |
|---|---|---|---|
| [`build/PRI_IA_Perception_Synthese.pdf`](build/PRI_IA_Perception_Synthese.pdf) | `synthese` | 6 | Présentation à l'encadrant, réunion de suivi |
| [`build/PRI_IA_Perception_Rapport.pdf`](build/PRI_IA_Perception_Rapport.pdf) | `rapport` | 39 | Dossier complet, annexe du rapport final |

```bash
pip install markdown playwright pypdfium2
python3 tools/build_pdf.py                     # les deux
python3 tools/build_pdf.py --profile synthese  # la note seule
```

Le rendu passe par Chromium. Si le binaire n'est pas à l'emplacement par défaut,
le préciser avec `CHROMIUM_PATH=/chemin/vers/chrome`.

## Feuille de route (livrables restants)

- [x] État de l'art et comparaison des modèles
- [ ] Choix argumenté du modèle (à valider par mesures réelles sur RPi 5)
- [ ] Jeu de données et protocole de préparation
- [ ] Modèle entraîné et optimisé
- [ ] Implémentation embarquée
- [ ] Protocole et résultats expérimentaux
- [ ] Rapport final + démonstration
