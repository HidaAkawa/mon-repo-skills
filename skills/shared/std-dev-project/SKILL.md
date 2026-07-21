---
name: std-dev-project
description: Conduire un projet de développement de bout en bout selon un cycle imposé en sept étapes — objectif macro, spécification non-fonctionnelle, spécification fonctionnelle, développement, tests et feedback, backlog, itération — chaque étape étant interrogée, documentée, commitée et poussée. À utiliser quand l'utilisateur veut démarrer un nouveau projet, reprendre proprement un projet existant, être guidé dans un cycle de développement structuré, ou quand un fichier .sdp/etat.json existe dans le projet courant. Use when starting or structuring a software project end to end.
---

# std-dev-project

Conduire un projet de développement selon un cycle en sept étapes dont **l'ordre
est imposé**. La valeur de ce skill n'est pas d'aider à coder : c'est de rendre
impossible le saut d'étape silencieux. Ne jamais le contourner par complaisance.

Ce skill s'exécute indifféremment sur plusieurs agents. Ne jamais nommer un
modèle ni un produit dans les échanges avec l'utilisateur : dire « l'agent ».

Résoudre `<skill-dir>` comme le dossier absolu contenant ce `SKILL.md`.

## Se situer

1. Chercher `.sdp/etat.json` à la racine du projet courant.
2. **Absent** → le projet n'est pas encore sous méthode : aller en phase 0.
3. **Présent** → le lire. Il donne la phase courante, l'itération, le profil de
   l'utilisateur et les décisions déjà verrouillées. Annoncer à l'utilisateur où
   il en est avant toute chose.

Toujours lire [references/0-methode.md](references/0-methode.md) avant d'agir :
il porte les règles transverses (cadrage des interrogations, gates, dérogations,
protocole Git). Charger ensuite **uniquement** le fichier de la phase courante.

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
- **Aucune phase ne se termine sans écrit.** Un document validé, commité.
- **Ne jamais pousser sans confirmation explicite** de l'utilisateur, à chaque
  fois. Committer localement est en revanche automatique.
- **Ne jamais interroger nu.** Toute phase marquée « interrogation » invoque le
  skill `grill-me` avec un bloc de cadrage construit selon `0-methode.md`.
- **Ne jamais poser une question hors de portée de l'utilisateur.** La trancher,
  l'annoncer comme tranchée, et expliquer pourquoi en langage clair.
- **Ne jamais écrire dans un projet préexistant** ouvert comme source
  documentaire. Il est en lecture seule, sans exception.
