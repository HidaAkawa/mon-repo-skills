# `std-dev-project`

**Compatibilité : Claude Code uniquement.** Prérequis : le skill
[`grill-me`](../../shared/grill-me/) et Git. Une CLI de forge est utile
seulement si le projet doit être publié.

Le skill conduit un projet logiciel jusqu'à une version vérifiée et publiable.
Il calibre ses questions sur trois axes indépendants, fournit les décisions
techniques de départ et réserve à l'utilisateur les choix qui changent le
produit, le risque, le coût ou le délai.

Version native Claude Code du
[skill Codex du même nom](../../codex/std-dev-project/) : **cycle, gates,
documents canoniques et état v4 sont identiques**. Seule l'exécution change ;
voir [Ce qui change côté Claude](#ce-qui-change-côté-claude).

## Cycle v4

| Étape | Gate observable | Documents créés ou consolidés |
|---|---|---|
| `initiate-and-frame` | charte approuvée, risques et profil compris | registre documentaire, charte projet |
| `define` | exigences testables, baseline et stratégie cohérentes | SRS, plan de développement |
| `build` | parcours principal, tests et télémétrie exécutables | mise à jour du SRS et du plan |
| `verify` | usage réel, contrôles locaux verts, revue close | rapport de vérification |
| `release-and-improve` | candidat traçable et PR/MR verte ou statut local explicite | record de release |

Une correction reste dans l'étape courante. Une étape antérieure n'est rouverte
que lorsque le problème, le périmètre, le risque ou l'architecture change.

## Ce qui change côté Claude

| | Variante Codex | Ici |
|---|---|---|
| Suivi des étapes | État `.sdp/state.json` seul | Une tâche par étape, en plus de l'état qui reste la source de vérité |
| Cadrage | Interrogation directe | Mode plan tant qu'aucune décision produit n'est arrêtée |
| Reviewer indépendant | `claude-independent-review` | `codex-independent-review` |
| Politique de revue | `.codex/claude-review.json` | `.claude/codex-review.json` |
| `reviews.mode` | `claude` ou `external-prompt` | `codex` ou `external-prompt` |

Ce sont deux variantes distinctes et **assumées comme divergentes** : une
évolution de l'une ne se reporte pas automatiquement sur l'autre.

## Skills composés

| Skill | Étape | Si absent |
|---|---|---|
| [`grill-me`](../../shared/grill-me/) | 1 et 2 | Prérequis dur : le skill s'arrête et demande son installation |
| [`plan-delegate-verify`](../plan-delegate-verify/) | 3 | Construction séquentielle, signalée dans le plan de développement |
| [`codex-independent-review`](../codex-independent-review/) | 2 et 4 | Bascule en `reviews.mode: external-prompt` |

Aucun skill absent n'est simulé et aucun ne bloque le cycle, sauf `grill-me`.

`plan-delegate-verify` ne se déclenche normalement que sur demande explicite
d'orchestration. Son invocation par `std-dev-project` vaut cette demande : à
l'étape 3, c'est le critère de découpe en lots indépendants qui décide, pas une
formulation de l'utilisateur.

## Aide aux profils guidés

`grill-me` commence par trois questions de calibrage sur le développement,
l'exploitation et l'assurance. Le skill ne pose ensuite que des questions
métier à un profil `guided`. Une réponse inconnue devient une hypothèse
`ASM-###` et déclenche une valeur prudente au lieu de bloquer le travail.

Les baselines couvrent les archétypes `web`, `api`, `mobile`, `cli`, `library`,
`batch` et `distributed` aux niveaux `standard`, `elevated` et `critical`. Elles
fournissent directement :

- contrôles de sécurité et de chaîne d'approvisionnement ;
- seuils initiaux de qualité et de performance ;
- traces, logs, métriques et règles d'exclusion de données ;
- tests, preuves, coûts et contraintes à expliquer.

Les valeurs sont des points de départ révisables et non des garanties
universelles. Une réduction exige une dérogation explicite.

## Documents et état

Six gabarits canoniques évitent l'empilement documentaire : registre, charte,
SRS, plan de développement, rapport de vérification et record de release. Les
noms sont ASCII en `kebab-case`, les IDs ne sont jamais réutilisés et les
documents portent leur version, statut, responsables, dates et baseline Git.

L'état vit dans `.sdp/state.json` avec `schema_version: 4`. Un projet v3 est
d'abord analysé sans écriture puis migré explicitement avec :

```text
python3 <skill-dir>/scripts/migrate-v3-to-v4.py --project <racine>
python3 <skill-dir>/scripts/migrate-v3-to-v4.py --project <racine> --apply
python3 <skill-dir>/scripts/migrate-v3-to-v4.py --project <racine> --finalize
```

La migration est atomique et idempotente. Elle conserve `.sdp/etat.json`, les
champs inconnus et les anciens documents, marqués `superseded` seulement après
validation des consolidations. Elle détecte une politique
`.claude/codex-review.json` pour choisir `reviews.mode`.

## Délégation de l'étape `build`

Un lot n'est délégué que si le travail restant se découpe en au moins deux
périmètres d'écriture réellement disjoints. Chaque lot reçoit ses exigences,
ses critères d'acceptation, son périmètre exact et les preuves attendues ; il
lui est interdit de toucher `.sdp/`, les documents canoniques et
`docs/reviews/`.

Aucune décision produit, dérogation, arbitrage de revue ou rédaction de gate
n'est déléguée. Les comptes rendus des sous-agents sont vérifiés sur preuves
avant la gate : une délégation ne réduit ni les contrôles, ni le niveau de
garantie.

## Revues et publication

Une revue finale est obligatoire ; la revue de conception dépend du niveau de
garantie. Les budgets de contre-revues sont `2 / 3 / 4`. Quand
`codex-independent-review` est disponible et déjà activé, il est utilisé dans
une autorisation bornée à la version et au budget. Sinon le skill produit une
mission neutre à copier dans un autre agent et attend son rapport.

Le reviewer doit rester un modèle **distinct** de l'agent principal :
`plan-delegate-verify` n'est jamais un substitut à ce jalon.

Une revue Codex n'est bornée que par son délai configuré ; le CLI Codex n'expose
aucun plafond de tours.

Les artefacts bruts restent dans `docs/reviews/`, automatiquement ignorés par
Git. Le rapport de vérification conserve seulement les IDs, décisions,
résultats et empreintes SHA-256.

Si une forge est configurée, les contrôles CI sont définis puis implémentés
selon la stack. Le push n'arrive que dans `release-and-improve`. Les itérations
successives actualisent la même branche et la même PR/MR jusqu'à sa fusion
manuelle. Le skill ne fusionne jamais à la place de l'utilisateur.

## Installation

Voir l'[installation générale](../../../README.md#installation). Ce skill se
copie dans `~/.claude/skills/std-dev-project/`.

## Vérifier le skill

Depuis la racine de ce dépôt :

```text
python3 skills/claude/std-dev-project/scripts/test_migrate_v3_to_v4.py
python3 skills/claude/std-dev-project/scripts/test_skill_contract.py
```

Les détails opérationnels restent dans les références chargées à la demande
par `SKILL.md`.
