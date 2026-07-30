# Observabilité et troubleshooting

À lire pendant les phases 2 à 5 et pour toute demande de diagnostic.

## Sommaire

- [Contrat universel](#contrat-universel)
- [Niveaux d'observabilité](#niveaux-dobservabilité)
- [Logs applicatifs](#logs-applicatifs)
- [Configuration OpenTelemetry](#configuration-opentelemetry)
- [Sécurité et coût](#sécurité-et-coût)
- [Tests et gates](#tests-et-gates)

## Contrat universel

Instrumenter toute unité d'exécution fonctionnelle significative :

- commande de CLI ;
- requête ou parcours utilisateur ;
- tâche planifiée ;
- traitement d'un message ;
- opération métier ;
- chargement ou action significative dans un jeu.

Créer un span racine pour l'unité et des spans enfants aux frontières utiles au
diagnostic. Chaque exécution obtient un `trace_id`; les logs émis dans son
contexte portent `trace_id` et `span_id`.

Ne pas tracer chaque frame, élément de boucle ou opération minuscule à haute
fréquence. Employer métriques ou événements agrégés et tracer les frontières
significatives : chargement, transaction, appel distant, sauvegarde, erreur.

## Niveaux d'observabilité

### `local`

Pour un processus simple :

- instrumenter avec OpenTelemetry ;
- exporter vers console, fichier structuré ou backend léger ;
- corréler logs et spans ;
- vérifier qu'une exécution complète est reconstituable ;
- ne pas imposer Collector distant ni dashboard.

### `distribue`

Pour plusieurs composants, de l'asynchrone ou un projet `renforce` :

- propager W3C Trace Context à travers HTTP, RPC, messages et tâches ;
- exporter en OTLP vers un Collector ou backend adapté ;
- conserver un sampling cohérent sur la trace entière ;
- instrumenter dépendances externes et opérations métier critiques.

### `operationnel`

Pour un projet `critique` :

- ajouter métriques, SLI/SLO, dashboards et alertes ;
- séparer audit et logs techniques ;
- documenter rétention, accès, redaction, sampling et coût ;
- fournir runbooks, exercices de panne et objectif de temps de diagnostic.

## Logs applicatifs

Si la stack possède une variable conventionnelle de niveau de log, l'utiliser
et documenter sa correspondance. Sinon imposer :

```
APP_LOG_LEVEL=trace|debug|info|warn|error|fatal
```

| Valeur | Usage |
|---|---|
| `trace` | détail maximal, temporaire pour troubleshooting |
| `debug` | diagnostic de développement et de test |
| `info` | fonctionnement normal en production |
| `warn` | anomalie sans échec complet |
| `error` | opération échouée |
| `fatal` | défaillance irrécupérable |

Valeurs par défaut : `debug` en développement et test, `info` en production,
`trace` temporairement pour un diagnostic approfondi.

Les modes `warn` et `error` ne désactivent jamais les événements obligatoires
d'audit ou de sécurité : les gérer par un flux indépendant.

`OTEL_LOG_LEVEL` est réservé au logger interne du SDK OpenTelemetry. Ne jamais
l'utiliser comme seuil des logs applicatifs.

Suivre le modèle de sévérité et les champs de corrélation OpenTelemetry :

- https://opentelemetry.io/docs/specs/otel/logs/data-model/
- https://opentelemetry.io/docs/specs/otel/compatibility/logging_trace_context/

## Configuration OpenTelemetry

Documenter et utiliser selon la stack :

```
OTEL_SERVICE_NAME
OTEL_RESOURCE_ATTRIBUTES
OTEL_TRACES_EXPORTER
OTEL_LOGS_EXPORTER
OTEL_EXPORTER_OTLP_ENDPOINT
OTEL_TRACES_SAMPLER
OTEL_TRACES_SAMPLER_ARG
```

Définir `OTEL_SERVICE_NAME`. Renseigner au minimum la version du service et
l'environnement de déploiement dans `OTEL_RESOURCE_ATTRIBUTES`, selon les
conventions sémantiques OpenTelemetry applicables.

En tests et en mode diagnostic :

```
APP_LOG_LEVEL=trace
OTEL_TRACES_SAMPLER=parentbased_always_on
```

La configuration officielle des variables est :
https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/

En production à fort volume, autoriser un sampling proportionné. Conserver les
erreurs, traces lentes et parcours critiques par une stratégie documentée.
Préserver la décision du parent entre composants.

## Sécurité et coût

- Ne jamais enregistrer secret, token, mot de passe, cookie de session ou donnée
  personnelle non nécessaire.
- Utiliser des noms de spans stables ; ne pas placer de valeur personnelle ou
  de forte cardinalité dans leur nom.
- Restreindre accès et rétention de la télémétrie.
- Assainir les valeurs pour empêcher l'injection de logs.
- Rendre l'export asynchrone et borné : l'indisponibilité du backend de
  télémétrie ne doit pas bloquer le métier.
- Mesurer les rejets, pertes ou saturations de la chaîne de télémétrie.
- Documenter le coût attendu pour les niveaux `renforce` et `critique`.

## Tests et gates

Écrire des tests qui prouvent :

1. qu'une unité significative possède un `trace_id` ;
2. que ses logs contiennent les identifiants de corrélation ;
3. que les spans localisent l'étape fautive ;
4. que service, version et environnement sont identifiables ;
5. qu'aucune donnée interdite n'est émise ;
6. que `APP_LOG_LEVEL` ou son équivalent change le seuil sans modifier le code ;
7. que la panne du backend de télémétrie ne casse pas l'opération métier.

La détection d'un secret, token ou autre donnée interdite doit faire échouer le
test concerné et bloque la release jusqu'à correction.

En phase 4, exécuter ces tests et montrer une trace complète réelle.

En phase 5, provoquer une défaillance représentative puis démontrer :

```
symptôme → trace → span fautif → logs corrélés → cause → action
```

Pour `essentiel`, consigner cette preuve dans `docs/feedback.md`. Pour
`renforce`, l'ajouter au rapport de tests. Pour `critique`, produire
`docs/qualite/validation-observabilite.md` avec environnement, version, preuves,
temps de diagnostic et risques résiduels.
