# `codex-independent-review`

**Compatibilité : Claude Code uniquement.** Ce skill est conçu pour que Claude
Code délègue un contrôle à un modèle externe. Codex y est le *reviewer*, pas
l'hôte : c'est Claude Code qui exécute le skill.

Le skill fait intervenir **Codex comme reviewer indépendant et en lecture
seule**, tandis que Claude Code conserve la responsabilité du cadrage, de
l'arbitrage et des corrections. Il peut examiner du code, de l'architecture, de
la sécurité, du design ou du contenu.

C'est le miroir de [`claude-independent-review`](../../codex/claude-independent-review/),
qui inverse les rôles. Les deux skills partagent le même contrat externe —
politique JSON versionnée, pointeur délimité, rapport immuable, autorisation
bornée `std-dev-project` — mais leur mécanique diffère là où les deux CLI
diffèrent réellement ; voir [Écarts assumés](#écarts-assumés).

## Workflow

1. Pour un projet neuf, Claude Code fait choisir explicitement le modèle Codex,
   puis inspecte le projet et fait valider une politique de revue.
2. Le runner fabrique un snapshot temporaire et filtré du projet.
3. Codex reçoit une mission neutre et tourne sous bac à sable `read-only`.
4. La réponse originale de Codex est conservée dans un rapport immuable.
5. Claude Code vérifie chaque constat, applique les corrections autorisées et
   consigne ses décisions dans une résolution séparée.
6. Toute contre-revue autonome doit être confirmée explicitement ; une
   préautorisation `std-dev-project` v4 est acceptée seulement pour sa version,
   son jalon et son budget `2 / 3 / 4`.

## Choix du modèle

À la première configuration, le skill découvre les modèles puis **demande le
modèle de façon bloquante**, avant toute autre question.

La découverte **ne fait aucune requête réseau**. Codex s'authentifie par sa
propre CLI et n'expose pas de clé exploitable par ce runner ; celui-ci lit donc
le catalogue que Codex maintient dans `$CODEX_HOME/models_cache.json`, ou
`~/.codex/models_cache.json` à défaut, et n'en retient que les modèles marqués
`visibility: list`. Sans cache lisible — typiquement un poste où Codex n'a
jamais tourné — il utilise un catalogue embarqué daté proposant Terra, Sol,
Luna, GPT-5.5, GPT-5.4, GPT-5.4-Mini ou la saisie d'un identifiant exact.
`gpt-5.6-terra` est recommandé mais **n'est jamais retenu sans réponse**.

Le choix est ensuite réutilisé sans être redemandé. Pour en changer, passer par
le remplacement explicite de politique : le skill ne modifie jamais
silencieusement le modèle, l'effort, les jalons ou les sources de vérité.

## Sécurité et traçabilité

- Les vrais fichiers `.env`, clés privées, `auth.json` et magasins
  d'identifiants usuels sont exclus de manière non désactivable.
- Les liens symboliques qui sortent du projet ne sont pas suivis.
- Chaque revue tourne avec `--sandbox read-only`, `--ephemeral`,
  `--ignore-user-config`, `--ignore-rules`, `--strict-config` et
  `web_search="disabled"` : ni écriture, ni session persistée, ni plugin, ni
  serveur MCP, ni règle d'execpolicy, ni accès web hérités du poste.
- Le runner refuse de démarrer si un drapeau de contournement du bac à sable
  apparaît dans la commande construite.
- Le modèle et l'effort configurés sont utilisés exactement, sans fallback
  silencieux.
- Pendant une revue, une progression JSONL expurgée est émise sur `stderr` :
  phase, durée, tours observés, avec un battement toutes les 15 secondes.
  `stdout` reste réservé au résultat JSON final.
- Les snapshots, prompts temporaires, logs, caches et tentatives échouées sont
  supprimés.
- Seuls les éléments utiles à l'audit restent dans le projet : politique,
  pointeur `CLAUDE.md`, rapport réussi, résolution éventuelle, manifeste
  d'empreintes et diff Git filtré éventuel. Le runner ajoute `/docs/reviews/`
  et tout `reports.directory` distinct au `.gitignore`, sans désindexer les
  audits déjà suivis.
- Le skill ne committe, ne pousse et ne publie jamais les artefacts d'un projet
  sans demande distincte.

Le bac à sable `read-only` empêche d'écrire, **pas de lire**. C'est donc le
filtrage du snapshot, et lui seul, qui protège les secrets d'un projet.

Autres valeurs par défaut : effort `high`, français, timeout de 20 minutes,
rapports dans `docs/reviews`. Le snapshot est limité à 20 000 fichiers et
250 Mio ; au-delà, le runner s'arrête et demande un cadrage explicite.

## Écarts assumés

Trois différences avec le miroir Claude viennent du CLI Codex lui-même, pas
d'un choix de conception :

| Miroir Claude | Ici | Conséquence |
|---|---|---|
| `--max-turns 40` | *(inexistant)* | Une revue n'est bornée que par `timeout_minutes`. `turns_observed` est indicatif, jamais une garantie. |
| `--append-system-prompt` | *(inexistant)* | Le mandat de contrôleur voyage en bande, en tête du prompt, séparé de la mission par une clôture. |
| API Models d'Anthropic | Cache local de Codex | La découverte est hors ligne et dépend d'une installation Codex déjà utilisée sur le poste. |

L'absence de plafond de tours n'est pas un oubli : la demande correspondante,
[openai/codex#12336](https://github.com/openai/codex/issues/12336), a été
fermée en « not planned ». Ne pas l'attendre d'une mise à jour.

En sens inverse, le bac à sable système de Codex est un verrou **plus fort**
que la liste d'outils du miroir : la lecture seule est imposée par le système
d'exploitation, pas par une restriction d'outillage.

## Désactiver dans un projet

La désactivation retire **uniquement** `.claude/codex-review.json` et le bloc
délimité dans le `CLAUDE.md` racine :

```bash
python3 <skill-dir>/scripts/codex_review.py disable-policy --project <racine>
```

**Tous les rapports, résolutions et dossiers de preuves restent en place.** La
commande est idempotente, refuse un bloc `CLAUDE.md` incomplet ou dupliqué, et
restaure l'état initial si une opération échoue. Supprimer les audits eux-mêmes
est une action distincte, qui exige une autorisation explicite. La règle
`/docs/reviews/` reste elle aussi dans `.gitignore`.

Une réactivation ultérieure suit le parcours d'initialisation et ne remplace
jamais les audits conservés.

## Prérequis spécifiques

En plus de Claude Code :

- Python 3.10 ou plus récent ;
- [Codex](https://developers.openai.com/codex/), connecté à un compte autorisé.

Les identifiants ne sont jamais inclus dans ce dépôt. S'authentifier séparément
sur chaque machine :

```text
codex login
```

Puis vérifier :

```text
python3 --version
codex --version
codex login status
```

Sous Windows, `py -3 --version` peut remplacer `python3 --version`. Si
l'exécutable `codex` n'est pas dans le `PATH` — c'est le cas d'une installation
Windows par défaut — le runner le cherche aussi dans ses emplacements usuels, et
l'option `--codex <chemin>` permet toujours de le désigner explicitement.

La découverte des modèles peut être vérifiée séparément :

```text
python3 <skill-dir>/scripts/codex_review.py discover-models
```

Ajouter `--offline` pour utiliser uniquement le catalogue embarqué.

## Installation

Voir l'[installation générale](../../../README.md#installation). Ce skill se
copie dans `~/.claude/skills/codex-independent-review/`.

## Vérifier l'installation

macOS, Linux, WSL2 :

```bash
python3 ~/.claude/skills/codex-independent-review/scripts/codex_review.py doctor
```

Windows PowerShell :

```powershell
py -3 "$env:USERPROFILE\.claude\skills\codex-independent-review\scripts\codex_review.py" doctor
```

Le diagnostic doit confirmer que Python, Git le cas échéant et l'exécutable
Codex sont utilisables, et que les verrous attendus sont disponibles.

## Première utilisation

Dans une nouvelle session Claude Code ouverte à la racine du projet :

```text
Utilise codex-independent-review pour configurer des revues indépendantes sur ce projet.
```

Claude Code demandera d'abord le modèle, puis inspectera le projet et proposera
en une seule fois : langue, effort, sources de vérité, exclusions, seuils et
jalons. **Aucun fichier ne sera créé avant validation.** Après accord, le skill
ajoutera :

- `.claude/codex-review.json`, la politique versionnable du projet ;
- un petit bloc délimité dans le `CLAUDE.md` racine ;
- la règle `/docs/reviews/` dans `.gitignore`.

Pour une revue ponctuelle :

```text
Utilise codex-independent-review pour faire une revue sécurité de ce projet.
```

Une demande explicite autorise la revue initiale. Une contre-revue autonome des
corrections demande toujours une nouvelle confirmation et le runner exige
`--confirm-counter-review`. Lors d'un appel par `std-dev-project`, l'option
`--sdp-authorized` fait valider et consommer la préautorisation bornée de
`.sdp/state.json` v4, à condition que `reviews.mode` y vaille `codex`.

Les politiques créées dans les projets ne résident pas dans ce dépôt de skills.
Les rapports restent dans leurs projets sous `docs/reviews/`, hors Git ; les
documents canoniques peuvent conserver leurs IDs, décisions et empreintes.

## Contenu

```text
codex-independent-review/
├── SKILL.md
├── README.md
├── references/
│   ├── configuration.md
│   └── reviewer-mandate.md
└── scripts/
    ├── codex_review.py
    └── test_codex_review.py
```

Le runner Python utilise uniquement la bibliothèque standard. Les tests simulés
se lancent depuis la racine du dépôt avec :

```bash
python3 skills/claude/codex-independent-review/scripts/test_codex_review.py
```

Ils utilisent un faux exécutable `codex` : **aucune requête n'est envoyée à
OpenAI et aucun quota n'est consommé.** En contrepartie, ils vérifient que la
bonne ligne de commande est construite, pas que Codex y répond comme prévu.

`doctor`, lui, s'exécute sans coût contre le vrai CLI et couvre ce que la
simulation ne peut pas : résolution de l'exécutable, présence effective des
verrous dans `codex exec --help`, statut de connexion. Le lancer avant la
première revue d'un poste :

```bash
python3 <skill-dir>/scripts/codex_review.py doctor
```

Le chemin de revue lui-même n'a pas été exercé contre le service : un premier
usage réel reste le seul moyen de le confirmer.
