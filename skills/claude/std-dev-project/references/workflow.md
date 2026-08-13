# Workflow v4

Lire ce fichier pour commencer ou reprendre un projet. Les gates portent sur
des résultats observables, pas sur une quantité de documentation.

## Sommaire

- [État v4](#état-v4)
- [Règles transverses](#règles-transverses)
- [1 — Initialiser et cadrer](#1--initialiser-et-cadrer)
- [2 — Définir](#2--définir)
- [3 — Construire](#3--construire)
- [4 — Vérifier](#4--vérifier)
- [5 — Livrer et améliorer](#5--livrer-et-améliorer)

## État v4

Conserver `.sdp/state.json` dans Git. Utiliser cette forme. Le champ optionnel
`migration` est réservé à la transition v3 ; ne pas ajouter d'autre champ de
premier niveau sans nouvelle version de schéma :

```json
{
  "schema_version": 4,
  "method_version": "4.0",
  "project": {"name": "…", "origin": "new", "archetype": "web"},
  "stage": {"id": "initiate-and-frame", "status": "in-progress", "iteration": 1, "gate": null},
  "profile": {"development": "guided", "operations": "guided", "assurance": "guided"},
  "guarantee": {"level": "standard", "reasons": [], "review_if": []},
  "baseline": {"id": "BL-WEB-STANDARD-v1", "catalog_version": "1.0", "overrides": []},
  "assumptions": [],
  "risks": [],
  "derogations": [],
  "reviews": {
    "mode": "external-prompt",
    "authorization": {"source": "std-dev-project-v4", "version": "v1", "granted": true},
    "counter_reviews": {"maximum": 2, "used": 0},
    "milestones": [],
    "reports": []
  },
  "delivery": {
    "working_version": "v1",
    "candidate_version": null,
    "forge": "none",
    "branch": null,
    "change_request_url": null,
    "ci_status": "not-configured"
  },
  "documents": {
    "DOC-REG-001": {"path": "docs/document-register.md", "status": "draft", "version": "v1", "baseline": "git:pending"},
    "PRJ-CHTR-001": {"path": "docs/project-charter.md", "status": "draft", "version": "v1", "baseline": "git:pending"},
    "SRS-001": {"path": "docs/software-requirements-specification.md", "status": "planned", "version": "v1", "baseline": "git:pending"},
    "SDP-001": {"path": "docs/software-development-plan.md", "status": "planned", "version": "v1", "baseline": "git:pending"},
    "VVR-v1": {"path": "docs/verification/v1.md", "status": "planned", "version": "v1", "baseline": "git:pending"},
    "REL-v1": {"path": "docs/releases/v1.md", "status": "planned", "version": "v1", "baseline": "git:pending"}
  },
  "last_commit": null,
  "updated_at": "YYYY-MM-DD"
}
```

Chaque entrée de `reviews.reports` porte au minimum `id`, `milestone`,
`result`, `decision`, `sha256`, `counter_review_number` et, pour `elevated` ou
`critical`, une `archive_reference` non secrète. À chaque nouvelle
`delivery.working_version`, remettre `counter_reviews.used` à zéro et remplacer
`authorization.version` ; une autorisation d'une version antérieure n'est
jamais reportée implicitement.

Valeurs fermées :

- étapes : `initiate-and-frame`, `define`, `build`, `verify`,
  `release-and-improve` ;
- statuts : `in-progress`, `gate-failed`, `complete` ;
- profils : `guided`, `collaborative`, `autonomous` ;
- garanties : `standard`, `elevated`, `critical` ;
- origines : `new`, `reconstruction`, `migration` ;
- archétypes : `web`, `api`, `mobile`, `cli`, `library`, `batch`,
  `distributed` ;
- revues : `codex` ou `external-prompt` ;
- forges : `none`, `github`, `gitlab`, `other` ;
- CI : `not-configured`, `local-green`, `pending`, `failed`, `green`.

Dans `documents`, `planned` indique qu'un document n'est pas encore créé ; un
fichier existant utilise les statuts documentaires du profil normatif.

Chaque objet de `assumptions`, `risks` et `derogations` porte un ID immuable,
un énoncé, un statut, un propriétaire et sa source ou autorité. `documents`
indexe les six IDs canoniques avec chemin, statut, version et baseline Git.
`last_commit` désigne le `candidate_commit` effectivement évalué, jamais le
commit qui contient son propre enregistrement de gate. Mettre à jour
`updated_at` à chaque gate et après chaque changement de livraison observable.

## Règles transverses

### Mécanique native Claude Code

Trois mécanismes propres à Claude Code portent ce cycle ; ils changent
l'exécution, jamais les critères.

**Suivi des étapes.** Tenir une tâche par étape dans le gestionnaire de tâches
de la session, passée `in_progress` à l'entrée et `completed` seulement quand sa
gate est enregistrée. Une gate échouée laisse la tâche `in_progress` et ouvre
une tâche de correction. Le gestionnaire de tâches est un affichage : la source
de vérité reste `.sdp/state.json`. En cas de divergence, l'état fait foi et les
tâches sont recréées à partir de lui.

**Cadrage en mode plan.** Pendant `initiate-and-frame` et `define`, rester en
mode plan tant qu'aucune décision produit n'est arrêtée : l'observation et
l'interrogation ne doivent rien écrire. Sortir du mode plan pour créer le dépôt,
`.sdp/` et les documents, une fois la charte validée.

**Délégation.** L'étape `build` peut être confiée à `plan-delegate-verify`
lorsque le travail est décomposable. Voir « 3 — Construire ». Aucune autre étape
n'est déléguée : le cadrage, l'arbitrage des revues et les décisions de gate
restent tenus par l'agent principal.

**Skills composés.** Ce skill en invoque trois. Si l'un manque, ne pas le
simuler et ne pas bloquer :

| Skill | Rôle | Absent |
|---|---|---|
| `grill-me` | Interrogation calibrée | Prérequis dur. Arrêter et demander son installation. |
| `plan-delegate-verify` | Lots parallèles de l'étape `build` | Construire séquentiellement et le signaler dans le plan de développement. |
| `codex-independent-review` | Revues indépendantes | Basculer en `reviews.mode: external-prompt`. |

L'invocation de `plan-delegate-verify` par ce skill vaut demande explicite : son
déclenchement dépend du critère de découpe de l'étape 3, pas d'une demande
d'orchestration formulée par l'utilisateur.

### Documents canoniques

Maintenir :

| ID | Chemin | Création |
|---|---|---|
| `DOC-REG-001` | `docs/document-register.md` | étape 1 |
| `PRJ-CHTR-001` | `docs/project-charter.md` | étape 1 |
| `SRS-001` | `docs/software-requirements-specification.md` | étape 2 |
| `SDP-001` | `docs/software-development-plan.md` | étape 2 |
| `VVR-<version>` | `docs/verification/<version>.md` | étape 4 |
| `REL-<version>` | `docs/releases/<version>.md` | étape 5 |

Git porte l'historique. Mettre à jour les documents canoniques au lieu de créer
un différentiel par itération. Ajouter architecture, sécurité, traçabilité,
ADR ou runbook comme annexe seulement si le document canonique devient illisible.

### IDs

Ne jamais renuméroter ni réutiliser un ID : `ASM-###`, `RSK-###`, `DRG-###`,
`STK-###`, `SWR-FUN-###`, `SWR-SEC-###`, `SWR-QUA-###`, `SWR-OBS-###`,
`AC-###`, `TST-###`, `EVD-###`, `IR-###` et `ADR-####`.

### Gates et corrections

Une gate échouée maintient le projet dans l'étape courante. Corriger une
implémentation, un test ou une exigence ambiguë sur place. Rouvrir une étape
antérieure uniquement si le problème, le périmètre, le risque ou l'architecture
change ; consigner précisément ce qui est rouvert.

Pour obtenir un candidat reproductible à chaque gate :

1. terminer les changements de l'étape et les contrôles qui produisent des
   artefacts ;
2. committer le candidat avec le message indiqué par l'étape ;
3. vérifier que les chemins évalués sont propres, puis relancer les contrôles
   non mutateurs sur ce commit ;
4. enregistrer son SHA sous `stage.gate.candidate_commit`, avec date et IDs de
   preuve ;
5. committer séparément cet enregistrement avec
   `chore(sdp): enregistrer la gate <stage> v<N>`.

Le second commit porte la décision de gate et ne se référence jamais lui-même.
Le premier commit existe aussi pour `initiate-and-frame` : ne pas utiliser
`unborn` comme preuve. Aucun de ces commits n'autorise un push avant
`release-and-improve`.

Une dérogation indique l'ID, le contrôle écarté, le motif, l'autorité qui
l'accepte, l'échéance et le risque résiduel. Une dérogation ne rend jamais
licite une livraison interdite ni acceptable un risque humain non maîtrisé.

## 1 — Initialiser et cadrer

### Observer avant de demander

Inspecter le dépôt, les documents et l'environnement. Pour une reconstruction,
lire le projet source sans jamais y écrire et séparer les faits observés des
déductions.

Rester en mode plan pendant toute cette observation et toute l'interrogation qui
suit : rien n'est écrit tant que la charte n'est pas validée.

### Calibrer

Invoquer `grill-me` avec une salve initiale de trois questions :

1. code et configuration : décider et expliquer, valider des recommandations,
   ou comparer les options ensemble ;
2. mise en service et incidents : jamais, avec aide, ou autonome ;
3. tests, sécurité et documentation : appliquer une baseline, valider les
   choix importants, ou définir les contrôles ensemble.

Mapper les réponses sur `guided`, `collaborative`, `autonomous`. Ne jamais
afficher un jugement global de compétence. Ajuster le profil plus tard si
l'utilisateur le demande ou si davantage d'explication devient nécessaire.

Pour une interaction, utiliser l'axe concerné : `development` pour le code et
les choix d'implémentation, `operations` pour le déploiement et les incidents,
`assurance` pour tests, sécurité et preuves. Si une question touche plusieurs
axes, retenir le niveau le plus guidé. Le cadrage produit utilise le plus guidé
de `development` et `assurance`.

### Cadrer le produit

Passer à `grill-me` :

```text
CADRAGE
profil : <interaction calculée ; niveau le plus guidé parmi development et assurance>
axes : development=<...>, operations=<...>, assurance=<...>
max_questions_par_salve : guided=1, collaborative=3, autonomous=4
vocabulaire : simple | expliqué | technique
sujets : problème, utilisateurs, succès observable, périmètre, exclusions,
         délai, budget, exposition, données, conséquences d'une erreur ou panne
verrouille : faits déjà observés
```

Pour un fait inconnu, créer `ASM-###`, expliquer l'hypothèse prudente et
continuer. Créer le dépôt, `.sdp/`, le `.gitignore`, les deux premiers documents
et l'état v4. Si une forge est souhaitée, enregistrer son type mais ne pas
pousser.

**Gate :** profil calibré ; charte au statut `approved` avec décision,
approbateur et date ; chaque risque métier ouvert a un propriétaire et une
action ; état v4 et dépôt local prêts. Appliquer le protocole reproductible
ci-dessus. Commit du candidat :
`docs(sdp): cadrer le projet v<N>`.

## 2 — Définir

Lire `baselines.md`. Déduire l'archétype et la garantie depuis les faits ; ne
jamais demander à l'utilisateur de choisir un niveau. Appliquer le profil
`BL-<ARCHETYPE>-<GUARANTEE>-v1`, générer les exigences et expliquer seulement
coût, délai, données conservées et contraintes d'exploitation.

Choisir un archétype principal pour son budget de performance. Si le projet
cumule plusieurs formes, appliquer aussi tous les contrôles des overlays
secondaires et les consigner dans `baseline.overrides` avec `action: add` ; par
exemple une API à plusieurs services utilise le budget `api` et les contrôles
de propagation/résilience `distributed`.

Produire le SRS et le plan de développement. Chaque exigence a une source, une
raison, un critère d'acceptation et un lien de vérification. Définir la CI si
une forge est configurée : build, tests, lint, sécurité et preuves exigés par la
baseline.

Exécuter la revue de conception selon `independent-reviews.md` pour
`elevated` et `critical`, ou pour un projet `standard` sensible ou techniquement
nouveau.

**Gate :** exigences testables, baseline appliquée, architecture et stratégie
de vérification cohérentes, revue requise close sans P0–P2. Appliquer le
protocole reproductible. Commit du candidat :
`docs(sdp): définir la version v<N>`.

## 3 — Construire

Construire le parcours principal de bout en bout avant d'élargir. Développer
code, tests, sécurité, instrumentation et configuration CI dans le même lot.
Un changement visible exige d'abord une mise à jour de l'exigence.

### Déléguer les lots

Invoquer `plan-delegate-verify` seulement si le travail restant se découpe en
au moins deux lots réellement indépendants, dont les périmètres d'écriture ne se
recoupent pas. Un parcours principal court, séquentiel ou fortement couplé se
construit directement : le dire au lieu de fabriquer des lots artificiels.

Chaque lot délégué reçoit, sans que le sous-agent ait à les redécouvrir :

- les `SWR-###` qu'il implémente et leurs critères `AC-###` ;
- son périmètre d'écriture exact, disjoint de celui des autres lots ;
- les contrôles baseline applicables et les preuves `EVD-###` attendues ;
- l'interdiction de modifier `.sdp/`, les documents canoniques et `docs/reviews/`.

Ne jamais déléguer une décision produit, une dérogation, un arbitrage de revue
ni la rédaction d'une gate. Les comptes rendus des sous-agents sont des
affirmations : la gate de cette étape exige des preuves réellement obtenues,
vérifiées par l'agent principal. Une délégation ne réduit ni les contrôles, ni
les preuves, ni le niveau de garantie.

Ne pas créer de journal narratif obligatoire : commits, issues, tests et traces
sont les preuves. Créer un ADR uniquement pour une décision durable.

Exécuter localement le build, les tests applicables et une unité significative.
Montrer trace racine, spans utiles et logs corrélés. Vérifier que la panne de la
télémétrie ne casse pas le métier.

**Gate :** parcours principal exécutable, tests et observabilité intégrés,
preuves réelles obtenues. Renseigner le registre « Build gate evidence » du
plan de développement, puis appliquer le protocole reproductible avec les IDs
`EVD-###`. Commit du candidat : `feat: construire le produit v<N>`.

## 4 — Vérifier

Faire utiliser le produit pour une tâche réelle. Exécuter les contrôles locaux
équivalents à la CI, les tests d'acceptation, une panne représentative sûre et
le diagnostic `symptôme → trace → cause → action`.

Créer `docs/verification/<version>.md`. Exécuter la revue indépendante finale,
arbitrer chaque constat, corriger et utiliser le budget de contre-revues.

**Gate :** usage réel effectué, exigences vérifiées, CI locale verte, aucun
P0–P2 retenu non traité. Appliquer le protocole reproductible. Commit du
candidat : `test(sdp): vérifier la version v<N>`.

## 5 — Livrer et améliorer

Créer le record de release et prioriser le backlog. Sans forge, terminer avec
`delivery.ci_status: local-green` et `ready-not-published` dans le record.
Exécuter les contrôles locaux, committer d'abord le candidat avec
`chore(sdp): préparer la release v<N>`, vérifier les chemins propres, puis
écrire et committer séparément la gate qui référence ce SHA.

Avec une forge :

1. exécuter les contrôles locaux, committer le record, le backlog et tous les
   changements du candidat avec `chore(sdp): préparer la release v<N>`, puis
   vérifier les chemins propres ;
2. présenter branche, remote, contenu et contrôles ; obtenir la confirmation ;
3. pousser ce candidat et créer une PR/MR si `change_request_url` est nul,
   sinon mettre à jour la même ;
4. suivre la CI, corriger, committer et repousser sur la même branche jusqu'à
   obtenir `green` ; le dernier `HEAD` vert devient `candidate_commit` ;
5. écrire `stage.gate` avec ce SHA et les preuves, créer le commit séparé
   `chore(sdp): enregistrer la gate release-and-improve v<N>`, le pousser sur
   la même PR/MR et attendre de nouveau sa CI verte ;
6. si ce dernier contrôle échoue, corriger sur la même branche puis répéter les
   étapes 4 et 5 avec le nouveau SHA vert ;
7. ouvrir la PR/MR prête à relire, sauf demande explicite de brouillon, puis
   laisser l'utilisateur contrôler et fusionner quand il le souhaite.

Si la PR/MR reste ouverte, incrémenter l'itération et continuer sur la même
branche : chaque push actualise la même demande. Après fusion seulement,
actualiser la branche principale, vérifier que les commits sont intégrés,
retirer la branche locale devenue inutile et la branche distante si la forge
ne l'a pas déjà fait, puis créer une nouvelle branche. Ne jamais supprimer une
branche non fusionnée ni supprimer ou recréer une PR/MR ouverte pour publier
une nouvelle itération.

**Gate :** release candidate identifiable, preuves référencées, risques
résiduels acceptés, backlog priorisé et PR/MR verte ou statut local explicite.
Avec une forge, la gate n'est complète que si la CI du commit qui porte son
enregistrement est elle-même verte et si cet enregistrement référence le
dernier candidat vert. Les corrections et les deux commits restent toujours
sur la même branche et la même PR/MR.
