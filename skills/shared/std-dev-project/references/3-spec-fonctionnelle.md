# Phase 3 — Spécification fonctionnelle

**Interrogation : oui.**

## Ce que cette phase produit

Ce que le produit fait, du point de vue de celui qui l'utilise. Chaque
fonctionnalité assortie de **critères d'acceptation observables** — c'est d'eux
que les tests de la phase 4 sont dérivés mécaniquement.

Reprendre ici la liste des débordements notés en phase 1 : l'utilisateur avait
déjà des idées de fonctionnalités, elles ont leur place maintenant.

## Cadrage à passer à `grill-me`

```
sujets :
  - le parcours principal, de bout en bout, du point de vue de l'utilisateur
  - les fonctionnalités indispensables au MVP, et celles qui attendront
  - pour chacune : à quoi on voit qu'elle marche
  - ce qui se passe quand ça se passe mal — erreurs, saisies invalides, absence
  - qui a le droit de faire quoi, si plusieurs rôles existent
verrouille : objectif, spec-nf
```

Rappeler que `objectif` et `spec-nf` sont verrouillés. Si l'utilisateur veut une
fonctionnalité que l'architecture retenue ne permet pas, ne pas rouvrir la phase
2 en douce : le dire, et poser le choix — renoncer à la fonctionnalité, ou
ouvrir une itération pour changer l'architecture.

## Découper le MVP

Le premier MVP sert de **preuve de concept des deux spécifications** : il doit
valider que l'architecture tient, pas seulement que le code marche. Le découpage
suit donc une règle simple : **le MVP contient ce qui, s'il ne marchait pas,
invaliderait la spécification non-fonctionnelle.**

Concrètement, y faire figurer en priorité le parcours qui traverse le plus de
couches — celui qui exerce à la fois l'interface, la logique et le stockage.

Tout le reste part au backlog sans culpabilité. Un MVP qui fait trois choses
complètement vaut mieux qu'un MVP qui en ébauche dix.

## Critères d'acceptation

Pour chaque fonctionnalité retenue, exiger une formulation observable :

- ❌ « la recherche fonctionne bien »
- ✅ « en saisissant un nom partiel, la liste ne montre que les fiches dont le
  nom contient cette chaîne, sans tenir compte des accents ni de la casse »

Refuser les critères invérifiables. S'ils résistent, c'est en général que la
fonctionnalité elle-même est mal définie — creuser là.

## Dériver les cas de test

Aucune interrogation ici : la transformation est mécanique.

Pour chaque fonctionnalité : critère d'acceptation → cas de test nominal, puis
un cas par mode de défaillance identifié. La profondeur suit le niveau
d'exigence fixé en phase 2 :

| Niveau | Cas dérivés |
|---|---|
| `leger` | le nominal seulement |
| `standard` | nominal, plus chaque cas d'erreur listé |
| `strict` | ci-dessus, plus les cas limites et les tentatives d'accès non autorisé |

Les consigner dans la spécification, sous chaque fonctionnalité. Ils deviennent
le contrat de la phase 4.

## Document de sortie

`docs/spec-fonctionnelle-v1.md`, depuis
[templates/spec-fonctionnelle.md](../templates/spec-fonctionnelle.md).

## Sortie de phase

1. Validation explicite.
2. `etat.verrouille` += `"spec-fonctionnelle"`, `phase` → 4.
3. Commit : `docs(sdp): spécification fonctionnelle v1`.
4. Proposer le push.

Puis [4-developpement.md](4-developpement.md).
