# Phase 7 — Itération

**Interrogation : non.** Lire `0-garantie.md`.

## Ce que cette phase fait

Figer les preuves de la version terminée, incrémenter la version, remettre le
cycle à la phase 2 et transmettre seulement ce qui doit être rouvert.

## Procédure

1. Créer `docs/releases/v<N>.md` depuis
   [templates/manifeste-release.md](../templates/manifeste-release.md).
2. Référencer le commit exact du produit essayé, l'environnement, les tests,
   les preuves d'observabilité, les documents canoniques et risques acceptés.
3. Incrémenter `etat.iteration`, passer `etat.version` à `v<N+1>`.
4. Passer `phase` à 2 et `phase_nom` à `spec-nf`.
5. Retirer de `etat.verrouille` seulement les décisions touchées par les issues
   retenues ; conserver les décisions stables.
6. Rappeler dérogations non soldées et hypothèses ouvertes.
7. Mettre `docs/index.md` à jour.
8. Commit : `chore(sdp): release v<N> et ouverture v<N+1>`.

## Ce qui est transmis

- portée mineure ou majeure ;
- issues retenues ;
- décisions fonctionnelles et architecturales affectées ;
- niveau de garantie requis, sécurité ou observabilité affectés ;
- dérogations et hypothèses à solder.

## Ne pas recommencer

Pour une itération mineure, mettre à jour les seules sections touchées des
documents canoniques. Demander une confirmation uniquement si un fait métier
n'est pas déjà établi.

Pour une itération majeure, réinterroger uniquement les axes remis en cause et
réévaluer le niveau de garantie requis si les conséquences ont changé.

Git porte le diff et l'historique ; le manifeste de release porte la baseline
approuvée. Ne jamais créer de document différentiel `-vN+1`.

Puis [2-spec-non-fonctionnelle.md](2-spec-non-fonctionnelle.md).
