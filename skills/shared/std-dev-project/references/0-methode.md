# Méthode — règles transverses

À lire avant toute phase. Ces règles priment sur le contenu des fichiers de
phase en cas de contradiction.

## 1. Cadrer l'interrogation

Chaque phase marquée « interrogation » invoque le skill `grill-me`. **Jamais nu.**
Toujours avec un bloc de cadrage, construit à partir de `.sdp/etat.json` :

```
CADRAGE
profil : <profil.niveau_archi>, code lui-même : <profil.code>
max_questions_par_salve : <selon le profil, voir ci-dessous>
vocabulaire : <simple | technique>
sujets : <liste exhaustive fournie par le fichier de phase>
verrouille : <etat.verrouille — ne jamais rouvrir>
```

### Calibrage par profil

| `profil.code` | Salve max | Vocabulaire | Décisions techniques |
|---|:---:|---|---|
| `non` — ne code pas | 3 | simple, tout terme défini ou évité | **tranchées d'office**, présentées en conséquences concrètes : coût, délai, risque |
| `assiste` — code avec un agent | 4 | technique si expliqué en une ligne | proposées avec recommandation, l'utilisateur arbitre |
| `oui` — développeur confirmé | 4 | technique, sans glose | posées directement, sans pédagogie |

### Règles absolues

- **Toujours proposer une réponse recommandée.** Une question sans
  recommandation transfère à l'utilisateur une charge qui revient à l'agent.
- **Ne jamais poser une question dont la réponse dépasse le profil.** La
  trancher, dire qu'elle a été tranchée, expliquer pourquoi en une phrase. Un
  utilisateur noyé abandonne la méthode ; c'est le principal risque d'échec.
- **Ne pas déborder des `sujets`.** Ce qui appartient à une autre phase y sera
  traité. Le signaler et passer.
- **Ne jamais rouvrir un point `verrouille`.** S'il doit vraiment changer, cela
  relève d'une nouvelle itération, pas d'un retour en arrière.
- Une question de fait se cherche dans le projet, jamais auprès de l'utilisateur.

### Traduire une décision technique pour un profil `non`

Ne pas demander « PostgreSQL ou SQLite ? » mais :

> Deux façons de stocker tes données. L'une tient dans un simple fichier :
> gratuite, immédiate, mais un seul utilisateur à la fois. L'autre est un vrai
> serveur : quelques euros par mois, mais plusieurs utilisateurs simultanés.
> Vu que tu prévois de partager l'outil, je pars sur la seconde.

La décision est prise, la raison est dite, l'utilisateur peut objecter.

## 2. Gates et dérogations

L'ordre des phases est imposé. À toute demande de saut :

1. **Refuser d'abord.** Nommer le coût concret et spécifique du saut — pas une
   généralité sur les bonnes pratiques.
2. Si l'utilisateur insiste, **céder** — mais seulement en inscrivant la
   dérogation.
3. Écrire dans `DETTE.md` (créer depuis `templates/DETTE.md` si absent) et
   ajouter l'entrée à `etat.derogations`.
4. **La rappeler au début de chaque phase suivante**, en une ligne, jusqu'à ce
   qu'elle soit soldée.

Une dérogation se solde en revenant faire le travail sauté. La rayer alors dans
`DETTE.md` et retirer l'entrée de `etat.derogations`.

Formulation type du refus :

> Passer au développement sans spécification fonctionnelle m'obligerait à
> deviner le comportement attendu. Le risque concret : construire quelque chose
> que tu jetteras, et perdre plus de temps que la spécification n'en aurait
> pris. Je te recommande de ne pas sauter cette étape.
>
> Si tu veux quand même, je l'inscris dans `DETTE.md` et je te la rappellerai à
> chaque étape.

## 3. Terminer une phase

Une phase n'est terminée que si les quatre conditions sont réunies :

1. Le document de sortie existe et est complet.
2. L'utilisateur l'a **explicitement validé** — pas un silence, pas un « ok »
   ambigu sur autre chose.
3. `.sdp/etat.json` est à jour : `phase`, `phase_nom`, `verrouille`, `maj`.
4. Le tout est commité.

Ne jamais annoncer une phase terminée si l'une manque.

## 4. Git

**Commit local : automatique.** À la fin de chaque phase, sans demander.

```
docs(sdp): <phase> v<N> — <résumé court>
```

**Push : jamais sans confirmation explicite, à chaque fois.** Pousser publie du
contenu hors de la machine, y compris vers un dépôt privé. Présenter d'abord ce
qui part :

> Commit local créé : « docs(sdp): objectif v1 ».
> Prêt à pousser vers `origin/main` (dépôt privé `<nom>`). Je pousse ?

Avant tout `git add` large, vérifier ce qui est inclus avec `git status`. En cas
de fichier suspect — même au nom anodin — en lire le contenu avant de committer.

Ne jamais exécuter de commande destructive (`reset`, `checkout` écrasant,
`clean`, suppression) sans avoir vérifié `git status` et mis à l'abri le travail
non commité.

## 5. Documents et versionnage

Tout vit dans `docs/` à la racine du projet guidé :

```
docs/objectif-v1.md   spec-nf-v1.md   spec-fonctionnelle-v1.md   feedback-v1.md
```

- **Ne jamais réécrire un document en place** d'une itération à l'autre.
  L'itération N+1 crée `-vN+1`.
- Un document `-vN+1` est un **diff ciblé** : il ne reprend que ce qui change et
  renvoie explicitement à `-vN` pour le reste. Ne pas recopier l'inchangé.
- `DETTE.md` et `.sdp/etat.json` sont les deux seuls fichiers modifiés en place.

## 6. État

`.sdp/etat.json`, versionné avec le reste.

```json
{
  "version": "v1",
  "phase": 3,
  "phase_nom": "spec-fonctionnelle",
  "iteration": 1,
  "profil": { "code": "non", "discipline_process": "faible", "niveau_archi": "debutant" },
  "type_projet": "web",
  "origine": "neuf",
  "verrouille": ["objectif", "spec-nf"],
  "derogations": [],
  "dernier_commit": "a3f9c1e",
  "maj": "2026-07-21"
}
```

- `profil` est établi une seule fois en phase 0 et **n'est plus jamais
  réinterrogé**.
- `verrouille` liste les décisions actées. Une entrée y figure dès que son
  document est validé.
- `origine` vaut `neuf` ou `archeologie`.
- Écrire les dates en absolu, jamais en relatif.

## 7. Neutralité de plateforme

Ce skill tourne sur plusieurs agents. Dans tout échange avec l'utilisateur et
dans tout document produit :

- dire « l'agent », jamais le nom d'un modèle ou d'un produit ;
- ne nommer aucun outil propre à une plateforme ;
- ne rien supposer d'autre que la présence du skill `grill-me`, de `git` et,
  pour les phases qui en dépendent, de `gh`.
