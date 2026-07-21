# `std-dev-project`

**Compatibilité : Claude Code et Codex.** Prérequis : le skill
[`grill-me`](../grill-me/) installé à côté, `git`, et `gh` pour les phases qui
touchent au dépôt distant.

Conduit un projet de développement de bout en bout selon un cycle en sept étapes
dont **l'ordre est imposé**. Chaque étape est interrogée, documentée, commitée,
et poussée après confirmation.

La valeur du skill n'est pas d'aider à coder — un agent sait déjà le faire. Elle
est de **rendre impossible le saut d'étape silencieux**.

## Le cycle

| # | Étape | Interrogation | Sortie |
|---|---|:---:|---|
| 0 | Calibration et amorçage | — | profil, répertoire, dépôt |
| 0-bis | Archéologie *(projet existant)* | — | brouillons |
| 1 | Objectif macro | ✓ | `docs/objectif-vN.md` |
| 2 | Spécification non-fonctionnelle | ✓ | `docs/spec-nf-vN.md` |
| 3 | Spécification fonctionnelle | ✓ | `docs/spec-fonctionnelle-vN.md` + cas de test |
| 4 | Développement | — | code + suite de tests verte |
| 5 | Tests et feedback | ✓ | `docs/feedback-vN.md` |
| 6 | Backlog | — | GitHub Issues |
| 7 | Itération | — | retour à l'étape 2 |

## Utilisation

```text
Guide-moi pour construire <ton projet>
```

Le skill reprend automatiquement là où il s'était arrêté : l'état vit dans
`.sdp/etat.json`, versionné dans le dépôt du projet guidé. Le cycle s'étale sur
plusieurs sessions sans rien perdre.

## Ce qui le distingue

**Il s'adapte au niveau réel de l'utilisateur.** Trois questions en phase 0
établissent un profil, figé une fois pour toutes. Une décision hors de portée
n'est pas posée : elle est tranchée, annoncée comme telle, et justifiée en
langage clair. Un utilisateur noyé sous des questions d'architecture abandonne
la méthode — c'est le principal risque d'échec, et le cadrage existe pour lui.

**Il refuse les raccourcis, sans être un mur.** Sauter une étape est possible,
mais laisse une trace dans `DETTE.md`, rappelée à chaque phase suivante et
inscrite d'office au backlog.

**Il a une gate que personne ne peut assouplir.** Le niveau d'exigence en tests
est décidé en phase 2 comme une question métier — argent, données personnelles,
tiers dépendants. Les cas de test se dérivent mécaniquement de la phase 3. Et la
suite doit passer pour sortir de la phase 4. Toutes les autres portes du cycle
reposent sur un jugement ; celle-là est vérifiable par machine.

**Il sait repartir d'un projet existant** sans y toucher. Le projet source est
ouvert en lecture seule et sert de source documentaire pour reconstituer objectif
et spécifications ; le nouveau projet se construit dans un répertoire et un dépôt
séparés, par réécriture intégrale. Aucun risque pour un projet professionnel.

## Structure

```text
std-dev-project/
├── SKILL.md            orchestrateur : détecte la phase, charge la référence
├── references/         une par phase, chargée à la demande
│   ├── 0-methode.md    cadrage des interrogations, gates, dérogations, Git
│   └── …
└── templates/          gabarits des documents produits
```
