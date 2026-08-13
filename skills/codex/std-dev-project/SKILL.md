---
name: std-dev-project
description: Conduire, reconstruire ou reprendre un projet logiciel de bout en bout selon un cycle v4 en cinq étapes, avec cadrage adaptatif via grill-me, baselines automatiques de sécurité, qualité, performance et observabilité, preuves proportionnées au risque, lots délégués à des sous-agents, revues indépendantes bornées, CI et livraison par PR/MR. À utiliser lorsqu'un projet doit être structuré ou lorsqu'un état .sdp/state.json ou .sdp/etat.json existe. Use when starting, rebuilding, migrating, or running a software project end to end.
---

# std-dev-project

Livrer un produit utilisable selon cinq étapes ordonnées. Chercher les faits,
appliquer une baseline complète, puis demander uniquement les décisions métier
qui changent le produit, le risque, le coût ou le délai.

Résoudre `<skill-dir>` comme le dossier absolu contenant ce fichier. Dire
« l'agent » dans les échanges et rester neutre vis-à-vis de la plateforme.

## Se situer

1. Chercher `.sdp/state.json` à la racine du projet.
2. S'il existe avec `schema_version: 4`, lire
   [references/workflow.md](references/workflow.md) et reprendre `stage.id`.
3. Si `.sdp/etat.json` existe, ou si `state.json` n'est pas en v4, lire
   [references/migration-v4.md](references/migration-v4.md) avant toute écriture.
4. En l'absence d'état, commencer à `initiate-and-frame`.

Charger ensuite uniquement les ressources utiles :

- [references/baselines.md](references/baselines.md) pendant `define`, lors
  d'un changement de risque ou pour vérifier une gate ;
- [references/independent-reviews.md](references/independent-reviews.md) aux
  jalons de conception et de vérification ;
- [references/standards-profile.md](references/standards-profile.md) pour créer
  ou contrôler les documents, jamais pour inventer une certification.

## Skills composés

| Skill | Étape | Rôle |
|---|---|---|
| `grill-me` | 1 et 2 | Calibrage et cadrage produit |
| `plan-delegate-verify` | 3 | Lots parallèles quand le travail est décomposable |
| `claude-independent-review` | 2 et 4 | Revue indépendante en lecture seule |

`grill-me` est un prérequis dur. Les deux autres ont un comportement dégradé
explicite décrit dans `workflow.md` : construire séquentiellement, ou basculer en
`reviews.mode: external-prompt`. Ne jamais simuler un skill absent.

L'invocation de `plan-delegate-verify` par ce skill vaut demande explicite : son
déclenchement dépend du critère de découpe de l'étape 3, pas d'une demande
d'orchestration formulée par l'utilisateur.

## Axes indépendants

- `profile` règle le vocabulaire, le nombre de questions et l'autonomie laissée
  à l'utilisateur ;
- `guarantee` règle les contrôles, preuves et revues ;
- `project.archetype` règle les valeurs techniques de départ.

Ne jamais réduire la sécurité ou la qualité parce que l'utilisateur est guidé.
Décider davantage pour lui et expliquer les conséquences en langage clair.

## Invariants

- Respecter l'ordre des cinq étapes, mais les enchaîner sans pause artificielle.
- Invoquer `grill-me` avec le cadrage de `workflow.md` pour toute interrogation
  produit ; ne jamais poser une question technique à un profil `guided`.
- Appliquer les baselines automatiquement. Une valeur plus faible exige une
  dérogation ; une valeur plus forte est une adaptation normale.
- Traiter « je ne sais pas » comme une hypothèse `ASM-###` et avancer avec la
  valeur prudente. Bloquer seulement une livraison dont le risque reste
  potentiellement critique ou illicite.
- Maintenir les six documents canoniques et ne créer une annexe que si son
  contenu ne reste pas lisible dans le document principal.
- Ne déléguer que des lots de construction, jamais une décision produit, un
  arbitrage de revue ou la rédaction d'une gate. Vérifier soi-même les preuves :
  un compte rendu de sous-agent est une affirmation.
- Confier les revues indépendantes à un modèle **distinct**. Un sous-agent de la
  même famille partage les mêmes angles morts et ne vaut pas revue indépendante.
- Conserver les rapports bruts sous `docs/reviews/`, ajouter
  `/docs/reviews/` au `.gitignore` et ne jamais désindexer un rapport suivi sans
  confirmation.
- Committer localement à chaque gate. Ne pousser que pendant
  `release-and-improve`, après confirmation explicite.
- Mettre à jour la même PR/MR tant qu'elle reste ouverte. Ne jamais fusionner à
  la place de l'utilisateur.
- Ne jamais écrire dans un projet source utilisé pour une reconstruction.
