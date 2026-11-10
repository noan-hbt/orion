# Deploying Orion on a server (OVH VPS or other)

> Orion's app screens are in French. Screen and button names below are translated.

Orion runs as two processes (D28), under two Unix users that share a group:

- `orion-guardian` holds the secrets (Inkbox, Telegram, calendars, mail, web search,
  federation key, credential vault), serves the app and checks every effect on the world;
- `orion-core` holds only the model key (OpenRouter). It is root through `sudo`
  (`/etc/sudoers.d/orion-core`, D164), but every shell command is submitted to you (D96).

Caddy, in front of them, serves HTTPS and only lets Orion's paths through: the app (`/app/`),
the console (`/console/`), the secrets form (`/secrets/`), the machines (`/hands/`), places
(`/places/`), hooks (`/hooks/in/`), the phone (`/voice/live`), the Inkbox webhook and
federation. Everything else answers 404. The port table is in
[`docs/REFERENCE.md`](../docs/REFERENCE.md#ports).

## Installation

On a fresh VPS running Debian 12 or Ubuntu 24.04, logged in over SSH:

```bash
git clone https://github.com/noan-hbt/orion.git && cd orion
sudo deploy/install.sh orion.mydomain.com     # or with no argument: <ip>.sslip.io
```

For your own domain name, first create an A record pointing to the VPS IP (in OVH: Web Cloud >
Domains > DNS zone). Without a domain, the script uses `sslip.io`, which is enough to get a
certificate.

The script installs everything (Caddy, uv, Python, ffmpeg, Orion's browser, the users, the
services, the firewall), then asks a few questions (`orion setup --server`):

1. your first name and time zone;
2. whether to keep the secrets in a separate process (yes by default on a server);
3. the OpenRouter key (checked right away);
4. Telegram, optional: create a bot with @BotFather (`/newbot`) and paste its token (checked),
   then message the bot from your phone: Orion reads your id from that message, so you have
   nothing to copy. The bot replies to confirm. Without Telegram, the app is enough.

At the end, it shows the code to pair the app (see below).

To install from another repository or branch: put `ORION_REPO=… ORION_BRANCH=…` before
`install.sh`.

Secrets go to `/etc/orion/core.env` (the model key, `orion-core`) and `/etc/orion/guardian.env`
(everything else, `orion-guardian`), mode 0600, never in `orion.toml`. Then Orion starts.

**After that, no more file editing**: tell it "turn on mail", "add Angèle, she may know when
I'm free", "do your check-ins at 9 am". It changes its own settings
(`/srv/orion/config/orion.toml`), with your consent. What protects you (the guardian, the
channels, who can message it, the budget) only changes with your yes to the exact change,
checked by the guardian, which is the only process allowed to write that file (D92). Secrets
never go through messages: you enter them in the app (Settings), or in the guardian's form that
Orion sends you when it needs one, and they go straight to the guardian
(`/srv/orion/guardian/secrets.env`). Editing `/etc/orion/guardian.env` by hand still works,
followed by a restart.

Running the script again updates the code; it never touches the configuration or the secrets,
and only asks its questions again if the OpenRouter key is missing.

iMessage (through Inkbox, paid) instead of Telegram: set `[channels.imessage]` `enabled =
true`, your number and Orion's handle, `INKBOX_API_KEY` in `guardian.env`, then:

```bash
sudo /srv/orion/app/deploy/orion-admin inkbox setup \
    --webhook-url https://orion.mydomain.com/inkbox/webhook
```

Put the signing key it prints in `INKBOX_SIGNING_KEY` (`guardian.env`), send the connection
command it prints from your phone, and restart:
`sudo systemctl restart orion-guardian orion-core`.

`orion-admin` runs an `orion` command as the guardian's user, with its secrets
(`federation invite`, `inkbox calls`…). With `--core`, it runs it as the core's user, which is
where `doctor`, `memory` and `chat` always go. It is installed as `/usr/local/bin/orion`: on the
server, `orion memory` is enough.

## The app on the iPhone

Orion's app (D125) is the main channel: the conversation, your consents signed with Face ID,
notifications and all the controls. It is enabled on recent installs; on an older install, run
`sudo /srv/orion/app/deploy/install.sh` again (with your domain, or with no argument to keep
`<ip>.sslip.io`): it adds `[modules.mobile]` to `orion.toml`, updates Caddy, restarts Orion and,
if no phone is paired yet, shows the code for the first one.

Open the link it shows in Safari, Share > "Add to Home Screen", open Orion from the home
screen, enter the code (once, valid 10 minutes) and create the passkey. Notifications are
requested from the app.

**After that, nothing happens on the server any more (D154).** Everything is in the app,
Settings tab, and what matters is signed with Face ID:

- `orion.toml` settings and the modules;
- **secrets** (API keys, mailbox passwords, the OpenRouter key): they go straight to the
  guardian, Orion never sees them; the ones Orion asks you for show up there;
- **ChatGPT**: the connection to your subscription;
- **phone shortcuts**: the token and the URLs;
- **other Orions**: turn on, invite, accept a code, unlink;
- **machines**: the code to link one (the command to run on the machine);
- **phones**: add one, remove one;
- **passwords**: one by one, or by importing a CSV export;
- the **library**: your notes (.md, .txt);
- **my misses**: what Orion noted in the evening about what it got wrong (your 👎, your
  corrections);
- the version and updates, which happen on their own.

**The Claude subscription** is the exception (D100, D208): Anthropic wants you to log in to
Claude Code yourself, on the server. `install.sh` installs Claude Code in
`/usr/local/bin/claude`; run this once:

```bash
sudo orion claude login
```

Open the link, log in to your Claude account, paste the code: Orion restarts on your
subscription. The login lives in `/srv/orion/data/claude-code/login` (kept by `reset.sh`), and
Claude Code updates itself once a day with `orion-update`.

A passkey is tied to the server name (`public_url`): with `sslip.io`, if the VPS IP changes or
you switch to a real domain, you need to pair again (run `install.sh` again, it shows a code).
The `orion-admin …` commands are still there for troubleshooting.

## Day to day

- **Logs**: `journalctl -u orion-core -f`, `journalctl -u orion-guardian -f`.
- **If the core goes down**: systemd restarts it after 5 s. If it stays silent for more than 5
  minutes, the guardian warns you itself (the core cannot say it has stopped): through an app
  notification, otherwise through iMessage or Telegram, and again when it comes back.
- **Backups** (`orion-backup-core.timer`, `orion-backup-guardian.timer`): every night around
  4:15 am, a verified copy of the core's journal and the guardian's registry goes to
  `/srv/orion/backups/` (30 copies kept). Everything else (memory, people, reminders, mail
  records) is rebuilt from the journal.
  - For an off-server copy, with rclone to OVH Object Storage for example:
    `rclone sync /srv/orion/backups ovh:orion-backups` in a timer of your own.
  - The journal holds your life: encrypt the bucket.
- **Updates**: automatic (D94). Every 2 minutes, `orion-update.timer` checks whether the
  tracked branch has something new. If so, it installs it (code, services, sudo rule), checks
  the config, restarts and watches both processes for 75 s. If something breaks, it goes back
  to the previous version and sets that commit aside (`/srv/orion/update.bad`). It tells you on
  Telegram, when enabled, in both cases; otherwise, everything is in the log.
  Updates are batched (D251): not while you are using it (`data/busy-until`), at most one per
  hour, never held back more than 3 h; an `[urgent]` commit goes out right away.
  To skip the wait: Settings → Version → **Apply now** in the app (D254).
  Log: `journalctl -u orion-update`. Turn it off: `sudo systemctl disable --now
  orion-update.timer`. Change branch: `sudo git -C /srv/orion/app checkout <branch>`.
- **Secrets from the phone** (D94, D154): "turn on my mail" → the requested secret shows up in
  the app's Settings (or, on Telegram, a button opens the guardian's form, `/secrets/`). You
  paste the password there; it goes straight to the guardian
  (`/srv/orion/guardian/secrets.env`), never into the conversation.
- **Restore**: stop both services, copy `journal.sqlite3` from a backup into
  `/srv/orion/data/`, delete `memory.sqlite3` (rebuilt at startup), restart.
- **Full backup** (D290): the nightly backups only keep the journals. To keep everything
  (settings, secrets, ChatGPT and Claude Code logins, guardian vault, modules, files, photos,
  the browser and its logged-in sites), run `sudo /srv/orion/app/deploy/backup.sh`: it asks
  whether to back up or restore, where to put the archive and how to encrypt it (passphrase
  with age or gpg, or an age public key). Orion is stopped during the copy, a few seconds, and
  the journals are checked before the copy counts. The archive lands in
  `/root/orion-full-<date>.tar.gz[.age]`. Then copy it off the server.
  - Without questions: `backup.sh backup --encrypt age:<public key> --yes`, or
    `backup.sh restore <archive> [--identity <key>] --yes`.
  - Restoring on a fresh server: run `install.sh` first, then `backup.sh restore`. The archive
    is decrypted and checked before Orion is stopped. What was there is kept aside
    (`/root/orion-before-restore-<date>.tar.gz`, which restores the same way). If ChatGPT stops
    answering afterwards, log in again from the app: its login changes on every refresh.

## Starting over, uninstalling

**Reset**: Orion forgets everything it has lived and learned, but stays installed and
configured.

```bash
sudo /srv/orion/app/deploy/reset.sh
```

- **What goes** (`/srv/orion/data`): the journal, so all conversations and everything it has
  done, its memory, people, reminders, missions, tasks, the library, files, photos, and its
  browser with the sites it was logged in to.
- **What stays**: the code, `orion.toml` (its settings, the channels, who can message it), the
  secrets, installed modules, subscription logins (ChatGPT, Claude Code) and the console key.
- **Options**:
  - `--guardian` also erases the guardian's registry (consents, granted autonomies) and the
    vault's credentials;
  - `--backups` also erases the nightly backups: without it, the past stays there;
  - `--no-archive` keeps no copy;
  - `--yes` skips the question.

Before erasing, the script keeps a copy of what it removes in `/root/orion-reset-<date>.tar.gz`
(readable by root only). To go back: stop both services, `sudo tar -C / -xzf` that archive,
then start them again.

**Uninstall**: removes everything `install.sh` set up, that is the services and timers, the
code, Python and the browser, the data, the secrets, the sudo rule, the `orion-core` and
`orion-guardian` users, and Orion's site in Caddy (Caddy goes back to its default page).

```bash
sudo /srv/orion/app/deploy/uninstall.sh            # keeps an archive in /root
sudo /srv/orion/app/deploy/uninstall.sh --purge    # nothing is kept
```

Without `--purge`, the journal, the guardian's registry and credentials, the configuration and
the secrets first go to `/root/orion-<date>.tar.gz`. Keep that archive somewhere safe, or
delete it: it holds your life with Orion and your passwords. To reinstall with it: `install.sh`,
then `sudo /srv/orion/app/deploy/backup.sh restore` on the archive.

Left in place: Caddy, uv, ffmpeg, sqlite3 (other things may use them) and the firewall rules
(SSH, 80 and 443 open).

## Acting on your accounts

Like ChatGPT's browser (D116): Orion has a single browser that keeps its logins (on the
server, even after a restart). When a page needs you (logging in, a code received by SMS, a
captcha), it hands you **its** browser, on the page where it is: in the app, or through a
button on Telegram (the console must then be on https, `[modules.console] public_url`, set by
the install). Tap the image to click, type the text below it, then "I'm done": it picks up
again, logged in. What you type goes into the page, not into the conversation. To make it
forget a site: "log out of Leboncoin".

### Your passwords, like KeePass (D111), optional

So that Orion can log back in on its own when a site logs it out, the guardian can also keep
your credentials for a site: the username, the password and, if you want, the two-factor key.
Orion fills in the login page, but the guardian supplies the values, only on that site:
neither the model nor the journal ever sees your password.

- **In the app**: Settings > Passwords > Add an account, or tell Orion "keep my Doctolib
  login".
- **From your password manager**: export it as CSV (KeePass, KeePassXC, Bitwarden, Chrome,
  Firefox, 1Password), then Settings > Passwords > Import an export, and delete the file: it
  holds your passwords in plain text.

The app shows the stored credentials and removes one. A code received by SMS or email: Orion
asks you for it. A captcha: it hands you the page.

For Orion to send emails or forms on its own, add `"mail_send"` or `"browser"` to
`[guardian] autonomable` (or `"*"` for everything, D167): it can then only do so within the
limits you set when granting the autonomy (which recipients, which sites).

## Your machines

`[modules.hands]` is on after install. In the app, Settings > Machines gives a code and the
command to run on your Mac or PC (`orion hand pair https://<your domain> <code> --root
<folder>`). With `orion hand exit on`, its browser goes out through your connection when the
machine is on (D145).

## Place reminders (iPhone)

"Remind me to buy bread when I pass the bakery." Turn on `[modules.places]` (`enabled = true`,
in Settings > orion.toml), then Settings > Phone shortcuts > Create a token (making a new one
invalidates the old one).

On the iPhone, **Shortcuts** app > **Automation** > **Arrive** (or **Leave**) > pick the place >
action **Get Contents of URL**:
- URL: `https://<your domain>/places/event`, method **POST**;
- header `Authorization`: `Bearer <token>`;
- JSON body: `{"place": "bakery", "event": "arrive"}` (`"leave"` for leaving).

Check "Run Immediately". Orion only receives the name you gave the place, and only for places
where you set up an automation: never coordinates.
