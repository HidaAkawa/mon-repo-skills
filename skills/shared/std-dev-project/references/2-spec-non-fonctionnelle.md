# Phase 2 — Spécification non-fonctionnelle

**Interrogation : oui.** C'est la phase la plus risquée pour un utilisateur peu
technique : elle porte sur des sujets dont il ignore souvent jusqu'au vocabulaire.
Appliquer le calibrage de `0-methode.md` avec rigueur.

## Ce que cette phase produit

Comment le projet sera construit, hébergé, sécurisé et éprouvé. Pas ce qu'il
fait — cela reste pour la phase 3.

## Cadrage à passer à `grill-me`

```
sujets :
  - architecture de déploiement : où ça tourne, qui y accède, depuis où
  - architecture technique : langage, framework, base de données
  - données : lesquelles, à qui elles appartiennent, combien de temps gardées
  - sécurité : authentification, données personnelles, secrets, sauvegardes
  - niveau d'exigence en tests automatisés
  - contraintes : budget mensuel, échéance, compétences disponibles
  - ce qui doit tenir à la charge : nombre d'utilisateurs attendus
```

## Ce qui se tranche d'office

Pour un profil `code: non`, et largement pour `assiste` : ne **pas** demander de
choisir un framework, une base de données ou un fournisseur d'hébergement. Ces
questions n'ont pas de réponse informée à ce niveau et produisent soit un
blocage, soit un choix au hasard que l'utilisateur ne pourra pas défendre.

Trancher à partir de `type_projet` et des contraintes, puis **annoncer et
justifier en trois lignes**. L'utilisateur garde le droit d'objecter.

Ce qui reste toujours à l'utilisateur, quel que soit son profil, parce que ce
sont des décisions métier déguisées en décisions techniques :

- **qui doit pouvoir accéder au produit** — public, sur invitation, lui seul ;
- **quelles données personnelles sont manipulées** — il est le seul à le savoir,
  et cela commande toute l'architecture de sécurité ;
- **combien il peut dépenser par mois** ;
- **ce qui arrive si le produit tombe une journée** — anodin, ou inacceptable ;
- **le niveau d'exigence en tests**, voir ci-dessous.

## Le niveau d'exigence en tests

C'est une décision **métier**, pas technique. La poser à tous les profils, en ces
termes :

> Trois questions rapides : ce projet manipule-t-il de l'argent ? Des données
> personnelles d'autres gens ? Est-ce que quelqu'un d'autre que toi va en
> dépendre ?

| Réponses | Niveau | Ce que ça implique |
|---|---|---|
| Aucun oui | `leger` | Tests sur les chemins principaux uniquement |
| Un oui | `standard` | Tests sur toute la logique métier et les cas d'erreur |
| Argent ou données personnelles | `strict` | Ci-dessus, plus les cas limites et les accès non autorisés |

Consigner le niveau dans la spécification : la phase 4 s'en sert comme critère
de sortie, et c'est la seule gate du cycle qui soit vérifiable par machine.

Le framework de test, lui, découle de la stack. Le trancher sans demander.

## Points de vigilance

**La sécurité se traite ici ou jamais.** La rattraper après coup coûte une
réécriture. Même sur un prototype, poser la question des données personnelles :
la réponse conditionne des obligations légales que l'utilisateur ignore
probablement.

**Ne jamais accepter « on verra pour l'hébergement plus tard ».** Le lieu
d'exécution contraint la stack ; le décider après revient à choisir la stack
deux fois.

**Traduire tout coût en euros par mois.** C'est la seule unité qu'un profil non
technique peut arbitrer avec confiance.

## Document de sortie

`docs/spec-nf-v1.md`, depuis [templates/spec-nf.md](../templates/spec-nf.md).

Chaque décision y figure avec **sa justification en une phrase**. Une décision
sans raison écrite sera rouverte à chaque itération.

## Sortie de phase

1. Validation explicite.
2. `etat.verrouille` += `"spec-nf"`, `phase` → 3.
3. Commit : `docs(sdp): spécification non-fonctionnelle v1`.
4. Proposer le push.

Puis [3-spec-fonctionnelle.md](3-spec-fonctionnelle.md).
