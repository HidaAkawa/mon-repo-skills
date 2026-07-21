# Phase 6 — Backlog

**Interrogation : non.** Le tri est un arbitrage, pas une découverte.

## Ce que cette phase produit

Le contenu de la version suivante, sous forme de **GitHub Issues**. Chaque item
tracé, priorisé, et rattaché à son origine.

## Sources

Trois entrées, à balayer dans cet ordre :

1. `docs/feedback-v1.md` — les retours de la phase 5 ;
2. `docs/journal-dev-v1.md` — les écarts et difficultés de la phase 4 ;
3. `DETTE.md` — les dérogations non soldées. **Les inscrire au backlog
   systématiquement**, en priorité haute. Une dette qui n'entre jamais au
   backlog n'est pas une dette, c'est un abandon.

Ajouter les fonctionnalités écartées du MVP en phase 3.

## Prioriser

Proposer un classement, puis le faire arbitrer. Ne pas demander à l'utilisateur
de trier une liste brute de trente items — c'est la meilleure façon de le perdre.

Trois niveaux suffisent :

| Priorité | Critère |
|---|---|
| `haute` | empêche un usage réel, ou dette qui bloque la suite |
| `moyenne` | dégrade l'usage sans l'empêcher |
| `basse` | confort, idée à creuser |

Poser ensuite **une seule question d'arbitrage**, celle qui compte :

> Voici ce que je propose de mettre dans la prochaine version. Qu'est-ce qui
> manque, et qu'est-ce qui peut attendre encore un tour ?

## Créer les issues

```bash
gh issue create \
  --title "<intitulé orienté résultat>" \
  --label "<type>,<priorite>" \
  --body "<contexte, origine, critère d'acceptation attendu>"
```

Types : `bug`, `feature`, `dette`, `spec`. Priorités : `priorite-haute`,
`priorite-moyenne`, `priorite-basse`. Créer les labels au premier passage s'ils
n'existent pas.

Dans le corps, toujours indiquer **l'origine** : « issu du feedback v1 »,
« dérogation inscrite le <date> ». Trois itérations plus tard, c'est ce qui
permet de comprendre pourquoi l'item existe.

Créer une issue dans un dépôt distant est une écriture visible hors de la
machine : **présenter la liste complète et obtenir un accord** avant de la
créer. Si le projet n'a pas de dépôt distant, écrire un `BACKLOG.md` à la place
et le proposer en bascule vers les issues plus tard.

## Décider de la portée de l'itération

Terminer en qualifiant la version suivante :

- **mineure** — le périmètre et l'architecture ne bougent pas. La phase 2 sera
  expédiée : une confirmation que rien ne change suffit.
- **majeure** — l'architecture ou le périmètre évoluent. La phase 2 sera une
  vraie session d'interrogation.

Renseigner `etat.portee_iteration_suivante`.

## Sortie de phase

1. Issues créées, après accord.
2. `phase` → 7.
3. Commit : `docs(sdp): backlog pour v2`.
4. Proposer le push.

Puis [7-iteration.md](7-iteration.md).
