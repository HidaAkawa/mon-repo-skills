# Contrat de configuration du projet

## Table des matières

- [Emplacement et cycle de vie](#emplacement-et-cycle-de-vie)
- [Désactivation](#désactivation)
- [Choix du modèle Codex](#choix-du-modèle-codex)
- [Schéma version 1](#schéma-version-1)
- [Jalons](#jalons)
- [Règles de chemins](#règles-de-chemins)
- [Verrous d'exécution](#verrous-dexécution)
- [Artefacts persistants](#artefacts-persistants)

## Emplacement et cycle de vie

Conserver la politique dans `.claude/codex-review.json`. La faire valider par `<skill-dir>/scripts/codex_review.py validate-config`. Toute évolution doit être présentée à l'utilisateur avant `install-policy --replace`. L'installation ajoute idempotemment `/docs/reviews/` et, s'il diffère, le répertoire `reports.directory` au `.gitignore`. Elle signale sans les désindexer les audits déjà suivis dans l'un ou l'autre chemin.

Le runner accepte uniquement `schema_version: 1`. Un numéro futur ou inconnu est refusé sans migration implicite. Le sous-programme `migrate-config` peut convertir explicitement un brouillon version 0 en ajoutant les valeurs désormais obligatoires `timeout_minutes`, `max_files` et `max_bytes`, et en retirant un éventuel `max_turns` hérité du miroir Claude ; il écrit toujours un nouveau fichier et ne remplace jamais l'original.

## Désactivation

`disable-policy --project <racine>` retire uniquement `.claude/codex-review.json` et le bloc délimité géré par le skill dans `CLAUDE.md`. La commande ne parcourt pas le répertoire `reports.directory`, ne supprime ni rapports, ni résolutions, ni preuves et conserve la règle `/docs/reviews/` dans `.gitignore`. Elle est idempotente et restaure la politique et `CLAUDE.md` si une opération échoue.

Après désactivation, les audits restent des artefacts autonomes du projet. Une réactivation installe une nouvelle politique selon le parcours normal sans écraser ces fichiers.

## Choix du modèle Codex

Pour un projet sans politique, faire choisir une seule fois un modèle avant de proposer le reste de la configuration. Enregistrer l'identifiant exact choisi dans `codex.model`. Ne pas reposer la question lors des revues suivantes.

Avant le choix, exécuter `python3 <skill-dir>/scripts/codex_review.py discover-models`. La commande **ne fait aucune requête réseau** : Codex s'authentifie par sa propre CLI et n'expose pas de clé exploitable par ce runner. Elle lit le catalogue que Codex maintient lui-même dans `$CODEX_HOME/models_cache.json`, ou `~/.codex/models_cache.json` à défaut, et n'en retient que les modèles marqués `visibility: list`. Sans cache lisible, elle revient au catalogue embarqué et l'indique dans `source`, `status` et `warnings`. Utiliser `--offline` pour ignorer le cache.

Sur un poste où Codex n'a jamais tourné, le cache est absent : le repli embarqué est alors normal, et l'utilisateur peut toujours saisir un identifiant exact visible dans son propre sélecteur de modèle.

Catalogue embarqué versionné au 2026-08-08 :

| Choix | Identifiant exact | Profil |
|---:|---|---|
| 1 | `gpt-5.6-terra` | Équilibre capacité, rapidité et coût ; choix recommandé. |
| 2 | `gpt-5.6-sol` | Revue approfondie de code complexe, avec un coût et une latence supérieurs. |
| 3 | `gpt-5.6-luna` | Rapidité et coût réduit, pour une revue moins exigeante. |
| 4 | `gpt-5.5` | Génération précédente pour le code complexe et la recherche. |
| 5 | `gpt-5.4` | Génération précédente, pour les environnements qui la prennent encore en charge. |
| 6 | `gpt-5.4-mini` | Petit modèle rapide, pour une revue de faible enjeu. |
| 7 | Identifiant fourni par l'utilisateur | Accepter un autre identifiant exact pris en charge par son environnement. |

Lorsque la lecture du cache réussit, sa liste est prioritaire sur le catalogue embarqué car elle reflète les modèles réellement proposés par l'installation Codex présente. Conserver la saisie libre et faire confirmer le choix par l'utilisateur.

Ne pas transformer un choix en alias mouvant comme `default`, `best`, `codex`, `gpt`, `gpt-5`, `gpt-5.6`, `sol`, `terra`, `luna`, `mini` ou `spark` : ces valeurs peuvent changer de cible. Pour une politique existante, traiter un changement de modèle comme toute autre modification sensible : présenter la différence, obtenir l'accord, puis exécuter `install-policy --replace`.

## Schéma version 1

```json
{
  "schema_version": 1,
  "project": {
    "name": "Mon projet",
    "language": "fr"
  },
  "codex": {
    "model": "gpt-5.6-terra",
    "effort": "high",
    "timeout_minutes": 20
  },
  "reports": {
    "directory": "docs/reviews"
  },
  "context_files": [
    "CLAUDE.md",
    "docs/specification.md"
  ],
  "snapshot": {
    "max_files": 20000,
    "max_bytes": 262144000,
    "extra_excludes": []
  },
  "milestones": [
    {
      "id": "lot-ready",
      "condition": "Un lot cohérent est terminé et vérifié avant livraison.",
      "review_types": ["code"],
      "focus_paths": ["src/**", "tests/**"],
      "git_baseline": "HEAD"
    }
  ]
}
```

Valeurs de `review_types` : `code`, `architecture`, `security`, `design`, `content`, `general`.

Valeurs d'effort : `low`, `medium`, `high`, `xhigh`, `max`.

Il n'existe pas de plafond de tours. Le CLI Codex n'expose aucune option équivalente et la demande correspondante a été fermée en « not planned » en amont ; `timeout_minutes` est donc la **seule** borne dure d'une revue. Le nombre de tours observé est rapporté à titre indicatif dans `codex_usage.turns_observed`.

`reports.directory`, les sources de vérité et les chemins de focalisation doivent rester relatifs à la racine, sans `..`.

## Jalons

Écrire chaque condition comme un état observable par l'agent principal. Le jalon autorise une revue initiale après annonce, jamais à lui seul une contre-revue. Une contre-revue autonome exige `--confirm-counter-review` après confirmation explicite. `--sdp-authorized` remplace cette attestation seulement si `.sdp/state.json` v4 autorise le même jalon et la même version avec un budget `2 / 3 / 4` encore disponible, et si `reviews.mode` vaut `codex`. Combiner les jalons compatibles portant sur le même snapshot.

`focus_paths` cadre la mission mais ne réduit pas le snapshot normal. Après dépassement des seuils, utiliser des motifs `--include` validés ponctuellement par l'utilisateur. `git_baseline` indique la référence comparée au worktree ; utiliser `HEAD` par défaut et `null` hors Git.

## Règles de chemins

Les motifs suivent les globs avec `/` comme séparateur. Un nom de répertoire simple exclut ce répertoire à toute profondeur.

Les exclusions dures ne sont jamais réactivables : véritables fichiers `.env`, clés privées, magasins d'identifiants et secrets usuels, y compris les fichiers `auth.json`. `.env.example`, `.env.sample` et `.env.template` restent autorisés.

Le bac à sable `read-only` de Codex empêche toute écriture, mais **pas** la lecture. C'est donc le filtrage du snapshot, et lui seul, qui protège les secrets d'un projet : ne jamais présenter le bac à sable comme un substitut à ces exclusions.

En mode sans Git, le runner écarte également les gestionnaires de version, dépendances installées, caches, builds et anciens rapports. En mode Git, les fichiers ignorés sont absents sauf s'ils sont suivis ; les anciens rapports et `.claude` restent exclus.

Les liens symboliques vers l'extérieur sont consignés mais non copiés. Les liens internes vers un fichier sont matérialisés. Les liens internes vers un dossier sont consignés mais non développés.

## Verrous d'exécution

Chaque revue lance `codex exec` avec, sans exception :

| Verrou | Effet |
|---|---|
| `--sandbox read-only` | Bac à sable système ; aucune écriture possible |
| `--ephemeral` | Aucune session persistée sur disque |
| `--ignore-user-config` | Le `config.toml` de l'utilisateur, ses plugins et ses serveurs MCP ne sont pas chargés ; l'authentification reste disponible |
| `--ignore-rules` | Les fichiers `.rules` d'execpolicy ne sont pas chargés |
| `--strict-config` | Toute clé de configuration non reconnue échoue au lieu d'être ignorée |
| `--skip-git-repo-check` | Le snapshot n'est pas un dépôt Git |
| `--cd <snapshot>` | La racine de travail est le snapshot, jamais le projet |
| `--output-last-message` | Le rapport est écrit dans un fichier, hors du flux d'événements |
| `-c approval_policy="never"` | Aucune demande d'approbation interactive |
| `-c sandbox_mode="read-only"` | Redondance explicite avec `--sandbox` |
| `-c web_search="disabled"` | Aucun accès web |

Le runner refuse de démarrer si l'un des drapeaux de contournement `--dangerously-bypass-approvals-and-sandbox` ou `--dangerously-bypass-hook-trust` apparaît dans la commande construite.

Le rapport provient du fichier `--output-last-message`, jamais du flux `--json`. Ce découplage est délibéré : le format d'événements d'une CLI en alpha n'est pas un contrat, et il ne sert donc qu'à alimenter la progression. Un événement illisible est compté dans `codex_usage.unparsed_events` sans faire échouer la revue.

## Artefacts persistants

Après succès seulement, sous le `reports.directory` configuré
(`docs/reviews` par défaut) :

- `<reports.directory>/<horodatage>-<jalon>-codex.md` ;
- `<reports.directory>/evidence/<même-identifiant>/manifest.json` ;
- `<reports.directory>/evidence/<même-identifiant>/diff.patch` en mode Git si le diff n'est pas vide.

Le rapport contient la mission exacte, les métadonnées et la réponse Codex intacte. La progression `--progress` reste uniquement dans le terminal. Aucun snapshot, prompt séparé, stderr, session, cache, journal de progression ou artefact de tentative échouée ne doit subsister.

Tous ces chemins restent sous `reports.directory` et ne doivent pas entrer
dans Git. `/docs/reviews/` reste également ignoré. L'index Git existant n'est
jamais modifié automatiquement.
