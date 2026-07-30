# <Projet> — Observabilité

> Statut : brouillon / approuvé
> Version du projet : v<N>
> Propriétaire : <personne ou équipe>
> Dernière revue : <date absolue>
> Niveau : distribue / operationnel

## Objectif de diagnostic

<Ce qu'un opérateur doit pouvoir localiser et comprendre, et dans quel délai.>

## Unités d'exécution tracées

| Unité | Span racine | Spans enfants | Fin réussie | Fin en erreur |
|---|---|---|---|---|
| | | | | |

## Propagation et export

| Sujet | Décision |
|---|---|
| Propagation | W3C Trace Context |
| Exporteur | |
| Endpoint OTLP | |
| Sampling normal | |
| Sampling diagnostic | `parentbased_always_on` |

## Logs

| Sujet | Décision |
|---|---|
| Variable applicative | `APP_LOG_LEVEL` ou équivalent |
| Développement/test | `debug` |
| Production | `info` |
| Troubleshooting | `trace` temporaire |
| Corrélation | `trace_id`, `span_id` |
| Flux d'audit | séparé si applicable |

> Ne pas utiliser `OTEL_LOG_LEVEL` comme seuil des logs applicatifs.

## Ressources OpenTelemetry

```text
OTEL_SERVICE_NAME=
OTEL_RESOURCE_ATTRIBUTES=service.version=<version>,deployment.environment.name=<environnement>
OTEL_TRACES_EXPORTER=
OTEL_LOGS_EXPORTER=
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_TRACES_SAMPLER=
OTEL_TRACES_SAMPLER_ARG=
```

## Données et sécurité

- Données interdites :
- Redaction :
- Accès :
- Rétention :
- Protection contre l'altération :

## Résilience et coût

- Comportement si le backend est indisponible :
- Détection des pertes de télémétrie :
- Volume et coût attendus :

## Métriques, SLO et alertes

> Obligatoire pour `critique`, sinon seulement si utile.

| SLI | SLO | Alerte | Dashboard |
|---|---|---|---|
| | | | |

## Runbooks et validation

- Runbooks :
- Tests du contrat :
- Exercice de panne :
