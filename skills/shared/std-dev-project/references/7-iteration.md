# Phase 7 — Itération

**Interrogation : non.** Cette phase ne fait qu'ouvrir la suivante.

## Ce qu'elle fait

Incrémenter la version, remettre le cycle à la phase 2, et transmettre à
l'itération suivante ce qu'elle doit savoir.

## Procédure

1. Incrémenter `etat.iteration`, passer `etat.version` à `v<N+1>`.
2. `phase` → 2, `phase_nom` → `spec-nf`.
3. **Vider `etat.verrouille`** : les décisions redeviennent ouvertes, c'est
   précisément le sens d'une itération. Les documents `-vN` restent la référence
   tant qu'un `-vN+1` ne les contredit pas.
4. Rappeler les dérogations non soldées de `DETTE.md`.
5. Commit : `chore(sdp): ouverture de l'itération v<N+1>`.

## Ce qui est transmis à la phase 2

Composer un résumé court, à passer en tête du cadrage de l'itération suivante :

- la portée décidée en phase 6 — mineure ou majeure ;
- les issues retenues pour cette version ;
- les points d'architecture que le feedback a mis en doute ;
- les dérogations à solder.

## Le piège à éviter

Une itération ne recommence pas de zéro. Le `grill-me` de la phase 2 ne doit
réinterroger **que ce qui change** :

- **itération mineure** : demander la confirmation que l'architecture reste
  valable, en une question. Si oui, produire un `spec-nf-vN+1.md` de trois
  lignes renvoyant à la version précédente, et passer à la phase 3.
- **itération majeure** : interroger uniquement les axes que le feedback a
  remis en cause. Ne pas rejouer les sujets stables.

Refaire intégralement l'interrogation à chaque tour est le meilleur moyen de
faire abandonner la méthode. Le signaler si l'utilisateur le demande lui-même :

> On a déjà tranché l'hébergement et il n'a posé aucun problème. Je ne le
> rouvre pas — dis-le moi si tu veux qu'on y revienne.

## Documents de l'itération

Rappel de `0-methode.md` : les documents `-vN+1` sont des **diffs ciblés**. Ne
jamais recopier l'inchangé ; renvoyer à `-vN`.

Puis [2-spec-non-fonctionnelle.md](2-spec-non-fonctionnelle.md).
