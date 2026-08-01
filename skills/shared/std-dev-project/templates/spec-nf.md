# <Projet> — Spécification non-fonctionnelle

> Statut : brouillon / approuvé
> Version du projet : v<N>
> Propriétaire : <personne ou équipe>
> Dernière revue : <date absolue>
> Niveau de garantie requis : essentiel / renforce / critique

## Classement

| Axe | Décision | Motifs |
|---|---|---|
| Niveau de garantie requis | | |
| Complexité | | |
| Observabilité | local / distribue / operationnel | |

**Réévaluer si :** <changement de données, utilisateurs, réglementation,
architecture ou conséquence d'une erreur>.

## Déploiement et architecture

| Sujet | Décision | Pourquoi |
|---|---|---|
| Où ça tourne | | |
| Qui y accède | | |
| Composants | | |
| Coût mensuel estimé | | |

> Pour un projet renforcé ou critique, renvoyer à `architecture.md` si cette
> section ne suffit plus.

## Technique

| Sujet | Décision | Pourquoi |
|---|---|---|
| Langage | | |
| Framework | | |
| Stockage | | |
| Framework de test | | |

## Données

| Sujet | Décision | Pourquoi |
|---|---|---|
| Nature et propriétaire | | |
| Données personnelles/sensibles | | |
| Conservation | | |
| Sauvegarde et restauration | | |

## Sécurité

| Sujet | Décision | Pourquoi |
|---|---|---|
| Authentification et autorisation | | |
| Secrets | | |
| Confidentialité des échanges | | |
| Audit applicable | | |

## Tests

**Profondeur :** essentiel / renforce / critique

<Types de tests, erreurs et gates. Renvoyer à
`qualite/strategie-tests.md` seulement si nécessaire.>

## Observabilité

| Sujet | Décision |
|---|---|
| Unité d'exécution tracée | |
| Span racine et frontières enfant | |
| Export | console / fichier / OTLP |
| Niveau de logs | `APP_LOG_LEVEL` ou équivalent |
| Défaut développement/test | `debug` |
| Défaut production | `info` |
| Sampling | |
| Données interdites | |
| Panne du backend | métier non bloqué |

> `OTEL_LOG_LEVEL` ne règle que les diagnostics internes du SDK. Pour un projet
> renforcé ou critique, renvoyer à `observabilite.md`.

## Charge et disponibilité

<Utilisateurs, volumes, performance et indisponibilité acceptable.>

## Décisions prises par l'agent

| Décision | Raison | Conséquence métier |
|---|---|---|
| | | |

## Hypothèses ouvertes

| ID | Décision provisoire | Raison | Impact | Confiance | Validation attendue |
|---|---|---|---|---|---|
| | | | | | |
