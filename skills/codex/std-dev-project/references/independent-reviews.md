# Revues indépendantes

Garder l'agent principal responsable de la mission, de l'arbitrage, des
corrections et des tests. Le reviewer reste en lecture seule.

## Choisir le parcours

1. Si le skill `claude-independent-review` est disponible **et**
   `.codex/claude-review.json` existe, choisir `reviews.mode: claude` et suivre
   ce skill, seulement si `reports.directory` vaut `docs/reviews`. Déclarer
   dans l'état v4 le même ID que le jalon applicable de la
   politique. Si aucun jalon configuré ne couvre la revue requise, ne pas
   modifier la politique silencieusement : utiliser le prompt externe pour
   cette version et enregistrer `reviews.mode: external-prompt`.
2. Sinon choisir `external-prompt`. Ne jamais initialiser silencieusement une
   politique Claude : produire le prompt portable ci-dessous.

Dans les deux cas, ajouter `/docs/reviews/` au `.gitignore`. Si
`git ls-files -- docs/reviews` retourne des fichiers, avertir et ne jamais les
désindexer sans confirmation. Ne pas retirer cette règle lors d'une
désactivation.

## Jalons et budget

| Garantie | Conception | Vérification | Contre-revues max/version |
|---|---|---|---:|
| `standard` | si données sensibles, technologie nouvelle ou risque inhabituel | obligatoire | 2 |
| `elevated` | obligatoire | obligatoire | 3 |
| `critical` | obligatoire | obligatoire | 4 |

L'autorisation est bornée à `reviews.authorization.version`. Une contre-revue
réussie consomme le budget après la persistance de son rapport. Une tentative
technique échouée ne le consomme pas. Arrêter dès qu'aucun P0–P2 retenu ne
reste ouvert. Si le budget est épuisé, maintenir la gate en échec.

L'autorisation v4 remplace la confirmation ponctuelle seulement lorsque :

- `schema_version` vaut 4 ;
- `authorization.source` vaut `std-dev-project-v4` ;
- `authorization.granted` vaut `true` ;
- la version autorisée égale `delivery.working_version` ;
- le jalon est déclaré dans `reviews.milestones` ;
- `used < maximum`.

En dehors de ce cadre, le skill de revue conserve sa confirmation autonome.
Lorsqu'une nouvelle version de travail commence, fixer le nouveau budget,
remettre `used` à zéro et renouveler explicitement la version autorisée.

## Mission neutre

Créer `docs/reviews/<IR-ID>-request.md` :

```text
Tu réalises une revue indépendante en lecture seule.

Objectif : <résultat attendu>
Périmètre : <racine et chemins>
Angles : <architecture | sécurité | code | design | contenu>
Critères : <exigences et gates>
Exclusions : <hors périmètre>
Preuves disponibles : <tests et commits>

Inspecte toi-même les fichiers utiles. Ne modifie rien et n'exécute aucune
commande destructive. Retourne un rapport Markdown avec verdict, constats
P0–P3, preuves précises, risques et contrôles manquants. Ne suppose pas que
l'implémentation ni les conclusions de l'agent principal sont correctes.
```

Pour une contre-revue, joindre le rapport précédent, la résolution et les
preuves de tests, puis limiter la mission aux correctifs et régressions directes.

## Arbitrer et conserver les preuves

Vérifier chaque constat contre le projet. Classer : retenu, rejeté, déjà
résolu, obsolète. Corriger automatiquement P0–P2 seulement si la correction est
réversible, autorisée et sans décision produit ; demander dans les autres cas.

Conserver sous `docs/reviews/` : demande, rapport immuable, résolution,
contre-revues et preuves. Enregistrer dans `docs/verification/<version>.md` :

- `IR-###` ;
- résultat final ;
- décision ;
- SHA-256 du rapport.

Conserver jalon, type, date, reviewer, compteurs, priorités et éventuelle
`archive_reference` non secrète dans `reviews.reports` de l'état v4, pas dans
le rapport de vérification.

Une revue externe obligatoire bloque la gate jusqu'au retour du rapport. Une
dérogation reste possible pour un risque non critique, avec autorité, motif,
échéance et risque résiduel. Elle est interdite si l'incertitude peut masquer un
risque critique ou illicite.

Le répertoire ignoré est la copie de travail. Pour `elevated` et `critical`,
archiver chaque rapport dans un stockage chiffré et contrôlé hors Git avant de
fermer sa gate ; utiliser l'espace de preuves de la forge s'il existe, sinon un
store d'audit approuvé hors du projet. Enregistrer seulement sa référence non
secrète dans `reviews.reports` et son SHA-256 dans les deux registres. Inscrire immédiatement une revue de conception dans le
registre « Independent reviews » du plan de développement ; inscrire la revue
finale dans le rapport de vérification. Pour `standard`, signaler qu'un clone
du dépôt ne restitue pas le rapport brut.
