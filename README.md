# Mes skills Codex

Ce dépôt contient des skills personnels réutilisables avec Codex.

## `claude-independent-review`

Ce skill fait intervenir **Claude Code comme reviewer indépendant et en lecture seule**, tandis que Codex conserve la responsabilité du cadrage, de l'arbitrage et des corrections. Il peut examiner du code, de l'architecture, de la sécurité, du design ou du contenu.

Le workflow :

1. Codex inspecte le projet et fait valider une politique de revue.
2. Le runner fabrique un snapshot temporaire et filtré du projet.
3. Claude Code reçoit une mission neutre et ne dispose que de `Read`, `Glob` et `Grep`.
4. La réponse originale de Claude est conservée dans un rapport immuable.
5. Codex vérifie chaque constat, applique les corrections autorisées et consigne ses décisions dans une résolution séparée.
6. Toute contre-revue doit être confirmée explicitement.

### Sécurité et traçabilité

- Les vrais fichiers `.env`, clés privées et magasins d'identifiants usuels sont exclus de manière non désactivable.
- Les liens symboliques qui sortent du projet ne sont pas suivis.
- Aucun shell, navigateur, MCP ou lancement de tests n'est accessible à Claude.
- Le modèle et l'effort configurés sont utilisés exactement, sans fallback silencieux.
- Les snapshots, prompts temporaires, logs, caches et tentatives échouées sont supprimés.
- Seuls les éléments utiles à l'audit restent dans le projet : politique, pointeur `AGENTS.md`, rapport réussi, résolution éventuelle, manifeste d'empreintes et diff Git filtré éventuel.
- Le skill ne committe, ne pousse et ne publie jamais les artefacts d'un projet sans demande distincte.

Par défaut, les revues utilisent `claude-sonnet-5`, l'effort `high`, le français, un timeout de 20 minutes et au plus 40 tours. Le snapshot est limité à 20 000 fichiers et 250 Mio ; au-delà, le runner s'arrête et demande un cadrage explicite.

## Installation sur un autre ordinateur

### 1. Prérequis

Installer sur le nouvel ordinateur :

- [Codex](https://developers.openai.com/codex/) ;
- Python 3.10 ou plus récent ;
- Git ;
- [Claude Code](https://code.claude.com/docs/en/setup), connecté à un compte autorisé ;
- un accès GitHub au dépôt privé `HidaAkawa/mon-repo-skills`.

Installation native recommandée de Claude Code sur macOS, Linux ou WSL2 :

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Installation native recommandée sous Windows PowerShell :

```powershell
irm https://claude.ai/install.ps1 | iex
```

La [documentation officielle de Claude Code](https://code.claude.com/docs/en/setup) décrit aussi les installations avec Homebrew, WinGet et les gestionnaires de paquets Linux.

Les identifiants Claude et GitHub ne sont jamais inclus dans ce dépôt. Il faut s'authentifier séparément sur chaque machine :

```text
gh auth login
claude auth login
```

Vérifier ensuite que les commandes sont disponibles :

```text
python3 --version
claude --version
claude auth status --text
```

Sous Windows, `py -3 --version` peut remplacer `python3 --version`.

### 2. Cloner et copier le skill

#### macOS, Linux ou WSL2

```bash
gh repo clone HidaAkawa/mon-repo-skills
mkdir -p ~/.codex/skills
cp -R mon-repo-skills/skills/claude-independent-review ~/.codex/skills/
```

#### Windows PowerShell

```powershell
gh repo clone HidaAkawa/mon-repo-skills
$skillsDirectory = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $skillsDirectory | Out-Null
Copy-Item -Recurse -Force ".\mon-repo-skills\skills\claude-independent-review" $skillsDirectory
```

Le fichier doit finalement se trouver ici :

- macOS, Linux, WSL2 : `~/.codex/skills/claude-independent-review/SKILL.md` ;
- Windows : `%USERPROFILE%\.codex\skills\claude-independent-review\SKILL.md`.

Ouvrir ensuite une **nouvelle tâche Codex** afin que le skill soit découvert.

### 3. Vérifier l'installation

Sur macOS, Linux ou WSL2 :

```bash
python3 ~/.codex/skills/claude-independent-review/scripts/claude_review.py doctor
```

Sous Windows PowerShell :

```powershell
py -3 "$env:USERPROFILE\.codex\skills\claude-independent-review\scripts\claude_review.py" doctor
```

Le diagnostic doit confirmer que Python, Git le cas échéant et l'exécutable Claude sont utilisables, et que les options de sécurité attendues sont disponibles.

### 4. Première utilisation dans un projet

Dans une nouvelle tâche Codex ouverte à la racine du projet, demander par exemple :

```text
Utilise $claude-independent-review pour configurer des revues indépendantes sur ce projet.
```

Codex inspectera d'abord le projet et proposera en une seule fois : langue, modèle, effort, sources de vérité, exclusions, seuils et jalons. **Aucun fichier ne sera créé avant validation.** Après accord, le skill ajoutera :

- `.codex/claude-review.json`, la politique versionnable du projet ;
- un petit bloc délimité dans le `AGENTS.md` racine.

Pour demander une revue ponctuelle :

```text
Utilise $claude-independent-review pour faire une revue sécurité de ce projet.
```

Une demande explicite autorise la revue initiale. Une contre-revue des corrections demande toujours une nouvelle confirmation.

## Mise à jour

Dans le clone de ce dépôt :

```text
git pull
```

Recopier ensuite le dossier `skills/claude-independent-review` vers le même emplacement personnel. Avant de remplacer une version locale modifiée, en faire une sauvegarde. Redémarrer la tâche Codex puis relancer `doctor`.

Les politiques et rapports créés dans les projets ne résident pas dans ce dépôt de skills : ils restent dans leurs projets respectifs et peuvent y être versionnés pour conserver la trace des décisions.

## Contenu du dépôt

```text
skills/
└── claude-independent-review/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    │   ├── configuration.md
    │   └── reviewer-mandate.md
    └── scripts/
        ├── claude_review.py
        └── test_claude_review.py
```

Le runner Python utilise uniquement la bibliothèque standard. Les tests simulés peuvent être lancés avec :

```bash
python3 -m unittest skills/claude-independent-review/scripts/test_claude_review.py
```
