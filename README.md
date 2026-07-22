# Skills pour agents IA

Skills réutilisables pour **Claude Code** et **Codex**, au format `SKILL.md`
commun aux deux plateformes.

Le dépôt est organisé par compatibilité : un skill vit dans `shared/` s'il
fonctionne des deux côtés, dans `codex/` ou `claude/` s'il dépend de fonctions
propres à une plateforme.

## Catalogue

| Skill | Rôle | Claude | Codex |
|---|---|:---:|:---:|
| [`grill-me`](skills/shared/grill-me/) | Interroge sans relâche sur un plan ou une conception jusqu'à compréhension partagée | ✓ | ✓ |
| [`std-dev-project`](skills/shared/std-dev-project/) | Conduit un projet de développement selon un cycle en sept étapes imposées, documenté et versionné | ✓ | ✓ |
| [`claude-independent-review`](skills/codex/claude-independent-review/) | Fait intervenir Claude comme reviewer indépendant en lecture seule, Codex gardant l'arbitrage | — | ✓ |
| [`plan-delegate-verify`](skills/codex/plan-delegate-verify/) | Planifie des lots indépendants, les délègue à des sous-agents calibrés et vérifie chaque résultat sur preuves | — | ✓ |
| [`plan-delegate-verify`](skills/claude/plan-delegate-verify/) | Version native Claude Code du précédent : mêmes lots, délégation et vérification, portés sur l'outil Agent | ✓ | — |

## Installation

Les skills sont de simples répertoires : les installer consiste à les copier au
bon endroit, puis à ouvrir une nouvelle session pour qu'ils soient découverts.

### Prérequis

- [Claude Code](https://code.claude.com/docs/en/setup) ou
  [Codex](https://developers.openai.com/codex/), selon la plateforme visée ;
- Git ;
- certains skills ont des prérequis supplémentaires, indiqués dans leur README.

Les identifiants ne sont jamais inclus dans ce dépôt. S'authentifier séparément
sur chaque machine.

### macOS, Linux, WSL2

```bash
git clone https://github.com/HidaAkawa/mon-repo-skills
cd mon-repo-skills

# Pour Codex : les skills Codex et les skills communs
mkdir -p ~/.codex/skills
cp -R skills/codex/* skills/shared/* ~/.codex/skills/

# Pour Claude Code : les skills Claude et les skills communs
mkdir -p ~/.claude/skills
cp -R skills/claude/* skills/shared/* ~/.claude/skills/
```

### Windows PowerShell

```powershell
git clone https://github.com/HidaAkawa/mon-repo-skills
cd mon-repo-skills

$codex = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $codex | Out-Null
Copy-Item -Recurse -Force ".\skills\codex\*", ".\skills\shared\*" $codex

$claude = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path $claude | Out-Null
Copy-Item -Recurse -Force ".\skills\claude\*", ".\skills\shared\*" $claude
```

Chaque skill doit finalement se trouver sous
`~/.codex/skills/<nom>/SKILL.md` ou `~/.claude/skills/<nom>/SKILL.md`.

Ouvrir ensuite une **nouvelle session** pour que les skills soient découverts.

### Mise à jour

```bash
git pull
```

Puis recopier les répertoires. Sauvegarder d'abord toute version locale
modifiée : la copie écrase sans prévenir.

## Structure du dépôt

```text
skills/
├── shared/     skills fonctionnant sur Claude Code et Codex
│   ├── grill-me/
│   └── std-dev-project/
├── codex/      skills dépendant de fonctions propres à Codex
│   ├── claude-independent-review/
│   └── plan-delegate-verify/
└── claude/     skills dépendant de fonctions propres à Claude Code
    └── plan-delegate-verify/
```

Le répertoire `claude/` regroupe les skills qui dépendent de fonctions propres à
Claude Code (outil Agent, suivi de tâches).

La compatibilité est aussi déclarée dans le README de chaque skill, qui fait
foi : si un skill change de catégorie, son répertoire suit, mais sa
documentation reste la source de vérité.

## Licence

[MIT](LICENSE). Ce dépôt redistribue du code tiers sous la même licence — voir
[NOTICE.md](NOTICE.md) pour les attributions.
