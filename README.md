<img src="docs/assets/banner.jpg" alt="Orion. An always-on personal agent that lives on your server and only acts with your consent." width="100%">

<p align="center">
  <a href="#deploy-on-a-server">[install]</a>&nbsp;&nbsp;
  <a href="#what-it-does">[what it does]</a>&nbsp;&nbsp;
  <a href="#how-it-is-built">[architecture]</a>&nbsp;&nbsp;
  <a href="#writing-a-module">[write a module]</a>&nbsp;&nbsp;
  <a href="docs/DECISIONS.md">[decisions]</a>
</p>

<p align="center">
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-efe9da?labelColor=000000&logo=python&logoColor=efe9da">
  <img alt="Self-hosted" src="https://img.shields.io/badge/self--hosted-Debian%20%C2%B7%20Ubuntu-efe9da?labelColor=000000">
  <img alt="Pyright strict" src="https://img.shields.io/badge/pyright-strict-efe9da?labelColor=000000">
  <img alt="Ruff" src="https://img.shields.io/badge/lint-ruff-efe9da?labelColor=000000">
  <img alt="MIT license" src="https://img.shields.io/badge/license-MIT-efe9da?labelColor=000000">
</p>

Orion is an always-on personal agent. It lives on your server, talks to you from an app on your
iPhone (or over Telegram, iMessage, the phone), remembers your life, acts for you with your
consent, and gets along with other people's Orions.

It does more than answer: it keeps track of your commitments, warns you before what matters,
thinks overnight about what was left open, pursues missions for days, and only speaks first
when it is worth your attention.

| | |
|---|---|
| 🧠 **It remembers** | Dated, sourced facts, never overwritten, reread every night. "How do you know that?" always has an answer. |
| 🔭 **It speaks first, with restraint** | Morning and evening briefings, alerts before a deadline, follow-ups. At most 12 times a day, each time with its "why now". |
| 🛡️ **Nothing leaves without your yes** | A separate guardian holds the secrets and checks every effect on the world: email, message, form, order. |
| 🤝 **It gets along with other Orions** | "Set up lunch with Tom": both Orions agree on a time, sharing only your free slots. |
| 🧩 **It grows through modules** | Calendar, mail, browser, Home Assistant, missions… The core stays small; the rest is switched on in `orion.toml`. |

> **Language.** Orion talks to you in your language. The deployment guide and the reference are
> in English; the design notes (`docs/DECISIONS.md`, where the `Dxxx` references below point)
> and the internal docs are still in French.

## Contents

- [Before you install](#before-you-install)
- [What it does](#what-it-does)
- [Deploy on a server](#deploy-on-a-server)
- [Using it](#using-it)
- [Backup and restore](#backup-and-restore)
- [Reset, uninstall](#reset-uninstall)
- [Day-to-day running](#day-to-day-running)
- [On your machine, without a server](#on-your-machine-without-a-server)
- [How it is built](#how-it-is-built)
- [Development](#development)
- [Documentation](#documentation)

## Before you install

- **One Orion, one owner.** It is made for one person: you. Other people can write to it if you
  allow it, with what you grant them; their own assistant is their own Orion, linked to yours
  (federation).
- **It runs its server.** The core is root through `sudo` (D164): every shell command is shown
  to you before it runs, but give it a server of its own, not a machine that does something else.
- **Nothing leaves without the guardian.** An email, a message to someone else, a form, an
  order: your yes on the exact text, or an autonomy you granted, bounded, and that you take back
  with one word (D35, D167). It speaks first at most 12 times a day (D104).
- **Your server holds your life.** The journal keeps every conversation and everything it did;
  the guardian keeps your secrets and passwords. Back up, encrypt, and erase for good if you
  stop: everything is described below.
- **What it costs.** A VPS (a few euros a month) and the model: an OpenRouter key (pay as you
  go, capped per turn, `max_cost_usd_per_turn`), or your ChatGPT and Claude subscriptions, which
  take over the roles they can (D62, D100, D147). iMessage and the phone go through an Inkbox
  line, which is paid; Telegram and the app are free.
- **Secrets never go in a config file** or in the conversation: they are typed in the app and
  go straight to the guardian (`SecretRef`, D154).

## What it does

**Remember.** Dated, sourced facts, never overwritten; commitments (what I owe, what I am owed);
ongoing situations (D149); the people in your life and how they relate. Search by meaning and by
words. Every night, a pass rereads the whole memory: duplicates, contradictions, stale facts
(D174). "How do you know that?" always has an answer (D38). Forgetting a source erases
everything that came from it.

**Speak first, with restraint.** Morning and evening briefings, an alert before a deadline, a
watch over your life three times a day (D150), follow-ups when someone does not answer (D129),
one-off, recurring or location reminders, quiet hours, focus ("I'm working until 6 pm"). Every
time it speaks up is a journaled decision, with its "why now".

**Your daily life.** Calendars (Google, iCloud, Outlook), mail (triage, drafts in your voice,
sending, filing), paperwork (filed, expiry dates, a rental application in one PDF), photos and
files read on arrival (what is written in them is never an order), voice notes both ways,
contacts, RSS feeds, parcels and subscriptions, Home Assistant (D161), appointments booked for
you (D73), the day before a trip (D77).

**Think and search.** The web; its own browser, which it drives alone and hands over to you when
a page needs you (D116); a stronger model for hard questions (D46); missions over several days
(D47) and background tasks (D110); a library of your notes and of your whole conversation (D48).

**Know you.** It learns what you want and what you ignore, writes like you when it drafts for
someone (D68), dares to disagree once (D53, D66), notes its own mistakes and misses (D69, D177),
and keeps the chronicle of your week (D52).

**Other Orions.** Link your Orion to someone else's with an invitation; "set up lunch with Tom"
is enough, and only your free slots are shared (D29, D99, D102).

## Deploy on a server

This is the recommended setup: Orion is made to run day and night.

**You need** a fresh VPS running Debian 12 or Ubuntu 24.04 (OVH or any other), SSH access, an
[OpenRouter](https://openrouter.ai) key, and an iPhone for the app. A domain name is optional:
without one, `<ip>.sslip.io` is enough for HTTPS.

1. **Domain (optional).** Create an A record pointing to the VPS IP (at OVH: Web Cloud >
   Domains > DNS zone).
2. **Install**, over SSH on the VPS:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/noan-hbt/orion/main/install.sh | sudo bash
   ```

   Nothing to clone: this starts an interactive installer that walks you through it (it offers
   `<ip>.sslip.io` as the address, press Enter or type your own domain). To clone it yourself:
   `git clone https://github.com/noan-hbt/orion.git && cd orion && sudo ./install.sh orion.example.com`.

   The script installs everything (Caddy for HTTPS, Python, ffmpeg, Orion's browser, two users,
   the services, the firewall), then asks four questions: your first name and time zone, keeping
   secrets apart (yes), the OpenRouter key (checked right away), and Telegram as an option (a
   bot created with @BotFather).
3. **Pair the app.** At the end, the script prints a link and a code. Open the link in Safari,
   Share > "Add to Home Screen", open Orion from the home screen, type the code (valid for 10
   minutes) and create the passkey.
4. **The Claude subscription (optional)** is connected on the server, once:
   `sudo orion claude login` (D100, D208).

After that, **nothing is done over SSH anymore** (D154): settings, secrets, modules,
subscriptions, phones, machines and other Orions are managed in the app, and what matters is
signed with Face ID. Orion updates itself. Running `install.sh` again updates the code without
touching the configuration or the secrets.

All the details (iMessage through Inkbox, location reminders, password vault, ports):
[`deploy/README.md`](deploy/README.md).

## Using it

**Talk to it.** The app is the main channel: the conversation, your approvals signed with Face
ID, notifications, the work in progress (with Stop) and every setting. Telegram, iMessage and the
phone (Inkbox, D40) work too.

**Configure it by talking.** "Turn on mail", "move your briefings to 9 am", "add Angèle, she can
know when I'm free": it changes its own settings (`orion.toml`), with your yes on the exact change
(D92). What protects you (the guardian, the channels, who can write to it, the budget) only
changes with that yes, checked by the guardian.

**Connect your accounts**, in the app or by asking it:

- **Calendar**: the secret iCal address of each calendar (Google: "Secret address in iCal
  format"; iCloud: `webcal://` link; Outlook: "Publish a calendar"), and your addresses in
  `owner_emails`, otherwise your own events look like invitations.
- **Mail**: an app password per mailbox (Gmail, iCloud…, over IMAP). Outlook.com (OAuth) is not
  supported.
- **ChatGPT subscription**: Settings > ChatGPT.
- **Websites**: when a page needs you (sign-in, SMS code, captcha), it hands you its browser in
  the app; its sessions persist. The guardian can also keep your credentials (Settings >
  Passwords, or import a KeePass, Bitwarden, Chrome… export, D111).
- **Your machines**: Settings > Machines gives the command to run on your Mac or PC
  (`orion hand pair …`), so it can read the folders you share (D41).

**What it may do alone.** By default, it asks before acting on the world. To hand it a domain
(sending mail to some recipients, filling forms on some sites), grant it an autonomy when it
offers one; you take it back with one word.

**On the server**, to see what it does. `sudo orion …` runs the command as the guardian's user,
with its secrets; `--core` as the core's user, which holds the journal (`doctor`, `memory` and
`chat` go there automatically):

```bash
sudo orion doctor                        # configuration, storage, state of each module
sudo orion --core simulate --days 7      # what it would send this week, without sending anything
sudo orion --core week                   # interrupted turns, tool errors, corrections, cost
sudo orion --core initiative             # what it learned from your feedback, source by source
sudo orion --core misses                 # its misses: your 👎 and your corrections
```

## Backup and restore

**Every night, on its own**, around 4:15 am: a verified copy of the core's journal and of the
guardian's ledger goes to `/srv/orion/backups/` (30 copies kept). Memory, people and reminders
are rebuilt from the journal. These copies hold **only the journals**, and stay on the server.

**A full backup**, run it yourself (D290): settings, secrets, subscription sessions, password
vault, modules, files, photos, the browser and its signed-in sites.

```bash
sudo orion backup
```

It asks whether to back up or restore, where to put the archive (`/root` by default) and how to
encrypt it: a passphrase (age or gpg), an age public key, or nothing. Orion stops for a few
seconds during the copy, and the journals are verified before the copy counts. **Then copy the
archive off the server**, for example:

```bash
rclone copy /root/orion-full-<date>.tar.gz.age ovh:orion-backups
```

Without questions, for a timer of your own:

```bash
sudo orion backup full --encrypt age:<public key> --yes
```

**Restore**, on the same server or a new one: on a new server, run `install.sh` first (with the
same domain, otherwise you will need to pair the app again), then

```bash
sudo orion restore                # offers the archives in /root
sudo orion restore <archive>      # or a given one
```

The archive is decrypted and verified before Orion is stopped; what was there is kept aside
(`/root/orion-before-restore-<date>.tar.gz`), and restores the same way. If ChatGPT stops
answering afterwards, sign in again in the app: its session changes on every refresh.

To restore only one night's journal: stop both services, copy `journal.sqlite3` from
`/srv/orion/backups/core/<date>/` into `/srv/orion/data/`, delete `memory.sqlite3` (rebuilt at
startup), restart.

## Reset, uninstall

**Reset**: Orion forgets everything it lived through (conversations, memory, reminders,
missions, files, browser), but keeps its settings, secrets, modules and your subscription
sessions.

```bash
sudo orion reset               # the guardian and the backups stay
sudo orion reset --guardian    # ... the guardian forgets too (approvals, passwords)
sudo orion reset --backups     # ... and the nightly backups
```

A copy of what goes is kept first in `/root/orion-reset-<date>.tar.gz` (`--no-archive` to keep
none).

**Uninstall**: removes everything `install.sh` set up (services, code, Python, browser, data,
secrets, sudo rule, users, Caddy site).

```bash
sudo orion uninstall            # asks first, keeps an archive in /root
sudo orion uninstall --purge    # nothing is kept
```

Without `--purge`, data, configuration and secrets go first to `/root/orion-<date>.tar.gz`. To
come back later: `install.sh`, then `sudo orion restore` on that archive. To erase everything for
good, also delete the archives in `/root` and those you copied elsewhere: they hold your life
with Orion and your passwords. Caddy, uv, ffmpeg, sqlite3 and the firewall rules stay in place.

## Day-to-day running

- **Updates**: automatic (D94). Every 2 minutes, it checks whether its branch has something new,
  installs it, checks it, and rolls back if something breaks. Never while you are using it, at
  most once an hour (D251). To skip the wait: Settings > Version > Apply now.
- **If it goes down**: systemd restarts it; if it stays silent for more than 5 minutes, the
  guardian warns you itself, in the app or over Telegram.
- **Logs**: `journalctl -u orion-core -f` and `journalctl -u orion-guardian -f`.
- **After an IP or domain change**: the passkey is tied to the server name; run `install.sh`
  again with the new name, it prints a code to pair again.

## On your machine, without a server

To try it or work on it, all you need is [uv](https://docs.astral.sh/uv/):

```bash
uv tool install --editable .   # once, from the repo: `orion` then works everywhere
orion setup     # first name, time zone, OpenRouter key, Telegram as an option
orion chat      # talk to it in this terminal
orion serve     # the daemon (with `orion guardian` next to it if the guardian is separate)
```

`orion setup` writes `~/.orion/orion.toml`, and the secrets in `core.env` and `guardian.env`
next to it. An `orion.toml` in the current folder takes precedence; `ORION_HOME` or
`ORION_CONFIG` change the location (D180). Every option is described in
[`orion.example.toml`](orion.example.toml). Without a server, there is no iPhone app and no
nightly backups: `orion backup <folder>` copies the journal on demand.

## How it is built

- **An append-only journal** (SQLite) is the only source of truth. Everything else (memory,
  people, reminders, missions…) is a projection rebuilt from it. Every piece of content carries
  its provenance and its trust level.
- **Two processes** (D28): `orion guardian` holds the secrets and the channels, serves the app
  and checks every effect on the world; `orion serve`, the core, thinks. On a server, they run as
  two users (`orion-guardian`, `orion-core`), behind Caddy.
- **A plate and modules** (D24): the core keeps the journal, memory, guardian, inbox, initiative
  and reminders; everything else is a module switched on in `orion.toml` (see
  [`docs/REFERENCE.md`](docs/REFERENCE.md)).
- **Models**: through OpenRouter, a main model, one for background work, a stronger one for hard
  questions and the night, a verifier from another family, one for vision; or your ChatGPT
  (`chatgpt:<model>`) and Claude (`claude-code:<model>`) subscriptions. All set in `[agent]`.
- **On the server**: the code in `/srv/orion/app`, the settings in
  `/srv/orion/config/orion.toml`, the data in `/srv/orion/data`, the guardian in
  `/srv/orion/guardian`, the secrets in `/etc/orion`, the backups in `/srv/orion/backups`.

## Development

```bash
uv sync
uv run pytest -q tests/test_x.py                   # only the files you touched
uv run ruff format . && uv run ruff check .
uv run pyright --pythonplatform Linux              # strict, 0 errors
uv run python -m evals                             # evaluations on the real model (a few cents)
```

The repository rules (append-only journal, fail closed, `SecretRef`, prompt-cache contract,
behavioural tests) are in [`CLAUDE.md`](CLAUDE.md). No evals on the core's ChatGPT account for
now: both processes would refresh its tokens without a lock.

### Writing a module

A module is a subclass of `orion.modules.base.Module`. Every hook is optional:

```python
from orion.modules.base import Daemon, Module, ModuleSettings, Plate


class WeatherSettings(ModuleSettings):  # [modules.weather] section of orion.toml
    city: str = "Paris"


class Weather(Module):
    name = "weather"
    settings_model = WeatherSettings
    requires = ()  # other modules it needs

    def instructions_text(self) -> str:  # appended to the constitution
        return "# Weather\n\nYou know the weather through `weather`."

    async def assemble(self, plate: Plate) -> list[Tool]:
        return [...]  # tools given to the model

    async def serve(self, daemon: Daemon) -> None:
        daemon.add_service("weather.watch", self.watch)  # supervised service
        daemon.reports.append(self)  # reports for the initiative engine
```

Publish it as a package with an entry point in the `orion.modules` group
(`weather = "my_package:Weather"`), then switch it on with `[modules.weather] enabled = true`. Or
add it to the [catalog](catalog/README.md): Orion then installs it on your yes (D105).

## Documentation

- [`deploy/README.md`](deploy/README.md): installing and running Orion on a server, in detail
- [`docs/REFERENCE.md`](docs/REFERENCE.md): modules, commands, configuration
- [`orion.example.toml`](orion.example.toml): every option, commented
- [`docs/architecture/04-architecture.md`](docs/architecture/04-architecture.md): architecture
- [`docs/DECISIONS.md`](docs/DECISIONS.md): the decision log, the reason behind each choice
  (the `Dxxx` in this README)
- [`docs/PASSATION.md`](docs/PASSATION.md): where the work stands, for whoever picks it up
- [`docs/research/`](docs/research/): studies on Claude Code, the agent landscape, what makes a
  Jarvis, the app
- [`catalog/`](catalog/README.md): skills, MCP servers and modules any Orion can install

## License

[MIT](LICENSE)
