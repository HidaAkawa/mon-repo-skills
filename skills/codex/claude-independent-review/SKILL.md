---
name: claude-independent-review
description: Use Claude Code as a separate, read-only reviewer for code, architecture, security, design, or content, with filtered snapshots, immutable audit reports, Codex adjudication, resolution records, user-confirmed counter-reviews, and project-level disabling that preserves prior audits. Use when the user asks for a Claude or second-model review, when configuring or disabling persistent review milestones for a project, or when an AGENTS.md pointer says a configured independent-review milestone has been reached.
---

# Revue indépendante Claude

Faire intervenir Claude uniquement comme contrôleur indépendant. Garder Codex responsable du cadrage, de l'arbitrage des constats et des corrections.

Résoudre `<skill-dir>` comme le dossier absolu contenant ce `SKILL.md`. Exécuter toujours le runner avec `python3 <skill-dir>/scripts/claude_review.py`, quel que soit le répertoire courant du projet.

## Choisir le parcours

- Si l'utilisateur demande de désactiver le skill dans le projet, suivre **Désactiver dans le projet** avant de considérer l'absence éventuelle de politique.
- Si `.codex/claude-review.json` n'existe pas, suivre **Initialiser le projet**.
- Si l'utilisateur demande explicitement une revue, considérer cette revue initiale comme autorisée.
- Si un jalon configuré est atteint, annoncer mission, périmètre, angles et exclusions, puis lancer la revue sans redemander d'autorisation.
- Ne jamais lancer une contre-revue sans confirmation explicite. Une demande explicite de contre-revue vaut confirmation.
- Regrouper les jalons compatibles qui portent sur le même état.
- Limiter chaque revue à une seule racine de projet.

## Initialiser le projet

1. Lire [references/configuration.md](references/configuration.md). Demander immédiatement et de manière bloquante le modèle Claude à enregistrer, avant toute autre question de configuration. Utiliser le sélecteur natif de l'environnement et le catalogue versionné de la référence. Si le sélecteur ne peut pas présenter les quatre modèles et une saisie libre, proposer d'abord `claude-sonnet-5`, `claude-opus-4-8` et « autres options », puis proposer `claude-fable-5`, `claude-haiku-4-5-20251001` et la saisie d'un identifiant exact. Recommander `claude-sonnet-5`, mais ne jamais le choisir sans réponse.
2. Ne pas redemander le modèle lorsqu'une politique existe déjà. Pour le modifier, suivre le parcours de remplacement explicite décrit plus bas.
3. Inspecter le projet en lecture seule.
4. Proposer en un seul tableau : nom, langue, modèle exact choisi, effort, sources de vérité, exclusions supplémentaires, seuils et jalons adaptés.
5. Utiliser par défaut `high`, `fr`, 20 minutes, 40 tours, `docs/reviews`, 20 000 fichiers et 262 144 000 octets.
6. Demander une validation groupée avant toute écriture.
7. Écrire la proposition JSON dans un fichier temporaire hors du projet, puis exécuter :

   `python3 <skill-dir>/scripts/claude_review.py install-policy --project <racine> --config <proposition.json>`

8. Supprimer le fichier de proposition temporaire. Vérifier la configuration avec `validate-config`.
9. Pour modifier une politique existante, présenter les différences, obtenir l'accord, puis utiliser `install-policy --replace`. Ne jamais modifier silencieusement modèle, effort, jalons ou sources de vérité.

Pour un ancien brouillon `schema_version: 0`, utiliser `python3 <skill-dir>/scripts/claude_review.py migrate-config --input <ancien> --output <nouveau>`, faire valider les différences, puis installer le nouveau fichier. Ne jamais migrer implicitement une politique de projet.

Le programme ne conserve dans le projet que la politique et le bloc délimité dans `AGENTS.md`. En cas de bloc incomplet ou de conflit d'instructions, arrêter et demander un arbitrage.

## Désactiver dans le projet

1. Expliquer que la désactivation retire uniquement `.codex/claude-review.json` et le bloc délimité `claude-independent-review` dans le `AGENTS.md` racine. Préciser que tous les rapports, résolutions et dossiers de preuves restent en place.
2. Une demande explicite de désactivation autorise ces deux retraits. Sinon, obtenir une confirmation avant toute écriture.
3. Exécuter :

   `python3 <skill-dir>/scripts/claude_review.py disable-policy --project <racine>`

4. Vérifier le résultat JSON : `disabled` indique qu'au moins un élément d'intégration a été retiré ; `already_disabled` indique qu'il n'en restait aucun. Dans les deux cas, `reports_preserved` doit valoir `true`.
5. Ne jamais supprimer, déplacer ni modifier le répertoire de rapports pendant ce parcours, même s'il devient orphelin de sa politique. Traiter toute demande de suppression des audits comme une action distincte exigeant une autorisation explicite.

La commande est idempotente. Elle refuse un bloc `AGENTS.md` incomplet ou dupliqué avant de retirer la politique et restaure l'état initial si l'une des opérations échoue. Une réactivation ultérieure suit **Initialiser le projet** et ne remplace pas les audits conservés.

## Préparer une revue

1. Exécuter `python3 <skill-dir>/scripts/claude_review.py doctor` puis le même runner avec `validate-config --project <racine>`.
2. Formuler une mission neutre : objectif, résultat attendu, périmètre, angles de revue, critères, exclusions et preuves de tests déjà obtenues. Ne pas révéler les conclusions de Codex ni un défaut attendu lors d'une revue générale.
3. Pour une contre-revue, résumer la mission à l'utilisateur et obtenir sa confirmation. Inclure ensuite le rapport précédent et sa résolution avec `--audit-context`.
4. Utiliser `--include` uniquement après validation de l'utilisateur lorsque le snapshot dépasse les seuils. Ne jamais tronquer automatiquement.

## Lancer la revue

Passer la mission en UTF-8 par fichier temporaire hors du projet ou par entrée standard :

```text
python3 <skill-dir>/scripts/claude_review.py review \
  --project <racine> \
  --mission-file <mission-ou-> \
  --review-type code \
  --milestone <identifiant> \
  --progress \
  [--test-evidence <sortie-brute>] \
  [--audit-context <rapport-ou-resolution>] \
  [--include <glob>]
```

Utiliser `--kind counter` pour une contre-revue. Passer toujours `--progress` lorsque le skill lance une revue. Le runner émet alors sur `stderr` une progression JSONL expurgée avec les phases, la durée, les tours, les outils de lecture et un battement toutes les 15 secondes ; ne pas interpréter ces lignes comme le rapport. Il réserve `stdout` au résultat JSON final.

Le runner travaille dans un snapshot temporaire, n'expose à Claude que `Read`, `Glob` et `Grep`, et ne conserve aucun snapshot, log, cache ou artefact d'échec. Après une interruption contrôlée, expliquer l'erreur à partir de la dernière phase visible. Un arrêt non interceptable comme `SIGKILL` ne peut révéler que le dernier événement déjà émis.

## Arbitrer et résoudre

1. Lire le rapport original sans le modifier.
2. Vérifier chaque constat contre ses preuves et l'état courant. Classer : retenu, rejeté, déjà résolu ou devenu obsolète.
3. Corriger les P0 à P2 retenus si la correction est réversible, déjà autorisée et sans décision produit. Demander l'utilisateur dans les autres cas.
4. Corriger un P3 seulement s'il est local, simple, sans dépendance, migration, API publique ni extension fonctionnelle.
5. Exécuter les vérifications pertinentes avec les outils de Codex ; Claude n'exécute aucune commande. Préférer les options sans cache ni artefact, inventorier l'état avant le contrôle et supprimer seulement les fichiers jetables dont la création par cette passe est certaine. Ne jamais supprimer un cache ou un build préexistant.
6. Créer un fichier de résolution distinct seulement s'il existe des constats à arbitrer ou traiter. Référencer le rapport, les décisions, les corrections et les contrôles. Ne jamais réécrire le rapport Claude.
7. Proposer une contre-revue ciblée sur les correctifs et leurs régressions directes. Attendre une confirmation explicite avant chaque nouvelle passe.

Ne jamais committer, pousser ou publier les artefacts d'audit sans demande distincte.

## Ressources

- Lire [references/configuration.md](references/configuration.md) lors d'une initialisation, d'une migration ou d'un diagnostic de configuration.
- Le runner charge automatiquement [references/reviewer-mandate.md](references/reviewer-mandate.md) ; ne pas recopier ce mandat dans la mission.
- Utiliser `scripts/claude_review.py` pour toute invocation Claude afin de préserver les verrous et l'hygiène des projets.
