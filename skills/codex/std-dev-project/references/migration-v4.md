# Migration v3 vers v4

Migrer sans recommencer le cycle et sans supprimer un document historique.
Résoudre `<skill-dir>` depuis `SKILL.md`, puis utiliser le runner adapté à la
plateforme (`python3` ou `py -3`).

## Correspondance

| Phase v3 | Étape v4 |
|---|---|
| `0`, `0-bis` (alias historique `0.5`), `1` | `initiate-and-frame` |
| `2`, `3` | `define` |
| `4` | `build` |
| `5` | `verify` |
| `6`, `7` | `release-and-improve` |

Mapper `non/assiste/oui`, `debutant/notion/confirme` et
`faible/moyenne/forte` vers `guided/collaborative/autonomous`. Mapper
`essentiel/renforce/critique` vers `standard/elevated/critical`.
Mapper les anciens `HYP-###` sur de nouveaux `ASM-###` et les anciennes
dérogations sur `DRG-###`, en conservant `legacy_id` et toutes les clés métier
d'origine dans l'objet normalisé.

## Procédure

1. Vérifier que le projet est sauvegardé et inventorier les modifications Git.
2. Analyser sans écrire :

   `python3 <skill-dir>/scripts/migrate-v3-to-v4.py --project <racine>`

3. Présenter le mapping, les inconnues, les documents sources et les fichiers
   qui seraient écrits.
4. Après validation, appliquer :

   `python3 <skill-dir>/scripts/migrate-v3-to-v4.py --project <racine> --apply`

5. Consolider sémantiquement les documents ; le script ne réécrit jamais seul
   leur contenu métier.
6. Faire contrôler et committer localement les nouveaux documents afin que
   leur baseline Git soit vérifiable, puis finaliser :

   `python3 <skill-dir>/scripts/migrate-v3-to-v4.py --project <racine> --finalize`

Le mode `--apply` écrit atomiquement `.sdp/state.json`, ajoute la règle
`/docs/reviews/` et conserve `.sdp/etat.json`. Le mode `--finalize` vérifie les
documents attendus pour l'étape, marque les sources comme `superseded` dans
l'état et termine la migration. Aucun mode ne supprime ou déplace un ancien
fichier.

## Consolidation documentaire

| Sources v3 | Cible v4 |
|---|---|
| objectif et brouillon d'objectif | `project-charter.md` |
| spécifications fonctionnelle et non fonctionnelle | `software-requirements-specification.md` |
| architecture, observabilité, tests, menace, ADR | `software-development-plan.md` et annexes utiles |
| journal, feedback, rapports et validation d'observabilité | `verification/<version>.md` |
| manifeste de release et backlog | `releases/<version>.md` et issues ; si le chemin de release est déjà canonique, consolider en place sans le marquer `superseded` |

Conserver dans `migration.legacy_documents` le chemin, le SHA-256, la cible et
le statut. Inventorier aussi `BACKLOG.md`, `DETTE.md`, la traçabilité, les ADR,
les runbooks et les releases existantes. Les ADR et runbooks restent des
annexes `validated-retained`. Une release déjà au chemin canonique reste un
record historique inchangé ; créer le record de la nouvelle version au lieu de
la réécrire. Les fichiers ne peuvent être retirés qu'après une confirmation
distincte.

Si `state.json` v4 existe déjà, l'analyse et l'application sont idempotentes.
Refuser tout schéma inconnu, état JSON malformé ou conflit entre un état v4 et
un état v3 divergent.
