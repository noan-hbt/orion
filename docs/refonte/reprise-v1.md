# Refonte v2 — carte de la v1 à reprendre

*R0.3, 09/11/2026. Relevé sur `main` à `dd2a622`. Les tailles sont en lignes.*

Pour chaque brique que la v2 reprend (`00-cap.md`, D291) : les fichiers de `src/orion` où elle
vit, ce qui doit rester vrai, les décisions qui le fondent, et ce qu'on simplifie en la
reprenant. Une tâche qui reprend du code commence ici : elle relit les fichiers et les
décisions cités, **copie** ce qu'elle garde dans `next/` (jamais d'import depuis `src/orion`),
le simplifie, puis reprend les tests v1 qui comptent, réécrits sur le comportement.

Comment lire chaque section :

- **Fichiers** : la source, avec sa taille, pour savoir ce qu'on relit.
- **Invariants** : ce que la v2 doit garder, testé. C'est le contrat de la reprise.
- **Décisions** : le pourquoi (`docs/DECISIONS.md`). Une reprise qui contredit l'une d'elles
  pose la question dans `SUIVI.md` avant de coder.
- **On simplifie** : ce qui tenait à la forme v1 (un seul agent, un TOML, un serveur à soi, un
  propriétaire sur Telegram) et ne passe pas tel quel. Ce sont des propositions : la tâche
  tranche en relisant le code.
- **Tests v1** : ceux à relire pour savoir quels comportements comptent.

## Index par tâche

Le « Fait quand » de R0.3 : chaque tâche de P1–P7 qui reprend du code y trouve sa source. Les
tâches de P8–P10 qui reprennent quelque chose sont listées aussi.

| Tâche | Section | Source principale |
|---|---|---|
| R1.1 Squelette | — | rien à reprendre (outillage : `pyproject.toml`, `.github/workflows/ci.yml` à lire) |
| R1.2 Journal | [1](#1-journal-et-socle) | `core/journal.py`, `events.py`, `hlc.py`, `ids.py`, `upcast.py`, `sqlite.py`, `private.py` |
| R1.3 Projections | [1](#1-journal-et-socle) | `core/projections.py` |
| R1.4 Supervision | [1](#1-journal-et-socle) | `core/supervisor.py`, `core/web.py`, `serve.py` |
| R1.5 Réglages en base | [2](#2-réglages-et-chemins) | `config.py`, `configure/paths.py`, `configure/module.py` |
| R1.6 Sauvegarde | [1](#1-journal-et-socle) | `core/backup.py`, `deploy/backup.sh` |
| R2.1 AgentDefinition | — | neuf (aucun agent nommé en v1) |
| R2.2 Workspaces | — | neuf ; `core/private.py` (fichiers 0600) et le dossier de job délégué (`delegation/jobs.py`) comme points de départ |
| R2.3 Gardien et outbox | [3](#3-gardien-outbox-coffre-secretref) | `guardian/` |
| R2.4 Droits par agent | [3](#3-gardien-outbox-coffre-secretref) | `guardian/autonomy.py`, `guardian/limits.py`, `guardian/policy.py` (à transformer en `CapabilityGrant`) |
| R2.5 Registre d'outils | [4](#4-outils-et-effets) | `tools/base.py`, `tools/actions.py`, `tests/test_runtime_cache.py` |
| R3.1 Assignment | [5](#5-travaux-durables-et-incertitude) | inspiration : `workflows/engine.py` (états, D257) |
| R3.2 Mailbox | [8](#8-conversations-et-boîte-de-réception) | inspiration : `channels/inbox.py`, `guardian/outbox.py` (clé d'idempotence) |
| R3.3 Ordonnanceur | — | neuf |
| R3.4 Contrôles | [6](#6-boucle-native) | inspiration : stop d'un outil (`cognition/loop.py`, D261), pause (D200) |
| R3.5 Reprise après crash | [5](#5-travaux-durables-et-incertitude) | `tools/interrupted.py`, `workflows/engine.py` (D257, D271) |
| R3.6 Client CLI | — | neuf (`cli.py` v1 n'a que le style à lire) |
| R4.1 Contrat AgentEngine | [6](#6-boucle-native) | inspiration : événements de la boucle (`cognition/loop.py`, `MessageEmitted`…`Finished`) |
| R4.2 Boucle native | [6](#6-boucle-native), [7](#7-fournisseurs-de-modèles) | `cognition/loop.py`, `context/compiler.py`, `providers/` |
| R4.3 Sessions persistantes | — | neuf |
| R4.4 Claude Agent SDK | [7](#7-fournisseurs-de-modèles) | ce qu'a appris `providers/claude_code.py` (D100, D207, D213–D217, D227) |
| R4.5 Codex App Server | [7](#7-fournisseurs-de-modèles) | ce qu'ont appris `providers/chatgpt*.py` (D62, D228–D230) |
| R4.6 Relais entre moteurs | — | neuf ; `context/summary.py` (résumé de rebase) comme point de départ |
| R4.7 Coûts, quotas, replis | [7](#7-fournisseurs-de-modèles) | `providers/spending.py`, `providers/router.py`, `mobile/usage.py` |
| R4.8 Connexion fournisseurs | [7](#7-fournisseurs-de-modèles) | `providers/chatgpt_auth.py`, `deploy/claude-code` (D208) |
| R5.1 Fils et messages | [8](#8-conversations-et-boîte-de-réception) | `context/threads.py`, `channels/markup.py` (D126, D287) |
| R5.2 Messages directs | [8](#8-conversations-et-boîte-de-réception) | `channels/inbox.py` |
| R5.3–R5.5 Bus, canaux, fichiers | — | neufs ; `artifacts/module.py` à relire pour R5.5 |
| R5.6 Délégation par Orion | [5](#5-travaux-durables-et-incertitude) | `delegation/`, D110, D231, D274 |
| R6.1 Mémoire sourcée | [9](#9-mémoire) | `memory/` |
| R6.2 Portées | [9](#9-mémoire) | neuf sur la base de `memory/` |
| R6.3 Écritures et conflits | [9](#9-mémoire) | `memory/service.py`, `memory/batch.py` |
| R6.4 Mémoire visible | [9](#9-mémoire) | `memory/render.py`, D188 |
| R6.5 Skills et MCP | [10](#10-skills-et-mcp) | `skills/module.py`, `mcp/` |
| R6.6 Passe de nuit | [9](#9-mémoire) | `memory/night.py`, `memory/portrait.py` |
| R7.1 Initiative et attention | [11](#11-initiative-attention-heures-calmes) | `initiative/`, `adaptation/attention.py`, `notifications/policy.py` |
| R7.2 Missions | [12](#12-missions-et-engagements) | `missions/`, `goals/module.py`, commitments de `memory/` |
| R7.3 Contrat des modules | [13](#13-modules) | `modules/` |
| R7.4 Canaux externes | [14](#14-canaux-externes) | `channels/`, `guardian/telegram.py` |
| R7.5 Sources de vie | [15](#15-sources-de-vie) | un module v1 par source |
| R7.6 Evals | [16](#16-evals) | `evals/` |
| R8.1 Authentification | [19](#19-reprises-plus-tardives-p8p10) | `guardian/app.py` (passkeys, D125) |
| R8.8 Notifications | [19](#19-reprises-plus-tardives-p8p10) | `mobile/push.py`, `notifications/` |
| R9.1 Workflows | [5](#5-travaux-durables-et-incertitude) | `workflows/engine.py` |
| R9.2 Routines | [19](#19-reprises-plus-tardives-p8p10) | `hooks/` (D225, D264) |
| R9.4 Navigateur | [17](#17-navigateur-coffre-didentifiants-mains) | `computer/`, `guardian/logins.py` |
| R9.5 Ordinateur | [17](#17-navigateur-coffre-didentifiants-mains) | `hands/` |
| R9.8 Voix | [18](#18-voix-et-paiements) | `voice/`, `vocal/` (D40, D71) |
| R9.9 Paiements | [18](#18-voix-et-paiements) | `computer/direct.py` (`pay`), `guardian/policy.py`, `guardian/service.py` (D265) |
| R10.1 Image serveur | [19](#19-reprises-plus-tardives-p8p10) | `deploy/` (D30, D94, D251) |

---

## 1. Journal et socle

**Fichiers.** `core/journal.py` (223), `core/events.py` (88), `core/hlc.py` (99),
`core/ids.py` (61), `core/upcast.py` (48), `core/sqlite.py` (80), `core/private.py` (31),
`core/projections.py` (193), `core/supervisor.py` (103), `core/web.py` (20),
`core/backup.py` (116), `serve.py` (198). Hors du cœur : `core/busy.py` (58, D251) relève du
déploiement (R10.1).

**Invariants.**

- Le journal est append-only : `append`, `read`, `get`, `last_seq`, `follow`, et une seule
  mutation, `redact`, qui efface la charge mais garde la ligne (séquence et liens causaux
  intacts) et écrit un `journal.redacted` qui dit quoi et pourquoi. Aucun chemin de mise à jour.
- SQLite en WAL, un seul écrivain, tous les appels bloquants sur un fil dédié
  (`SqliteWorker`) : la boucle asyncio ne bloque jamais sur le disque.
- Chaque événement porte `Provenance` et `Trust` ; ce qui est dérivé de plusieurs entrées a la
  confiance minimale des entrées (`derive_trust`).
- Ids ULID monotones dans un processus ; horodatage HLC dont la forme texte se trie dans l'ordre
  du temps.
- Chaque événement est stocké avec la version de son type ; la lecture applique les
  upcasters manquants (purs, totaux, jamais supprimés), `RENAMED` pour un type renommé. Un
  événement d'une version plus récente que le code est refusé. Une charge effacée n'est pas
  convertie.
- Une projection est une fonction pure des événements vus : remise à zéro puis rejeu donnent
  le même état. Son checkpoint est écrit avec son état, atomiquement.
- Le superviseur relance un service qui plante, avec attente croissante ; au-delà de son
  budget il prévient le propriétaire et arrête tout l'arbre. Rien ne meurt en silence.
- Les serveurs HTTP laissent les signaux au processus (`core/web.py`) : sinon un uvicorn qui
  rend la main sur SIGTERM ressemble à une panne et boucle.
- Une sauvegarde ne compte que si elle se restaure : intégrité SQLite, puis chaque événement
  relu comme au démarrage, dans l'ordre, sans trou.
- Les fichiers privés (clés, cookies) sont créés 0600 d'emblée, sans fenêtre entre écriture et
  `chmod`.

**Décisions.** D6 (noyau propre), D80 (versions), D81 (reconstruction prouvée), D165 (un
redémarrage réveille Orion), D290 (sauvegarde complète), règles de `CLAUDE.md`.

**On simplifie.**

- Le journal v1 est un seul fichier pour tout. La v2 garde un journal par instance, mais le
  type d'événement doit dire l'agent et le fil concernés (portées, R6.2) : à prévoir dans
  `NewEvent` dès R1.2 plutôt que dans chaque charge.
- `Provenance` v1 suppose un seul propriétaire (`owned_by`) ; en v2 elle nomme aussi l'agent
  auteur.
- La vérification de reconstruction à la fin de chaque test (`tests/conftest.py`, D81) est
  reprise telle quelle : elle a trouvé de vrais défauts.
- La sauvegarde v1 ne copie que le journal (et le registre du gardien) ; R1.6 y ajoute le coffre
  chiffré et les espaces des agents (D290 l'avait commencé dans `deploy/backup.sh`).

**Tests v1.** `test_journal.py`, `test_ids_hlc.py`, `test_upcast.py`, `test_projections.py`,
`test_supervisor.py`, `test_private.py`, `test_serve.py`, `tests/conftest.py`
(`no_rebuild_check`).

## 2. Réglages et chemins

Brique **réécrite** (réglages en base, D292), mais la v1 dit ce qui se règle et qui peut le
changer.

**Fichiers.** `config.py` (836 : tous les réglages typés et leurs défauts),
`configure/paths.py` (498 : ce qu'Orion peut changer par message et qui doit dire oui),
`configure/module.py`, `setup.py` (123), `onboarding/service.py`.

**Invariants.**

- Les réglages sont typés (Pydantic, `extra="forbid"`) : une clé inconnue est une erreur, pas
  un réglage ignoré.
- Certains réglages sont des limites et ne se changent pas par l'agent lui-même (`[budget]`,
  ceux du gardien, D79, D72) ; les autres demandent l'accord du propriétaire (D92).
- Un réglage changé se voit tel qu'il est vraiment appliqué (D218).

**Décisions.** D55, D72, D92, D148, D180, D218, D233 (`[models]` : quel modèle fait quoi).

**On simplifie.** Plus de TOML ni de recherche de `orion.toml` (D180, D148) : une projection
`settings` alimentée par `settings.changed`. La table « qui peut changer quoi » de
`configure/paths.py` devient la donnée de départ de R1.5 et des droits (R2.4). `config.py`
sert d'inventaire pour R8.7 (« tout ce que la v1 réglait dans `orion.toml` se règle ici »).

## 3. Gardien, outbox, coffre, SecretRef

**Fichiers.** `guardian/outbox.py` (203), `guardian/policy.py` (354),
`guardian/autonomy.py` (390), `guardian/limits.py` (150), `guardian/ledger.py` (281),
`guardian/service.py` (1 533), `guardian/process.py` (179), `guardian/client.py` (361),
`guardian/wire.py` (112), `guardian/secrets.py` (50), `guardian/vault.py` (299),
`guardian/telegram.py` (337), `guardian/app.py` (601), `guardian/logins.py` (529, voir
§17), `guardian/federation.py` (668, voir « Pas repris »). `SecretRef` est dans `config.py`.

**Invariants.**

- Tout ce qui sort est journalisé avant l'envoi : `outbox.queued` → `outbox.delivered` |
  `outbox.failed`. L'id d'outbox est la clé d'idempotence donnée au canal : un envoi coupé
  repart au redémarrage avec la même clé et n'est livré qu'une fois. Un refus définitif (4xx)
  n'est pas réessayé.
- Les règles de la politique ne dépendent que des propriétés déclarées de l'outil, de la
  confiance du contexte et des réponses du propriétaire, jamais de ce que le modèle écrit.
- Un outil à effet externe ne s'exécute pas dans la boucle : il devient une proposition que le
  gardien décide.
- Le gardien tient ce qui doit rester vrai même si le cœur est compromis : les secrets, les
  destinations permises, le débit, les approbations vérifiées. Il a son propre registre
  append-only (`ledger.py`) et son état en est une projection. Le cœur refuse de démarrer s'il
  voit dans son environnement un secret du gardien (échec fermé).
- Une approbation n'a de valeur que vérifiée par le gardien (signature du propriétaire,
  `owner_said_yes`), à usage unique (`guardian.approval.used`).
- L'autonomie se gagne action par action, se perd au premier doute, peut avoir une fin, et peut
  être bornée (destinataires, domaines) ; les bornes sont vérifiées en code à chaque action, par
  le gardien et par le cœur.
- Un secret ne passe jamais par une conversation : il est saisi dans un formulaire servi par le
  gardien et va droit au coffre.

**Décisions.** D14, D19, D26, D28, D35, D49, D85, D89, D94, D103, D130, D134, D167, D168,
D232, D285.

**On simplifie.**

- **Un seul mode** : en v1 le gardien est optionnel (`[guardian] enabled`) et beaucoup de code
  existe en double (coffre local `computer/vault.py` contre `guardian/logins.py`, D120). En v2
  le gardien est toujours un service séparé (R2.3) : on ne reprend que le chemin séparé.
- `guardian/service.py` mêle le cœur du gardien et les règles de chaque connecteur (Inkbox,
  Telegram, agendas, mail). En v2, le gardien garde le mécanisme (secret, destination, débit,
  approbation) et chaque module déclare ses règles (R7.3).
- Les approbations passaient par des boutons Telegram ou l'app ; en v2 elles passent par la
  mailbox et le Workbench (R8.6). Le contrat (question écrite par le gardien, réponse signée,
  usage unique) reste.
- Autonomie (D35, D167), bornes (D49) et modes `prudent`/`équilibré`/`libre` (D85, D232)
  deviennent des `CapabilityGrant` par agent (R2.4) : sujet, action, ressource, expiration,
  impact maximal. Un worker n'hérite jamais d'une autonomie d'Orion.
- `SecretRef` v1 lit une variable d'environnement ; en v2 il désigne une entrée du coffre,
  remplie depuis l'interface (D292).

**Tests v1.** `test_guardian.py`, `test_tools_guardian.py`, `test_autonomy.py`,
`test_delegations.py`, `test_vault.py`, `test_app_vault.py`, `test_telegram_guardian.py`,
`test_mobile_split.py`, `fake_guardian.py`.

## 4. Outils et effets

**Fichiers.** `tools/base.py` (324), `tools/outcome.py` (98), `tools/actions.py` (233),
`tools/builtin.py` (100), `context/reread.py` (68).

**Invariants.**

- Défauts fermés : un outil qui ne dit rien est supposé à effet externe, irréversible, non
  concurrent, et refuse un contexte non fiable (`Effect`, `Reversibility`).
- `ToolContext` porte le fil, la corrélation, la confiance du contexte, l'accord éventuel, et
  une clé d'idempotence dérivée de (fil, corrélation, outil, arguments normalisés), jamais du
  `call_id` que le modèle change en redemandant.
- `ToolResult` porte sa confiance (le web et le mail l'abaissent) et, pour un outil qui agit,
  son issue (`Outcome`), l'action et la preuve : une action n'est dite qu'aussi loin que sa
  preuve.
- Une sortie coupée reste entière dans le journal (`tool.artifact`) et se relit.
- Registre fixe et trié, schémas stables : condition du cache (voir §6).

**Décisions.** D59 (un outil par domaine), D132, D151, D204, D234, D252, D258, D282.

**On simplifie.** Le registre v1 est global ; en v2 « installé » et « accordé » se séparent
(R2.5), et le schéma envoyé ne contient que les outils accordés à l'agent. Le tiroir (D151)
est une réponse v1 au trop-plein d'outils : à reconsidérer une fois les outils filtrés par
agent.

**Tests v1.** `test_actions.py`, `test_reread.py`, `test_runtime_cache.py`.

## 5. Travaux durables et incertitude

En v2 tout travail passe par `Assignment` (réécrit, R3.1). La v1 n'en a pas, mais trois pièces
en sont les prototypes éprouvés.

**Fichiers.** `workflows/engine.py` (458), `workflows/module.py` (113),
`tools/interrupted.py` (78), `delegation/jobs.py` (439), `delegation/claude_code.py` (156),
`delegation/module.py` (47).

**Invariants.**

- Une étape est journalisée avant et après (`workflow.step_began` → `step_done` |
  `step_failed` | `step_uncertain`) ; une étape finie n'est jamais refaite.
- Une étape coupée qui n'agit que dans l'instance est refaite ; une étape qui a peut-être agi
  dehors passe `UNCERTAIN`. Sa vérification (`check`) regarde avant tout nouvel essai ; sans
  vérification possible, le travail attend et le propriétaire est prévenu une fois. Jamais de
  rejeu à l'aveugle.
- Un appel d'outil coupé par un crash (`tool.started` sans `tool.executed`, avec `may_act`)
  reçoit au démarrage du démon une issue `UNCERTAIN`, dite une fois, jamais rejouée. Pas à
  chaque démarrage d'une commande annexe.
- Un modèle sans quota met le travail en attente sans consommer d'essai.
- Une tâche ou un job avec « fait quand » ne se dit fini que sur preuve.

**Décisions.** D110, D195, D231, D234, D235, D257, D260, D271, D272, D274, D276.

**On simplifie.** Les états v1 (`QUEUED`, `RUNNING`, `WAITING`, `UNCERTAIN`, `SUCCEEDED`,
`FAILED`, `CANCELLED`) sont un bon départ pour §8.2 de l'audit, qui en ajoute. Les trois
mécanismes v1 (workflows, jobs délégués, appels coupés) se fondent en un seul : Assignment /
Attempt / ToolEffect. R9.1 (DAG) reprend ensuite `workflows/engine.py` comme exécution par
nodes, non plus en ligne droite.

**Tests v1.** `test_workflows.py`, `test_cut_calls.py`, `test_delegation.py`, `test_tasks.py`.

## 6. Boucle native

**Fichiers.** `cognition/loop.py` (1 067), `runtime.py` (1 402), `context/compiler.py` (117),
`context/summary.py` (156), `context/meanwhile.py` (115), `context/recent.py` (158),
`cognition/finish.py` (196), `cognition/grounding.py` (287), `cognition/review.py` (292),
`cognition/verifier.py` (174), `providers/foreground.py` (27).

**Invariants.**

- **Contrat de cache** (`tests/test_runtime_cache.py`) : chaque requête prolonge la précédente
  octet pour octet. Rien de volatil dans le message système ; les messages journalisés sont
  rejoués tels qu'envoyés ; registre d'outils fixe et trié ; `session_id` stable. Un échec est
  un incident.
- La mémoire voyage dans les messages, jamais dans le prompt système ; l'heure est dans chaque
  tour (D17, D175).
- Le contexte se construit en couches favorables au cache ; on n'allège que quand le cache est
  parti ; un rebase garde le dernier échange et laisse un résumé (D128, D198).
- Raisons d'arrêt explicites (`StopReason`), budget par tour, échéance par appel d'outil, Stop
  qui coupe l'outil en cours et ne se dit fait qu'une fois fait (D260, D261).
- Des appels indépendants partent ensemble (D237) ; une boucle ne bute pas deux fois sur le
  même mur (D122).
- Le propriétaire qui écrit passe avant le travail de fond (D220, `foreground`).

**Décisions.** D43, D97, D118, D121, D122, D123, D128, D173, D175, D178, D182, D198, D200,
D210, D211, D216, D219, D220, D223, D237, D252, D253, D260, D261.

**On simplifie.**

- `runtime.py` câble tout (journal, projections, contexte, boucle, gardien) pour un seul agent.
  En v2 ce câblage se répartit entre le runtime d'Assignment (P3) et le moteur natif (R4.2) ;
  rien de ce fichier ne passe tel quel.
- Les événements de la boucle (`MessageEmitted`, `ModelCalled`, `ToolStarted`,
  `ToolExecuted`, `Finished`, `Told`) sont le point de départ de `EngineEvent` (R4.1).
- Les couches propres au compagnon (aller au bout, preuve avant les mots, relecture après coup,
  vérificateur, `tell`) sont propres à l'agent `primary` : elles deviennent des étapes
  optionnelles du moteur natif, activées par agent, plutôt que du code dans la boucle.
- Ce qui dépend d'un fournisseur (balises au lieu d'un schéma sur le forfait Claude, D217 ;
  deux messages sur ChatGPT, D230) va dans l'adaptateur du fournisseur, pas dans la boucle.

**Tests v1.** `test_runtime_cache.py` (à reprendre en premier), `test_loop.py`,
`test_finish.py`, `test_grounding.py`, `test_router_verifier.py`, `test_meanwhile.py`,
`test_prompt_budget.py`.

## 7. Fournisseurs de modèles

**Fichiers.** `providers/base.py` (273), `providers/router.py` (128),
`providers/openrouter.py` (498), `providers/chatgpt.py` (438),
`providers/chatgpt_auth.py` (332), `providers/claude_code.py` (648),
`providers/spending.py` (368), `mobile/usage.py`.

**Invariants.**

- Une seule entrée pour tout appel de modèle (`router`), avec repli sur un autre fournisseur.
  Un mauvais nom de modèle se dit (D209).
- Chaque appel est compté (`spend.recorded` : modèle, demandeur, premier plan ou fond) ; le
  décompte est une projection. Le premier plan n'est jamais coupé ; le fond s'arrête au plafond
  du jour ou du mois et échoue fermé (`ProviderError`). Prévenu une fois par période.
- Un forfait épuisé qui dure se dit au propriétaire (D249) ; un appel muet est lâché vite
  (D227).

**Décisions.** D5, D5-bis, D46, D55, D62, D79, D100, D147, D190, D207, D208, D209, D213–D217,
D221, D227–D230, D233, D249, D286.

**On simplifie.**

- `providers/base.py` est un `complete` ; en v2 un moteur a des sessions et des événements
  (R4.1). On reprend les types de messages et d'appels d'outils, pas l'interface.
- **La v1 n'a pas de fournisseur API Anthropic ni OpenAI** : elle passe par OpenRouter, par le
  forfait ChatGPT (D62) et par le forfait Claude via Claude Code (D100). R4.2 reprend
  OpenRouter et le router ; les adaptateurs API directs sont écrits à neuf.
- `claude_code.py` et `chatgpt*.py` contournent un CLI ou une API privée ; R4.4 (Claude Agent
  SDK) et R4.5 (Codex App Server) les remplacent. On en garde les leçons (cache réellement
  relu, D207 ; quota caché, D228 ; appel muet, D227) comme tests, pas le code.
- Le plafond de dépense devient par agent et par instance (R4.7, R10.4, D295).

**Tests v1.** `test_openrouter.py`, `test_chatgpt_provider.py`, `test_chatgpt_auth.py`,
`test_claude_code.py`, `test_spending.py`, `test_models_config.py`.

## 8. Conversations et boîte de réception

Brique **réécrite** (fils, canaux, messages typés), avec deux sources.

**Fichiers.** `context/threads.py` (187), `channels/inbox.py` (515),
`channels/markup.py` (151).

**Invariants.**

- Un fil est une projection du journal ; une simple lecture ne crée pas de fil (bug trouvé par
  D81).
- La boîte de réception est le seul chemin d'un message entrant vers un tour : quel que soit
  le canal, il arrive sur son fil ; un message répété est écarté ; un tour qui échoue le dit
  au propriétaire.
- Une pièce structurée dans un message (balises, D126) n'est perdue par aucun canal (D287).

**Décisions.** D23, D88, D109, D126, D141, D163, D200, D214, D219, D287.

**On simplifie.** `OwnerInbox` suppose un seul destinataire (Orion) et un seul interlocuteur
(le propriétaire) ; la mailbox de R3.2 la généralise à tout agent et toute origine (message,
webhook, routine, enfant, canal), durable et dédupliquée. L'`Outlet` v1 (comment répondre sur
un canal) reste l'idée du côté sortant, toujours par l'outbox.

**Tests v1.** `test_threads.py`, `test_inbox.py`, `test_markup.py`.

## 9. Mémoire

**Fichiers.** `memory/model.py` (179), `memory/service.py` (420), `memory/store.py` (591),
`memory/semantic.py` (152), `memory/provenance.py` (346), `memory/tools.py` (372),
`memory/render.py` (151), `memory/batch.py` (223), `memory/extractor.py` (383),
`memory/doubt.py` (348), `memory/night.py` (303), `memory/portrait.py` (248),
`memory/people.py` (213), `memory/situations.py` (177).

**Invariants.**

- La mémoire ne change que par des événements du journal (`memory.fact.asserted`,
  `invalidated`, `pinned`…), via `MemoryService` ; le magasin (SQLite + plein texte) en est une
  projection reconstructible.
- Les faits sont bitemporels (vrai quand / su quand) et sourcés.
- Oublier une source se propage : ce qui en dépend est retrouvé (`provenance.py`, traçage) et
  effacé par `redact` ; l'oubli se vérifie.
- On extrait après une conversation, pas après chaque message (D86) ; un sujet, un souvenir
  (D196).
- Une correction est un nouvel événement ; ce qu'Orion sait se lit, daté, et se corrige sur
  place (D188).
- Le portrait cite les faits dont vient chaque affirmation (D280).

**Décisions.** D11, D17, D27, D37, D38, D56, D83, D86, D144, D149, D174, D176, D186, D188,
D192, D193, D196, D201, D280, D281.

**On simplifie.**

- Tout est implicitement au propriétaire ; R6.2 ajoute la portée à chaque fait (sans copie
  entre portées) et R6.1 doit la prévoir dans les événements dès la reprise.
- Portrait, personnes et situations sont la vie personnelle : réservés à l'agent `primary`.
- La passe de nuit v1 (D174, D186, D201) a beaucoup bougé ; R6.6 reprend son contrat (tout
  revoir, consolider, réviser) par portée, pas son historique.
- `doubt.py` et la recherche sémantique sont des modules v1 ; à garder optionnels.

**Tests v1.** `test_memory.py`, `test_memory_batch.py`, `test_runtime_memory.py`,
`test_semantic.py`, `test_provenance.py`, `test_doubt.py`, `test_consolidation.py`,
`test_night.py`, `test_people.py`. « Les tests de la v1 qui comptent » (R6.1) : ceux de
`test_memory.py` et `test_provenance.py` sur l'oubli et la reconstruction d'abord.

## 10. Skills et MCP

**Fichiers.** `skills/module.py` (349), `mcp/client.py` (186), `mcp/module.py` (160),
`mcp/settings.py` (47).

**Invariants.** Un skill est un savoir-faire en Markdown avec un court en-tête ; un outil MCP
est une action sur le monde, nommé `mcp_<serveur>_<outil>`, soumis au gardien comme les
autres ; le jeton d'un serveur MCP peut rester au gardien (le client passe par sa socket).

**Décisions.** D95, D212.

**On simplifie.** En v1 les serveurs et skills sont globaux et listés au démarrage ; en v2 ils
sont accordés par agent et le retrait vaut aussi pour une session ouverte (R6.5). Le client
MCP v1, sans dépendance, se reprend tel quel si le SDK officiel n'apporte rien de nécessaire.

**Tests v1.** `test_plugins.py`, `test_modules.py`.

## 11. Initiative, attention, heures calmes

**Fichiers.** `initiative/engine.py` (1 539), `initiative/arbiter.py` (103),
`initiative/checks.py` (58), `initiative/timers.py` (299), `initiative/tools.py` (227),
`initiative/later.py` (167), `initiative/planned.py` (88), `initiative/simulate.py` (213),
`adaptation/attention.py` (70), `notifications/policy.py` (233),
`notifications/module.py` (212).

**Invariants.**

- Orion ne parle de lui-même que par le moteur d'initiative, et chaque décision est
  journalisée (`initiative.triggered`, `delivered`, `suppressed`) avec sa raison. Les règles
  décident, le modèle rédige ou propose (D20, D277).
- Chaque candidat passe la même porte : heures calmes (sauf si le propriétaire vient d'écrire,
  D98), budget d'attention du jour (qui ne compte que ce qu'Orion dit de lui-même, D104),
  registre de ce qui a déjà été dit.
- Un message proactif passe des contrôles séparés, chacun avec son issue journalisée (D279).
- L'arbitre juge si ça vaut une interruption maintenant, et apprend des retours source par
  source (D269) ; son attente est journalisée, un redémarrage ne la rajeunit pas (D278).
- Les rappels sont durables (`timer.scheduled` / `fired` / `cancelled`) ; un rappel dit la
  chose une fois et se tait si c'est déjà fait (D246). Un seul « plus tard » (D157).
- Une semaine d'initiative se joue d'avance sur une copie (D82).

**Décisions.** D12, D20, D36, D51, D78, D82, D98, D104, D146, D150, D155, D157, D166, D246,
D250, D262, D263, D269, D277, D278, D279.

**On simplifie.** `engine.py` porte à lui seul la porte, les sources, les résumés, les
rapports et la livraison. En v2 (R7.1) l'initiative produit un travail dans la mailbox d'Orion
au lieu de livrer elle-même : la porte (heures calmes, budget, registre, contrôles) reste,
la livraison suit le chemin d'un message. Les heures calmes et l'attention valent pour toute
l'instance, pas par agent : un worker ne réveille pas le propriétaire.

**Tests v1.** `test_initiative.py`, `test_arbiter.py`, `test_later.py`, `test_planned.py`,
`test_simulate.py`, `test_notifications.py`, `test_adaptation.py`, `test_cli_reminders.py`.

## 12. Missions et engagements

**Fichiers.** `missions/service.py` (452), `missions/module.py` (562), `goals/module.py`,
`awaiting/module.py`, `intentions/module.py`, les engagements de `memory/`
(`commitment.created` / `seen` / `closed`).

**Invariants.**

- Une mission est un but poursuivi sur plusieurs jours sans redemande ; elle s'arrête tout de
  suite quand on l'arrête et démarre tout de suite (D106) ; « je continue » est vrai (D108) ;
  une mission close peut se rouvrir (D202).
- Un engagement naît en un seul point : vu ailleurs, il n'est pas créé deux fois (D275) ; échu,
  il est demandé une fois puis laissé à la réponse (D250).
- Un objectif a un résultat à atteindre, prouvé (D267).

**Décisions.** D37, D47, D53, D106, D108, D129, D202, D250, D267, D268, D275, D284, D288.

**On simplifie.** Les passes de mission v1 sont déclenchées par leur propre service ; en v2 une
mission est un `Assignment` à long terme (R7.2) avec ses attentes d'événement, et ne garde
aucun ordonnanceur à elle. Objectifs, attentes et intentions sont à regrouper si un seul
concept suffit ; la tâche tranche.

**Tests v1.** `test_missions.py`, `test_goals.py`, `test_awaiting.py`, `test_intentions.py`,
`test_bench_multiday.py`.

## 13. Modules

**Fichiers.** `modules/base.py` (233), `modules/registry.py` (185),
`modules/installer.py` (282), `modules/tools.py` (147), `modules/guide.py` (53),
`capabilities/module.py`.

**Invariants.** Une capacité nouvelle est un module, pas du code dans le cœur (D24) ; un module
apporte services, outils, réglages ; on installe et retire un module natif avec l'accord du
propriétaire (D105) ; les consignes rares sont lues quand elles servent (D212).

**Décisions.** D24, D64, D105, D212, D283.

**On simplifie.** Le contrat v1 lit son réglage dans `[modules.<nom>]` et suppose un
redémarrage. R7.3 récrit le contrat (capacités, outils, réglages, droits demandés), sans
redémarrage ; `base.py` dit ce qu'un module v1 pouvait fournir, comme inventaire.

**Tests v1.** `test_modules.py`, `test_module_install.py`, `test_capabilities.py`.

## 14. Canaux externes

**Fichiers.** `channels/telegram.py` (782), `channels/telegram_module.py` (141),
`channels/imessage.py` (652), `channels/line.py`, `channels/inkbox.py`,
`channels/webhook.py` (77), `channels/terminal.py`, `guardian/telegram.py` (337),
`secretary/` (les proches qui écrivent au bot).

**Invariants.** Un seul contrat de canal (D88) ; le jeton du bot et la clé Inkbox ne quittent
pas le gardien (D89, D28) ; un envoi ne va qu'au propriétaire ou à un contact qu'il a permis,
avec un débit plafonné ; un webhook est signé.

**Décisions.** D2, D9, D18, D88, D89, D91, D93, D98, D141.

**On simplifie.** En v2 un canal est un module routé vers un agent et un fil (R7.4) ; la
console dans Telegram (D91) et le doublon app/Telegram (D141) disparaissent avec le Workbench.

**Tests v1.** `test_telegram.py`, `test_telegram_guardian.py`, `test_imessage.py`,
`test_inkbox.py`, `test_secretary.py`.

## 15. Sources de vie

Reprises une à une selon leur usage réel (R7.5), chacune comme module. Source v1 et décision
pour chacune :

| Source | Fichiers | Décisions |
|---|---|---|
| Agenda | `calendar/` | D25, D189, D271 (UID idempotent) |
| Mail | `mail/` | D75, D171, D179, D238 |
| Contacts | `contacts/` | D159 |
| Fichiers, Drive | `files/`, `drive/` | D61, D63, D206 |
| Photos | `photos/` | D50, D87 |
| Flux | `feeds/` | D160 |
| Lieux, départ | `places/`, `departure/` | D57, D77, D187 |
| Papiers, bibliothèque | `papers/`, `library/` | D48, D74, D131 |
| Téléphone | `mobile/` (carnet, appareils) | D153 |
| Rendez-vous | `booking/` | D73 |

Invariant commun : le contenu tiers entre avec une confiance basse et le dit (D26, D224).

## 16. Evals

**Fichiers.** `evals/harness.py` (601), `evals/cases.py` (1 382), `evals/__main__.py` (124).

**Invariants.** Des cas tirés des vraies conversations (D45), lancés sur le vrai modèle ou hors
ligne (`--offline`), avec `--case`, `--model`, `--repeat` ; on ajoute un cas quand Orion se
trompe pour de vrai.

**Décisions.** D45, D286.

**On simplifie.** Le harnais v1 monte un Orion entier ; en v2 il monte une instance avec ses
agents (R7.6) et ajoute des cas multi-agent. Les cas v1 se reprennent un par un, réécrits sur
le comportement.

**Tests v1.** `test_evals.py`.

## 17. Navigateur, coffre d'identifiants, mains

**Fichiers.** `computer/browser.py` (1 287), `computer/direct.py` (1 724),
`computer/disguise.py` (167), `computer/handover.py` (261), `computer/procedures.py` (331),
`computer/module.py` (208), `computer/vault.py` (159), `guardian/logins.py` (529),
`hands/desk.py` (305), `hands/hand.py` (339), `hands/exit.py` (171), `hands/module.py` (177).

**Invariants.**

- Le navigateur lit la page telle qu'elle est (D119) ; les identifiants ne sont jamais vus par
  le modèle ni journalisés : il nomme un champ, le gardien y tape (D111, D113).
- Un seul navigateur qui garde ses connexions ; le propriétaire peut prendre la main (D116).
- Le parcours d'une démarche réussie est gardé et resservi (D255).
- Le clic qui paie est retenu (§18).
- Les mains : appairage, chaque appareil n'agit que pour ce qui lui est demandé, la sortie
  réseau peut passer par la connexion du propriétaire (D1, D41, D145).

**Décisions.** D1, D33, D41, D42, D49, D111, D113, D115, D116, D119, D120, D145, D171, D172,
D245, D255, D265.

**On simplifie.** Un navigateur unique devient un profil par agent (R9.4), sans cookie partagé ;
le coffre d'identifiants n'existe qu'au gardien ; la prise en main passe par le Workbench au
lieu de Telegram. `direct.py` (1 724) mêle conduite, lecture de page et garde-fous : à découper
en reprenant.

**Tests v1.** `test_browser_direct.py`, `test_browser_overhaul.py`, `test_browser_apps.py`,
`test_computer.py`, `test_handover.py`, `test_logins.py`, `test_vault_local.py`,
`test_hands.py`.

## 18. Voix et paiements

Repris par D296 (R9.8, R9.9).

**Voix.** `voice/live.py` (209), `voice/channel.py` (429), `voice/brief.py` (103),
`voice/tools.py` (88), `voice/module.py` (119), `vocal/module.py` (104),
`vocal/audio.py` (93).

- Invariants : chaque phrase du propriétaire passe par la boîte de réception (canal `voix`)
  sur son fil, avec la même mémoire et les mêmes outils ; seul un flux signé avec le numéro du
  propriétaire entre ; le gardien ne diffuse un appel que vers l'adresse de l'instance ;
  appeler quelqu'un d'autre est un effet externe à accord, à chaque fois (D40). Les vocaux sont
  transcrits à l'entrée et lus à la sortie (D71).
- Décisions : D10, D23, D40, D71.
- On simplifie : la v1 dépend d'Inkbox pour la téléphonie ; en v2 la voix est d'abord dans le
  Workbench et la PWA (R9.8), Inkbox devient un module de canal parmi d'autres. Le contrat
  « une phrase = un message dans la mailbox du fil » est ce qu'on garde.
- Tests v1 : `test_live_voice.py`, `test_voice.py`, `test_vocal.py`.

**Paiements.** `computer/direct.py` (`pay`, détection des boutons et pages de paiement),
`guardian/policy.py` (`NEVER_FREE`), `guardian/service.py` (règle `pay`),
`guardian/limits.py` (domaines), `computer/procedures.py`.

- Invariants : un clic, Entrée ou un lien qui paie est retenu et renvoyé à `pay`, effet
  externe avec la page et ce qui est acheté ; `pay` ne clique que sur la page nommée, adresse
  entière, et rien n'est payé si elle a changé ; dans le doute sur une page de paiement, on
  demande ; ni la nuit ni la veille ne paient librement (`NEVER_FREE`) ; une autonomie peut
  être limitée à un site (D265).
- Décisions : D49, D115, D168, D247, D265, D296.
- On simplifie : la v1 détecte par mots et adresses, et l'accord par site tient lieu de
  plafond. En v2 (R9.9) le droit `pay` est accordé par agent avec un montant maximal, l'aperçu
  exact (marchand, articles, montant) est montré, et le paiement passe par l'outbox avec
  `UNCERTAIN` s'il a peut-être eu lieu. La détection v1 reste comme filet, avec sa limite
  connue (un bouton sans mot connu passe).
- Tests v1 : ceux de `pay` dans `test_browser_direct.py` et `test_guardian.py`.

## 19. Reprises plus tardives (P8–P10)

| Tâche | Fichiers | Décisions | Ce qu'on garde |
|---|---|---|---|
| R8.1 Authentification | `guardian/app.py`, `console/auth.py` | D125, D134 | passkeys, sessions signées tenues par le gardien |
| R8.8 Notifications | `mobile/push.py`, `notifications/` | D125, D154 | Web Push, débit par le gardien |
| R9.2 Routines | `hooks/cron.py`, `hooks/module.py`, `hooks/service.py` | D225, D264, D288 | une occurrence = une exécution ; un échec se dit une fois |
| R10.1 Image serveur | `deploy/` (`install.sh`, `orion-update`, `backup.sh`) | D30, D94, D251, D254 | mise à jour qui attend la fin du travail, retour arrière |

## Ce qui n'est pas repris

Pas de tâche dans la feuille de route pour ces briques v1. Elles restent dans la v1 jusqu'à la
bascule ; la matrice de parité (R11.2) dira si l'une manque.

- **Fédération entre Orion** (`federation/`, `guardian/federation.py`, D7, D8, D13, D29, D99,
  D102) : 2 600 lignes, aucune tâche v2. Point signalé dans `SUIVI.md`.
- **App mobile et console v1** (`mobile/` hors push et usage, `console/`) : remplacées par le
  Workbench (P8).
- **Shell sur le serveur** (`shell/`, D96, D164, D167) : relève de l'ordinateur (R9.5) et des
  droits (R2.4) ; à rediscuter là.
- Modules de compagnie sans brique de cœur (`advice/`, `chronicle/`, `curiosity/`,
  `expert/`, `focus/`, `recap/`, `relations/`, `style/`, `thinking/`, `watch/`,
  `adaptation/` hors attention, `onboarding/`) : ils reviendront comme modules ou comme
  comportements de l'agent `primary`, selon l'usage réel, après P7.
