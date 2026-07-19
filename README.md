# Catalogue de skills

Ce dépôt regroupe des skills personnels pour Codex et, lorsque leur format le permet, d'autres agents. Chaque skill est autonome dans `skills/<nom-du-skill>/` et possède sa propre documentation utilisateur.

## Catalogue

| Skill | Description | Documentation |
|---|---|---|
| `claude-independent-review` | Faire relire du code, de l'architecture, de la sécurité, du design ou du contenu par Claude Code en lecture seule, avec arbitrage final par Codex et désactivation sans perte des audits. | [Consulter le guide](skills/claude-independent-review/README.md) |

## Organisation

```text
skills/
└── <nom-du-skill>/
    ├── README.md
    ├── SKILL.md
    ├── agents/
    ├── references/
    └── scripts/
```

- `README.md` documente le skill pour les utilisateurs.
- `SKILL.md` contient les instructions chargées par Codex.
- `agents/` expose les métadonnées d'interface éventuelles.
- `references/` contient les références chargées à la demande.
- `scripts/` contient les outils déterministes et leurs tests.

## Installation

Cloner le dépôt, puis copier uniquement le sous-répertoire du skill voulu dans le répertoire personnel des skills Codex :

```bash
gh repo clone HidaAkawa/mon-repo-skills
mkdir -p ~/.codex/skills
cp -R mon-repo-skills/skills/<nom-du-skill> ~/.codex/skills/
```

Consulter le README du skill pour ses prérequis, sa vérification et ses instructions d'utilisation. Ouvrir une nouvelle tâche Codex après installation ou mise à jour afin que la version déployée soit découverte.

## Contribution

Conserver chaque skill dans son sous-répertoire, limiter `SKILL.md` aux instructions nécessaires à l'agent et placer les détails utilisateur dans le README local. Exécuter les validations et tests indiqués par le skill avant publication.
