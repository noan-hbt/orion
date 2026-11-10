# Refonte v2 — le cap

*Ouvert le 09/11/2026. Décisions D291 à D295. Référence : `audit OpenBot, non publié` (ce
dossier).*

## Le nom : Telos (D294)

*Telos* (τέλος) est le mot grec de la fin, au sens du **but** : ce en vue de quoi une chose
existe. Chez Aristote, c'est la « cause finale ». Le telos du gland est le chêne, celui de
l'œil est de voir. On ne comprend vraiment une chose qu'en sachant vers quoi elle tend. Du même
mot vient *teleios*, « achevé, accompli » : atteindre son telos, c'est aller au bout.

Pourquoi ce nom :

- **Comprendre le but, pas seulement la demande.** Un bon agent cherche ce que son
  propriétaire veut vraiment atteindre derrière ce qu'il dit, et l'aide à y aller, parfois
  avant qu'il le demande.
- **Aller au bout.** La v1 laissait des choses à moitié faites. Le critère de réussite de la v2
  est le travail mené à terme et prouvé (audit §1.4) : un travail n'est fini que quand son but
  est atteint.
- **Une équipe tendue vers un même but.** Chaque agent a sa fonction, et tous servent les buts
  d'une seule personne.

Le produit s'appelle Telos ; l'agent personnel de chacun porte le nom que son propriétaire lui
donne au premier lancement (le nôtre reste Orion).

## Pourquoi

Orion v1 est un compagnon personnel solide : un journal append-only, une mémoire sourcée, un
gardien, de l'initiative, des missions. Mais il ne tourne que pour une personne qui sait
installer un serveur et éditer `orion.toml`, et c'est **un seul agent** qui fait tout.

La v2 vise autre chose :

- **une équipe d'agents persistants** : Orion, l'agent personnel, plus des agents spécialisés
  (chercheur, développeur, secrétaire…) que l'on crée, à qui l'on parle directement, qui ont
  chacun leur modèle, leurs droits, leur espace de travail et leur mémoire de travail, et qui
  collaborent dans des canaux ;
- **un poste de travail** (le Workbench) où l'on voit les agents, leurs conversations, leurs
  travaux en cours, la file d'attente, les approbations, le navigateur, et où l'on intervient ;
- **ouvert à n'importe qui** : rien ne demande de savoir coder. On installe, on se connecte à un
  fournisseur de modèle, tout se règle dans l'interface.

Inspirations nommées par le propriétaire : OpenBot, OpenMausBot, OpenAI Dots, Claude Duet. Ce
sont des références de comportement, pas de code (OpenBot est sous PolyForm Noncommercial :
aucune copie de code, voir l'audit, page 6).

## Ce que la v2 est, en dix phrases

1. On ouvre Orion et on voit ses agents, ce qu'ils savent faire et ce qu'ils font.
2. On parle à Orion ou à un agent spécialisé, et on retrouve le fil en revenant.
3. Orion délègue, gère les dépendances, synthétise les résultats.
4. Les agents se parlent et collaborent dans un canal, sans boucle ni réponses en double.
5. Un agent garde ses fichiers, ses skills, son modèle, sa session et son navigateur.
6. On suit les outils, la file, les progrès, les approbations et les erreurs, et on intervient.
7. Une routine peut mobiliser plusieurs agents des heures ou des jours, même après un redémarrage.
8. L'accès à la vie privée, aux comptes et aux machines reste borné et réversible.
9. Si une action a peut-être été faite, Orion le dit et ne la refait pas sans preuve.
10. Orion apprend les usages du propriétaire et termine de mieux en mieux ce qu'on lui confie.

## Les choix de départ

### Nouveau socle, briques reprises (D291)

On ne migre pas la v1 pas à pas, et on ne repart pas non plus de rien. La v2 est un **nouveau
projet, propre, dans `next/`**, à côté de la v1 qui continue de tourner. On y **reprend, après
relecture**, ce que la v1 a de prouvé ; le reste est réécrit pour la nouvelle forme.

| Repris (relu, adapté) | Réécrit |
|---|---|
| Journal append-only, HLC, ids, upcast, projections | Runtime (un moteur de travail unique : Assignment) |
| Gardien, outbox, coffre, `SecretRef` | Configuration (en base, réglée dans l'interface, plus de TOML à éditer) |
| Mémoire datée et sourcée, oubli propagé (`redact`) | Conversations (fils, canaux, messages typés) |
| Initiative, attention, heures calmes, missions | Fournisseurs (moteurs à sessions, pas seulement `complete`) |
| Navigateur, coffre d'identifiants, mains | Interface (Workbench), installation, mises à jour |
| Evals et cas réels | Modules : contrat repensé, catalogue |

Règles :

- **Rien n'est importé depuis `src/orion`.** Une brique reprise est copiée dans `next/`, relue,
  simplifiée, testée. Le paquet v2 s'appelle `telos` et vit dans son propre projet
  (`next/pyproject.toml`), avec ses tests et sa CI.
- **La v1 n'évolue plus**, sauf correctif urgent pour l'instance en service.
- **La bascule est la dernière partie** : import des données de l'instance v1, parité vérifiée,
  puis `next/` remonte à la racine et l'ancien code part.
- Les invariants de la v1 restent (CLAUDE.md, « Rules ») : journal append-only, projections
  reconstructibles, provenance et confiance, échec fermé, pas de secret en clair, tout effet
  externe par l'outbox, initiative journalisée.

### Une instance = un propriétaire, trois façons de l'avoir (D292)

Le cœur ne connaît qu'**un propriétaire et ses agents**. Pas de multi-locataire dans le code
métier : c'est ce qui garde la mémoire privée hors de portée des autres.

Trois distributions du même cœur :

1. **App de bureau** (Mac, Windows, Linux) : un installeur, Orion tourne sur la machine,
   s'ouvre dans une fenêtre. Le plus simple pour démarrer.
2. **Serveur auto-hébergé** : une image (Docker) ou un script en une commande sur un VPS, puis
   tout se fait dans l'interface web. Pour l'avoir allumé en permanence.
3. **Service hébergé** : on s'inscrit, on obtient **sa propre instance isolée** (un conteneur,
   ses données, ses secrets). L'hébergement orchestre des instances ; il ne mélange jamais des
   données de deux personnes dans une même instance.

Conséquences pour tout le code :

- **Aucun réglage n'exige un fichier** ni une ligne de commande. Le premier lancement est un
  assistant (choisir un fournisseur, se connecter, nommer son Orion).
- **Les chemins, ports et services sont découverts**, pas configurés à la main.
- **Les secrets** viennent de l'interface et vont au coffre ; jamais dans un fichier lisible par
  un agent.
- **Une même interface web** sert les trois : le bureau l'affiche dans une fenêtre, le serveur
  et l'hébergé dans le navigateur et en PWA sur le téléphone.

### Le suivi de la refonte (D293)

Le travail de la refonte est suivi **dans le dépôt**, pas dans Jira (mis de côté pour
l'instant) : `01-feuille-de-route.md` dit quoi faire, `SUIVI.md` dit où on en est. Le protocole
de travail est dans `CLAUDE.md` (« Refonte v2 »).

## Ce qu'on ne sacrifie pas

- Le journal temporel, la provenance et le droit de retirer un fait.
- Le gardien indépendant, qui vérifie les effets et garde les secrets.
- La proactivité qui respecte le coût d'une interruption.
- Les missions et engagements personnels : c'est ce qui distingue Orion d'un IDE à bots.
- Le fonctionnement autonome, sans PC allumé (mode serveur et hébergé).
- L'état `UNCERTAIN` : une absence de réponse n'est pas une absence d'effet.
- La réponse rapide par le moteur natif, sans lancer une session de coding agent à chaque
  question.

## Anti-patterns interdits (audit §20.2)

- Un « agent » qui n'est qu'Orion avec un autre prompt système.
- Une `asyncio.Queue` comme file de travail : la file est durable ou elle n'existe pas.
- Des agents qui ne sont que des outils d'Orion : on doit pouvoir leur parler directement.
- Dupliquer tout le contexte du propriétaire dans chaque agent.
- Des droits accordés à la création et jamais revérifiés : on vérifie à chaque effet.
- Rejouer un outil faute de résultat.
- Des secrets dans les fichiers d'un agent.
- Faire l'interface d'abord : elle viendrait masquer un runtime qui perd des messages.
- Copier le code d'OpenBot.

## Glossaire

**Agent** : identité durable (instructions, modèle, droits, espace, mémoire). `primary` =
Orion, le seul à porter la vie personnelle ; `worker` = agent spécialisé, droits réduits.
**Engine** : ce qui produit les tours (boucle native, Claude Agent SDK, Codex, ACP…).
**Thread** : conversation canonique, indépendante de la session d'un moteur.
**ProviderSession** : état privé d'un moteur, recréable.
**Assignment** : travail durable (parent/enfant), avec un état et un budget. **Attempt** : une
exécution d'un assignment. **Delivery** : un ordre en file. **Lane** : ce qui empêche deux
exécutions simultanées sur la même ressource.
**Channel** : conversation partagée entre agents, avec un responsable.
**ToolEffect** : action, éventuellement externe, avec sa preuve ou son incertitude.
**Workspace** : l'espace disque d'un agent. **Memory scope** : qui peut voir un souvenir.
