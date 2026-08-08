# Baselines automatiques

Appliquer une baseline sans demander à l'utilisateur de la remplir. Composer
un socle de garantie et un overlay d'archétype ; leur produit couvre les
21 combinaisons. L'ID est `BL-<ARCHETYPE>-<GUARANTEE>-v1`.

## Sommaire

- [Sélection](#sélection)
- [Socles de garantie](#socles-de-garantie)
- [Overlays d'archétype](#overlays-darchétype)
- [Exigences générées](#exigences-générées)

## Sélection

Le niveau le plus élevé déclenché l'emporte :

- `standard` : usage personnel/local, conséquences réversibles, données non
  sensibles ;
- `elevated` : produit partagé ou public, comptes, données de tiers,
  dépendance externe ou impact financier/opérationnel modéré ;
- `critical` : réglementation, données sensibles, argent ou droits de tiers,
  conséquence juridique/humaine, irréversibilité ou disponibilité forte.

Une incertitude touchant données, argent, droits, légalité ou sécurité fait
monter provisoirement d'un niveau. Une valeur par défaut est une hypothèse de
départ traçable, pas une promesse universelle.

Pour un produit hybride, sélectionner l'archétype de l'interface ou de l'unité
de travail dont le budget caractérise le mieux l'expérience principale, puis
ajouter les contrôles de tous les autres overlays applicables. Ne jamais
moyenner deux budgets ni retirer un contrôle lors de cette composition.

## Socles de garantie

| Domaine | `standard` | `elevated` | `critical` |
|---|---|---|---|
| Sécurité | secrets hors code/logs, dépendances verrouillées, validation aux frontières, moindre privilège, erreurs assainies | précédent + authentification/autorisation explicites, TLS, chiffrement des données sensibles, rate limiting, scan secrets/SCA/SAST, SBOM, sauvegarde et restauration testée | précédent + classification des données, modèle de menace, séparation des rôles, rotation des clés, provenance/signature des artefacts, DAST ou test d'intrusion applicable, exercice de reprise et audit inviolable |
| Vulnérabilités | bloquer une vulnérabilité critique exploitable ; accepter explicitement les autres risques élevés | bloquer critiques et élevées ; évaluer les moyennes | bloquer critiques et élevées ; toute moyenne exige propriétaire, traitement et échéance avant release |
| Tests | chaque critère d'acceptation, parcours nominal et erreurs essentielles | précédent + erreurs, accès interdits, dépendances et restauration | précédent + limites, sécurité, résilience, reprise et preuves conservées |
| Performance | mesurer le budget d'archétype ; signaler une régression > 20 % | bloquer une régression > 10 % | bloquer une régression > 5 % et tester charge/dégradation |
| Observabilité | OpenTelemetry local, une trace par unité significative, logs avec `trace_id`/`span_id`, `debug` en dev et `info` en production | propagation W3C, OTLP, métriques latence/erreur/saturation, health check, alertes et rétention définie | précédent + SLI/SLO, audit séparé, dashboards, exercice de panne, temps de diagnostic et coût contrôlé |
| Revue | finale ; conception si sensibilité ou nouveauté | conception + finale, 3 contre-revues maximum | conception + finale, 4 contre-revues maximum |

Le niveau `standard` autorise 2 contre-revues maximum. L'export de télémétrie
est toujours asynchrone et borné. Ne jamais émettre mot de passe, secret,
token, cookie de session ou donnée personnelle inutile.

## Protocole initial de mesure et d'exploitation

Ces valeurs évitent une nouvelle question technique ; une contrainte métier
connue les remplace et devient la source de l'exigence.

| Élément | `standard` | `elevated` | `critical` |
|---|---|---|---|
| Performance interactive | build release local, 5 échauffements puis au moins 30 mesures et 5 min à 1 utilisateur simultané | environnement proche production, 10 min à au moins 20 utilisateurs simultanés ou au pic attendu s'il est supérieur | 30 min à au moins 50 utilisateurs simultanés ou 1,5 × le pic attendu s'il est supérieur, plus montée, dégradation et récupération |
| Batch/library | 1 000 éléments/opérations, un worker et 5 exécutions | 10 000 éléments/opérations, 4 workers ou le volume attendu s'il est supérieur, pendant 10 min minimum | 100 000 éléments/opérations, 8 workers ou 1,5 × volume/concurrence attendus s'ils sont supérieurs, avec reprise et saturation contrôlées |
| Disponibilité | fenêtre glissante de 30 jours, toute indisponibilité visible comptée | même fenêtre, mesure synthétique depuis le parcours principal | SLI contractuel et budgets d'erreur sur 30 jours, sauf règle métier plus stricte |
| Rétention télémétrie | 7 jours en local, sans donnée sensible | 14 jours dans le backend approuvé | 30 jours opérationnels ; audit selon obligation métier, stockage séparé et accès contrôlé |
| Alertes | aucune astreinte par défaut ; échec visible localement | erreur > 5 % sur 5 min, latence > 2 × budget sur 10 min ou saturation > 85 % sur 15 min | burn rate SLO > 14,4 × sur 1 h confirmé sur 5 min, ou > 6 × sur 6 h confirmé sur 30 min ; plus perte d'audit ou de télémétrie |

Documenter charge, environnement, jeu de données, échauffement, durée, nombre
d'échantillons et outil dans l'évidence. Pour un profil `guided`, appliquer le
protocole sans lui demander de sélectionner un outil. Une rétention supérieure
exige d'expliquer coût, accès et exposition des données.

La cible de disponibilité sur 30 jours est un objectif opérationnel, pas une
attente de 30 jours avant la première release. Avant livraison d'un produit
neuf, vérifier le calcul du SLI, la collecte, les alertes, une panne sûre et un
soak test de 30 minutes ; enregistrer l'absence d'historique comme `ASM-###`.
Mesurer la fenêtre réelle après mise en service et fermer l'hypothèse lors de
l'itération suivante. Pour un produit critique qui exige un historique avant
exposition, utiliser un pilote ou une montée en charge progressive.

## Overlays d'archétype

Chaque triplet indique `standard / elevated / critical`.

| Archétype | Budget initial | Contrôles et instrumentation spécifiques |
|---|---|---|
| `web` | réponse serveur p95 `1000 / 500 / 250 ms`; disponibilité `99.5 / 99.9 / 99.95 %` | test du parcours principal dans un navigateur, accessibilité applicable, erreurs frontend corrélées au backend, headers et cookies sûrs |
| `api` | opération interactive p95 `1000 / 500 / 250 ms`; erreurs `2 / 1 / 0.1 %` | contrat versionné, tests de compatibilité, authN/authZ, quotas, trace par requête et appels sortants |
| `mobile` | démarrage à chaud p95 `3000 / 2000 / 1000 ms`; sessions sans crash `99 / 99.5 / 99.9 %` | stockage local protégé, réseau dégradé, synchronisation/retry, spans lancement–action–backend |
| `cli` | démarrage p95 `2000 / 1000 / 500 ms`; commande interactive p95 `5 / 2 / 1 s` | codes de sortie, stdout/stderr stables, absence de secret dans l'historique, trace par commande |
| `library` | régression benchmark `20 / 10 / 5 %` maximum | API publique versionnée, matrice de compatibilité, tests de contrat et provenance du paquet |
| `batch` | fin avant la fenêtre avec marge `10 / 20 / 30 %` | idempotence, reprise, checkpoint, dead-letter applicable, trace par lot et métriques de débit/rejets |
| `distributed` | parcours p95 `2000 / 1000 / 500 ms`; disponibilité `99.5 / 99.9 / 99.95 %` | propagation W3C à chaque frontière, corrélation messages/tâches, timeouts, retries bornés, circuit breaker applicable |

Si une opération est volontairement longue, remplacer son budget interactif
par une échéance métier et un retour de progression. Ne jamais fausser une gate
en excluant silencieusement une opération lente.

## Exigences générées

Créer automatiquement :

- `SWR-SEC-###` pour chaque contrôle de sécurité applicable ;
- `SWR-QUA-###` pour disponibilité, performance, compatibilité, accessibilité et
  résilience ;
- `SWR-OBS-###` pour traces, logs, métriques, données interdites et diagnostic ;
- `AC-###`, `TST-###` et `EVD-###` liés à chaque exigence.

Chaque exigence indique `source: baseline`, le profil complet, la raison, la
valeur initiale et la condition de révision. Résumer à un profil `guided` les
conséquences concrètes : coût mensuel estimé, effort supplémentaire, données
conservées et contrainte d'exploitation. Ne jamais lui demander de choisir un
framework de test, un sampler ou un format de logs.
