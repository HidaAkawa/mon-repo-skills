# Phase 5 — Tests et feedback

**Interrogation : oui.**

## Ce que cette phase cherche

Les tests automatisés de la phase 4 ont vérifié qu'on a construit **conformément
à la spécification**. Cette phase-ci découvre si on a construit **la bonne
chose**. Régression contre exploration : les deux sont nécessaires, aucune ne
remplace l'autre.

C'est aussi ici qu'on éprouve le MVP en tant que **preuve de concept des
spécifications** : l'architecture a-t-elle tenu ?

## Faire essayer avant d'interroger

Ne pas lancer l'interrogation sur un souvenir. Demander à l'utilisateur
d'utiliser réellement le produit, si possible en accomplissant une tâche vraie,
et **de le faire avant** la session de questions.

Lui donner une consigne concrète plutôt qu'un « teste-le » :

> Prends dix minutes et sers-t'en pour de vrai, comme si je n'étais pas là.
> Note tout moment où tu hésites, où tu es surpris, ou où tu dois t'y reprendre
> à deux fois.

## Cadrage à passer à `grill-me`

```
sujets :
  - ce qui a fonctionné sans y penser
  - où il a hésité, ou dû s'y reprendre
  - ce qu'il s'attendait à trouver et qui n'existe pas
  - ce qui est là mais ne sert à rien
  - confrontation au critère de réussite de l'objectif : atteint, ou pas
  - confrontation aux choix d'architecture : tiennent-ils à l'usage réel
  - ce qui l'a agacé, même si ça paraît mineur
verrouille : objectif, spec-nf, spec-fonctionnelle
```

## Points de vigilance

**L'agacement mineur est le signal le plus fiable.** Un utilisateur minimise
toujours les frictions de son propre produit. Creuser chaque « c'est pas grave
mais » — c'est généralement là que se cache le vrai problème.

**Distinguer trois natures de retour**, elles n'ont pas la même suite :

| Nature | Suite |
|---|---|
| Ça ne marche pas comme spécifié | correctif, backlog en priorité haute |
| Ça marche comme spécifié, mais la spécification avait tort | révision de spec à l'itération suivante |
| Ça marche, il en veut plus | nouvelle fonctionnalité, backlog |

Confondre les deuxièmes et les troisièmes est l'erreur classique : la première
révèle une erreur de conception, la seconde une simple envie.

**Poser franchement la question de l'architecture.** Si l'hébergement retenu
s'est révélé pénible, si la base de données ne suffit pas, c'est maintenant
qu'il faut le dire — l'itération suivante repart de la phase 2, c'est
exactement l'occasion de corriger.

**Ne pas défendre le travail accompli.** L'agent a construit ce produit ;
argumenter contre un retour négatif fausse toute la phase.

## Document de sortie

`docs/feedback-v1.md`, depuis [templates/feedback.md](../templates/feedback.md).

Chaque retour y est consigné avec sa nature et sa gravité. C'est la matière
première de la phase 6 — ne rien filtrer à ce stade, le tri vient après.

## Sortie de phase

1. Validation explicite.
2. `phase` → 6.
3. Commit : `docs(sdp): feedback v1`.
4. Proposer le push.

Puis [6-backlog.md](6-backlog.md).
