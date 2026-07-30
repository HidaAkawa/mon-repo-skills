# Méthode — règles transverses

À lire avant toute phase. Ces règles priment sur les fichiers de phase.

## Sommaire

- [Préparer l'interrogation](#1-préparer-linterrogation)
- [Gates et dérogations](#2-gates-et-dérogations)
- [Terminer une phase](#3-terminer-une-phase)
- [Git](#4-git)
- [Documents canoniques](#5-documents-canoniques)
- [État v2](#6-état-v2)
- [Neutralité de plateforme](#7-neutralité-de-plateforme)

## 1. Préparer l'interrogation

Avant d'invoquer `grill-me` :

1. chercher les faits dans le projet, ses documents et son environnement ;
2. retirer les sujets déjà résolus ;
3. trancher les décisions techniques hors de portée du profil ;
4. ne conserver comme questions que les faits ou arbitrages qui changent le
   produit, sa criticité, son coût ou son délai.

Construire ensuite ce cadrage :

```
CADRAGE
profil : <profil.niveau_archi>, code lui-même : <profil.code>
max_questions_par_salve : <selon le profil>
vocabulaire : <simple | technique>
faits_connus : <faits établis, ne pas redemander>
sujets : <sujets encore réellement ouverts>
decisions_agent : <choix déjà tranchés avec leur raison>
verrouille : <etat.verrouille — ne pas rouvrir dans la phase courante>
```

La liste des `sujets` est exhaustive **après** retrait des faits connus et des
décisions techniques prises par l'agent. Elle n'impose pas une question par
sujet : regrouper et conclure dès que la réponse est suffisante.

Une décision verrouillée ne peut être rouverte que par la procédure ciblée de
la phase 7, lorsqu'une issue retenue l'affecte explicitement. Ne jamais vider
globalement `etat.verrouille`.

### Calibrage par profil

| `profil.code` | Salve max | Vocabulaire | Décisions techniques |
|---|:---:|---|---|
| `non` | 3, une si possible | simple | trancher, annoncer coût/délai/risque |
| `assiste` | 4 | technique expliqué brièvement | recommander, laisser objecter |
| `oui` | 4 | technique | demander seulement les vrais arbitrages |

### Frontière des hypothèses

Ne jamais supposer silencieusement un fait que seul l'utilisateur connaît :

- personnes concernées et nature de leurs données ;
- conséquence financière, juridique ou humaine d'une erreur ;
- caractère réglementé d'une activité ;
- durée d'indisponibilité réellement acceptable ;
- autorité habilitée à accepter un risque métier.

Poser ces questions en langage courant. Pour le reste, choisir une solution
raisonnable et consigner toute hypothèse significative sous cette forme :

```
HYP-<NNN>
décision : <ce qui est retenu>
raison : <pourquoi>
impact : <ce que cela change>
confiance : haute | moyenne | faible
validation attendue : <fait ou événement qui confirme ou invalide>
```

Garder uniquement les hypothèses ouvertes dans `.sdp/etat.json`. Une hypothèse
confirmée devient une décision du document concerné ; une hypothèse invalidée
est remplacée et son historique reste dans Git.

## 2. Gates et dérogations

À toute demande de saut :

1. refuser d'abord en nommant le coût concret ;
2. si l'utilisateur insiste et que la gate est dérogeable, écrire la dérogation
   dans `DETTE.md` et `etat.derogations` ;
3. la rappeler au début des phases suivantes ;
4. la solder en réalisant le travail et en conservant son historique Git.

Les documents secondaires sont dérogeables si leur absence ne force pas
l'agent à deviner et ne compromet ni sécurité ni livraison.

Ne jamais déclarer une release prête sans les gates suivantes :

- tests applicables verts ;
- exécution significative tracée de bout en bout ;
- logs corrélés à la trace ;
- absence connue de secret, token ou donnée interdite dans la télémétrie ;
- niveau de log configurable sans modification du code ;
- produit réellement essayé.

Pour `assurance.niveau: critique`, sécurité, audit, intégrité, reprise et
diagnostic des défaillances critiques sont également non dérogeables. Le
développement expérimental peut continuer, mais la release reste non prête.

## 3. Terminer une phase

Une phase n'est terminée que si :

1. sa preuve de sortie existe et satisfait le niveau d'assurance ;
2. l'utilisateur a explicitement validé les faits et décisions métier ;
3. l'agent a relu les décisions techniques et annoncé les hypothèses ouvertes ;
4. `.sdp/etat.json` et `docs/index.md` sont à jour ;
5. le tout est commité.

Ne pas demander à un utilisateur non technique de certifier une architecture
ou une stratégie de sampling. Lui faire valider leurs conséquences métier.

## 4. Git

Commit local automatique à la fin de chaque phase :

```
docs(sdp): <phase> v<N> — <résumé court>
```

Ne jamais pousser sans confirmation explicite, à chaque fois. Présenter le
commit, la branche, la destination et ce qui sera publié.

Avant un `git add` large, lire `git status` et inspecter tout fichier suspect.
Ne jamais exécuter de commande destructive sans avoir vérifié et mis à l'abri
le travail non commité.

## 5. Documents canoniques

Maintenir ces documents courants dans `docs/` :

```
index.md  objectif.md  spec-nf.md  spec-fonctionnelle.md  feedback.md
```

Git porte l'historique. Ne pas créer un document différentiel à chaque
itération. Mettre à jour le document canonique et créer, en phase 7, un
manifeste `docs/releases/v<N>.md` qui référence le commit du produit validé et
les preuves applicables.

Créer les artefacts supplémentaires uniquement selon
[0-assurance.md](0-assurance.md). Ne créer aucun dossier vide.

Chaque document indique au minimum :

- statut : brouillon, en revue, approuvé ou historique ;
- version du projet ;
- propriétaire ;
- date de dernière revue ;
- décisions, hypothèses et liens utiles.

## 6. État v2

Versionner `.sdp/etat.json` avec le projet :

```json
{
  "schema_version": 2,
  "version": "v1",
  "phase": 3,
  "phase_nom": "spec-fonctionnelle",
  "iteration": 1,
  "profil": {
    "code": "non",
    "discipline_process": "faible",
    "niveau_archi": "debutant"
  },
  "type_projet": "web",
  "origine": "neuf",
  "assurance": {
    "niveau": "renforce",
    "motifs": ["application partagée"],
    "reviser_si": ["ajout de données sensibles"]
  },
  "complexite": {
    "multi_composants": false,
    "asynchrone": false,
    "api_exposee": true,
    "donnees_persistantes": true
  },
  "observabilite": {
    "niveau": "distribue",
    "unite_tracee": "une requête utilisateur",
    "niveau_log_defaut": "info"
  },
  "hypotheses_ouvertes": [],
  "verrouille": ["objectif", "spec-nf"],
  "derogations": [],
  "dernier_commit": null,
  "maj": "2026-07-30"
}
```

Le profil utilisateur reste définitif. Réévaluer assurance, complexité et
observabilité seulement si le périmètre ou les conséquences changent.

Pour un état sans `schema_version: 2`, suivre la migration de
[0-assurance.md](0-assurance.md) sans ramener le projet à la phase 0.

## 7. Neutralité de plateforme

Dans les échanges et les documents :

- dire « l'agent », jamais le nom d'un modèle ou produit d'agent ;
- ne dépendre d'aucune fonction propre à une plateforme ;
- ne supposer que `grill-me`, `git` et, si nécessaire, `gh`.

OpenTelemetry, W3C Trace Context et OTLP sont des standards du projet produit,
pas des dépendances de la plateforme de l'agent : ils peuvent être nommés.
