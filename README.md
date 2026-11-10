<img src="docs/assets/banner.jpg" alt="Orion. Un agent personnel toujours allumé, qui vit sur ton serveur et n'agit qu'avec ton accord." width="100%">

<p align="center">
  <a href="#déployer-sur-un-serveur">[installer]</a>&nbsp;&nbsp;
  <a href="#ce-quil-fait">[ce qu'il fait]</a>&nbsp;&nbsp;
  <a href="#comment-cest-fait">[architecture]</a>&nbsp;&nbsp;
  <a href="#écrire-un-module">[écrire un module]</a>&nbsp;&nbsp;
  <a href="docs/DECISIONS.md">[décisions]</a>
</p>

<p align="center">
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-efe9da?labelColor=000000&logo=python&logoColor=efe9da">
  <img alt="Auto-hébergé" src="https://img.shields.io/badge/auto--h%C3%A9berg%C3%A9-Debian%20%C2%B7%20Ubuntu-efe9da?labelColor=000000">
  <img alt="Pyright strict" src="https://img.shields.io/badge/pyright-strict-efe9da?labelColor=000000">
  <img alt="Ruff" src="https://img.shields.io/badge/lint-ruff-efe9da?labelColor=000000">
</p>

Orion est un agent personnel toujours actif. Il vit sur ton serveur, te parle depuis une app
sur ton iPhone (ou par Telegram, iMessage, le téléphone), se souvient de ta vie, agit pour toi
avec ton accord, et sait s'entendre avec les Orion d'autres personnes.

Il ne se contente pas de répondre : il garde tes engagements, te prévient avant ce qui compte,
repense la nuit à ce qui est resté ouvert, poursuit des missions pendant des jours, et ne te
parle en premier que quand ça vaut ton attention.

| | |
|---|---|
| 🧠 **Il se souvient** | Des faits datés et sourcés, jamais écrasés, relus chaque nuit. « Comment tu sais ça ? » a toujours une réponse. |
| 🔭 **Il parle en premier, avec mesure** | Points du matin et du soir, alertes avant une échéance, relances. Au plus 12 fois par jour, chaque fois avec son « pourquoi maintenant ». |
| 🛡️ **Rien ne sort sans ton oui** | Un gardien séparé détient les secrets et vérifie chaque effet sur le monde : mail, message, formulaire, commande. |
| 🤝 **Il s'entend avec les autres Orion** | « Cale un déjeuner avec Tom » : les deux Orion se mettent d'accord, en ne partageant que tes créneaux libres. |
| 🧩 **Il s'étend par modules** | Agenda, mail, navigateur, Home Assistant, missions… Le cœur reste petit ; le reste s'active dans `orion.toml`. |

## Sommaire

- [À savoir avant d'installer](#à-savoir-avant-dinstaller)
- [Ce qu'il fait](#ce-quil-fait)
- [Déployer sur un serveur](#déployer-sur-un-serveur)
- [L'utiliser](#lutiliser)
- [Sauvegarder et restaurer](#sauvegarder-et-restaurer)
- [Remettre à zéro, désinstaller](#remettre-à-zéro-désinstaller)
- [Le tenir au quotidien](#le-tenir-au-quotidien)
- [Sur ta machine, sans serveur](#sur-ta-machine-sans-serveur)
- [Comment c'est fait](#comment-cest-fait)
- [Développer](#développer)
- [Documentation](#documentation)

## À savoir avant d'installer

- **Un Orion, un propriétaire.** Il est fait pour une personne, toi. D'autres personnes peuvent
  lui écrire si tu le permets, avec ce que tu leur accordes ; leur propre assistant, c'est leur
  Orion à elles, relié au tien (fédération).
- **Il a la main sur son serveur.** Le cœur est root par `sudo` (D164) : chaque commande shell
  t'est soumise avant de partir, mais donne-lui un serveur à lui, pas une machine qui fait autre
  chose.
- **Rien ne sort sans le gardien.** Un mail, un message à un tiers, un formulaire, une commande :
  ton oui sur le texte exact, ou une autonomie que tu lui as accordée, bornée, et que tu retires
  d'un mot (D35, D167). Il ne te parle en premier qu'au plus 12 fois par jour (D104).
- **Ton serveur contient ta vie.** Le journal garde chaque conversation et tout ce qu'il a fait ;
  le gardien garde tes secrets et tes mots de passe. Sauvegarde, chiffre, et efface pour de bon
  si tu arrêtes : tout est décrit plus bas.
- **Ce que ça coûte.** Un VPS (quelques euros par mois) et le modèle : une clé OpenRouter
  (payée à l'usage, plafonnée par tour, `max_cost_usd_per_turn`), ou tes forfaits ChatGPT et
  Claude, qui reprennent les rôles qu'ils peuvent (D62, D100, D147). iMessage et le téléphone
  passent par une ligne Inkbox, payante ; Telegram et l'app sont gratuits.
- **Les secrets ne vont jamais dans un fichier de config** ni dans la conversation : ils se
  saisissent dans l'app et vont droit au gardien (`SecretRef`, D154).

## Ce qu'il fait

**Se souvenir.** Des faits datés et sourcés, jamais écrasés ; les engagements (je dois, on me
doit) ; les situations qui durent (D149) ; les gens de ta vie et leurs liens. Recherche par le
sens et par les mots. Chaque nuit, une passe relit toute la mémoire : doublons, contradictions,
faits périmés (D174). « Comment tu sais ça ? » a toujours une réponse (D38). Oublier une source
efface tout ce qui en vient.

**Parler en premier, avec mesure.** Points du matin et du soir, alerte avant une échéance,
veille sur ta vie trois fois par jour (D150), relances quand quelqu'un ne répond pas (D129),
rappels ponctuels, récurrents ou de lieu, heures calmes, concentration (« je bosse jusqu'à
18 h »). Chaque prise de parole est une décision journalisée, avec son « pourquoi maintenant ».

**Ta vie quotidienne.** Agendas (Google, iCloud, Outlook), mail (tri, brouillons dans ta voix,
envoi, rangement), papiers (rangés, expiration, dossier de location en un PDF), photos et
fichiers lus à l'arrivée (ce qui y est écrit n'est jamais un ordre), vocaux dans les deux sens,
contacts, flux RSS, colis et abonnements, Home Assistant (D161), rendez-vous réservés pour toi
(D73), la veille d'un départ (D77).

**Penser et chercher.** Le web ; son propre navigateur, qu'il conduit seul et qu'il te passe
quand une page a besoin de toi (D116) ; un modèle plus fort pour les questions dures (D46) ; des
missions de plusieurs jours (D47) et des tâches de fond (D110) ; une bibliothèque de tes notes
et de toute votre conversation (D48).

**Te connaître.** Il apprend ce que tu veux et ce que tu ignores, écrit comme toi quand il
rédige pour quelqu'un (D68), ose te contredire une fois (D53, D66), relève ses erreurs et ses
ratés (D69, D177), et tient la chronique de ta semaine (D52).

**Les autres Orion.** Relie ton Orion à celui de quelqu'un par une invitation ; « cale un
déjeuner avec Tom » suffit, et seuls tes créneaux libres sont partagés (D29, D99, D102).

## Déployer sur un serveur

C'est l'installation recommandée : Orion est fait pour tourner jour et nuit.

**Il te faut** un VPS neuf sous Debian 12 ou Ubuntu 24.04 (OVH ou autre), un accès SSH, une clé [OpenRouter](https://openrouter.ai), et un iPhone pour l'app.
Un nom de domaine est facultatif : sans lui, `<ip>.sslip.io` suffit pour le HTTPS.

1. **Domaine (facultatif).** Crée un enregistrement A vers l'IP du VPS (chez OVH : Web Cloud >
   Domaines > Zone DNS).
2. **Installer**, en SSH sur le VPS :

   ```bash
   git clone https://github.com/noan-hbt/orion.git && cd orion
   sudo deploy/install.sh orion.mondomaine.fr     # ou sans argument : <ip>.sslip.io
   ```

   Le script installe tout (Caddy pour le HTTPS, Python, ffmpeg, le navigateur d'Orion, deux
   utilisateurs, les services, le pare-feu), puis pose quatre questions : ton prénom et ton
   fuseau, garder les secrets à part (oui), la clé OpenRouter (vérifiée tout de suite), et
   Telegram en option (un bot créé avec @BotFather).
3. **Appairer l'app.** À la fin, le script affiche un lien et un code. Ouvre le lien dans Safari,
   Partager > « Sur l'écran d'accueil », ouvre Orion depuis l'écran d'accueil, saisis le code
   (valable 10 minutes) et crée la passkey.
4. **Le forfait Claude (facultatif)** se connecte sur le serveur, une fois :
   `sudo orion claude login` (D100, D208).

Ensuite, **plus rien ne se fait en SSH** (D154) : réglages, secrets, modules, forfaits,
téléphones, machines et autres Orion se gèrent dans l'app, et ce qui compte se signe avec
Face ID. Orion se met à jour seul. Relancer `install.sh` met le code à jour sans toucher à la
configuration ni aux secrets.

Tous les détails (iMessage par Inkbox, rappels de lieu, coffre des mots de passe, ports) :
[`deploy/README.md`](deploy/README.md).

## L'utiliser

**Lui parler.** L'app est le canal principal : la conversation, tes accords signés par Face ID,
les notifications, le travail en cours (avec Stop) et tous les réglages. Telegram, iMessage et le
téléphone (Inkbox, D40) marchent aussi.

**Le régler en lui parlant.** « Active le mail », « mets tes points à 9 h », « ajoute Angèle,
elle peut savoir quand je suis libre » : il change ses réglages lui-même (`orion.toml`), avec
ton oui sur le changement exact (D92). Ce qui te protège (le gardien, les canaux, qui peut lui
écrire, le budget) ne change qu'avec ce oui, vérifié par le gardien.

**Connecter tes comptes**, dans l'app ou en lui demandant :

- **Agenda** : l'adresse iCal secrète de chaque agenda (Google : « Adresse secrète au format
  iCal » ; iCloud : lien `webcal://` ; Outlook : « Publier un calendrier »), et tes adresses dans
  `owner_emails`, sinon tes événements passent pour des invitations.
- **Mail** : un mot de passe d'application par boîte (Gmail, iCloud…, en IMAP). Outlook.com
  (OAuth) n'est pas pris en charge.
- **Forfait ChatGPT** : Réglages > ChatGPT.
- **Sites** : quand une page a besoin de toi (connexion, code SMS, captcha), il te passe son
  navigateur dans l'app ; ses connexions restent. Le gardien peut aussi garder tes identifiants
  (Réglages > Mots de passe, ou l'import d'un export KeePass, Bitwarden, Chrome…, D111).
- **Tes machines** : Réglages > Machines donne la commande à lancer sur ton Mac ou ton PC
  (`orion hand pair …`), pour qu'il lise les dossiers que tu partages (D41).

**Ce qu'il peut faire seul.** Par défaut, il demande avant d'agir sur le monde. Pour lui
confier un domaine (envoyer des mails à certains destinataires, remplir des formulaires sur
certains sites), accorde-lui une autonomie quand il la propose ; tu la retires d'un mot.

**Sur le serveur**, pour regarder ce qu'il fait. `sudo orion …` lance la commande sous
l'utilisateur du gardien, avec ses secrets ; `--core` sous celui du cœur, qui tient le journal
(`doctor`, `memory` et `chat` y vont d'office) :

```bash
sudo orion doctor                        # configuration, stockage, état de chaque module
sudo orion --core simulate --days 7      # ce qu'il enverrait cette semaine, sans rien envoyer
sudo orion --core week                   # tours interrompus, erreurs d'outils, corrections, coût
sudo orion --core initiative             # ce qu'il a appris de tes retours, source par source
sudo orion --core misses                 # ses ratés : tes 👎 et tes corrections
```

## Sauvegarder et restaurer

**Chaque nuit, tout seul**, vers 4 h 15 : une copie vérifiée du journal du cœur et du registre
du gardien va dans `/srv/orion/backups/` (30 copies gardées). La mémoire, les personnes, les
rappels se reconstruisent à partir du journal. Ces copies ne gardent **que les journaux**, et
restent sur le serveur.

**Une sauvegarde complète**, à lancer toi-même (D290) : réglages, secrets, connexions aux
forfaits, coffre des mots de passe, modules, fichiers, photos, navigateur et ses sites
connectés.

```bash
sudo /srv/orion/app/deploy/backup.sh
```

Il demande s'il faut sauvegarder ou restaurer, où ranger l'archive (`/root` par défaut) et
comment la chiffrer : une phrase de passe (age ou gpg), une clé publique age, ou rien. Orion
est arrêté quelques secondes le temps de la copie, et les journaux sont vérifiés avant que la
copie compte. **Copie ensuite l'archive hors du serveur**, par exemple :

```bash
rclone copy /root/orion-full-<date>.tar.gz.age ovh:orion-backups
```

Sans questions, pour un timer à toi :

```bash
sudo /srv/orion/app/deploy/backup.sh backup --encrypt age:<clé publique> --yes
```

**Restaurer**, sur le même serveur ou un neuf : lance d'abord `install.sh` sur un serveur neuf
(avec le même domaine, sinon il faudra réappairer l'app), puis

```bash
sudo /srv/orion/app/deploy/backup.sh restore     # propose les archives de /root
```

L'archive est déchiffrée et vérifiée avant qu'Orion soit arrêté ; ce qui était là est gardé à
part (`/root/orion-before-restore-<date>.tar.gz`), et se restaure de la même façon. Si ChatGPT
ne répond plus ensuite, reconnecte-toi dans l'app : sa connexion change à chaque
rafraîchissement.

Pour remettre seulement le journal d'une nuit : arrête les deux services, copie
`journal.sqlite3` de `/srv/orion/backups/core/<date>/` dans `/srv/orion/data/`, supprime
`memory.sqlite3` (reconstruit au démarrage), redémarre.

## Remettre à zéro, désinstaller

**Remise à zéro** : Orion oublie tout ce qu'il a vécu (conversations, mémoire, rappels,
missions, fichiers, navigateur), mais garde ses réglages, ses secrets, ses modules et tes
connexions aux forfaits.

```bash
sudo /srv/orion/app/deploy/reset.sh               # le gardien et les sauvegardes restent
sudo /srv/orion/app/deploy/reset.sh --guardian    # ... le gardien oublie aussi (accords, mots de passe)
sudo /srv/orion/app/deploy/reset.sh --backups     # ... et les sauvegardes de la nuit
```

Une copie de ce qui part est gardée d'abord dans `/root/orion-reset-<date>.tar.gz`
(`--no-archive` pour n'en garder aucune).

**Désinstaller** : retire tout ce que `install.sh` a posé (services, code, Python, navigateur,
données, secrets, règle sudo, utilisateurs, site Caddy).

```bash
sudo /srv/orion/app/deploy/uninstall.sh            # garde une archive dans /root
sudo /srv/orion/app/deploy/uninstall.sh --purge    # rien n'est gardé
```

Sans `--purge`, données, configuration et secrets vont d'abord dans `/root/orion-<date>.tar.gz`.
Pour revenir plus tard : `install.sh`, puis `backup.sh restore` sur cette archive. Pour tout
effacer pour de bon, supprime aussi les archives de `/root` et celles que tu as copiées
ailleurs : elles contiennent ta vie avec Orion et tes mots de passe. Restent en place Caddy,
uv, ffmpeg, sqlite3 et les règles du pare-feu.

## Le tenir au quotidien

- **Mises à jour** : automatiques (D94). Toutes les 2 minutes, il regarde si sa branche a du
  nouveau, installe, vérifie, et revient à la version d'avant si quelque chose casse. Jamais
  pendant que tu t'en sers, au plus une par heure (D251). Pour ne pas attendre : Réglages >
  Version > Appliquer maintenant.
- **S'il tombe** : systemd le relance ; s'il reste muet plus de 5 minutes, le gardien te
  prévient lui-même, dans l'app ou par Telegram.
- **Logs** : `journalctl -u orion-core -f` et `journalctl -u orion-guardian -f`.
- **Après un changement d'IP ou de domaine** : la passkey est liée au nom du serveur ; relance
  `install.sh` avec le nouveau nom, il affiche un code pour réappairer.

## Sur ta machine, sans serveur

Pour l'essayer ou le développer, il suffit de [uv](https://docs.astral.sh/uv/) :

```bash
uv tool install --editable .   # une fois, depuis le dépôt : `orion` marche ensuite partout
orion setup     # prénom, fuseau, clé OpenRouter, Telegram en option
orion chat      # lui parler dans ce terminal
orion serve     # le démon (avec `orion guardian` à côté si le gardien est séparé)
```

`orion setup` écrit `~/.orion/orion.toml`, et les secrets dans `core.env` et `guardian.env` à
côté. Un `orion.toml` dans le dossier courant passe avant ; `ORION_HOME` ou `ORION_CONFIG`
changent l'emplacement (D180). Toutes les options sont décrites dans
[`orion.example.toml`](orion.example.toml). Sans serveur, pas d'app sur l'iPhone ni de
sauvegardes de nuit : `orion backup <dossier>` copie le journal à la demande.

## Comment c'est fait

- **Un journal append-only** (SQLite) est la seule vérité. Le reste (mémoire, personnes,
  rappels, missions…) est une projection qui se reconstruit à partir de lui. Chaque contenu porte
  sa provenance et son niveau de confiance.
- **Deux processus** (D28) : `orion guardian` détient les secrets et les canaux, sert l'app et
  vérifie chaque effet sur le monde ; `orion serve`, le cœur, pense. Sur un serveur, ils tournent
  sous deux utilisateurs (`orion-guardian`, `orion-core`), derrière Caddy.
- **Une plaque et des modules** (D24) : le cœur garde le journal, la mémoire, le gardien, la
  boîte de réception, l'initiative et les rappels ; tout le reste est un module qu'on active dans
  `orion.toml` (voir [`docs/REFERENCE.md`](docs/REFERENCE.md)).
- **Les modèles** : par OpenRouter, un modèle principal, un pour le travail de fond, un plus
  fort pour les questions dures et la nuit, un vérificateur d'une autre famille, un pour la
  vision ; ou tes forfaits ChatGPT (`chatgpt:<modèle>`) et Claude (`claude-code:<modèle>`).
  Tout se règle dans `[agent]`.
- **Sur le serveur** : le code dans `/srv/orion/app`, les réglages dans
  `/srv/orion/config/orion.toml`, les données dans `/srv/orion/data`, le gardien dans
  `/srv/orion/guardian`, les secrets dans `/etc/orion`, les sauvegardes dans
  `/srv/orion/backups`.

## Développer

```bash
uv sync
uv run pytest -q tests/test_x.py                   # seulement les fichiers touchés
uv run ruff format . && uv run ruff check .
uv run pyright --pythonplatform Linux              # strict, 0 erreur
uv run python -m evals                             # évaluations sur le vrai modèle (quelques centimes)
```

Les règles du dépôt (journal append-only, fail closed, `SecretRef`, contrat du cache de prompt,
tests sur le comportement) sont dans [`CLAUDE.md`](CLAUDE.md). Pas d'éval sur le compte ChatGPT
du cœur pour l'instant : les deux processus renouvelleraient ses jetons sans verrou.

### Écrire un module

Un module est une sous-classe de `orion.modules.base.Module`. Chaque crochet est facultatif :

```python
from orion.modules.base import Daemon, Module, ModuleSettings, Plate


class WeatherSettings(ModuleSettings):  # section [modules.weather] d'orion.toml
    city: str = "Paris"


class Weather(Module):
    name = "weather"
    settings_model = WeatherSettings
    requires = ()  # autres modules nécessaires

    def instructions_text(self) -> str:  # ajouté à la constitution
        return "# La météo\n\nTu connais la météo avec `weather`."

    async def assemble(self, plate: Plate) -> list[Tool]:
        return [...]  # outils donnés au modèle

    async def serve(self, daemon: Daemon) -> None:
        daemon.add_service("weather.watch", self.watch)  # service supervisé
        daemon.reports.append(self)  # comptes rendus pour l'initiative
```

On le publie comme paquet avec un point d'entrée dans le groupe `orion.modules`
(`weather = "mon_paquet:Weather"`), puis on l'active avec `[modules.weather] enabled = true`. Ou
on l'ajoute au [catalogue](catalog/README.md) : Orion l'installe alors sur ton oui (D105).

## Documentation

- [`deploy/README.md`](deploy/README.md) — installer et tenir Orion sur un serveur, en détail
- [`docs/REFERENCE.md`](docs/REFERENCE.md) — les modules, les commandes, la configuration
- [`orion.example.toml`](orion.example.toml) — chaque option, commentée
- [`docs/architecture/04-architecture.md`](docs/architecture/04-architecture.md) — architecture
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — journal des décisions : la raison de chaque choix
  (les `Dxxx` de ce README)
- [`docs/PASSATION.md`](docs/PASSATION.md) — où en est le travail, pour qui le reprend
- [`docs/research/`](docs/research/) — études : Claude Code, paysage des agents, ce qui fait un
  Jarvis, l'application
- [`catalog/`](catalog/README.md) — skills, serveurs MCP et modules que tout Orion peut installer
