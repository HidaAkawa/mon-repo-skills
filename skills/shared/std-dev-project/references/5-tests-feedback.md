# Phase 5 — Tests et feedback

**Interrogation : oui.** Lire `0-observabilite.md`.

## Ce que cette phase cherche

Les tests automatisés vérifient la conformité aux spécifications. Cette phase
vérifie qu'on a construit la bonne chose et que le système se diagnostique
réellement lorsqu'elle fonctionne mal.

## Faire essayer avant d'interroger

Demander un usage réel avant la session :

> Sers-t'en pour une tâche réelle. Note les hésitations, surprises, erreurs et
> moments où tu dois recommencer.

## Exercer le diagnostic

Dans un environnement sûr, provoquer au moins une défaillance représentative :
entrée invalide, dépendance indisponible, timeout ou erreur métier. Ne jamais
injecter une panne destructive en production.

Démontrer :

```
symptôme → trace → span fautif → logs corrélés → cause → action
```

Vérifier que l'indisponibilité du backend de télémétrie ne casse pas le métier.
Mesurer le temps de diagnostic pour un projet critique.

## Cadrage à passer à `grill-me`

```
sujets :
  - ce qui a fonctionné sans y penser
  - où l'utilisateur a hésité ou recommencé
  - ce qu'il attendait et qui manque
  - ce qui existe mais ne sert pas
  - critère de réussite atteint ou non
  - architecture adaptée à l'usage réel
  - diagnostic suffisant pour comprendre les problèmes rencontrés
  - agacements, même mineurs
verrouille : objectif, spec-nf, spec-fonctionnelle
```

## Classer les retours

| Nature | Suite |
|---|---|
| Écart à la spécification | correctif prioritaire |
| Spécification erronée | révision à l'itération suivante |
| Besoin supplémentaire | fonctionnalité au backlog |
| Diagnostic insuffisant | dette d'observabilité |

Ne pas défendre le travail accompli.

## Documents de sortie

Toujours : `docs/feedback.md`, depuis
[templates/feedback.md](../templates/feedback.md).

Pour `renforce`, créer ou mettre à jour
`docs/qualite/rapport-tests.md` depuis
[templates/rapport-tests.md](../templates/rapport-tests.md). Pour `critique`,
produire aussi `docs/qualite/validation-observabilite.md` depuis
[templates/validation-observabilite.md](../templates/validation-observabilite.md).

## Sortie de phase

1. Gates de release vérifiées sur une version et un environnement identifiés.
2. Validation explicite du produit et du feedback.
3. Rapports proportionnés et `docs/index.md` à jour.
4. Passer `phase` à 6.
5. Commit : `docs(sdp): feedback et preuves v<N>`.
6. Proposer le push.

Puis [6-backlog.md](6-backlog.md).
