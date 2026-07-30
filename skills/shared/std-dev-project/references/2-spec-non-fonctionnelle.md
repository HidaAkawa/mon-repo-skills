# Phase 2 — Spécification non-fonctionnelle

**Interrogation : oui.** Lire `0-assurance.md` et `0-observabilite.md`. C'est la
phase la plus risquée pour un utilisateur peu technique : appliquer le
calibrage de `0-methode.md` avec rigueur.

## Ce que cette phase produit

Le niveau d'assurance, la complexité, puis la manière dont le projet sera
construit, hébergé, sécurisé, éprouvé et diagnostiqué. Pas ce qu'il fait — cela
reste pour la phase 3.

## Sommaire

- [Classer avant d'interroger](#classer-avant-dinterroger)
- [Cadrage à passer à grill-me](#cadrage-à-passer-à-grill-me)
- [Ce qui se tranche d'office](#ce-qui-se-tranche-doffice)
- [Tests et observabilité](#tests-et-observabilité)
- [Documents de sortie](#documents-de-sortie)

## Classer avant d'interroger

Lire objectif, projet et brouillons éventuels. Préremplir assurance et
complexité avec les faits établis. Ne demander que les faits métier qui peuvent
modifier le classement. Ne jamais demander à l'utilisateur de choisir entre
`essentiel`, `renforce` et `critique`.

Annoncer la proposition ainsi :

> Je classe ce projet en `<niveau>` parce que `<conséquences concrètes>`. Cela
> implique `<tests, preuves et exploitation en langage clair>`. Je prends les
> choix techniques correspondants ; signale-moi seulement si un fait métier est
> faux.

## Cadrage à passer à `grill-me`

```
sujets :
  - qui accède au produit et depuis où
  - quelles données concernent d'autres personnes et leur sensibilité
  - conséquences financières, juridiques ou humaines d'une erreur
  - durée d'indisponibilité acceptable
  - budget mensuel et nombre d'utilisateurs attendus
```

Retirer tout sujet déjà résolu. Pour un profil non technique, ne jamais ajouter
framework, stockage, sampling, format de logs ou architecture de traces.

## Ce qui se tranche d'office

À partir du classement et de la complexité, décider :

- architecture technique et de déploiement ;
- langage, framework, stockage et hébergement ;
- framework et profondeur des tests ;
- niveau d'observabilité ;
- unité d'exécution tracée ;
- exporteur, propagation et sampling ;
- variable de logs de la stack ou `APP_LOG_LEVEL`.

Pour `code: non`, trancher tout cela. Pour `assiste`, recommander et expliquer
brièvement. Pour `oui`, demander uniquement les arbitrages dont plusieurs
réponses restent raisonnables.

Chaque décision porte une raison et, si elle reste incertaine, une hypothèse
`HYP-<NNN>`.

## Tests et observabilité

Déduire la profondeur des tests :

- `essentiel` : parcours principal, erreurs essentielles et contrat
  d'observabilité ;
- `renforce` : logique métier, modes d'erreur, accès non autorisés et
  dépendances ;
- `critique` : cas limites, sécurité, résilience, reprise et preuves conservées.

Le tracing de bout en bout est obligatoire dans les trois cas. Déterminer
`observabilite.niveau` :

- `local` pour un processus simple ;
- `distribue` pour plusieurs composants, de l'asynchrone ou un projet renforcé ;
- `operationnel` pour un projet critique.

Définir l'unité d'exécution significative, les niveaux de logs et les variables
OpenTelemetry selon `0-observabilite.md`.

## Points de vigilance

**La sécurité se traite ici.** Même sur un prototype, vérifier les données
personnelles et les conséquences d'un accès non autorisé.

**Ne jamais accepter « on verra pour l'hébergement plus tard ».** Le lieu
d'exécution contraint la stack.

**Traduire tout coût en euros par mois** pour les profils non techniques.

**Ne pas surdocumenter.** Si architecture, observabilité ou stratégie de tests
tiennent lisiblement dans `spec-nf.md`, ne pas créer un document autonome.

## Documents de sortie

Toujours : `docs/spec-nf.md`, depuis
[templates/spec-nf.md](../templates/spec-nf.md).

Selon `0-assurance.md` et seulement si utiles :

- `docs/architecture.md` depuis
  [templates/architecture.md](../templates/architecture.md) ;
- `docs/observabilite.md` depuis
  [templates/observabilite.md](../templates/observabilite.md) ;
- `docs/qualite/strategie-tests.md` depuis
  [templates/strategie-tests.md](../templates/strategie-tests.md) ;
- ADR depuis [templates/adr.md](../templates/adr.md) ;
- modèle de menace depuis
  [templates/modele-menaces.md](../templates/modele-menaces.md) ;
- runbooks depuis [templates/runbook.md](../templates/runbook.md).

Chaque décision porte une justification en une phrase.

## Sortie de phase

1. Faire valider les faits et conséquences métier par l'utilisateur.
2. Relire techniquement le classement, l'architecture et l'observabilité.
3. Renseigner `assurance`, `complexite`, `observabilite` et les hypothèses.
4. Mettre `docs/index.md` à jour.
5. Ajouter `"spec-nf"` à `etat.verrouille`, passer `phase` à 3.
6. Commit : `docs(sdp): spécification non-fonctionnelle v<N>`.
7. Proposer le push.

Puis [3-spec-fonctionnelle.md](3-spec-fonctionnelle.md).
