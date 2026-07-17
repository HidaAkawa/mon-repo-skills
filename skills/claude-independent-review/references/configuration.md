# Contrat de configuration du projet

## Table des matières

- [Emplacement et cycle de vie](#emplacement-et-cycle-de-vie)
- [Schéma version 1](#schéma-version-1)
- [Jalons](#jalons)
- [Règles de chemins](#règles-de-chemins)
- [Artefacts persistants](#artefacts-persistants)

## Emplacement et cycle de vie

Conserver la politique dans `.codex/claude-review.json`. La faire valider par `<skill-dir>/scripts/claude_review.py validate-config`. Toute évolution doit être présentée à l'utilisateur avant `install-policy --replace`.

Le runner accepte uniquement `schema_version: 1`. Un numéro futur ou inconnu est refusé sans migration implicite. Le sous-programme `migrate-config` peut convertir explicitement un brouillon version 0 en ajoutant les valeurs désormais obligatoires `max_turns`, `max_files` et `max_bytes`; il écrit toujours un nouveau fichier et ne remplace jamais l'original.

## Schéma version 1

```json
{
  "schema_version": 1,
  "project": {
    "name": "Mon projet",
    "language": "fr"
  },
  "claude": {
    "model": "claude-sonnet-5",
    "effort": "high",
    "timeout_minutes": 20,
    "max_turns": 40
  },
  "reports": {
    "directory": "docs/reviews"
  },
  "context_files": [
    "AGENTS.md",
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

`reports.directory`, les sources de vérité et les chemins de focalisation doivent rester relatifs à la racine, sans `..`.

## Jalons

Écrire chaque condition comme un état observable par Codex. Le jalon autorise une revue initiale après annonce, jamais une contre-revue. Combiner les jalons compatibles portant sur le même snapshot.

`focus_paths` cadre la mission mais ne réduit pas le snapshot normal. Après dépassement des seuils, utiliser des motifs `--include` validés ponctuellement par l'utilisateur. `git_baseline` indique la référence comparée au worktree ; utiliser `HEAD` par défaut et `null` hors Git.

## Règles de chemins

Les motifs suivent les globs avec `/` comme séparateur. Un nom de répertoire simple exclut ce répertoire à toute profondeur.

Les exclusions dures ne sont jamais réactivables : véritables fichiers `.env`, clés privées, magasins d'identifiants et secrets usuels. `.env.example`, `.env.sample` et `.env.template` restent autorisés.

En mode sans Git, le runner écarte également les gestionnaires de version, dépendances installées, caches, builds et anciens rapports. En mode Git, les fichiers ignorés sont absents sauf s'ils sont suivis ; les anciens rapports et `.codex` restent exclus.

Les liens symboliques vers l'extérieur sont consignés mais non copiés. Les liens internes vers un fichier sont matérialisés. Les liens internes vers un dossier sont consignés mais non développés.

## Artefacts persistants

Après succès seulement :

- `docs/reviews/<horodatage>-<jalon>-claude.md` ;
- `docs/reviews/evidence/<même-identifiant>/manifest.json` ;
- `docs/reviews/evidence/<même-identifiant>/diff.patch` en mode Git si le diff n'est pas vide.

Le rapport contient la mission exacte, les métadonnées et la réponse Claude intacte. Aucun snapshot, prompt séparé, stderr, session, cache ou artefact de tentative échouée ne doit subsister.
