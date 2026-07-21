# Attributions

Ce dépôt redistribue du code tiers sous licence MIT.

## `skills/shared/grill-me`

Dérivé des skills `grill-me` et `grilling` de
[mattpocock/skills](https://github.com/mattpocock/skills), sous licence MIT.

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Modifications apportées

- Fusion des deux skills amont : `grill-me` n'était en amont qu'un alias
  déléguant à `grilling`. La version d'ici est autonome.
- Retrait de `disable-model-invocation: true`, afin que d'autres skills — en
  particulier `std-dev-project` — puissent invoquer l'interrogation eux-mêmes.
- Ajout d'une section de cadrage, permettant à un skill appelant de moduler la
  profondeur et le rythme des questions selon le profil de l'utilisateur.
