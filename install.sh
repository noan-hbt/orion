#!/usr/bin/env bash
# ==============================================================================
#   🌌 ORION — Assistant d'installation interactif
#
#   Installez Orion en une seule commande sur un serveur vierge (VPS) :
#   curl -fsSL https://raw.githubusercontent.com/noan-hbt/orion/main/install.sh | sudo bash
# ==============================================================================
set -euo pipefail

# Si le script est exécuté via un pipe (curl | bash), reconnecter l'entrée standard au terminal
if [ ! -t 0 ] && [ -e /dev/tty ]; then
    exec < /dev/tty
fi

# Couleurs et styles
if [ -t 1 ]; then
    BOLD="\033[1m"
    GREEN="\033[1;32m"
    BLUE="\033[1;34m"
    CYAN="\033[1;36m"
    YELLOW="\033[1;33m"
    RED="\033[1;31m"
    DIM="\033[2m"
    RESET="\033[0m"
else
    BOLD=""
    GREEN=""
    BLUE=""
    CYAN=""
    YELLOW=""
    RED=""
    DIM=""
    RESET=""
fi

REPO="${ORION_REPO:-https://github.com/noan-hbt/orion.git}"
BRANCH="${ORION_BRANCH:-main}"
ROOT=/srv/orion

clear 2>/dev/null || true

cat << "EOF"
  ____       _             
 / __ \_____(_)___  ____   
/ / / / ___/ / __ \/ __ \  
/ /_/ / /  / / /_/ / / / /  
\____/_/  /_/\____/_/ /_/   

EOF

echo -e "${BOLD}Bienvenue dans l'assistant d'installation d'Orion !${RESET}"
echo -e "${DIM}Votre agent personnel proactif, respectueux de votre vie privée et toujours éveillé.${RESET}\n"

# 1. Vérification des droits administrateur (root)
if [ "$(id -u)" != 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        echo -e "${YELLOW}Ce script nécessite les privilèges administrateur (sudo) pour installer les services système.${RESET}"
        echo -e "Élévation des droits en cours...\n"
        exec sudo bash "$0" "$@"
    else
        echo -e "${RED}Erreur : ce script doit être exécuté en tant que root (ou avec sudo).${RESET}" >&2
        exit 1
    fi
fi

# 2. Vérification du système d'exploitation
echo -e "${CYAN}==> Vérification du système...${RESET}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME="${PRETTY_NAME:-$ID}"
    echo -e "    Système détecté : ${BOLD}$OS_NAME${RESET}"
else
    echo -e "    ${YELLOW}Attention : système non identifié. Debian 12 ou Ubuntu 24.04 recommandé.${RESET}"
fi

# 3. Détection de l'adresse IP publique
echo -e "${CYAN}==> Recherche de votre adresse IP publique...${RESET}"
PUBLIC_IP="$(curl -fsS4 --max-time 5 https://api.ipify.org 2>/dev/null || \
             curl -fsS4 --max-time 5 https://ifconfig.me 2>/dev/null || \
             curl -fsS4 --max-time 5 https://icanhazip.com 2>/dev/null || true)"

DEFAULT_DOMAIN=""
if [[ "$PUBLIC_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    DEFAULT_DOMAIN="${PUBLIC_IP//./-}.sslip.io"
    echo -e "    Adresse IP trouvée : ${BOLD}$PUBLIC_IP${RESET}"
else
    echo -e "    ${YELLOW}Impossible de détecter l'IP automatiquement (pas de connexion IPv4 directe).${RESET}"
fi

echo ""
echo -e "${BOLD}Configuration de votre adresse web (HTTPS)${RESET}"
echo -e "Orion a besoin d'une adresse web sécurisée pour que vous puissiez lui parler"
echo -e "depuis l'application de votre smartphone.\n"

GIVEN_DOMAIN="${1:-}"
if [ -n "$GIVEN_DOMAIN" ]; then
    DOMAIN="$GIVEN_DOMAIN"
    echo -e "    Domaine fourni en argument : ${GREEN}${BOLD}$DOMAIN${RESET}"
elif [ -n "$DEFAULT_DOMAIN" ]; then
    echo -e "💡 ${GREEN}Option recommandée sans configuration DNS :${RESET}"
    echo -e "   Appuyez simplement sur ${BOLD}[Entrée]${RESET} pour utiliser l'adresse automatique gratuite :"
    echo -e "   👉 ${CYAN}https://$DEFAULT_DOMAIN${RESET} (certificat SSL automatique inclus)\n"
    echo -e "🌐 Ou saisissez votre propre nom de domaine (ex: ${DIM}orion.mon-domaine.fr${RESET}) :"
    read -r -p "Domaine [$DEFAULT_DOMAIN] : " USER_DOMAIN
    DOMAIN="${USER_DOMAIN:-$DEFAULT_DOMAIN}"
else
    echo -e "🌐 Entrez votre nom de domaine (ex: ${DIM}orion.mon-domaine.fr${RESET}) :"
    read -r -p "Domaine : " DOMAIN
    while [ -z "$DOMAIN" ]; do
        echo -e "${RED}Veuillez entrer un domaine valide.${RESET}"
        read -r -p "Domaine : " DOMAIN
    done
fi

DOMAIN="$(echo "$DOMAIN" | tr -d ' ')"
echo -e "✓ Domaine sélectionné : ${GREEN}${BOLD}$DOMAIN${RESET}\n"

# 4. Préparation et récupération du code
echo -e "${CYAN}==> Récupération du code d'Orion...${RESET}"
apt-get update -qq
apt-get install -y -qq git curl ca-certificates sudo >/dev/null

if [ -d "$ROOT/app/.git" ]; then
    echo -e "    Mise à jour du dépôt existant dans $ROOT/app..."
    git -C "$ROOT/app" fetch -q origin "$BRANCH"
    git -C "$ROOT/app" checkout -q -B "$BRANCH" "origin/$BRANCH"
else
    echo -e "    Téléchargement d'Orion dans $ROOT/app..."
    install -d -m 0755 "$ROOT"
    git clone -q --branch "$BRANCH" "$REPO" "$ROOT/app"
fi

# 5. Lancement de l'installation technique complète
echo -e "\n${CYAN}==> Installation des composants d'Orion...${RESET}"
echo -e "${DIM}Cette étape configure Caddy (HTTPS), Python, Chromium, les utilisateurs et le pare-feu.${RESET}"
bash "$ROOT/app/deploy/install.sh" "$DOMAIN"

# 6. Message de succès et instructions d'accueil
echo ""
echo -e "${GREEN}==============================================================================${RESET}"
echo -e "${GREEN}${BOLD}           🎉 FÉLICITATIONS ! VOTRE ORION EST INSTALLÉ ET ACTIF           ${RESET}"
echo -e "${GREEN}==============================================================================${RESET}"
echo ""
echo -e "Votre assistant tourne en arrière-plan sur : ${CYAN}${BOLD}https://$DOMAIN${RESET}"
echo ""
echo -e "${BOLD}📱 Connecter votre iPhone en 3 étapes :${RESET}"
echo -e "  1. Ouvrez ${BOLD}Safari${RESET} sur votre téléphone et accédez à : ${CYAN}https://$DOMAIN/app/${RESET}"
echo -e "  2. Touchez le bouton ${BOLD}Partager${RESET} (carré avec flèche vers le haut) puis ${BOLD}« Sur l'écran d'accueil »${RESET}"
echo -e "  3. Ouvrez l'application Orion depuis votre écran d'accueil, saisissez le code affiché plus haut et validez avec ${BOLD}Face ID${RESET}."
echo ""
echo -e "${BOLD}🛠️ Commandes utiles sur votre serveur :${RESET}"
echo -e "  - Vérifier l'état de santé :      ${DIM}sudo orion doctor${RESET}"
echo -e "  - Voir la mémoire d'Orion :       ${DIM}sudo orion memory${RESET}"
echo -e "  - Lancer une sauvegarde manuelle :${DIM}sudo /srv/orion/app/deploy/backup.sh${RESET}"
echo -e "  - Consulter les journaux récents :${DIM}sudo journalctl -u orion-core -f${RESET}"
echo ""
echo -e "${DIM}Vous n'avez plus besoin de vous connecter en SSH. Tout se pilote désormais depuis l'application !${RESET}\n"
