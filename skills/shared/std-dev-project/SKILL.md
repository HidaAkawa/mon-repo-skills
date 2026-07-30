---
name: std-dev-project
description: Conduire un projet de développement de bout en bout selon un cycle imposé en sept étapes, avec interrogations adaptées au niveau de l'utilisateur, documentation proportionnée à la criticité, tests et observabilité OpenTelemetry de bout en bout. À utiliser pour démarrer, reconstruire ou reprendre un projet structuré, notamment lorsqu'un fichier .sdp/etat.json existe. Use when starting, rebuilding, or structuring a software project end to end.
---

# std-dev-project

Conduire un projet selon un cycle en sept étapes dont **l'ordre est imposé**.
Livrer un produit utilisable reste le but : ne produire un écrit que s'il aide
à construire, vérifier, diagnostiquer, exploiter ou faire évoluer le produit.

Ce skill s'exécute indifféremment sur plusieurs agents. Ne jamais nommer un
modèle ni un produit dans les échanges avec l'utilisateur : dire « l'agent ».

Résoudre `<skill-dir>` comme le dossier absolu contenant ce `SKILL.md`.

## Les trois axes

Ne jamais les confondre :

- le **profil de l'utilisateur** règle le vocabulaire et ce qu'on lui demande ;
- le **niveau d'assurance** règle les preuves et la profondeur documentaire ;
- la **complexité technique** règle les artefacts spécialisés et le tracing.

Un utilisateur débutant peut porter un produit critique : l'agent prend alors
les décisions techniques et les documente au lieu de réduire l'exigence.

## Se situer

1. Chercher `.sdp/etat.json` à la racine du projet courant.
2. **Absent** → le projet n'est pas encore sous méthode : aller en phase 0.
3. **Présent sans `schema_version: 2`** → lire
   [references/0-assurance.md](references/0-assurance.md), migrer sans
   recommencer le cycle, puis reprendre la phase en cours.
4. **Présent en v2** → annoncer la phase, l'itération, le niveau d'assurance et
   les éventuelles dérogations avant d'agir.

Toujours lire [references/0-methode.md](references/0-methode.md) avant d'agir :
il porte les règles transverses. Charger ensuite **uniquement** :

- le fichier de la phase courante ;
- [references/0-assurance.md](references/0-assurance.md) pour une migration ou
  les phases 2, 6 et 7 ;
- [references/0-observabilite.md](references/0-observabilite.md) pour les
  phases 2 à 5 ou toute demande de diagnostic.

## Routage des phases

| Phase | Fichier à charger |
|---|---|
| 0 — Calibration et amorçage | [references/0-calibration.md](references/0-calibration.md) |
| 0-bis — Archéologie *(projet existant)* | [references/0bis-archeologie.md](references/0bis-archeologie.md) |
| 1 — Objectif macro | [references/1-objectif.md](references/1-objectif.md) |
| 2 — Spécification non-fonctionnelle | [references/2-spec-non-fonctionnelle.md](references/2-spec-non-fonctionnelle.md) |
| 3 — Spécification fonctionnelle | [references/3-spec-fonctionnelle.md](references/3-spec-fonctionnelle.md) |
| 4 — Développement | [references/4-developpement.md](references/4-developpement.md) |
| 5 — Tests et feedback | [references/5-tests-feedback.md](references/5-tests-feedback.md) |
| 6 — Backlog | [references/6-backlog.md](references/6-backlog.md) |
| 7 — Itération | [references/7-iteration.md](references/7-iteration.md) |

## Invariants

Ces règles ne souffrent aucune exception, quelle que soit la phase.

- **L'ordre des phases est imposé.** Toute demande de saut déclenche la procédure
  de dérogation de `0-methode.md`. Ne jamais céder sans elle.
- **Chaque phase laisse une preuve utile**, proportionnée au niveau d'assurance,
  relue par la bonne partie prenante et commitée.
- **Ne jamais noyer l'utilisateur.** Chercher les faits, poser seulement les
  questions qui changent le produit, son risque ou son coût, et trancher le
  reste en explicitant les hypothèses.
- **Le tracing de bout en bout est obligatoire.** Sa profondeur et son
  infrastructure restent proportionnées à la complexité et à la criticité.
- **Ne jamais pousser sans confirmation explicite** de l'utilisateur, à chaque
  fois. Committer localement est en revanche automatique.
- **Ne jamais interroger nu.** Toute phase marquée « interrogation » invoque le
  skill `grill-me` avec un bloc de cadrage construit selon `0-methode.md`.
- **Ne jamais poser une question hors de portée de l'utilisateur.** La trancher,
   l'annoncer comme tranchée, et expliquer pourquoi en langage clair.
- **Ne jamais écrire dans un projet préexistant** ouvert comme source
  documentaire. Il est en lecture seule, sans exception.
