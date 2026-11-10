# Refonte v2 — fiches d'inspiration (R0.2)

*Rédigé le 09/11/2026. Sources publiques seulement (README, sites, annonces, presse) ; aucune
ligne de code lue pour être reprise. Pour OpenBot et OpenMausBot, l'audit du 09/11/2026
(`audit OpenBot, non publié`) a déjà étudié le code : on s'y renvoie (`§`), sans rien en
copier.*

Quatre produits, deux familles :

- **Équipes d'agents sur sa machine** : OpenBot, OpenMausBot. Des agents nommés, chacun avec son
  modèle et son espace, qui se parlent dans des canaux. Proches de ce qu'Orion veut héberger.
- **Un agent toujours allumé, dans le nuage** : OpenAI Dots, Claude Duet. Un seul agent qui
  travaille entre les conversations, sur sa propre machine virtuelle, et revient vers vous. Proches
  de ce qu'Orion est déjà, en plus poli.

Chaque fiche : ce que voit l'utilisateur, ce qu'on retient, les sources. La synthèse « on prend /
on ne prend pas » est à la fin ; **c'est elle que le propriétaire valide**.

---

## OpenBot

**Ce que c'est.** Une app de bureau (Mac, Windows, Linux), plus un serveur auto-hébergé (systemd
ou Docker) avec un client web et une app iPhone qui se connecte à l'hôte. Slogan : « Persistent AI
teammates on your own computer ». Gratuit pour un usage non commercial (PolyForm Noncommercial
1.0.0) ; une offre « Teams » hébergée et payante pour les entreprises.

**Vu par l'utilisateur.**

- On crée des agents (nom, instructions, espace de travail), y compris en le demandant en
  langage naturel. Chacun tourne sur un moteur au choix : Codex, Claude Code, Gemini, Grok,
  OpenCode, Cursor, Cline… (via ACP), une API compatible OpenAI, ou un modèle local (Ollama,
  LM Studio). Il **réutilise les abonnements déjà payés** par les connexions des CLI locales.
- Chaque agent garde son espace et sa conversation au redémarrage **et quand on change de
  fournisseur** ; si un forfait atteint sa limite, il passe sur un modèle de secours. Le contexte
  est compacté avant de déborder.
- Les messages passent par des **files FIFO qui survivent aux plantages**, qu'on met en pause,
  reprend ou annule.
- Les agents s'écrivent, répondent, réagissent, s'envoient fichiers et images.
- **Canaux partagés** : un seul responsable par tâche, délégation explicite, historique commun ;
  Stop, Reprendre, Réassigner, Archiver, Restaurer.
- Un navigateur intégré que l'agent pilote et qu'on regarde ; contrôle de l'ordinateur en option.
- **Workflows** : enchaîner agents, modèles et étapes d'approbation (« rapport hebdo, validé
  avant publication »).
- Données locales ; comptes optionnels (code par mail).
- **Revers** : après un accord au premier lancement, les agents lisent, écrivent, exécutent et
  vont sur le réseau **sans plus rien demander**. Le README conseille de ne confier que des tâches
  sûres et de garder des sauvegardes.

**Ce qu'on retient.** C'est la forme cible de l'expérience (audit §1.1) : des agents persistants
qu'on choisit, à qui on parle, qui gardent leur fil d'un moteur à l'autre, dans une file durable,
avec un poste de travail pour tout voir. On n'en prend pas le modèle de sécurité : chez nous le
gardien vérifie chaque effet (D291, `00-cap.md`).

**Sources.**
[openbot.run](https://openbot.run/) ·
[README, github.com/nightly-labs/openbot](https://github.com/nightly-labs/openbot) ·
audit §1, §2, §22.2.

---

## OpenMausBot

**Ce que c'est.** Une app de bureau libre (Apache 2.0, sauf un dossier `enterprise/`) : « your own
team of AI bots, in a chat app ». Chaque bot est un vrai agent qui tourne par la CLI Claude, Codex
ou Grok déjà installée.

**Vu par l'utilisateur.**

- Les bots sont **des contacts dans une messagerie** : on les épingle, renomme, duplique, masque.
  Chacun a sa personnalité, son modèle (changeable en pleine conversation), son ordinateur, ses
  applis connectées.
- **Canaux** séparés (travail, perso, projet), chacun avec son historique, ses instructions
  communes et ses bots. Un petit modèle rapide **route un message sans mention** vers le bot le
  plus adapté.
- **Équipes en un fichier** : une équipe entière s'installe ou se partage en un Markdown/YAML.
- **Assignments** : on confie un travail dans la conversation, le bot rend compte en route ; une
  CLI peut confier un travail et attendre que le bot et ceux qu'il a mobilisés aient fini.
- **Proactivité** : horaires, webhooks, événements d'applis (un nouveau mail), réglés en langage
  naturel. Rien ne se déclenche si l'app est fermée.
- Applis connectées (Composio : Gmail, Slack, GitHub…) autorisées une fois pour tous les bots ;
  MCP maison.
- **Approbations en cartes** dans la conversation (Autoriser / Refuser) avant une commande ou une
  modification de fichier ; les questions du bot arrivent aussi en cartes.
- **Ordinateurs** : bureau Linux dans le nuage, VM locale isolée, ou (sur accord explicite) la
  machine de l'utilisateur.
- Voix : réponses lues, appel vocal avec un bot.
- Mémoire par fil ; tout est stocké localement (`~/.openmausbot`).

**Ce qu'on retient.** Côté produit : les bots comme contacts, les cartes d'approbation dans le
fil, le routage des messages sans mention, l'équipe partageable en un fichier. Côté architecture
(audit §5, déjà repris dans la feuille de route) : **un seul `Assignment` pour tout travail**
(R3.1), le bac à sable par agent (R2.2), la politique d'outils par agent (R2.5), la mémoire
lisible et corrigible (R6.4), le guetteur de blocages et de coûts (R9.6). Limite à ne pas
reproduire : des déclencheurs qui meurent avec l'app, et des applis autorisées pour tous les bots
d'un coup.

**Sources.**
[README, github.com/milind-soni/OpenMausBot](https://github.com/milind-soni/OpenMausBot) ·
audit §5, §22.3.

---

## OpenAI Dots

**Ce que c'est.** Des agents toujours allumés dans ChatGPT, annoncés au DevDay du 29/09/2026 :
« a dot keeps working when the conversation stops ». Pour les forfaits Pro et Business Premium
(premier dot inclus), bêta pour Enterprise ; hors EEE, Suisse et Royaume-Uni pour Pro. Pas d'API
annoncée.

**Vu par l'utilisateur.**

- On donne à son dot **une responsabilité**, pas une tâche : tenir un lancement, suivre les
  retours clients, relancer une analyse quand de nouvelles données arrivent. Exemple mis en avant :
  il remarque une facture oubliée, la prépare, l'envoie après accord.
- Il **revient vers vous** avec un avancement, une question ou une décision à prendre.
- Il a son propre ordinateur et navigateur dans le nuage, **qu'on peut ouvrir pour regarder ou
  intervenir**. La machine locale n'est accessible que si on la branche exprès.
- **Règles par action**, quatre niveaux : agir sans demander, agir si c'était demandé dans la
  consigne, demander avant, ou vous passer la main. Une revue automatique des actions sensibles,
  qu'aucune règle ne désactive ; certaines actions (changer un mot de passe) restent toujours à
  l'humain.
- **Recherche proactive en lecture seule** : quand on ne lui parle pas, il cherche comment aider,
  mais sans envoyer, modifier, ni piloter le navigateur.
- Mémoire : il hérite des souvenirs de ChatGPT et en forme d'autres (y compris depuis les applis).
  Déconnecter une appli n'efface pas ce qu'il en a appris ; effacer ses souvenirs propres =
  supprimer le dot.
- On lui écrit ou on l'appelle depuis ChatGPT (bureau, web, mobile), Slack, Teams, SMS (bêta) ; il
  ne peut pas encore appeler.
- Un seul dot au départ ; des équipes de dots sont annoncées pour plus tard.
- Les conversations ne comptent pas dans les limites ; le travail de fond puise dans une
  enveloppe du forfait.

**Ce qu'on retient.** La **responsabilité durable** comme unité (c'est la mission d'Orion, R7.2) ;
les **quatre niveaux d'autonomie par action** et le plancher non désactivable (à poser sur les
droits R2.4 et le gardien R2.3) ; le **mode proactif en lecture seule** (l'initiative explore sans
agir, R7.1) ; l'ordinateur de l'agent qu'on peut regarder et reprendre en main (R9.4–R9.5). Contre-
exemple : l'oubli qui ne se propage pas (déconnecter une source laisse ce qui en a été appris) ;
chez nous `redact` se propage (R6.2).

**Sources.**
[Annonce OpenAI, « Introducing dots »](https://openai.com/index/introducing-dots/) (page
inaccessible au robot le 09/11/2026 ; contenu repris des articles suivants) ·
[DataCamp, « OpenAI Dots: Always-On Agents in ChatGPT, Explained »](https://www.datacamp.com/blog/openai-dots).

---

## Claude Duet

**Ce que c'est.** L'agent toujours allumé d'Anthropic, pour les professionnels et petites
entreprises, en préversion depuis le 21/10/2026. App iOS et Android à part, et sur claude.ai ;
sur liste d'attente pour les forfaits Pro et Max aux États-Unis. Tourne sur Claude Opus 5.5.

**Vu par l'utilisateur.**

- **Brief du matin** : un court résumé de ce qui compte dans les applis connectées.
- Il passe en revue les comptes toutes les quelques heures et **n'écrit que quand quelque chose
  demande votre attention** ; on règle de quoi et à quelle fréquence on veut entendre parler.
- Trois onglets : **Chat**, **Tâches** (le travail de fond), **Make** (projets et modèles).
- Il travaille sur **sa propre VM avec navigateur** : le téléphone ou le PC peuvent être éteints.
- Il lit et prépare librement, mais **avant d'envoyer, payer, signer ou supprimer, il montre
  exactement ce qu'il va faire et attend le feu vert**. Certaines actions restent interdites même
  avec accord (bourse, virements entre comptes) ; il refuse par défaut les numéros de carte et
  pièces d'identité.
- Achats en ligne via Link (Stripe) ou Shop Pay, sur accord.
- Reprend les outils, projets, conversations, mémoire et skills du compte Claude ; plus de 6 000
  connecteurs.
- Le travail de fond consomme les mêmes limites que Claude ; un testeur les a vite épuisées.
- Limites : pas de fichiers locaux ; on ne regarde pas son navigateur en direct.
- Il range les sujets récurrents dans leurs propres fils et tient la liste de ce qu'il fait et de
  ce qu'il attend de vous (Every).
- Accueil partagé : « le premier agent personnel que j'appellerais un outil pro » (Every), mais
  aussi « beau, et j'ai quand même oublié de m'en servir » (titre de Lenny's Newsletter).

**Ce qu'on retient.** C'est ce qu'Orion v1 fait déjà (brief, attention, heures calmes, gardien) :
Duet confirme le cap, et montre la barre de finition. À prendre : **l'aperçu exact de l'effet
avant accord** (l'approbation montre ce qui partira, pas un résumé ; R2.3, R8.6) ; la **liste
d'actions interdites même avec accord** ; les **réglages d'attention en langage simple** (R7.1,
R8.8) ; un onglet **Tâches** distinct de la conversation (R8.6). Leçon de « j'ai oublié de m'en
servir » : la valeur doit venir à l'utilisateur (initiative, canaux qu'il utilise déjà, R7.4),
pas l'obliger à ouvrir une app de plus. Le coût du travail de fond doit se voir et se borner
(R4.7, D295).

**Sources.**
[TechCrunch, 22/10/2026](https://techcrunch.com/2026/10/22/claude-duet-app-is-anthropics-bet-on-agents/) ·
[Zapier, « What Is Claude Duet? »](https://zapier.com/blog/claude-duet/) ·
[Every, « Vibe Check: Duet »](https://every.to/vibe-check/vibe-check-duet-anthropic-s-always-on-agent) ·
[Lenny's Newsletter, « Claude Duet is beautiful. I still forgot to use it »](https://www.lennysnewsletter.com/p/claude-duet-is-beautiful-i-still).

---

## Synthèse — à valider par le propriétaire

### On prend

| # | Quoi | D'où | Où dans la feuille de route |
|---|---|---|---|
| 1 | Des agents persistants nommés, chacun son moteur, son espace, son fil, qu'on crée aussi en le demandant | OpenBot, OpenMausBot | R2.1, R2.2, R5.2 |
| 2 | Le fil survit au redémarrage et au changement de moteur ; modèle de secours quand un forfait sature | OpenBot | R4.3, R4.6, R4.7 |
| 3 | Réutiliser les abonnements déjà payés (connexion à un forfait, CLI installées) | OpenBot, OpenMausBot | R4.4, R4.5, R4.8 |
| 4 | Une file durable qu'on met en pause, reprend, annule | OpenBot | R3.2–R3.4 |
| 5 | Canaux avec un seul responsable par travail, délégation explicite, Stop/Réassigner | OpenBot | R5.4 |
| 6 | Un seul `Assignment` pour tout travail, quelle qu'en soit l'origine | OpenMausBot | R3.1 |
| 7 | Bots comme contacts (épingler, renommer, dupliquer, masquer) | OpenMausBot | R2.1, R8.5 |
| 8 | Routage d'un message sans mention vers l'agent adapté, par un petit modèle | OpenMausBot | R5.4 |
| 9 | Approbations et questions en cartes dans le fil | OpenMausBot | R8.6 |
| 10 | Aperçu exact de l'effet avant accord (ce qui partira, tel quel) | Duet | R2.3, R8.6 |
| 11 | Autonomie réglable par action en niveaux (agir / agir si demandé / demander / passer la main) avec un plancher non désactivable et des actions interdites même avec accord | Dots, Duet | R2.4, R2.3 |
| 12 | Proactivité en lecture seule quand on ne parle pas à l'agent ; agir reste soumis aux droits | Dots | R7.1 |
| 13 | Confier une responsabilité durable, pas seulement une tâche ; l'agent revient avec avancement, question ou décision | Dots | R7.2 |
| 14 | Brief et alertes réglés en langage simple ; n'écrire que si ça mérite l'attention | Duet (déjà en v1) | R7.1, R8.8 |
| 15 | Onglet « Travaux » distinct de la conversation | Duet | R8.6 |
| 16 | L'ordinateur/navigateur de l'agent, qu'on peut regarder et reprendre en main | OpenBot, Dots | R9.4, R9.5 |
| 17 | Workflows avec étapes d'approbation ; déclencheurs horaires, webhooks, événements | OpenBot, OpenMausBot | R9.1, R9.2 |
| 18 | Mémoire lisible et corrigible par l'utilisateur (vue projetée du journal) | OpenMausBot | R6.4 |
| 19 | Un guetteur qui signale blocages, boucles, coûts, sans décider à la place | OpenMausBot | R9.6 |
| 20 | Coût du travail de fond visible et plafonné | Duet (contre-exemple) | R4.7, R10.4 |
| 21 | Achats en ligne par l'agent, toujours sur accord, avec l'aperçu exact (marchand, articles, montant) ; jamais de virement ni de bourse (ex-refus H, D296) | Duet | R9.9 |
| 22 | Réponses lues à voix haute et appel vocal avec un agent, depuis l'app et le téléphone (ex-refus I, D296) | OpenMausBot, Dots | R9.8 |

### On ne prend pas

| # | Quoi | D'où | Pourquoi |
|---|---|---|---|
| A | Accès complet sans plus rien demander après le premier lancement | OpenBot | Le gardien vérifie chaque effet (D291, anti-patterns `00-cap.md`) |
| B | Applis autorisées une fois pour tous les agents | OpenMausBot | Les droits sont par agent, vérifiés à chaque effet (R2.4) |
| C | Déclencheurs qui ne marchent que si l'app est ouverte | OpenMausBot | Orion tourne aussi en serveur et en hébergé (D292) |
| D | Un oubli qui ne se propage pas (déconnecter une source garde ce qui en a été appris) | Dots | `redact` se propage (règles CLAUDE.md, R6.2) |
| E | Mémoire seulement par fil | OpenMausBot | Mémoire sourcée avec portées (R6.1, R6.2) |
| F | Agent enfermé dans un seul fournisseur et un seul cloud | Dots, Duet | Multi-fournisseurs, instance à soi (D292) |
| G | Une app de plus qu'il faut penser à ouvrir | Duet (critique) | L'initiative et les canaux existants portent la valeur (R7.1, R7.4) |
| H | ~~Achats et paiements par l'agent~~ | Duet | Repris le 09/11/2026 : voir « on prend » 21 (D296) |
| I | ~~Voix et appel vocal avec un agent~~ | OpenMausBot, Dots | Repris le 09/11/2026 : voir « on prend » 22 (D296) |
| J | Équipe partagée en un fichier Markdown/YAML | OpenMausBot | Utile mais pas prioritaire ; à rouvrir avec le catalogue de modules (R7.3) |
| K | Tout code d'OpenBot | OpenBot | PolyForm Noncommercial (audit p. 6) |

**Validée par le propriétaire le 09/11/2026**, avec H et I repris (D296) : ils deviennent les
points 21 et 22 et les tâches R9.8 et R9.9. Les points 1 à 20 tombent dans des tâches déjà
prévues. J reste un refus *pour l'instant*.
