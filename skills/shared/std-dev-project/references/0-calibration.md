# Phase 0 — Calibration et amorçage

**Interrogation : non.** Ces questions établissent le cadre, elles ne sont pas
une session `grill-me`.

Objectif : connaître l'utilisateur, créer le terrain, et ne plus jamais avoir à
redemander qui il est.

## 1. Établir le profil

Poser ces trois questions **en une seule fois**. Les présenter comme un réglage,
jamais comme un examen : l'utilisateur ne doit pas avoir l'impression d'être
jugé, sans quoi il surestimera son niveau et se retrouvera noyé plus tard.

> Trois questions pour que je cale mon niveau d'explication sur le tien. Il n'y
> a pas de bonne réponse.

1. **Sur un projet, qui écrit le code ?**
   `oui` je l'écris moi-même · `assiste` je le fais écrire par un agent et je
   relis · `non` je ne code pas
2. **As-tu déjà mis une application à disposition d'autres personnes** —
   hébergement, serveur, mise en ligne ?
   `confirme` plusieurs fois · `notion` une ou deux fois · `debutant` jamais
3. **Sur tes projets passés, écrivais-tu ce que devait faire le produit avant de
   le construire ?**
   `forte` oui · `moyenne` parfois · `faible` non, je commençais directement

Renseigner `profil.code`, `profil.niveau_archi`, `profil.discipline_process`.
**Ce profil est définitif** : ne plus jamais le réinterroger.

Si `discipline_process` vaut `faible`, prévenir sans moraliser :

> Tu vas trouver les premières étapes lentes — elles produisent des documents,
> pas du code. C'est exactement ce à quoi elles servent.

## 2. Situer le projet

- **Type** : web, mobile, API, CLI, script, bibliothèque, autre. Une question
  ouverte suffit, l'agent classe. Renseigner `type_projet` ; il conditionne les
  recommandations d'architecture de la phase 2.
- **Origine** : projet neuf, ou reconstruction à partir d'un projet existant ?
  Renseigner `origine` à `neuf` ou `archeologie`.

Si `archeologie` : demander le chemin du projet source, vérifier qu'il existe,
puis **poursuivre l'amorçage ci-dessous** avant de basculer sur
[0bis-archeologie.md](0bis-archeologie.md). Rappeler dès maintenant que le
projet source ne sera jamais modifié.

## 3. Créer le terrain

1. **Nom du projet.** Le demander. En `archeologie`, proposer
   `<nom-source>-v2` par défaut, jamais le nom du projet source.
2. **Répertoire.** Créer `~/Projects/<nom>/` sauf indication contraire de
   l'utilisateur ou d'une consigne de son environnement. Ne jamais créer un
   projet dans le répertoire courant par défaut, ni dans le répertoire
   personnel, ni sur le bureau.
3. **Git.** `git init` dans le nouveau répertoire.
4. **Squelette** : `docs/`, `.sdp/`, un `.gitignore` adapté au type de projet,
   un `README.md` minimal ne contenant que le nom du projet — il sera enrichi à
   la phase 1.

## 4. Créer le dépôt distant

Vérifier d'abord l'outillage :

```bash
gh auth status
```

Si l'authentification manque, **orienter** l'utilisateur vers `gh auth login` et
attendre. Ne jamais tenter de gérer des identifiants, ni de les saisir à sa
place.

Puis **demander la visibilité** — à chaque projet, sans jamais présumer :

> Dépôt privé ou public ? Public veut dire que le code et toute la
> documentation seront visibles de tous, dès maintenant et de façon
> difficilement réversible une fois indexés. Dans le doute, privé : on peut
> toujours ouvrir plus tard.

```bash
gh repo create <nom> --private --source=. --remote=origin
```

Si l'utilisateur préfère différer, poursuivre sans dépôt distant : les commits
locaux fonctionnent, le dépôt pourra être branché plus tard.

## 5. Écrire l'état initial

Créer `.sdp/etat.json` :

```json
{
  "version": "v1",
  "phase": 1,
  "phase_nom": "objectif",
  "iteration": 1,
  "profil": { "code": "…", "discipline_process": "…", "niveau_archi": "…" },
  "type_projet": "…",
  "origine": "neuf",
  "verrouille": [],
  "derogations": [],
  "dernier_commit": null,
  "maj": "<date du jour, absolue>"
}
```

En `origine: archeologie`, mettre `phase: 0.5` et `phase_nom: "archeologie"`.

## Sortie de phase

Commit local automatique :

```
chore(sdp): amorçage du projet <nom>
```

Puis proposer le push, avec confirmation explicite.

Enchaîner sur [0bis-archeologie.md](0bis-archeologie.md) si `origine` vaut
`archeologie`, sinon sur [1-objectif.md](1-objectif.md).
