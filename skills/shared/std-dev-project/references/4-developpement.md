# Phase 4 — Développement

**Interrogation : non.** L'agent implémente, l'utilisateur relit et valide.

## Le contrat

Ce qui est construit découle des deux spécifications validées. Rien d'autre.

Si une question se pose que les spécifications ne tranchent pas — et il y en
aura — **ne pas l'inventer en silence**. Deux cas :

- **Détail d'implémentation** sans conséquence visible pour l'utilisateur :
  trancher, et le noter dans le journal de phase.
- **Question qui change le comportement du produit** : c'est un trou dans la
  spécification fonctionnelle. Le signaler, obtenir la réponse, et **amender le
  document** de la phase 3 — pas seulement le code. Une spécification qui ment
  est pire que pas de spécification.

## Conduite

Découper en tâches qui correspondent aux fonctionnalités du MVP, dans l'ordre
qui fait traverser les couches le plus tôt possible : le but est de vérifier
l'architecture, pas d'accumuler des morceaux.

Après chaque tâche : commit local avec un message qui référence la
fonctionnalité. Ne pas attendre la fin de la phase pour committer.

Pour un profil `code: non`, expliquer en une ligne ce qui vient d'être fait, en
termes de produit et non de code :

> Tu peux maintenant créer une fiche et la retrouver dans la liste. Le reste de
> l'écran est encore vide.

## Écrire les tests

Écrire les cas de test dérivés en phase 3, au niveau d'exigence fixé en phase 2.
Ni plus, ni moins : un projet `leger` sur-testé décourage autant qu'un projet
`strict` sous-testé.

Les tests découlent des critères d'acceptation. Ne pas écrire de test qui ne
corresponde à aucun critère — s'il en manque, c'est la spécification qu'il faut
compléter.

## La gate de sortie

**La suite de tests doit passer.** Intégralement. C'est la seule condition du
cycle qui ne dépende d'aucun jugement : ni l'agent ni l'utilisateur ne peuvent
l'assouplir par complaisance.

Exécuter la suite et **montrer la sortie réelle**. Ne jamais annoncer que les
tests passent sans les avoir lancés dans la session.

Si des tests échouent : ils sont corrigés, ou la phase n'est pas terminée. Un
test qu'on désactive pour passer la gate est une dérogation — il relève de
`DETTE.md` et de la procédure de `0-methode.md`, au même titre qu'un saut
d'étape.

## Journal de phase

`docs/journal-dev-v1.md` : les écarts constatés entre spécification et réalité,
les détails tranchés en cours de route, ce qui s'est révélé plus difficile que
prévu. Il alimente directement les phases 5 et 6.

## Sortie de phase

1. Suite de tests verte, sortie affichée.
2. Validation explicite de l'utilisateur sur le produit lui-même — il l'a
   ouvert, il l'a essayé.
3. `phase` → 5.
4. Commit : `feat: MVP v1`.
5. Proposer le push.

Puis [5-tests-feedback.md](5-tests-feedback.md).
