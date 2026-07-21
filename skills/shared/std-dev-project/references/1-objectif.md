# Phase 1 — Objectif macro

**Interrogation : oui.**

## Ce que cette phase produit — et ne produit pas

Un **objectif macro** : ce que le projet cherche à obtenir, pour qui, et à quoi
on saura qu'il a réussi.

Pas une liste de fonctionnalités. Pas un choix technique. **La confusion entre
objectif et spécification fonctionnelle est l'erreur que cette phase existe pour
prévenir.** Dès que l'utilisateur part dans « et il faudra un bouton pour… »,
l'arrêter :

> Note-le, on y revient à l'étape 3. Ici on décide ce que le projet doit
> accomplir, pas comment il s'utilise.

Tenir une liste de ces débordements et la transmettre à la phase 3 : ce sont des
matériaux, pas des parasites.

## Cadrage à passer à `grill-me`

Construire le bloc selon `0-methode.md`, avec :

```
sujets :
  - le problème réel, et pour qui il se pose
  - qui utilisera le résultat, et dans quel contexte
  - à quoi on reconnaîtra que le projet a réussi — critère observable
  - ce que le projet ne fera pas (frontière explicite)
  - ce qui existe déjà pour résoudre ce problème, et pourquoi ça ne suffit pas
  - l'échéance et le temps que l'utilisateur peut réellement y consacrer
```

En `origine: archeologie`, ajouter :

```
  - confirmation ou correction de chaque point du brouillon d'objectif
  - ce qui, dans le projet source, ne doit surtout pas être reconduit
```

## Points de vigilance

**Le critère de réussite est le plus important et le plus souvent bâclé.**
Refuser « que ça marche bien » ou « que les gens l'utilisent ». Exiger quelque
chose d'observable : un délai, un volume, une tâche accomplie en moins de X.
Sans lui, la phase 5 n'aura rien contre quoi évaluer le résultat.

**La frontière — ce que le projet ne fera pas — est le meilleur garde-fou contre
l'inflation du périmètre.** Y consacrer une vraie question, même si l'utilisateur
la trouve prématurée.

**Un objectif qui tient en une phrase est un bon objectif.** S'il en faut cinq,
il y a probablement deux projets. Le dire.

## Document de sortie

`docs/objectif-v1.md`, depuis [templates/objectif.md](../templates/objectif.md).

Le relire à voix haute avec l'utilisateur avant validation. Un objectif qu'il ne
peut pas reformuler lui-même n'est pas validé.

## Sortie de phase

1. Validation explicite de l'utilisateur.
2. Enrichir le `README.md` du projet avec l'objectif en quelques lignes.
3. `etat.verrouille` += `"objectif"`, `phase` → 2.
4. Commit : `docs(sdp): objectif macro v1`.
5. Proposer le push, avec confirmation.

Puis [2-spec-non-fonctionnelle.md](2-spec-non-fonctionnelle.md).
