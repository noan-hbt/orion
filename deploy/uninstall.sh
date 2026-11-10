#!/usr/bin/env bash
# ==============================================================================
#   ⚠️  ORION — Assistant de désinstallation
#
#   Supprime Orion du serveur proprement : services, code, données, utilisateurs.
#
#   Usage interactif :
#     sudo orion uninstall            # ou : sudo deploy/uninstall.sh
#
#   Options :
#     --purge    Supprime tout sans garder d'archive de secours dans /root
#     --yes      Confirme la désinstallation sans poser de question
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

ROOT="${ORION_ROOT:-/srv/orion}"  # ORION_ROOT et ORION_ETC : installation de test
ETC="${ORION_ETC:-/etc}"
PURGE=0
YES=0

for arg in "$@"; do
    case "$arg" in
        --purge) PURGE=1 ;;
        --yes) YES=1 ;;
        *) echo "unknown option: $arg (--purge, --yes)"; exit 2 ;;
    esac
done

[ -n "${ORION_ROOT:-}" ] || [ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }

if [ ! -d "$ROOT" ] && [ ! -d "$ETC/orion" ] && ! compgen -G "$ETC/systemd/system/orion-*" >/dev/null; then
    echo "Orion is not installed here."
    exit 0
fi

ARCHIVE="${ORION_ARCHIVE_DIR:-/root}/orion-$(date +%Y%m%d-%H%M%S).tar.gz"

if [ -t 0 ] && [ "$YES" != 1 ]; then
    echo -e "${YELLOW}══════════════════════════════════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}${RED}             ⚠️  ASSISTANT DE DÉSINSTALLATION D'ORION${RESET}"
    echo -e "${YELLOW}══════════════════════════════════════════════════════════════════════════════${RESET}\n"
    echo -e "Cette opération va retirer Orion de ce serveur."
    echo -e "${BOLD}Ce qui sera supprimé :${RESET}"
    echo -e "  - Les services d'arrière-plan (${DIM}orion-core${RESET}, ${DIM}orion-guardian${RESET}, ${DIM}timers${RESET})"
    echo -e "  - L'application, l'environnement Python et le navigateur"
    echo -e "  - Vos données de vie (${DIM}journal de bord, mémoire, conversations, fichiers${RESET})"
    echo -e "  - Les utilisateurs système isolés et les droits sudo"
    echo -e "  - Le site web Caddy (Caddy retrouvera sa page d'accueil par défaut)\n"
    echo -e "${BOLD}Ce qui reste sur votre serveur :${RESET}"
    echo -e "  - Les paquets système généraux (${DIM}Caddy, uv, ffmpeg, sqlite3${RESET})"
    echo -e "  - Les règles de pare-feu (${DIM}SSH, 80 et 443 restent ouverts${RESET})\n"
    
    if [ "$PURGE" != 1 ]; then
        echo -e "${CYAN}💡 Option de sécurité :${RESET}"
        echo -e "Par défaut, une archive de sauvegarde de vos souvenirs, réglages et secrets"
        echo -e "sera automatiquement créée et conservée dans : ${BOLD}$ARCHIVE${RESET}\n"
        echo -e "Souhaitez-vous conserver cette archive de sécurité ?"
        echo -e "  ${BOLD}1)${RESET} Oui, créer une archive de secours dans /root ${GREEN}(recommandé)${RESET}"
        echo -e "  ${BOLD}2)${RESET} Non, supprimer définitivement sans aucune copie (${RED}--purge${RESET})"
        read -r -p "Votre choix [1] : " choice
        case "${choice:-1}" in
            1) PURGE=0 ;;
            2) PURGE=1 ;;
            *) echo "Nothing done."; exit 1 ;;
        esac
        echo ""
    fi
fi

# Messages d'information (attendus par les tests et l'utilisateur)
echo "This removes Orion from this server: services, code, data, secrets, users."
if [ "$PURGE" = 1 ]; then
    echo "--purge: no archive is kept. Its memory, your logins and its secrets are gone for good."
else
    echo "An archive of the data, config and secrets is kept first: $ARCHIVE"
fi

# Confirmation explicite
if [ "$YES" != 1 ]; then
    [ -t 0 ] || { echo "no terminal to confirm: add --yes"; exit 1; }
    echo -e "${YELLOW}Êtes-vous absolument certain de vouloir désinstaller Orion ?${RESET}"
    read -r -p "Type 'uninstall' to go on: " answer
    [ "$answer" = "uninstall" ] || { echo "Nothing done."; exit 1; }
fi

echo "==> services"
units=()
for path in "$ETC"/systemd/system/orion-*.service "$ETC"/systemd/system/orion-*.timer; do
    [ -e "$path" ] && units+=("$(basename "$path")")
done
for unit in "${units[@]}"; do
    systemctl disable --now -q "$unit" 2>/dev/null || true
done
for unit in "${units[@]}"; do
    rm -f "$ETC/systemd/system/$unit"
done
systemctl daemon-reload
systemctl reset-failed 'orion-*' 2>/dev/null || true

if [ "$PURGE" != 1 ]; then
    echo "==> archive"
    kept=()
    for path in "$ROOT/data" "$ROOT/guardian" "$ROOT/config" "$ROOT/backups" "$ETC/orion"; do
        [ -e "$path" ] && kept+=("${path#/}")
    done
    if [ "${#kept[@]}" -gt 0 ]; then
        (umask 077 && tar -C / -czf "$ARCHIVE" "${kept[@]}")
        echo "    $ARCHIVE"
    fi
fi

echo "==> Caddy"
if [ -f "$ETC/caddy/Caddyfile" ] && grep -q "Orion's public face" "$ETC/caddy/Caddyfile"; then
    cat > "$ETC/caddy/Caddyfile" <<'CADDY'
# Caddy's default site (Orion was removed).
:80 {
	root * /usr/share/caddy
	file_server
}
CADDY
    systemctl reload-or-restart caddy 2>/dev/null || true
fi

echo "==> files"
rm -rf "$ROOT" "$ETC/orion" "$ETC/sudoers.d/orion-core"

echo "==> users"
for user in orion-core orion-guardian; do
    [ -z "${ORION_ROOT:-}" ] || break  # a pretend installation has none of its own
    if id "$user" >/dev/null 2>&1; then
        pkill -u "$user" 2>/dev/null || true
        userdel "$user"
    fi
done
[ -z "${ORION_ROOT:-}" ] && getent group orion >/dev/null && groupdel orion

echo
echo "Orion is uninstalled."

if [ "$PURGE" != 1 ] && [ -f "$ARCHIVE" ]; then
    echo -e "${GREEN}✓ Vos données et souvenirs ont été sécurisés dans :${RESET} ${BOLD}$ARCHIVE${RESET}"
    echo -e "  Pour réinstaller Orion et restaurer votre historique un jour :"
    echo -e "  1. Lancez l'installation : ${DIM}curl -fsSL https://raw.githubusercontent.com/.../install.sh | sudo bash${RESET}"
    echo -e "  2. Restaurez votre archive : ${DIM}sudo orion restore $ARCHIVE${RESET}\n"
fi
