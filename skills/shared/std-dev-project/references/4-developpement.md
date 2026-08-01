# Phase 4 — Développement

**Interrogation : non.** L'agent implémente, l'utilisateur essaie et valide.
Lire `0-observabilite.md`.

## Le contrat

Construire uniquement ce qui découle des spécifications validées.

Si une question n'y est pas tranchée :

- détail d'implémentation sans conséquence visible : trancher et journaliser ;
- changement de comportement : obtenir la réponse métier et corriger la
  spécification avant le code.

## Conduite

Découper les tâches par fonctionnalité du MVP, en traversant les couches tôt.
Développer fonctionnalité, tests et instrumentation dans le même lot. Ne pas
remettre logging et tracing à la fin.

Après chaque tâche, créer un commit local qui référence la fonctionnalité.

Pour `profil.code: non`, expliquer le résultat en une ligne de produit, jamais
en jargon de code.

## Tests

Écrire les cas dérivés en phase 3 au niveau de garantie requis fixé en phase 2.
Un test sans critère révèle une spécification à compléter.

Tester aussi le contrat d'observabilité :

- trace racine et spans utiles ;
- logs avec `trace_id` et `span_id` ;
- seuil modifiable par `APP_LOG_LEVEL` ou son équivalent ;
- absence de secret, token ou donnée interdite ;
- opération métier préservée si l'export de télémétrie échoue.

## Gates de sortie

Exécuter les tests applicables et montrer leur sortie réelle. Exécuter une unité
significative et montrer :

```
trace racine → spans enfants → logs corrélés
```

Ne jamais annoncer une gate verte sans exécution dans la session. Un échec se
corrige ; désactiver test ou instrumentation ne rend pas la release prête.

Pour un projet critique, exécuter également les contrôles de sécurité, audit,
intégrité et résilience prévus en phase 2.

## Journal et décisions

Maintenir `docs/journal-dev.md` depuis
[templates/journal-dev.md](../templates/journal-dev.md) : écarts entre
spécification et réalité, décisions prises et difficultés utiles aux phases 5
et 6.

Mettre à jour ADR et runbooks seulement lorsqu'une décision durable ou un mode
de défaillance significatif apparaît.

## Sortie de phase

1. Tests applicables verts, sortie affichée.
2. Trace complète et logs corrélés affichés.
3. Contrôles de données interdites et de configuration des logs verts.
4. Produit ouvert et essayé par l'utilisateur ; validation explicite.
5. Journal, index et état à jour ; passer `phase` à 5.
6. Commit : `feat: MVP v<N>`.
7. Proposer le push.

Puis [5-tests-feedback.md](5-tests-feedback.md).
