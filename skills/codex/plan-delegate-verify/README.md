# `plan-delegate-verify`

**Compatibilité : Codex uniquement.** Aucun prérequis externe : le skill utilise
les outils de collaboration multi-agent fournis par Codex lorsqu'ils sont
disponibles dans la session.

Orchestre les travaux substantiels et décomposables selon une boucle persistante :
évaluer le travail restant, planifier un horizon borné, déléguer des lots à des
agents calibrés, vérifier les résultats, intégrer les preuves puis replanifier
jusqu'à la résolution de l'objectif global.

## Utilisation

Le skill ne se déclenche que sur une demande explicite d'orchestration
multi-agent, par exemple :

```text
Planifie, délègue et vérifie cette migration avec des sous-agents.
```

```text
Utilise des agents en parallèle pour réaliser cette tâche et vérifier le résultat.
```

L'activation doit être explicite. Une fois déclenché, le skill reste actif après
chaque vague, jalon ou compaction de contexte jusqu'à ce que l'objectif soit
`DONE`, `BLOCKED`, `CANCELLED` ou redirigé par l'utilisateur.

## Workflow

1. **Évaluer** — comparer l'objectif global aux progrès déjà vérifiés.
2. **Planifier** — définir le prochain horizon utile et ses critères observables.
3. **Router** — choisir par lot le modèle et l'effort minimisant le coût total
   attendu.
4. **Déléguer** — exécuter en vagues les lots indépendants, dans la limite de la
   capacité réelle.
5. **Vérifier** — contrôler chaque résultat sur des preuves déterministes, puis
   sémantiques lorsque nécessaire.
6. **Intégrer et replanifier** — mettre à jour l'état vérifié et recommencer tant
   que tous les critères globaux ne sont pas satisfaits.

Chaque lot précise sa mission, ses entrées, son périmètre d'écriture, ses
critères de fin, ses dépendances, son routage et son niveau de risque. Deux
agents ne modifient jamais simultanément les mêmes fichiers.

## Budget, routage et télémétrie

Les budgets de tours d'agents sont définis par cycle, afin qu'un objectif long ne
retombe pas silencieusement en exécution locale après une première vague. Le
skill privilégie le coût total attendu — exécution, vérification, risque de
reprise et conséquence d'une erreur non détectée — plutôt que le modèle le moins
cher à chaque appel.

Il ne contient aucun identifiant de modèle figé. Les modèles, niveaux d'effort
et limites de concurrence sont découverts dans le contrat d'outils actif. Une
capacité absente ou impossible à classer est héritée de la session et signalée.

Le script `scripts/telemetry.py` enregistre hors du dépôt les rôles, modèles,
niveaux d'effort, reprises et escalades. Son rapport final permet de détecter le
sous-routage, le sur-routage ou un abandon progressif de la délégation. Les
tokens et crédits ne sont consignés que si la plateforme les expose réellement.

## Garanties

- Aucun agent ne remplace la responsabilité de l'orchestrateur.
- Toute vague matérielle est suivie d'une vérification et d'une replanification.
- Les prompts délégués sont autonomes et bornent précisément les écritures.
- Les résultats sont vérifiés critère par critère avec `PASS`, `FAIL` ou
  `BLOCKED`.
- Les reprises sont ciblées, diagnostiquées et limitées à deux par lot.
- Les échecs sont classés avant toute hausse de modèle ou d'effort.
- Aucun résultat n'est déclaré terminé tant qu'un critère requis reste non
  vérifié ou bloqué sans explication.

## Contenu

```text
plan-delegate-verify/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── routing.md
│   ├── telemetry.md
│   └── verification.md
└── scripts/
    └── telemetry.py
```
