# Refonte v2 — feuille de route

Le cap est dans `00-cap.md`. Ici, le travail, découpé en **parties** (P0 à P11) et en
**tâches** (`R<partie>.<n>`). Où on en est : `SUIVI.md`.

- **Une tâche = une branche `refonte/R<p>.<n>-<sujet>` = une PR** dont le titre commence par
  `R<p>.<n>`. Elle tient dans une session de travail ; sinon on la coupe en deux ici avant de
  commencer.
- **On suit l'ordre.** Une tâche ne commence que si ses prérequis sont fusionnés. Les tâches
  marquées ∥ peuvent avancer en parallèle de la précédente.
- **« Fait quand » est le contrat.** Une tâche dont le « Fait quand » n'est pas tenu, ou qui
  contredit une décision, s'arrête et pose la question au propriétaire (`SUIVI.md`, section
  « Questions ouvertes »).
- **Fin de partie = démonstration** : ce que le propriétaire peut voir marcher, écrit dans
  `SUIVI.md`.
- Les renvois `§` et `ORB-` pointent vers l'audit (`audit OpenBot, non publié`).

Ordre des parties : on fiabilise le moteur avant de le montrer (audit §20.2). L'interface
arrive en P8, mais **un client minimal en ligne de commande** existe dès P3 pour tout tester.

```
P0 cadrage → P1 socle → P2 agents & droits → P3 moteur de travail → P4 modèles
  → P5 conversations → P6 mémoire & skills → P7 Orion personnel → P8 Workbench
  → P9 automatisations & ordinateur → P10 distribution → P11 bascule
```

---

## P0 — Cadrage

Le plan, les décisions, la façon de travailler.

- **R0.1 — Cap, feuille de route, suivi.** `00-cap.md`, ce fichier, `SUIVI.md`, D291–D293,
  `CLAUDE.md` (« Refonte v2 »). *Fait quand* : fusionné.
- **R0.2 — Fiches d'inspiration.** Pour OpenBot, OpenMausBot, OpenAI Dots et Claude Duet : ce
  que fait chacun, vu par l'utilisateur, en une page (`docs/refonte/inspirations.md`), et ce
  qu'on en retient pour Orion. Sources publiques seulement, aucune copie de code. *Fait quand* :
  chaque fiche cite ses sources ; une liste « on prend / on ne prend pas » est validée par le
  propriétaire.
- **R0.3 — Carte de la v1 à reprendre.** Pour chaque brique reprise (`00-cap.md`), les fichiers
  de `src/orion`, leurs invariants, les décisions qui les fondent, ce qu'on simplifie
  (`docs/refonte/reprise-v1.md`). *Fait quand* : chaque tâche de P1–P7 qui reprend du code y
  trouve sa source.

**Démonstration** : le plan est lisible et validé.

## P1 — Le socle neuf

Le projet `next/` existe, outillé, avec le journal et ce qui le porte.

- **R1.1 — Squelette `next/`.** `next/pyproject.toml` (uv, Python 3.12+, paquet `telos`, commande `telos`), ruff,
  pyright strict, pytest (timeout 60 s), job CI séparé dans `.github/workflows/ci.yml`,
  `next/CLAUDE.md` court qui renvoie au cap. Arborescence de l'audit §6.4, sans fichiers vides
  inutiles. *Fait quand* : `uv run pytest` et `pyright` passent à vide dans `next/`, en CI aussi.
- **R1.2 — Journal.** Reprise de `core/journal.py`, `hlc.py`, `ids.py`, `events.py`, `upcast.py`,
  `sqlite.py`, `private.py`. Événements typés et versionnés, `Provenance`/`Trust`, `redact`.
  *Fait quand* : ajout, relecture, redaction et upcast testés ; aucun chemin de mise à jour.
- **R1.3 — Projections.** Reprise de `core/projections.py` : runner, reconstruction depuis le
  journal, versions de schéma. *Fait quand* : une projection détruite se reconstruit à l'identique.
- **R1.4 — Supervision et cycle de vie.** Reprise de `core/supervisor.py` : services supervisés,
  arrêt propre, journalisation des pannes. Un point d'entrée `telos serve` minimal.
  *Fait quand* : un service qui plante est relancé et journalisé ; `serve` démarre et s'arrête.
- **R1.5 — Réglages en base.** Les réglages vivent dans une projection éditable par API (avec
  événement `settings.changed`), plus de TOML obligatoire ; chemins de données découverts selon
  la plateforme (bureau, serveur, conteneur). *Fait quand* : premier lancement sans aucun fichier
  de config ; un réglage changé survit au redémarrage.
- **R1.6 — Sauvegarde et restauration.** Archive cohérente de tout l'état (journaux, coffre
  chiffré, espaces), vérification avant restauration (D81, D290). *Fait quand* : une instance
  restaurée dans un dossier neuf rejoue son journal à l'identique.

**Démonstration** : `telos serve` démarre sans configuration, journalise, se sauvegarde et se
restaure.

## P2 — Agents et droits

Des identités d'agents, leurs espaces, et ce qu'elles ont le droit de faire.

- **R2.1 — AgentDefinition et registre** (ORB-006). Identifiant stable (ULID), nom modifiable,
  `primary`/`worker`, instructions, moteur, modèle, état (actif, suspendu, archivé). Écritures
  par le journal, registre en projection. Création, modification avec version, duplication,
  suspension. L'agent `primary` est créé au premier lancement. *Fait quand* : 100 agents créés,
  modifiés, dupliqués ; tout revient à l'identique après redémarrage ; une écriture concurrente
  est refusée, pas écrasée.
- **R2.2 — Workspaces isolés** (ORB-008). Un dossier par agent, projets partagés explicites ;
  refus des traversées et liens symboliques sortants ; quotas. *Fait quand* : l'agent A ne lit
  pas le dossier de B ; renommer ou dupliquer un agent ne déplace ni ne divulgue rien.
- **R2.3 — Gardien et outbox** (reprise). Reprise de `guardian/` : outbox journalisée et
  idempotente, coffre, `SecretRef`, approbations. Le gardien reste un processus/service séparé
  qui seul voit les secrets. *Fait quand* : un effet externe sans accord est refusé ; un même
  envoi rejoué ne part qu'une fois ; aucun secret dans le journal.
- **R2.4 — Droits par agent** (ORB-009). `CapabilityGrant` (sujet, action, ressource,
  expiration, impact maximal), politique compilée par agent, vérifiée **à chaque effet** ; un
  enfant n'a jamais plus que son parent. *Fait quand* : tests d'escalade enfant→parent ; une
  révocation s'applique au tour suivant d'un vieux fil.
- **R2.5 — Registre d'outils contextualisé** (ORB-010). Outils installés ≠ outils autorisés ;
  le schéma envoyé au modèle ne contient que les outils accordés, triés et stables (contrat de
  cache). *Fait quand* : un outil non accordé est absent du schéma et refusé s'il est appelé.

**Démonstration** : on crée trois agents aux droits différents ; chacun ne voit et ne touche
que ce qui lui est accordé.

## P3 — Le moteur de travail

Tout travail, quelle que soit son origine, passe par une file durable et une seule machine
d'état (audit §8). C'est la partie la plus risquée : on la fait lentement.

- **R3.1 — Assignment, Attempt, Delivery** (ORB-011). États et transitions de §8.2, raisons
  terminales, arbre parent/enfant, budgets qui ne grandissent jamais vers l'enfant. *Fait
  quand* : toute transition illégale est refusée ; tous les états se rejouent depuis le journal.
- **R3.2 — Mailbox idempotente** (ORB-012). `enqueue()` pour message direct, webhook, routine,
  enfant, canal ; clés de déduplication de §8.4. *Fait quand* : la même requête envoyée 50 fois
  donne un seul delivery ; un crash entre écriture et accusé ne double rien.
- **R3.3 — Ordonnanceur** (ORB-013). Lanes exclusives, leases avec fencing token, priorités sans
  famine, limites globales/agent/fournisseur (§8.6). *Fait quand* : 1 000 travaux simulés sans
  chevauchement dans une lane ; chacun progresse ; un redémarrage forcé ne crée pas deux
  exécutions.
- **R3.4 — Contrôles** (ORB-015, ORB-016). Éditer, déplacer, retirer avant le claim ; stop
  demandé ≠ stop constaté ; steer ; attente d'un événement ou d'un humain ; pause/reprise.
  *Fait quand* : stop pendant un outil puis crash ne donne ni faux `CANCELLED` ni seconde action.
- **R3.5 — Reprise après crash** (ORB-017, ORB-047). Réconciliation de §8.5 : on rejoue ce qui
  n'a pas d'effet, on passe en `UNCERTAIN` ce qui en a peut-être eu, on le signale au
  propriétaire. Tests de chaos (kill -9 à cinq moments d'un tour). *Fait quand* : tous les
  invariants de §8.3 sont prouvés par des tests reproductibles.
- **R3.6 — Client en ligne de commande.** `telos chat <agent>`, `telos queue`, `telos stop` sur
  l'API interne, pour tester sans interface. *Fait quand* : on envoie un travail à un agent fictif
  (moteur de test) et on le suit jusqu'au bout.

**Démonstration** : on tue Orion en plein travail ; au redémarrage rien n'est perdu, rien n'est
fait deux fois, et ce qui est incertain est dit.

## P4 — Moteurs de modèles

Chaque agent tourne sur un moteur ; un moteur a des sessions, des événements, des capacités.

- **R4.1 — Contrat AgentEngine** (ORB-019). `EngineEvent` (texte, raisonnement visible, outil
  début/résultat, usage, demande d'approbation, artefact, sous-agent, erreur, fin), capacités
  déclarées au démarrage, empreinte des outils. Moteur factice pour les tests. *Fait quand* :
  le moteur factice émet chaque type d'événement et le runtime les journalise tous.
- **R4.2 — Boucle native** (ORB-014). Reprise de `cognition/loop.py` et des fournisseurs API
  (`providers/` : OpenRouter, Anthropic, OpenAI) derrière le contrat ; reprise du contrat de
  cache (`tests/test_runtime_cache.py`) et du repli de modèle. *Fait quand* : un agent répond
  par la boucle native, sur deux fournisseurs ; le test de cache passe.
- **R4.3 — Sessions persistantes** (ORB-020). Une session par agent × fil × moteur ; poignée
  externe, empreintes, invalidation ; la vérité reste le fil canonique. *Fait quand* : trois
  sessions reprennent indépendamment après redémarrage ; en invalider une ne touche pas les autres.
- **R4.4 — Claude Agent SDK** ∥ (ORB-021). Agent durable sur Claude (session, flux, outils
  accordés, stop). *Fait quand* : un agent tient 10 tours, redémarre, reprend ; un changement de
  droits invalide la session.
- **R4.5 — Codex App Server** ∥ (ORB-022). Même contrat. *Fait quand* : nouveau/reprise/stop
  sur le flux réel, panne du processus sans corruption du fil.
- **R4.6 — Passage de relais entre moteurs** (ORB-024). Dossier de relais (sources, contraintes,
  artefacts, état des travaux) quand on change de moteur. *Fait quand* : après bascule, le
  nouveau moteur reprend sans inventer les étapes faites ; rien de privé ne fuit vers un worker.
- **R4.7 — Coûts, quotas, replis** (ORB-025). Usage par agent/fournisseur/travail ; budget
  dépassé = plus de tour ; quota = attente ou relais, jamais de boucle. *Fait quand* : un budget
  atteint arrête net ; l'usage est consultable.
- **R4.8 — Connexion aux fournisseurs sans terminal.** Clé d'API ou connexion à un forfait
  (ChatGPT, Claude) depuis l'API, secret au coffre. *Fait quand* : un fournisseur se branche et se
  débranche sans fichier ni commande.
- *Plus tard (P9 ou après)* : ACP et autres CLI (ORB-023).

**Démonstration** : trois agents sur deux fournisseurs travaillent en parallèle, redémarrent et
reprennent leur conversation.

## P5 — Conversations et collaboration

- **R5.1 — Fils et messages typés** (ORB-026). Auteur typé, parties, pièces jointes,
  références, visibilité, confiance, causalité. *Fait quand* : texte, fichiers et outils gardent
  leur ordre ; la redaction d'une source se propage.
- **R5.2 — Messages directs** (ORB-027). Parler à n'importe quel agent ; contextes étanches.
  *Fait quand* : on alterne entre trois agents sans mélange de contexte.
- **R5.3 — Bus agent↔agent** (ORB-028). Un agent écrit à un autre via la mailbox ; `root_id`,
  profondeur, réponse attendue, échéance ; anti-boucle et budgets (§10.3). *Fait quand* : A
  obtient une réponse de B ; A→B→A en boucle est détecté et arrêté.
- **R5.4 — Canaux** (ORB-029, ORB-030). Membres, mentions, un responsable par travail, relais
  explicite. *Fait quand* : réassigner 20 fois en concurrence ne crée jamais deux responsables ;
  un non-membre ne lit rien.
- **R5.5 — Fichiers partagés** (ORB-031). Artefacts versionnés entre espaces. *Fait quand* :
  téléchargeable par un membre, refusé à un autre.
- **R5.6 — Délégation par Orion.** Orion crée un travail pour un agent, suit, synthétise.
  *Fait quand* : « fais faire une recherche par l'agent chercheur et résume-moi » aboutit avec la
  trace des étapes.

**Démonstration** : un projet à trois agents fait recherche → développement → relecture, avec
artefacts et preuves ; une interruption ne double aucun envoi.

## P6 — Mémoire et savoir-faire

- **R6.1 — Mémoire sourcée, reprise** (cf. `memory/`). Faits datés, sources, oubli propagé,
  recherche. *Fait quand* : les tests de la v1 qui comptent passent sur la v2.
- **R6.2 — Portées** (ORB-032, §7.4). `owner-private`, `agent-private`, `project`, `channel`,
  `shared`, `session`. Un fait référencé dans plusieurs portées sans être copié. *Fait quand* : un
  agent sans accord ne voit jamais un fait privé (tests négatifs) ; l'oubli traverse les portées.
- **R6.3 — Écritures et conflits** (ORB-033). Écriture différée, versions. *Fait quand* : 100
  courses suppression/consolidation sans résurrection.
- **R6.4 — Mémoire visible et modifiable** (ORB-034). Ce qu'un agent sait de lui et du projet,
  lisible et corrigible. *Fait quand* : une correction est un nouvel événement ; l'oubli se voit.
- **R6.5 — Skills et MCP par agent** (ORB-035). Catalogue, installation, accord par agent.
  *Fait quand* : retirer un MCP le retire même d'une session ouverte.
- **R6.6 — Passe de nuit par portée.** Consolidation, révision (reprise de la passe de nuit
  D174/D176). *Fait quand* : elle tourne pour Orion et pour un worker sans mélanger.

## P7 — Orion personnel

Ce qui fait d'Orion un compagnon et pas un IDE à bots, porté par l'agent `primary`.

- **R7.1 — Initiative et attention.** Reprise du moteur d'initiative, de l'arbitrage
  d'attention et des heures calmes ; Orion parle de lui-même via la mailbox, chaque décision
  journalisée. *Fait quand* : une initiative suit le même chemin qu'un message, et se tait la nuit.
- **R7.2 — Missions et engagements.** Reprise des missions comme `Assignment` à long terme.
  *Fait quand* : une mission de plusieurs jours survit à trois redémarrages sans rappel double.
- **R7.3 — Contrat des modules.** Nouveau contrat de module (capacités, outils, réglages,
  droits demandés) et catalogue. *Fait quand* : un module s'installe et se désinstalle depuis
  l'API, sans redémarrage.
- **R7.4 — Canaux externes.** Telegram, iMessage, téléphone en modules, routés vers un agent.
  *Fait quand* : un message Telegram arrive dans le bon fil, la réponse repart par l'outbox.
- **R7.5 — Sources de vie** (une tâche par lot, à découper au moment venu) : agenda, mail,
  contacts, fichiers, flux… reprises une à une selon leur usage réel.
- **R7.6 — Evals.** Reprise de `evals/` sur la v2, cas multi-agent ajoutés. *Fait quand* :
  `python -m evals` tourne sur la v2 et son score est noté dans `SUIVI.md`.

## P8 — API et Workbench

- **R8.1 — API versionnée** (ORB-037). REST + schémas Pydantic, OpenAPI, erreurs stables, tout
  mutateur soumis aux droits. Authentification (passkey, reprise de D125+). *Fait quand* :
  l'OpenAPI est validée ; aucun endpoint mutateur sans contrôle.
- **R8.2 — Flux temps réel** (ORB-038). SSE ou WebSocket avec reprise depuis un curseur. *Fait
  quand* : deux minutes sans réseau, la reconnexion restitue tout.
- **R8.3 — Choix de la pile front.** Prototype court, décision écrite (D…). Une seule interface
  pour le bureau, le web et la PWA. *Fait quand* : décision acceptée par le propriétaire.
- **R8.4 — Premier lancement.** Assistant : langue, nom de l'agent personnel, fournisseur, connexion, premier
  message. *Fait quand* : une personne qui n'a jamais vu Telos arrive à son premier échange sans
  aide. L'agent personnel prend le nom choisi ici.
- **R8.5 — Agents, canaux, conversation** (ORB-039). Barre latérale, conversation riche
  (outils, fichiers, réactions), création et réglage d'un agent. *Fait quand* : 3 agents, 2
  canaux, 5 fils, navigation fluide sur ordinateur et téléphone.
- **R8.6 — Travaux, file, approbations** (ORB-040). Inspecteur de travail, Stop, file
  éditable, approbations. *Fait quand* : chaque action de l'interface a un effet vérifiable ou une
  erreur claire.
- **R8.7 — Réglages sans fichier** (ORB-041). Fournisseurs, skills, MCP, droits, espaces,
  mémoire, sauvegarde. *Fait quand* : tout ce que la v1 réglait dans `orion.toml` se règle ici.
- **R8.8 — Mobile et notifications.** PWA, push, notifications agrégées selon l'attention.

**Démonstration** : les scénarios du §19 de l'audit faits depuis un ordinateur et un téléphone,
sans terminal.

## P9 — Automatisations et ordinateur

- **R9.1 — Workflows DAG** (ORB-042). Définitions versionnées, validation, exécution par nodes
  sur le moteur de travail. *Fait quand* : un graphe cyclique est refusé ; stop/redémarrage
  conserve chaque node.
- **R9.2 — Routines et déclencheurs** (ORB-043). Horaires, webhooks, événements. *Fait quand* :
  10 occurrences donnent 10 exécutions, pas 11 ; un webhook réessayé ne double rien.
- **R9.3 — Éditeur visuel de workflows.** Dans le Workbench.
- **R9.4 — Navigateur par agent** (ORB-044). Reprise du navigateur v1, un profil par agent,
  passage de la main au propriétaire, coffre d'identifiants. *Fait quand* : deux agents naviguent
  en parallèle sans partager de cookies.
- **R9.5 — Ordinateur** (ORB-045). Contrôle d'une machine appairée (reprise des mains). *Fait
  quand* : seul l'agent autorisé contrôle la machine ; une déconnexion suspend le travail.
- **R9.6 — Observabilité** (ORB-046). Santé, coûts, blocages par agent, une alerte par
  incident.
- **R9.7 — ACP et autres CLI** (ORB-023).
- **R9.8 — Voix** (D296). Reprise de la voix v1 au téléphone (D40) ; réponses lues et appel
  vocal avec n'importe quel agent depuis le Workbench et la PWA. Chaque phrase entre par la
  mailbox du fil, comme un message écrit. *Fait quand* : on appelle un agent, il répond avec le
  contexte de son fil ; ce qui a été dit se relit ensuite dans ce fil.
- **R9.9 — Paiements** (D296). Reprise du garde-fou de paiement du navigateur v1 (D265) pour
  tous les agents : un achat est un effet par l'outbox, toujours soumis à l'accord du
  propriétaire avec l'aperçu exact (marchand, articles, montant), droit `pay` accordé par agent
  avec un plafond. Jamais de virement entre comptes ni d'ordre de bourse, même avec accord.
  *Fait quand* : un achat sans accord ou au-dessus du plafond est refusé ; un achat accordé puis
  rejoué après un crash ne paie qu'une fois (ou passe en `UNCERTAIN`).

## P10 — Distribution

- **R10.1 — Image serveur.** Docker (et script une commande pour un VPS nu), mises à jour avec
  retour arrière (reprise D94). *Fait quand* : un VPS vierge a Orion en une commande, le reste
  dans le navigateur.
- **R10.2 — App de bureau.** Fenêtre native autour de l'interface web, cœur Python embarqué,
  installeurs Mac/Windows/Linux, mise à jour. Vérification du nom « Telos » côté marques avant toute diffusion publique (D294). Choix de la technique écrit (D…). *Fait quand* :
  installation par double-clic, Orion continue quand la fenêtre est fermée.
- **R10.3 — Passer du bureau au serveur.** Exporter son instance et la reprendre ailleurs (via
  R1.6). *Fait quand* : une instance de bureau déménage sur un serveur sans perte.
- **R10.4 — Hébergé.** Inscription, création d'une instance isolée par personne, accès,
  sauvegardes, suppression du compte. Pour l'instant le propriétaire paie les modèles (D295) : plafond de dépense par instance, coupure nette quand il est atteint. *Fait quand* :
  deux comptes de test ne peuvent rien voir l'un de l'autre, même avec un accès au conteneur
  voisin refusé par construction.
- **R10.5 — Documentation utilisateur.** Installer, démarrer, sauvegarder, partir. Pour des
  non-développeurs.

## P11 — Bascule

- **R11.1 — Import de la v1.** Lire un journal v1 et en tirer l'état v2 (agent `primary`, fils,
  mémoire, missions, réglages, coffre). *Fait quand* : une copie de l'instance réelle importée
  dans un environnement isolé ; ce que le propriétaire attend d'Orion y est.
- **R11.2 — Parité et canari.** Matrice de parité (audit §2 et §19), evals, usage réel sous
  budget strict. *Fait quand* : la matrice est verte ou ses écarts acceptés par le propriétaire.
- **R11.3 — Remontée et ménage.** `next/` devient la racine, `src/orion` v1 et ses docs partent
  (gardés dans l'historique git), `CLAUDE.md` et `README.md` réécrits. *Fait quand* : une seule
  base de code, CI verte.
