# Profil normatif léger 1.0

Dernière vérification : 2026-08-08.

Utiliser ces références comme vocabulaire, structure et aide à la couverture.
Ne jamais écrire « conforme » ou « certifié » sans audit formel indépendant.

## Conventions documentaires

- encoder les fichiers en UTF-8 et terminer les fichiers texte par une fin de
  ligne ;
- utiliser des chemins ASCII en `kebab-case`, des dates ISO 8601 et des
  empreintes SHA-256 en hexadécimal minuscule ;
- utiliser `draft`, `in-review`, `approved` ou `superseded` pour les statuts
  documentaires ;
- conserver les IDs après suppression logique et ne jamais renuméroter une
  exigence, un risque, une preuve ou une décision ;
- versionner les releases selon le schéma public du projet, SemVer 2.0.0 par
  défaut pour un produit compatible, et préciser dans `version` s'il s'agit de
  la release couverte ou de la révision propre au document ;
- employer `MUST`, `MUST NOT`, `SHOULD` et `MAY` seulement pour exprimer la
  force normative d'une exigence, selon BCP 14 ;
- référencer les standards sans en recopier le contenu protégé et épingler
  l'édition réellement utilisée.

| Référence | Usage dans le skill |
|---|---|
| [ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html) | processus du cycle logiciel |
| [ISO/IEC/IEEE 15289:2019](https://www.iso.org/standard/74909.html) | types et consolidation des informations de cycle de vie |
| [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) | exigences et traçabilité |
| [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | caractéristiques de qualité produit |
| [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) | description d'architecture lorsque nécessaire |
| [ISO/IEC/IEEE 29119-2:2021](https://www.iso.org/standard/79428.html) et [29119-3:2021](https://www.iso.org/standard/79429.html) | processus et preuves de test |
| [ISO 31000:2018](https://www.iso.org/standard/65694.html) | identification, traitement et suivi des risques |
| [ISO/IEC 27001:2022](https://www.iso.org/standard/27001.html), amendement 1:2024 | gestion des risques de sécurité de l'information |
| [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final) | pratiques de développement logiciel sécurisé |
| [W3C Trace Context](https://www.w3.org/TR/trace-context/) et [OpenTelemetry](https://opentelemetry.io/docs/specs/otel/) | propagation, traces, logs et métriques |

N'utiliser qu'une publication finale comme baseline. Par exemple, SSDF 1.2
reste un brouillon au 2026-08-08 ; le catalogue conserve donc SSDF 1.1.

Épingler ce profil dans `baseline.catalog_version`. Une future édition exige
une mise à jour du skill et une migration explicite du profil, jamais une
réinterprétation silencieuse d'une baseline approuvée.
