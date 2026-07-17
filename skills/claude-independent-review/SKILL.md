---
name: claude-independent-review
description: Use Claude Code as a separate, read-only reviewer for code, architecture, security, design, or content, with filtered snapshots, immutable audit reports, Codex adjudication, resolution records, and user-confirmed counter-reviews. Use when the user asks for a Claude or second-model review, when configuring persistent review milestones for a project, or when an AGENTS.md pointer says a configured independent-review milestone has been reached.
---

# Revue indépendante Claude

Faire intervenir Claude uniquement comme contrôleur indépendant. Garder Codex responsable du cadrage, de l'arbitrage des constats et des corrections.

Résoudre `<skill-dir>` comme le dossier absolu contenant ce `SKILL.md`. Exécuter toujours le runner avec `python3 <skill-dir>/scripts/claude_review.py`, quel que soit le répertoire courant du projet.

## Choisir le parcours

- Si `.codex/claude-review.json` n'existe pas, suivre **Initialiser le projet**.
- Si l'utilisateur demande explicitement une revue, considérer cette revue initiale comme autorisée.
- Si un jalon configuré est atteint, annoncer mission, périmètre, angles et exclusions, puis lancer la revue sans redemander d'autorisation.
- Ne jamais lancer une contre-revue sans confirmation explicite. Une demande explicite de contre-revue vaut confirmation.
- Regrouper les jalons compatibles qui portent sur le même état.
- Limiter chaque revue à une seule racine de projet.

## Initialiser le projet

1. Inspecter le projet en lecture seule. Lire [references/configuration.md](references/configuration.md).
2. Proposer en un seul tableau : nom, langue, modèle exact, effort, sources de vérité, exclusions supplémentaires, seuils et jalons adaptés.
3. Utiliser par défaut `claude-sonnet-5`, `high`, `fr`, 20 minutes, 40 tours, `docs/reviews`, 20 000 fichiers et 262 144 000 octets.
4. Demander une validation groupée avant toute écriture.
5. Écrire la proposition JSON dans un fichier temporaire hors du projet, puis exécuter :

   `python3 <skill-dir>/scripts/claude_review.py install-policy --project <racine> --config <proposition.json>`

6. Supprimer le fichier de proposition temporaire. Vérifier la configuration avec `validate-config`.
7. Pour modifier une politique existante, présenter les différences, obtenir l'accord, puis utiliser `install-policy --replace`. Ne jamais modifier silencieusement modèle, effort, jalons ou sources de vérité.

Pour un ancien brouillon `schema_version: 0`, utiliser `python3 <skill-dir>/scripts/claude_review.py migrate-config --input <ancien> --output <nouveau>`, faire valider les différences, puis installer le nouveau fichier. Ne jamais migrer implicitement une politique de projet.

Le programme ne conserve dans le projet que la politique et le bloc délimité dans `AGENTS.md`. En cas de bloc incomplet ou de conflit d'instructions, arrêter et demander un arbitrage.

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
  [--test-evidence <sortie-brute>] \
  [--audit-context <rapport-ou-resolution>] \
  [--include <glob>]
```

Utiliser `--kind counter` pour une contre-revue. Le runner travaille dans un snapshot temporaire, n'expose à Claude que `Read`, `Glob` et `Grep`, et ne conserve aucun snapshot, log, cache ou artefact d'échec. Il imprime en JSON les chemins du rapport et des preuves créés.

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
