# Phase 6 — Backlog

**Interrogation : non.** Le tri est un arbitrage, pas une découverte. Lire
`0-garantie.md`.

## Ce que cette phase produit

Le contenu de la version suivante, sous forme de GitHub Issues ou, sans dépôt
distant, de `BACKLOG.md`. Chaque item est priorisé et rattaché à son origine.

## Sources

Balayer :

1. `docs/feedback.md` ;
2. `docs/journal-dev.md` ;
3. rapports de tests et validation d'observabilité ;
4. `DETTE.md` — toute dérogation non soldée entre en priorité haute ;
5. hypothèses ouvertes et fonctionnalités écartées du MVP.

## Prioriser

Proposer le classement avant de le faire arbitrer :

| Priorité | Critère |
|---|---|
| `haute` | bloque l'usage, la sécurité, une gate ou une dette critique |
| `moyenne` | dégrade l'usage ou le diagnostic sans l'empêcher |
| `basse` | confort ou idée à creuser |

Poser une seule question :

> Voici ce que je recommande pour la prochaine version. Qu'est-ce qui manque,
> et qu'est-ce qui peut attendre ?

## Créer les issues

Présenter la liste complète et obtenir un accord avant toute écriture distante.

Chaque issue contient résultat attendu, contexte, origine et critère
d'acceptation. Types principaux : `bug`, `feature`, `dette`, `spec`. Ajouter
`observabilite`, `securite` ou `documentation` si utile.

Sans dépôt distant, écrire `BACKLOG.md`. Créer une roadmap autonome seulement
si plusieurs étapes de livraison doivent être coordonnées ; sinon les issues
priorisées suffisent.

## Préparer l'itération

Qualifier la portée :

- **mineure** : périmètre et architecture stables, mise à jour ciblée ;
- **majeure** : architecture, niveau de garantie requis, observabilité ou
  périmètre évoluent.

Renseigner `etat.portee_iteration_suivante` et lister précisément les décisions
à rouvrir.

## Sortie de phase

1. Issues créées après accord, ou `BACKLOG.md` écrit.
2. Roadmap créée seulement si nécessaire.
3. Index et état à jour ; passer `phase` à 7.
4. Commit : `docs(sdp): backlog pour v<N+1>`.
5. Proposer le push.

Puis [7-iteration.md](7-iteration.md).
