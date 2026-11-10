# Refonte v2 — suivi

Le fichier qu'une nouvelle session lit en premier. Il dit où on en est et quoi faire ensuite.
On le met à jour **à la fin de chaque tâche**, dans la PR de la tâche.

## Où on en est

- **Partie en cours** : P1 — Le socle neuf (P0 terminée)
- **Prochaine tâche** : R1.5 — Réglages en base
- **Dernière mise à jour** : 09/11/2026, R1.4

## Tâches

Statuts : `à faire` · `en cours` · `en revue` (PR ouverte) · `fait` (fusionnée) · `bloqué`.

| Tâche | Statut | PR | Note |
|---|---|---|---|
| R0.1 Cap, feuille de route, suivi | fait | #238 | |
| R0.2 Fiches d'inspiration | fait | #239 | synthèse validée, H et I repris (D296) |
| R0.3 Carte de la v1 à reprendre | fait | #240 | `reprise-v1.md` |
| R1.1 Squelette `next/` | fait | #241 | paquet `orion`, commande `orion --version`, job CI `v2` |
| R1.2 Journal | fait | #242 | `orion.core` : journal, événements, versions, fichiers privés |
| R1.3 Projections | fait | #243 | runner, `SqliteProjection` (checkpoint et version de schéma), vérification D81 en fin de test |
| R1.4 Supervision et cycle de vie | fait | #244 | `orion.core.supervisor`, `orion serve` (`orion.host`), pannes et cycle de vie journalisés |
| R1.5 Réglages en base | à faire | | |
| R1.6 Sauvegarde et restauration | à faire | | |

Les tâches suivantes s'ajoutent ici quand leur partie commence (liste complète :
`01-feuille-de-route.md`).

## Passation

Ce que la prochaine session doit savoir et qui n'est ni dans le code ni dans la feuille de
route : un piège, un choix provisoire, un test lent. Court ; on efface ce qui ne sert plus.

- La v1 (`src/orion`) tourne toujours en production. On n'y touche pas, sauf correctif urgent.
- Les 20 « on prend » de `inspirations.md` renvoient tous à une tâche existante ; en reprenant
  une de ces tâches, relire la ligne correspondante.
- **Toute tâche qui reprend du code commence par sa section de `reprise-v1.md`** (index par
  tâche en tête) : fichiers, invariants, décisions, ce qu'on simplifie, tests v1 à relire.
- R0.3 : la v1 n'a **pas** de fournisseur API Anthropic ni OpenAI (seulement OpenRouter et les
  forfaits ChatGPT et Claude Code) ; dans R4.2, ces deux adaptateurs sont écrits à neuf.
- R0.3 : la **fédération entre Orion** (`federation/`, D29, D102, ~2 600 lignes) n'a aucune
  tâche dans la feuille de route, ni le shell serveur (D96). Pas bloquant avant P11 ; à
  trancher au plus tard pour la matrice de parité (R11.2).
- R1.1 : l'arborescence de l'audit §6.4 n'est **pas** créée d'avance (« sans fichiers vides
  inutiles ») ; chaque sous-paquet (`core`, `agents`, `queue`…) naît avec sa première tâche,
  la liste est dans `next/CLAUDE.md`. Le délai de 60 s des tests vient de `pytest-timeout`.
- R1.1 : `next/` a son propre `uv.lock` et son job CI `v2` ; le job v1 `check` ne le voit
  que par `ruff` (même réglages).
- R1.2 : l'append-only est tenu **par la base** (déclencheurs SQLite) : seule une redaction
  (`payload = '{}'`, `redacted = 1`) passe ; tout autre `UPDATE` ou `DELETE` échoue. Un
  `secure_delete` efface les pages libérées. Les versions d'événements sont une instance
  `EventVersions` passée au journal (défaut : `upcast.VERSIONS`), plus des dictionnaires
  globaux. `NewEvent` porte `agent_id` et `thread_id` (portées, R6.2), `Provenance.agent`
  l'agent auteur.
- R1.2, simplifié par rapport à la v1 : pas de migration d'anciens journaux, pas de
  `HybridClock.observe` (rien n'échange d'événements entre instances), niveaux de confiance
  `TRUSTED_PEER`/`OWNER_INSTANCE` retirés (fédération), `enclosed`/`owned_by` non repris (ils
  reviendront avec leur premier usage).
- R1.3 : une projection sur disque hérite de `SqliteProjection` (un fichier SQLite par
  projection, `name`, `version`, `schema`, `apply_event`). Version de schéma dans
  `PRAGMA user_version` : si elle diffère du code, les tables sont jetées et le journal rejoué,
  **pas de migration**. Le checkpoint est écrit dans la même transaction que l'état.
- R1.3 : le registre des runners est tenu **par journal et en référence forte**
  (`ProjectionRunner.on(journal)`) ; en v1 c'était un `WeakSet` et un runner créé à la volée
  échappait à la vérification de fin de test (constaté ici). Le `journal` de
  `tests/conftest.py` vérifie chaque runner encore ouvert ; un test qui casse la règle exprès
  porte `no_rebuild_check`. `test_journal.py` garde sa propre fixture `journal`.
- R1.3 → R1.5 : rien ne fait encore tourner les runners en continu (suivre le journal avec
  `follow`). R1.4 ne l'a pas branché faute de projection à servir : la première projection de
  `serve` (les réglages, R1.5) l'ajoute comme service supervisé.
- R1.4 : le superviseur **écrit dans le journal** (`service.crashed` à chaque panne,
  `service.gave_up` au-delà du budget) ; un journal qui refuse l'écriture arrête l'arbre (on
  n'avale pas). `serve` journalise `host.started` puis `host.stopped` (`reason` : le signal, ou
  `failure`, code de sortie 1). Pas encore de canal pour prévenir le propriétaire : le crochet
  `escalate` existe, `serve` ne le branche pas encore.
- R1.4 : `--data-dir` vaut `~/.orion` par défaut, **provisoire** : R1.5 découvre le dossier
  selon la plateforme. `core/web.py` (serveur HTTP qui laisse les signaux au processus) n'est
  pas repris : à reprendre avec le premier serveur HTTP (API, P5), sinon un uvicorn qui rend la
  main sur SIGTERM ressemble à une panne et boucle.

## Questions ouvertes

Ce qui attend une décision du propriétaire. Une tâche qui en dépend ne commence pas.

*(aucune)*

Tranchées le 10/11/2026 :

- **Le produit conserve le nom Orion pour la v2** (D297, annule D294). Paquet et commande : `orion`.

Tranchées le 09/11/2026 :

- **Hébergé : le propriétaire paie les modèles** pour l'instant (D295). R10.4 prévoit donc un
  plafond de dépense par instance.
- **Synthèse des inspirations validée**, avec la voix et les achats par l'agent repris (D296) :
  nouvelles tâches R9.8 (voix) et R9.9 (paiements). R0.3 doit donc aussi cartographier la voix
  v1 (D40) et le garde-fou de paiement (D265).

## Démonstrations de fin de partie

Ce que le propriétaire a vu marcher, partie par partie.

- **P0 — Cadrage** : le plan se lit en quatre fichiers.
  `00-cap.md` (le but), `01-feuille-de-route.md` (les tâches), `inspirations.md` (ce qu'on
  prend ailleurs, validé, D296), `reprise-v1.md` (ce qu'on reprend de la v1, tâche par tâche).
