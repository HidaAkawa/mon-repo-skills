# `plan-delegate-verify`

**Compatibilité : Codex uniquement.** Aucun prérequis externe : le skill utilise
les outils de collaboration multi-agent fournis par Codex lorsqu'ils sont
disponibles dans la session.

Orchestre les travaux substantiels et décomposables selon une boucle stricte :
planifier des lots vérifiables, les déléguer à des agents calibrés, puis
contrôler chaque résultat contre des preuves primaires.

## Utilisation

Le skill ne se déclenche que sur une demande explicite d'orchestration
multi-agent, par exemple :

```text
Planifie, délègue et vérifie cette migration avec des sous-agents.
```

```text
Utilise des agents en parallèle pour réaliser cette tâche et vérifier le résultat.
```

Une tâche courte, séquentielle ou trop couplée reste exécutée directement. Le
skill l'annonce au lieu de créer artificiellement des sous-tâches.

## Workflow

1. **Planifier** — résoudre les faits disponibles, définir les critères
   d'acceptation et découper le travail en un nombre minimal de lots autonomes.
2. **Déléguer** — choisir pour chaque lot un modèle et un niveau d'effort adaptés
   au coût d'un échec, puis exécuter les lots indépendants en parallèle dans la
   limite de la capacité réelle.
3. **Vérifier** — traiter les comptes rendus des agents comme des affirmations,
   contrôler chaque critère sur des preuves, et corriger uniquement les échecs
   démontrés.

Chaque lot précise sa mission, ses entrées, son périmètre d'écriture, ses
critères de fin, ses dépendances, son routage et son niveau de risque. Deux
agents ne modifient jamais simultanément les mêmes fichiers.

## Budget et routage

Le skill borne le nombre de tours d'agents selon la difficulté globale. Il
privilégie le coût total attendu — première exécution et risque de reprise —
plutôt que le modèle le moins cher à chaque appel.

Il ne contient aucun identifiant de modèle figé. Les modèles, niveaux d'effort
et limites de concurrence sont découverts dans le contrat d'outils actif. Une
capacité absente ou impossible à classer est héritée de la session et signalée
dans le plan.

## Garanties

- Aucun agent ne remplace la responsabilité de l'orchestrateur.
- Les prompts délégués sont autonomes et bornent précisément les écritures.
- Les résultats sont vérifiés critère par critère avec `PASS`, `FAIL` ou
  `BLOCKED`.
- Les reprises sont ciblées, diagnostiquées et limitées à deux par lot.
- Une vérification indépendante supplémentaire est réservée aux risques
  critiques ou aux preuves contradictoires.
- Aucun résultat n'est déclaré terminé tant qu'un critère requis reste non
  vérifié ou bloqué sans explication.

## Contenu

```text
plan-delegate-verify/
├── SKILL.md
├── README.md
└── agents/
    └── openai.yaml
```
