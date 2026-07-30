# Assurance, complexité et documentation proportionnée

À lire pour migrer un état, classer le projet en phase 2, préparer le backlog ou
ouvrir une itération.

## Sommaire

- [Classer sans interroger techniquement](#classer-sans-interroger-techniquement)
- [Niveaux d'assurance](#niveaux-dassurance)
- [Déclencheurs de complexité](#déclencheurs-de-complexité)
- [Artefacts attendus](#artefacts-attendus)
- [Migration d'un projet existant](#migration-dun-projet-existant)

## Classer sans interroger techniquement

Déduire d'abord le niveau à partir de l'objectif, du code, des données et du
contexte déjà connus. Ne demander que les faits métier manquants qui pourraient
faire monter le niveau. Ne jamais demander « quel niveau d'assurance veux-tu ? ».

Questions possibles, en langage courant :

- Qu'arrive-t-il concrètement si le résultat est faux ?
- Les données concernent-elles d'autres personnes ?
- Une erreur peut-elle avoir une conséquence financière, juridique ou humaine ?
- Combien de temps le produit peut-il être indisponible sans conséquence grave ?

L'agent propose le classement, en donne les motifs et laisse l'utilisateur
signaler un fait erroné. Le niveau le plus élevé déclenché l'emporte.

## Niveaux d'assurance

### `essentiel`

Choisir si l'usage est personnel ou local, les conséquences sont réversibles,
les données non sensibles et la dépendance extérieure faible.

Exiger :

- parcours principal et erreurs essentielles testés ;
- tracing local de bout en bout ;
- documents cœur courts ;
- architecture, observabilité et tests résumés dans les spécifications.

### `renforce`

Choisir dès qu'un produit est partagé ou public, dépend d'un service extérieur,
traite les données de tiers ou entraîne un impact financier, opérationnel ou
réputationnel modéré.

Ajouter selon le besoin :

- architecture explicite et diagrammes utiles ;
- ADR pour les décisions significatives ;
- cas d'erreur et accès non autorisés ;
- stratégie et rapport de tests ;
- observabilité distribuée et runbooks des défaillances majeures.

### `critique`

Choisir en présence de réglementation, données sensibles, décisions touchant
l'argent ou les droits de personnes, conséquence juridique ou humaine,
opération irréversible ou forte exigence de disponibilité.

Ajouter :

- traçabilité exigences-décisions-tests-preuves ;
- modèle de menace, audit et contrôles d'intégrité ;
- SLI/SLO, reprise et runbooks ;
- cas limites, sécurité, résilience et exercices de panne ;
- rapports de tests et de diagnostic conservés.

## Déclencheurs de complexité

La complexité peut imposer un artefact sans augmenter la criticité :

| Fait observé | Artefact ou pratique déclenché |
|---|---|
| Plusieurs processus ou services | tracing distribué et diagramme de conteneurs |
| Messages, files ou tâches asynchrones | propagation du contexte et schéma du flux |
| API exposée | contrat d'API et tests de compatibilité |
| Données persistantes significatives | modèle de données et stratégie de migration |
| Interface utilisateur significative | parcours, design utile et accessibilité applicable |
| Boucle à haute fréquence | métriques/événements agrégés, pas un span par itération |

Ne créer aucun artefact si son contenu tient clairement dans une section du
document cœur et reste lisible.

## Artefacts attendus

Toujours maintenir :

- `docs/index.md` ;
- `docs/objectif.md` ;
- `docs/spec-nf.md` ;
- `docs/spec-fonctionnelle.md` ;
- `docs/feedback.md` à partir de la phase 5.

Pour `essentiel`, garder dans les documents cœur les sections architecture,
observabilité, stratégie de tests et résultats.

Pour `renforce`, créer seulement si applicables :

- `docs/architecture.md` ;
- `docs/decisions/ADR-<NNNN>-<titre>.md` ;
- `docs/observabilite.md` ;
- `docs/qualite/strategie-tests.md` ;
- `docs/qualite/rapport-tests.md` ;
- `docs/runbooks/<incident>.md`.

Pour `critique`, ajouter :

- `docs/securite/modele-menaces.md` ;
- `docs/qualite/traceabilite.md` ;
- `docs/qualite/validation-observabilite.md` ;
- les runbooks, preuves de reprise et éléments d'audit applicables.

La phase 7 crée `docs/releases/v<N>.md`. Ne créer aucun dossier avant son
premier fichier utile.

## Migration d'un projet existant

Pour un état sans `schema_version: 2` :

1. ne pas changer `phase`, `iteration` ni `version` ;
2. lire les documents, manifestes et configurations avant toute question ;
3. remplir `assurance`, `complexite` et `observabilite` avec ce qui est établi ;
4. demander uniquement les faits métier manquants qui peuvent changer une gate ;
5. ajouter `schema_version: 2` et les `hypotheses_ouvertes` ;
6. créer `docs/index.md` et y classer les anciens `*-vN.md` comme historiques ;
7. créer ou mettre à jour un document canonique seulement quand sa phase est
   touchée, sans déplacer ni réécrire les anciens fichiers ;
8. produire un bilan d'écart ;
9. reprendre directement la phase enregistrée, sans retour au début du cycle.

Une lacune de sécurité, d'intégrité ou d'observabilité critique bloque la
prochaine release. Une lacune documentaire secondaire entre dans `DETTE.md` et
au backlog sans forcer un retour à la phase 0.
