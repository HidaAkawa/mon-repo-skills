# `grill-me`

**Compatibilité : Claude Code et Codex.** Aucun prérequis au-delà de l'agent
lui-même.

Une interrogation sans complaisance sur un plan, une décision ou une conception,
jusqu'à ce qu'une compréhension partagée soit atteinte. L'agent descend chaque
branche de l'arbre de décision, résout les dépendances une à une, et propose
systématiquement sa réponse recommandée.

Le principe : les *faits* se cherchent dans l'environnement, les *décisions*
reviennent à l'utilisateur.

## Utilisation

```text
grill me sur ce plan de migration
```

L'agent n'agit pas tant que l'utilisateur n'a pas confirmé que la compréhension
est partagée.

## Invocation par un autre skill

Contrairement à la version amont, ce skill est **invocable par un agent** et
accepte un bloc de cadrage. Un skill appelant peut restreindre l'interrogation :

| Clé | Effet |
|---|---|
| `profil` | Toute décision hors de portée de l'utilisateur est tranchée pour lui et expliquée, au lieu de lui être posée |
| `max_questions_par_salve` | Surcharge le défaut « une question à la fois » |
| `sujets` | Liste exhaustive des sujets que la session doit couvrir |
| `verrouille` | Décisions déjà actées, à ne jamais rouvrir |
| `vocabulaire` | Impose de définir ou d'éviter tout terme technique |

Sans bloc de cadrage, le skill se comporte comme une interrogation libre.

C'est ce mécanisme qu'utilise `std-dev-project` pour calibrer chaque phase sur
le niveau réel de l'utilisateur.

## Origine

Dérivé des skills `grill-me` et `grilling` de
[mattpocock/skills](https://github.com/mattpocock/skills), sous licence MIT.
Les modifications sont détaillées dans [NOTICE.md](../../../NOTICE.md) à la
racine du dépôt.
