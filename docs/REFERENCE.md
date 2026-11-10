# Reference

What exists in the code as of 28/10/2026 (up to D177): the modules, the `orion` commands, the
configuration and the ports. The why of each thing is in [`DECISIONS.md`](DECISIONS.md).

## Modules

A module (D24) is a subclass of `orion.modules.base.Module`: it adds instructions to the
constitution (`src/orion/resources/<name>.md`), tools, supervised services and reports for the
initiative engine. The list of bundled modules is `builtin_modules()` in
`src/orion/modules/registry.py`; others load through the `orion.modules` entry point or are
installed from the catalog (`orion modules install`, D105).

A module runs if its section has `enabled = true`. Loading fails (fail closed) for an unknown
enabled module, or for an enabled module whose required module is not enabled. The list is fixed
at startup.

Some tools are kept in a drawer: the `orion` tool lists and opens them (D151).

### On by default

| Module | What it does | Tools |
|---|---|---|
| `adaptation` | Learns your manual: what you want, what you ignore (`[adaptation]`) | `adapt`, `unlearn`, `initiative_settings`, `playbook` |
| `consolidation` | The nightly pass over all of memory (D174) | service |
| `doubt` | Asks again about what may have changed (D83) | `doubt_confirm`, `doubt_stale` |
| `feeds` | RSS and Atom feeds it follows (D160) | `feed_add`, `feed_drop`, `feed_list` |
| `files` | Makes and sends images, PDFs, downloads (D60, D61) | `file` |
| `onboarding` | Getting to know you, at most one question a day (D34) | `onboarding_stop` |
| `focus` | Focus mode: only urgent things get through (D70) | `focus_start`, `focus_stop` |
| `hooks` | "When this happens, do that": an event, a time or a URL triggers an instruction, a tool or a notification (D225) | `hooks` |
| `notifications` | What rings, how and where, type by type; five new types on request (D225) | `notifications` |
| `expert` | A stronger model for hard questions (D46) | `consult_expert`, `think_harder` |
| `missions` | Goals pursued alone over several days (D47) | `mission`, `missions` |
| `tasks` | Background tasks (D110) | `task` |
| `library` | Your notes, your documents, the whole conversation (D48) | `library_*`, `conversations_search` |
| `photos` | Photos and files received, looked at once (D50, D63) | `attachment_look` |
| `papers` | The vault for your papers (D74, D131); requires `files`, `photos` | `papers` |
| `thinking` | Coming back to what was left open (D51, D117) | `think_later`, `follow_up*` |
| `watch` | The daytime watch over your life (D150, D155) | service |
| `awaiting` | Waits for an answer and follows up (D129) | `awaiting_*` |
| `chronicle` | The page of your week, its mistakes (D52, D69) | `chronicle`, `mistake` |
| `intentions` | Who you want to become, and the right to contradict you (D53, D66) | `intention_*`, `intentions` |
| `goals` | Your goals: milestones reached on evidence, links, Sunday review (D267) | `goal` |
| `relations` | Birthdays, before seeing someone, keeping in touch (D56) | `person_birthday`, `keep_in_touch`, `saw_someone`, `meeting_soon` |
| `contacts` | Your phone's address book (D159) | `contacts` |
| `departure` | The day before a trip or an exam (D77) | `departure_*` |
| `advice` | Its advice and how it turned out (D65) | `advice_*` |
| `style` | Writing like you (D68) | `owner_style` |
| `configure` | Changing its settings with your yes, asking for a secret (D72, D92) | `configure_show`, `configure_change`, `secret_ask` |
| `vocal` | Voice messages: transcribed on arrival, `say` to answer (D71); requires `files` | `say` |
| `recap` | The evening recap | — |
| `skills` | Know-how as text and a public catalog (D95) | `skill` |
| `curiosity` | One lead of its own per week (D76); only runs with `web` | `curiosity_*` |
| `booking` | Booking an appointment (D73); only runs with `computer` | `booking` |

### To turn on

| Module | Section | What it does | Tools |
|---|---|---|---|
| `mobile` | `[modules.mobile]` | The iPhone app: channel, Face ID consents, settings (D125, D154) | channel |
| `telegram` | `[channels.telegram]` | Your Telegram bot (D88, D89) | channel |
| `imessage` | `[channels.imessage]` | iMessage through an Inkbox line | channel |
| `voice` | `[voice]` | Phone calls on the Inkbox line (D40); requires `imessage` | `call_me`, `call_someone` |
| `calendar` | `[modules.calendar]` | Your calendars as iCal, writing to Google or CalDAV (D25, D32) | `agenda`, `calendar_add` |
| `mail` | `[modules.mail]` | Your mailboxes over IMAP, read live (D75, D171, D179) | `mail`, `mail_send`, `mail_tidy`, `mail_draft`, `mail_mark` |
| `web` | `[modules.web]` | Search and page reading (D31) | `web_search`, `web_read` |
| `computer` | `[modules.computer]` | Its persistent browser, handed to your phone when needed (D116) | `browser` |
| `console` | `[modules.console]` | The control page in the browser (D39) | `console_link` |
| `hands` | `[modules.hands]` | Your machines: shared files, notifications (D41) | `hands`, `hand_*` |
| `places` | `[modules.places]` | Arrivals, departures and place-based instructions through iPhone Shortcuts (D57, D153, D187) | `remind_at_place`, `places` |
| `secretary` | `[modules.secretary]` | The people close to you who can message Orion (D54) | `contact_note`, `contact_message` |
| `federation` | `[federation]` | Other Orions (D29); requires `calendar` and the separate guardian | `peers`, `meeting_*`, `peer_message` |
| `delegation` | `[delegation]` | Long tasks handed to the `claude` CLI | `delegate`, `jobs_status` |
| `mcp` | `[modules.mcp]` | Connected MCP servers (D95) | `mcp_<server>_<tool>` |
| `shell` | `[modules.shell]` | The server's shell, every command approved (D96, D164) | `shell` |

### Core tools

Always there, outside modules: `remember`, `recall`, `forget_fact`, `commitment_*`,
`commitments_list`, `situation_*`, `situations_list`, `provenance`, `contain_source`, `person`,
`people`, `same_person`, `remind_me`, `reminder_*`, `reminders_list`, `planned`, `later` (D157),
`tell` (D173), `plan`, `autonomy`, `autonomy_revoke`, `spending`.

## Packages

| Package | Role |
|---|---|
| `core/` | IDs, HLC clock, events, append-only journal, projections, supervisor, backup |
| `guardian/` | Policy, consents, autonomy, secrets, vault, outbox, registry, federation crypto |
| `memory/` | Bi-temporal facts, commitments, people, provenance, situations, doubt, nightly pass, portrait |
| `initiative/` | The engine that speaks first: rules, reminders, check-ins, arbiter, `later`, simulation |
| `cognition/` | The agent loop (`loop.py`), seeing things through (`finish.py`), verifier, evidence before speech (`grounding.py`) and after-the-fact review (`review.py`, D253) |
| `context/` | The context compiler (stable first, for the cache), threads, summaries, `<pendant_ce_temps>` |
| `providers/` | `openrouter`, `chatgpt`, `claude_code`, `router` (fallback), `spending` (cap) |
| `channels/` | Terminal, iMessage (Inkbox), Telegram, unified inbox, message tags |
| `tools/` | The tool contract (fail closed), tools grouped by domain, `tell`, `plan` |
| `modules/` | The module contract, the registry, the installer |
| `mobile/` | The app server, notifications, devices, the web app |
| `observability/` | Structured logs (structlog) |
| `resources/` | The instructions: `constitution.md`, `closing.md`, one per module |

At the top: `app.py` assembles Orion for each entry point, `serve.py` is the daemon, `setup.py`
the setup wizard, `config.py` the typed configuration, `cli.py` the commands.

## Commands

`orion [--config orion.toml] <command>`, from any folder after `uv tool install --editable .`.
Without `--config`: `$ORION_CONFIG`, else `orion.toml` in the current folder, else
`$ORION_HOME/orion.toml` (`~/.orion` by default, D180). On the server, `deploy/orion-admin` runs
them as the guardian's user (or the core's with `--core`).

| Command | What it does |
|---|---|
| `setup [--server] [--secrets DIR]` | The wizard: first name, time zone, separate guardian, OpenRouter key, Telegram |
| `doctor` | Checks the configuration, the storage and each module |
| `chat` | A conversation in the terminal |
| `serve` | The daemon: channels, initiative, modules |
| `guardian` | The guardian process |
| `memory` | What it knows about you (writes `profile.md`) |
| `forget SOURCE [--reason]` | Forgets everything that came from a source |
| `contain SOURCE [--apply]` | Quarantines a source and what it touched (D38) |
| `misses [--case N]` | Its misses; `--case` turns one into an evaluation case |
| `week` | Its week: interrupted turns, tool errors, corrections, cost |
| `models` | Which model does what, how hard it thinks, and where each setting comes from (D233) |
| `simulate [--days 7]` | What it would send, without sending anything |
| `reminders list \| cancel ID` | Reminders |
| `contacts import FILE.vcf` | Import an address book |
| `library import FOLDER` | Import notes |
| `logins add \| import \| remove \| list` | The credential vault (D111) |
| `modules list \| install NAME \| remove NAME` | Catalog modules |
| `app pair NAME \| devices \| revoke NAME` | The app's phones |
| `hands pair NAME \| revoke NAME` | Machines, server side |
| `hand pair SERVER CODE [--root DIR] [--exit] \| exit on\|off \| run` | On your machine |
| `chatgpt login \| status \| models \| logout` | Your ChatGPT subscription |
| `google auth CLIENT_ID` | Writing to Google Calendar |
| `inkbox setup [--webhook-url URL] \| calls` | The iMessage and phone line |
| `federation keygen \| peers \| invite \| accept \| revoke` | Other Orions |
| `console link` | A login link to the console |
| `places token` | The token for iPhone Shortcuts |
| `notify TEXT` | Message you on Telegram (used by updates) |
| `backup DEST [--keep 14] [--guardian]` | A verified backup |
| `check-backup PATH` | Check that a backup restores |
| `version` | The version |

## Configuration

`orion.toml`, described option by option in [`orion.example.toml`](../orion.example.toml).
Secrets are never in it: they are named (`SecretRef`) and read from the environment, or from the
guardian's vault when they come from the app.

| Section | Contents |
|---|---|
| `[agent]` | Models (`model`, `strong_model`, `vision_model`…), consents (`approvals`: `equilibre` or `prudent`, D85) |
| `[models]` | One line per role (`conversation`, `tasks`, `memory`, `thinking`…): `model` and `effort` (D233) |
| `[budget]` | Daily and monthly spending cap (D79) |
| `[providers.openrouter]`, `[providers.chatgpt]` | Providers |
| `[channels.telegram]`, `[channels.imessage]`, `[voice]` | Channels |
| `[initiative]` | Daily check-ins, quiet hours, attention budget |
| `[adaptation]`, `[delegation]`, `[memory]` | Core modules |
| `[guardian]` | Separate guardian, actions that can be entrusted to it (`autonomable`, `*` for everything, D167) |
| `[federation]` | Other Orions: `public_url`, `listen_port` |
| `[modules.<name>]` | Each module, with `enabled` |
| `[logging]` | Log level and format |

## Ports

Everything listens on `127.0.0.1`; Caddy serves HTTPS in front (`deploy/Caddyfile`).

| Path | Port | Process |
|---|---|---|
| `/inkbox/webhook` | 8787 | core |
| `/.well-known/agent-card.json`, `/a2a` | 8788 | guardian (federation) |
| `/console/*` | 8790 | core |
| `/voice/live` | 8791 | core |
| `/hands/*` | 8792 | core |
| `/places/*` | 8793 | core |
| `/hooks/in/*` | 8797 | core (hook URLs, D225) |
| `/secrets/*` | 8794 | guardian (secrets form) |
| `/app/*` | 8795 | guardian (the app, pairing, signatures, D134) |
| `/app/api/*` | 8796 | core |
