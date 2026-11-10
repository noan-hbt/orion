#!/usr/bin/env bash
# ==============================================================================
#   💾  ORION — Assistant de Sauvegarde et Restauration Complète
#
#   Usage interactif :
#     sudo orion backup               # Assistant interactif (sauvegarder ou restaurer)
#     sudo orion restore              # Assistant interactif de restauration
#     sudo deploy/backup.sh
#
#   Commandes directes :
#     sudo ./backup.sh backup  [--to DIR] [--encrypt passphrase|age:<clé>|none]
#                              [--with-nightly] [--yes]
#     sudo ./backup.sh restore [ARCHIVE] [--identity FICHIER] [--no-archive] [--yes]
# ==============================================================================
set -euo pipefail

# Reconnecter stdin au terminal si exécuté via pipe
if [ ! -t 0 ] && [ -e /dev/tty ]; then
    exec < /dev/tty
fi

# Couleurs et styles
if [ -t 1 ]; then
    BOLD="\033[1m"
    GREEN="\033[1;32m"
    CYAN="\033[1;36m"
    YELLOW="\033[1;33m"
    RED="\033[1;31m"
    DIM="\033[2m"
    RESET="\033[0m"
else
    BOLD=""
    GREEN=""
    CYAN=""
    YELLOW=""
    RED=""
    DIM=""
    RESET=""
fi

ROOT="${ORION_ROOT:-/srv/orion}"  # ORION_ROOT, ORION_ETC : installation de test
ETC="${ORION_ETC:-/etc}"
DIR="${ORION_ARCHIVE_DIR:-/root}"
ORION="$ROOT/app/.venv/bin/orion"
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
INFO=orion-backup.txt

# Ordre d'arrêt : timers d'abord pour éviter tout redémarrage intempestif
UNITS=(orion-update.timer orion-backup-core.timer orion-backup-guardian.timer orion-core orion-guardian)

ACTION="" ARCHIVE="" TO="" ENCRYPT="" NIGHTLY=0 IDENTITY="" KEEP_CURRENT=1 YES=0
usage="backup [--to DIR] [--encrypt passphrase|age:<key>|none] [--with-nightly] [--yes]
       restore [ARCHIVE] [--identity FILE] [--no-archive] [--yes]"

while [ $# -gt 0 ]; do
    case "$1" in
        backup | restore)
            [ -z "$ACTION" ] || { echo "one action at a time"; exit 2; }
            ACTION="$1" ;;
        --to) TO="${2:?--to needs a folder}"; shift ;;
        --encrypt) ENCRYPT="${2:?--encrypt needs passphrase, age:<key> or none}"; shift ;;
        --with-nightly) NIGHTLY=1 ;;
        --identity) IDENTITY="${2:?--identity needs a key file}"; shift ;;
        --no-archive) KEEP_CURRENT=0 ;;
        --yes) YES=1 ;;
        -*) echo "unknown option: $1"; echo "usage: $usage"; exit 2 ;;
        *)
            [ "$ACTION" = restore ] && [ -z "$ARCHIVE" ] || { echo "unknown argument: $1"; exit 2; }
            ARCHIVE="$1" ;;
    esac
    shift
done

die() { echo "$*" >&2; exit 1; }
asks() { [ "$YES" != 1 ] && [ -t 0 ]; }

[ -n "${ORION_ROOT:-}" ] || [ "$(id -u)" = 0 ] || die "run as root (sudo)"
for path in "$ROOT" "$ETC" "$DIR"; do
    case "$path" in /*) ;; *) die "$path: give an absolute path" ;; esac
done

TESTING=0
[ -z "${ORION_ROOT:-}" ] || TESTING=1

if [ -z "$ACTION" ]; then
    asks || die "say what to do: $usage"
    if [ -t 0 ]; then
        echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════════${RESET}"
        echo -e "${BOLD}       💾  ORION — ASSISTANT DE SAUVEGARDE ET DE RESTAURATION${RESET}"
        echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════════${RESET}\n"
        echo -e "Que souhaitez-vous faire ?"
        echo -e "  ${BOLD}1)${RESET} Sauvegarder complètement Orion ${DIM}(souvenirs, réglages, mots de passe)${RESET}"
        echo -e "  ${BOLD}2)${RESET} Restaurer une sauvegarde précédente\n"
    else
        echo "1) back Orion up completely"
        echo "2) restore a full backup"
    fi
    read -r -p "Choice [1]: " choice
    case "${choice:-1}" in
        1) ACTION=backup ;;
        2) ACTION=restore ;;
        *) die "Nothing done." ;;
    esac
fi

# --- Arrêt et redémarrage propre d'Orion --------------------------------------

was_on=()
stop_orion() {
    local unit
    for unit in "${UNITS[@]}"; do
        if systemctl is-active -q "$unit" 2>/dev/null; then was_on+=("$unit"); fi
    done
    echo "==> stopping Orion"
    systemctl stop "${UNITS[@]}"
}

start_again() {  # Redémarre ce qui tournait (le gardien avant le cœur, les timers en dernier)
    local unit
    [ "${#was_on[@]}" -gt 0 ] || return 0
    echo "==> starting Orion again"
    for unit in orion-guardian orion-core orion-update.timer orion-backup-core.timer orion-backup-guardian.timer; do
        if printf '%s\n' "${was_on[@]}" | grep -qxF "$unit"; then systemctl start "$unit"; fi
    done
    was_on=()
}

TMP="" SWAPPING=0 BEFORE=""
finish() {
    local status=$?
    [ -z "$TMP" ] || rm -rf "$TMP"
    if [ "$SWAPPING" = 1 ]; then
        echo "The restore stopped halfway: Orion is left stopped." >&2
        [ -z "$BEFORE" ] || echo "Back to before: sudo $SELF restore $BEFORE" >&2
    else
        start_again
    fi
    exit "$status"
}
trap finish EXIT

private_tmp() { TMP="$(umask 077 && mktemp -d "$1/.orion-backup.XXXXXX")"; }

# --- Ce qu'une sauvegarde complète contient -----------------------------------

items() {  # Chemins relatifs à /
    local path
    for path in "$ROOT/config" "$ROOT/data" "$ROOT/guardian" "$ETC/orion"; do
        [ ! -e "$path" ] || echo "${path#/}"
    done
    if [ "$NIGHTLY" = 1 ] && [ -d "$ROOT/backups" ]; then echo "${ROOT#/}/backups"; fi
    return 0
}

CHECKS=""
check_journal() {
    local file="$1" copy said
    [ -f "$file" ] || return 0
    if [ ! -x "$ORION" ]; then
        [ "$TESTING" = 1 ] || die "no orion at $ORION to check $file: run install.sh first"
        CHECKS+="  $(basename "$file"): not checked (no orion here)"$'\n'
        return 0
    fi
    copy="$(umask 077 && mktemp -d)"
    cp -p "$file"* "$copy/"
    if ! said="$("$ORION" check-backup "$copy/$(basename "$file")" 2>&1)"; then
        rm -rf "$copy"
        die "$file cannot be restored, nothing done: $said"
    fi
    rm -rf "$copy"
    CHECKS+="  $(basename "$file"): ${said##* : }"$'\n'
}

make_archive() {
    local out="$1" commit=""
    shift
    [ ! -d "$ROOT/app/.git" ] || commit="$(git -C "$ROOT/app" rev-parse --short HEAD 2>/dev/null || true)"
    {
        echo "Orion, full backup"
        echo "made: $(date -u +%Y-%m-%dT%H:%M:%SZ) on $(uname -n)"
        echo "code: ${commit:-unknown}"
        echo "holds:"
        printf '  /%s\n' "$@"
        echo "journals:"
        printf '%s' "$CHECKS"
    } > "$TMP/$INFO"
    (umask 077 && tar -czf "$out" -C "$TMP" "$INFO" -C / "$@")
    tar -tzf "$out" > /dev/null  # Lisible jusqu'au bout, sinon elle ne compte pas
}

# --- Action de sauvegarde -----------------------------------------------------

do_backup() {
    [ -d "$ROOT/data" ] || die "Orion is not installed here ($ROOT/data is missing)."
    if asks; then
        [ -n "$TO" ] || { read -r -p "Folder for the backup [$DIR]: " TO; TO="${TO:-$DIR}"; }
        if [ -z "$ENCRYPT" ]; then
            echo "Encrypt it? It holds every secret and your whole life."
            echo "  1) with a passphrase (recommended)"
            echo "  2) with an age public key (age1...)"
            echo "  3) no: root only on this server"
            read -r -p "Choice [1]: " choice
            case "${choice:-1}" in
                1) ENCRYPT=passphrase ;;
                2) read -r -p "Public key: " key; ENCRYPT="age:$key" ;;
                3) ENCRYPT=none ;;
                *) die "Nothing done." ;;
            esac
        fi
        if [ "$NIGHTLY" != 1 ] && [ -d "$ROOT/backups" ]; then
            read -r -p "Add the nightly backups (/srv/orion/backups) too? [y/N] " answer
            case "$answer" in y | Y | o | O | yes | oui) NIGHTLY=1 ;; esac
        fi
    fi
    TO="${TO:-$DIR}"
    ENCRYPT="${ENCRYPT:-none}"
    local ext="" tool=""
    case "$ENCRYPT" in
        none) ;;
        passphrase)
            [ -t 0 ] || die "a passphrase needs a terminal: use --encrypt age:<key> or none"
            if command -v age > /dev/null; then tool=age; ext=.age
            elif command -v gpg > /dev/null; then tool=gpg; ext=.gpg
            else die "no age or gpg to encrypt with: apt-get install age"; fi ;;
        age:age1*)
            command -v age > /dev/null || die "age is not installed: apt-get install age"
            tool=age-key; ext=.age ;;
        *) die "--encrypt: passphrase, age:<public key> (age1...) or none, not '$ENCRYPT'" ;;
    esac
    install -d -m 0700 "$TO"
    local out
    out="$TO/orion-full-$(date +%Y%m%d-%H%M%S).tar.gz$ext"
    [ ! -e "$out" ] || die "$out is already there"
    mapfile -t what < <(items)

    echo "A full backup of Orion goes to $out:"
    printf '  /%s\n' "${what[@]}"
    echo "  ($(du -shc "${what[@]/#//}" 2>/dev/null | tail -n 1 | cut -f 1) before compression)"
    [ "$ENCRYPT" != none ] || echo "Not encrypted: readable by root on this server only."
    echo "Orion is stopped while it is copied, a few seconds."
    if [ "$YES" != 1 ]; then
        [ -t 0 ] || die "no terminal to confirm: add --yes"
        read -r -p "Go on? [Y/n] " answer
        case "${answer:-y}" in y | Y | o | O | yes | oui) ;; *) die "Nothing done." ;; esac
    fi

    private_tmp "$TO"
    stop_orion
    check_journal "$ROOT/data/journal.sqlite3"
    check_journal "$ROOT/guardian/guardian.sqlite3"
    echo "==> copying"
    make_archive "$TMP/plain.tar.gz" "${what[@]}"
    start_again  # Orion redémarre avant le chiffrement : coupure minime

    case "$tool" in
        "") mv "$TMP/plain.tar.gz" "$out" ;;
        age) echo "==> encrypting (age)"; age -p -o "$out" "$TMP/plain.tar.gz" ;;
        age-key) echo "==> encrypting (age)"; age -r "${ENCRYPT#age:}" -o "$out" "$TMP/plain.tar.gz" ;;
        gpg)
            echo "==> encrypting (gpg)"
            gpg --symmetric --cipher-algo AES256 --pinentry-mode loopback -o "$out" "$TMP/plain.tar.gz" ;;
    esac
    chmod 0600 "$out"

    echo
    echo "Done: $out ($(du -h "$out" | cut -f 1))"
    printf '%s' "$CHECKS"
    echo "Keep a copy off the server, e.g. rclone copy $out ovh:orion-backups"
    echo "Restore: sudo orion restore $(basename "$out")"
}

# --- Action de restauration ---------------------------------------------------

choose_archive() {
    local found=() i
    mapfile -t found < <(ls -1t "$DIR"/orion-full-*.tar.gz* "$DIR"/orion-before-restore-*.tar.gz 2> /dev/null || true)
    [ "${#found[@]}" -gt 0 ] || die "no full backup in $DIR: give its path"
    if [ -t 0 ]; then
        echo -e "\n${CYAN}Archives disponibles dans $DIR :${RESET}"
    fi
    for i in "${!found[@]}"; do
        echo "  $((i + 1))) $(basename "${found[$i]}")  ($(du -h "${found[$i]}" 2>/dev/null | cut -f 1))"
    done
    read -r -p "Which one [1]: " choice
    choice="${choice:-1}"
    [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#found[@]}" ] \
        || die "Nothing done."
    ARCHIVE="${found[$((choice - 1))]}"
}

outside() {
    awk -v r="${ROOT#/}" -v e="${ETC#/}" -v i="$INFO" '
        function under(p) { return $0 == p || $0 == p "/" || index($0, p "/") == 1 }
        $0 == i { next }
        /(^|\/)\.\.(\/|$)/ { print; exit }
        under(r "/config") || under(r "/data") || under(r "/guardian") || under(r "/backups") \
            || under(e "/orion") { next }
        { print; exit }' "$1"
}

do_restore() {
    if [ "$TESTING" != 1 ]; then
        id orion-core > /dev/null 2>&1 && [ -x "$ORION" ] \
            || die "install Orion first (sudo ./install.sh), then restore over it"
    fi
    if [ -z "$ARCHIVE" ]; then
        asks || die "which archive? sudo $SELF restore <archive>"
        choose_archive
    fi
    [ -f "$ARCHIVE" ] || [ ! -f "$DIR/$ARCHIVE" ] || ARCHIVE="$DIR/$ARCHIVE"
    [ -f "$ARCHIVE" ] || die "no archive at $ARCHIVE"

    private_tmp "$DIR"
    local plain="$ARCHIVE"
    case "$ARCHIVE" in
        *.age)
            command -v age > /dev/null || die "age is not installed: apt-get install age"
            if [ -z "$IDENTITY" ] && asks; then
                read -r -p "Its age key file (empty if it was a passphrase): " IDENTITY
            fi
            plain="$TMP/plain.tar.gz"
            echo "==> decrypting"
            if [ -n "$IDENTITY" ]; then age -d -i "$IDENTITY" -o "$plain" "$ARCHIVE"
            else age -d -o "$plain" "$ARCHIVE"; fi ;;
        *.gpg)
            command -v gpg > /dev/null || die "gpg is not installed: apt-get install gnupg"
            plain="$TMP/plain.tar.gz"
            echo "==> decrypting"
            gpg --pinentry-mode loopback -d -o "$plain" "$ARCHIVE" ;;
        *.tar.gz) ;;
        *) die "$ARCHIVE: not a full backup (.tar.gz, .tar.gz.age or .tar.gz.gpg)" ;;
    esac

    tar -tzf "$plain" > "$TMP/list"
    grep -qxF "${ROOT#/}/data/journal.sqlite3" "$TMP/list" \
        || die "$ARCHIVE is not a full backup of an Orion in $ROOT (no data/journal.sqlite3)"
    local bad
    bad="$(outside "$TMP/list")"
    [ -z "$bad" ] || die "$ARCHIVE reaches outside Orion's folders ($bad): nothing done"

    echo "==> unpacking aside"
    mkdir "$TMP/new"
    tar -C "$TMP/new" -xpzf "$plain"
    [ "$plain" = "$ARCHIVE" ] || rm -f "$plain"
    check_journal "$TMP/new$ROOT/data/journal.sqlite3"
    check_journal "$TMP/new$ROOT/guardian/guardian.sqlite3"

    echo
    sed 's/^/  /' "$TMP/new/$INFO" 2> /dev/null || true
    echo "checked again here:"
    printf '%s' "$CHECKS"
    echo "It replaces Orion's settings, secrets, logins, journal, memory and files here."
    if [ "$KEEP_CURRENT" = 1 ]; then
        BEFORE="$DIR/orion-before-restore-$(date +%Y%m%d-%H%M%S).tar.gz"
        echo "What is here now is kept first: $BEFORE"
    else
        echo "--no-archive: what is here now is not kept."
    fi
    if [ "$YES" != 1 ]; then
        [ -t 0 ] || die "no terminal to confirm: add --yes"
        read -r -p "Type 'restore' to go on: " answer
        [ "$answer" = restore ] || die "Nothing done."
    fi

    stop_orion
    if [ "$KEEP_CURRENT" = 1 ]; then
        mapfile -t current < <(NIGHTLY=0 items)
        if [ "${#current[@]}" -gt 0 ]; then
            echo "==> keeping what is here"
            CHECKS=""
            make_archive "$BEFORE" "${current[@]}"
        else
            BEFORE=""
        fi
    fi

    echo "==> putting the backup in place"
    SWAPPING=1
    local path
    for path in "$ROOT/config" "$ROOT/data" "$ROOT/guardian" "$ETC/orion"; do
        [ -e "$TMP/new$path" ] || continue
        rm -rf "${path:?}"
        mkdir -p "$(dirname "$path")"
        mv "$TMP/new$path" "$path"
    done
    if [ -d "$TMP/new$ROOT/backups" ]; then  # Ajouté aux sauvegardes de la nuit, aucune supprimée
        mkdir -p "$ROOT/backups"
        cp -a "$TMP/new$ROOT/backups/." "$ROOT/backups/"
    fi
    SWAPPING=0
    start_again

    echo
    echo "Orion is back as it was in $(basename "$ARCHIVE")."
    echo "Check: sudo orion doctor"
    echo "If ChatGPT no longer answers, sign in again from the app: its login rotates."
    [ -z "$BEFORE" ] || echo "Undo: sudo orion restore $BEFORE"
}

case "$ACTION" in
    backup) do_backup ;;
    restore) do_restore ;;
esac
