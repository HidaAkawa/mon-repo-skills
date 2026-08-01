# `std-dev-project`

**Compatibilité : Claude Code et Codex.** Prérequis : le skill
[`grill-me`](../grill-me/), `git`, et `gh` pour les écritures GitHub.

Conduit un projet de développement selon un cycle en sept étapes imposées. Le
skill adapte les questions au niveau de l'utilisateur, le niveau de garantie
requis aux risques du produit et les artefacts à sa complexité technique.

Le but reste de livrer un produit : la documentation n'existe que pour aider à
construire, vérifier, diagnostiquer, exploiter ou faire évoluer.

## Le cycle

| # | Étape | Sortie principale |
|---|---|---|
| 0 | Calibration | profil, dépôt, état v3 |
| 0-bis | Archéologie | brouillons en lecture seule |
| 1 | Objectif | `docs/objectif.md` |
| 2 | Non-fonctionnel | niveau de garantie requis, architecture, tests, observabilité |
| 3 | Fonctionnel | comportements, tests et signaux diagnostiques |
| 4 | Développement | produit, tests et trace réelle |
| 5 | Tests et feedback | recette et exercice de troubleshooting |
| 6 | Backlog | issues priorisées, roadmap si utile |
| 7 | Itération | manifeste de release et décisions à rouvrir |

## Trois axes indépendants

- **Profil utilisateur** : règle vocabulaire et questions.
- **Niveau de garantie requis** : `essentiel`, `renforce` ou `critique`, selon
  les conséquences d'une erreur.
- **Complexité** : déclenche tracing distribué, contrats, modèles et diagrammes.

Un utilisateur débutant n'abaisse jamais la qualité d'un projet critique :
l'agent prend les décisions techniques, les explique simplement et les
documente.

## Observabilité

Toute unité d'exécution significative est tracée de bout en bout avec
OpenTelemetry. Les logs portent les identifiants de corrélation. Un projet
simple exporte localement ; un projet distribué propage W3C Trace Context ; un
projet critique ajoute métriques, SLO, alertes, audit et runbooks.

Le niveau applicatif se règle par la variable conventionnelle de la stack ou :

```text
APP_LOG_LEVEL=trace|debug|info|warn|error|fatal
```

`OTEL_LOG_LEVEL` reste réservé aux diagnostics internes du SDK OpenTelemetry.

## Documentation

Les documents cœur sont canoniques et versionnés par Git :

```text
docs/index.md
docs/objectif.md
docs/spec-nf.md
docs/spec-fonctionnelle.md
docs/feedback.md
```

Architecture, ADR, stratégie et rapport de tests, modèle de menace, traçabilité
et runbooks ne sont créés que lorsqu'ils apportent une preuve ou une aide
opérationnelle réelle. Aucun dossier documentaire vide n'est créé.

Les projets utilisant l'ancien schéma migrent sans recommencer le cycle. En v2,
le champ `assurance` devient `garantie_requise` sans changer son contenu. Les
documents `*-vN.md` restent historiques ; les documents canoniques apparaissent
progressivement lorsque leur phase est touchée.

## Utilisation

```text
Guide-moi pour construire <projet>
```

L'état vit dans `.sdp/etat.json` et permet de reprendre sur plusieurs sessions.
