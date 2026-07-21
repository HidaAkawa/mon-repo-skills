# `claude-independent-review`

**Compatibilité : Codex uniquement.** Ce skill est conçu pour que Codex délègue
un contrôle à un modèle externe. Claude Code y est le *reviewer*, pas l'hôte :
c'est Codex qui exécute le skill.

Le skill fait intervenir **Claude Code comme reviewer indépendant et en lecture
seule**, tandis que Codex conserve la responsabilité du cadrage, de l'arbitrage
et des corrections. Il peut examiner du code, de l'architecture, de la sécurité,
du design ou du contenu.

## Workflow

1. Pour un projet neuf, Codex fait choisir explicitement le modèle Claude, puis
   inspecte le projet et fait valider une politique de revue.
2. Le runner fabrique un snapshot temporaire et filtré du projet.
3. Claude Code reçoit une mission neutre et ne dispose que de `Read`, `Glob` et
   `Grep`.
4. La réponse originale de Claude est conservée dans un rapport immuable.
5. Codex vérifie chaque constat, applique les corrections autorisées et consigne
   ses décisions dans une résolution séparée.
6. Toute contre-revue doit être confirmée explicitement.

## Choix du modèle

À la première configuration, le skill **demande le modèle de façon bloquante**,
avant toute autre question. Il propose Sonnet 5, Opus 4.8, Fable 5, Haiku 4.5 ou
la saisie d'un identifiant exact. `claude-sonnet-5` est recommandé mais **n'est
jamais retenu sans réponse**.

Le choix est ensuite réutilisé sans être redemandé. Pour en changer, passer par
le remplacement explicite de politique : le skill ne modifie jamais
silencieusement le modèle, l'effort, les jalons ou les sources de vérité.

## Sécurité et traçabilité

- Les vrais fichiers `.env`, clés privées et magasins d'identifiants usuels sont
  exclus de manière non désactivable.
- Les liens symboliques qui sortent du projet ne sont pas suivis.
- Aucun shell, navigateur, MCP ou lancement de tests n'est accessible à Claude.
- Le modèle et l'effort configurés sont utilisés exactement, sans fallback
  silencieux.
- Pendant une revue, une progression JSONL expurgée est émise sur `stderr` :
  phase, durée, tours et outils de lecture, avec un battement toutes les
  15 secondes. `stdout` reste réservé au résultat JSON final.
- Les snapshots, prompts temporaires, logs, caches et tentatives échouées sont
  supprimés.
- Seuls les éléments utiles à l'audit restent dans le projet : politique,
  pointeur `AGENTS.md`, rapport réussi, résolution éventuelle, manifeste
  d'empreintes et diff Git filtré éventuel.
- Le skill ne committe, ne pousse et ne publie jamais les artefacts d'un projet
  sans demande distincte.

Autres valeurs par défaut : effort `high`, français, timeout de 20 minutes, au
plus 40 tours, rapports dans `docs/reviews`. Le snapshot est limité à
20 000 fichiers et 250 Mio ; au-delà, le runner s'arrête et demande un cadrage
explicite.

## Désactiver dans un projet

La désactivation retire **uniquement** `.codex/claude-review.json` et le bloc
délimité dans le `AGENTS.md` racine :

```bash
python3 <skill-dir>/scripts/claude_review.py disable-policy --project <racine>
```

**Tous les rapports, résolutions et dossiers de preuves restent en place.** La
commande est idempotente, refuse un bloc `AGENTS.md` incomplet ou dupliqué, et
restaure l'état initial si une opération échoue. Supprimer les audits eux-mêmes
est une action distincte, qui exige une autorisation explicite.

Une réactivation ultérieure suit le parcours d'initialisation et ne remplace
jamais les audits conservés.

## Prérequis spécifiques

En plus de Codex :

- Python 3.10 ou plus récent ;
- [Claude Code](https://code.claude.com/docs/en/setup), connecté à un compte
  autorisé.

Installation native de Claude Code sur macOS, Linux ou WSL2 :

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Sous Windows PowerShell :

```powershell
irm https://claude.ai/install.ps1 | iex
```

La [documentation officielle](https://code.claude.com/docs/en/setup) décrit
aussi les installations avec Homebrew, WinGet et les gestionnaires de paquets
Linux.

Les identifiants ne sont jamais inclus dans ce dépôt. S'authentifier séparément
sur chaque machine :

```text
gh auth login
claude auth login
```

Puis vérifier :

```text
python3 --version
claude --version
claude auth status --text
```

Sous Windows, `py -3 --version` peut remplacer `python3 --version`.

## Installation

Voir l'[installation générale](../../../README.md#installation). Ce skill se
copie dans `~/.codex/skills/claude-independent-review/`.

## Vérifier l'installation

macOS, Linux, WSL2 :

```bash
python3 ~/.codex/skills/claude-independent-review/scripts/claude_review.py doctor
```

Windows PowerShell :

```powershell
py -3 "$env:USERPROFILE\.codex\skills\claude-independent-review\scripts\claude_review.py" doctor
```

Le diagnostic doit confirmer que Python, Git le cas échéant et l'exécutable
Claude sont utilisables, et que les options de sécurité attendues sont
disponibles.

## Première utilisation

Dans une nouvelle tâche Codex ouverte à la racine du projet :

```text
Utilise $claude-independent-review pour configurer des revues indépendantes sur ce projet.
```

Codex demandera d'abord le modèle, puis inspectera le projet et proposera en une
seule fois : langue, effort, sources de vérité, exclusions, seuils et jalons.
**Aucun fichier ne sera créé avant validation.** Après accord, le skill
ajoutera :

- `.codex/claude-review.json`, la politique versionnable du projet ;
- un petit bloc délimité dans le `AGENTS.md` racine.

Pour une revue ponctuelle :

```text
Utilise $claude-independent-review pour faire une revue sécurité de ce projet.
```

Une demande explicite autorise la revue initiale. Une contre-revue des
corrections demande toujours une nouvelle confirmation.

Les politiques et rapports créés dans les projets ne résident pas dans ce dépôt
de skills : ils restent dans leurs projets respectifs et peuvent y être
versionnés pour conserver la trace des décisions.

## Contenu

```text
claude-independent-review/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── configuration.md
│   └── reviewer-mandate.md
└── scripts/
    ├── claude_review.py
    └── test_claude_review.py
```

Le runner Python utilise uniquement la bibliothèque standard. Les tests simulés
se lancent depuis la racine du dépôt avec :

```bash
python3 skills/codex/claude-independent-review/scripts/test_claude_review.py
```
