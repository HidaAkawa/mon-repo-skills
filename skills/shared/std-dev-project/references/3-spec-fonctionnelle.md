# Phase 3 — Spécification fonctionnelle

**Interrogation : oui.**

## Ce que cette phase produit

Ce que le produit fait, du point de vue de celui qui l'utilise. Chaque
fonctionnalité porte des critères d'acceptation observables, des modes d'erreur,
des cas de test et les signaux nécessaires au diagnostic.

Reprendre les idées de fonctionnalités notées en phase 1.

## Cadrage à passer à `grill-me`

```
sujets :
  - parcours principal de bout en bout
  - fonctionnalités indispensables au MVP et celles qui attendront
  - pour chacune : à quoi on voit qu'elle marche
  - comportement attendu en cas d'erreur, saisie invalide ou absence
  - droits des rôles éventuels
verrouille : objectif, spec-nf
```

Retirer les faits déjà établis. Ne jamais demander à l'utilisateur comment
nommer les spans ou quels champs journaliser.

Si une fonctionnalité contredit l'architecture, ne pas rouvrir la phase 2 en
silence : renoncer à la fonctionnalité ou ouvrir une nouvelle itération.

## Découper le MVP

Le MVP est une preuve de concept des deux spécifications. Il contient en
priorité le parcours qui traverse les couches et dépendances significatives.

Tout le reste part au backlog. Un MVP court mais complet vaut mieux qu'un
périmètre large et incomplet.

## Critères d'acceptation

Exiger une formulation observable :

- refusé : « la recherche fonctionne bien » ;
- accepté : « un nom partiel ne montre que les fiches correspondantes, sans
  tenir compte des accents ni de la casse ».

## Dériver tests et signaux

Pour chaque fonctionnalité, dériver :

1. un cas nominal ;
2. les modes de défaillance exigés par le niveau de garantie requis ;
3. le nom stable de l'opération ou du span ;
4. les spans enfants utiles au diagnostic ;
5. les événements et erreurs à journaliser ;
6. les données explicitement interdites dans logs et spans.

Profondeur :

| Niveau de garantie requis | Cas dérivés |
|---|---|
| `essentiel` | nominal, erreurs essentielles, contrat d'observabilité |
| `renforce` | ci-dessus, chaque erreur, accès et dépendance |
| `critique` | ci-dessus, limites, sécurité, résilience et reprise |

Pour `essentiel`, conserver tout dans `docs/spec-fonctionnelle.md`. Pour
`renforce`, lier la stratégie de tests. Pour `critique`, maintenir
`docs/qualite/traceabilite.md` depuis
[templates/traceabilite.md](../templates/traceabilite.md).

## Document de sortie

`docs/spec-fonctionnelle.md`, depuis
[templates/spec-fonctionnelle.md](../templates/spec-fonctionnelle.md).

## Sortie de phase

1. Validation explicite des comportements et erreurs par l'utilisateur.
2. Vérifier que chaque parcours du MVP a tests et signaux diagnostiques.
3. Mettre `docs/index.md` et la traçabilité applicable à jour.
4. Ajouter `"spec-fonctionnelle"` à `etat.verrouille`, passer `phase` à 4.
5. Commit : `docs(sdp): spécification fonctionnelle v<N>`.
6. Proposer le push.

Puis [4-developpement.md](4-developpement.md).
