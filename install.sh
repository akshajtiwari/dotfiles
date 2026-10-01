#!/usr/bin/env bash
# install.sh — reproduce this Hyprland setup on an Arch-based system.
#
# Safe to run repeatedly: packages use --needed, links that are already correct are
# skipped, and anything that would be overwritten is moved to ~/.dotfiles-backup/.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES=(hyprland config)               # stow-style packages, mirrored into $HOME
BACKUP_DIR="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
WALLPAPER_DIR="$HOME/Pictures/Wallpapers/Walls-main/Wallpapers"

DRY=0 YES=0 DO_PKG=0 DO_LINK=0 DO_SYS=0 DO_ZSH=0 DO_HW=0

usage() {
    cat <<'EOF'
Usage: ./install.sh [options]

  --packages    install pacman + AUR packages (system/packages/*.txt)
  --link        symlink the configs into $HOME (existing files are backed up)
  --system      install /etc files and enable services (uses sudo)
  --hardware    with --system: also install hardware-specific modprobe files
  --zsh         install oh-my-zsh and powerlevel10k if missing
  --all         --packages --link --system --zsh
  -y, --yes     do not ask for confirmation
  -n, --dry-run print what would happen without changing anything
  -h, --help    show this help

Typical first run on a fresh Arch install:   ./install.sh --all
Just refresh the symlinks after pulling:     ./install.sh --link
EOF
}

log()  { printf '\033[1;34m::\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

run() {
    if (( DRY )); then printf '   + %s\n' "$*"; else "$@"; fi
}

confirm() {
    (( YES || DRY )) && return 0
    local reply
    read -r -p "$1 [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

read_list() {   # print package names from a list file, ignoring comments/blank lines
    sed -e 's/#.*//' -e 's/[[:space:]]*$//' "$1" | awk 'NF {print $1}'
}

# ── arguments ────────────────────────────────────────────────────────────────
(( $# )) || { usage; exit 0; }
while (( $# )); do
    case "$1" in
        --packages) DO_PKG=1 ;;
        --link)     DO_LINK=1 ;;
        --system)   DO_SYS=1 ;;
        --hardware) DO_HW=1 ;;
        --zsh)      DO_ZSH=1 ;;
        --all)      DO_PKG=1 DO_LINK=1 DO_SYS=1 DO_ZSH=1 ;;
        -y|--yes)   YES=1 ;;
        -n|--dry-run) DRY=1 ;;
        -h|--help)  usage; exit 0 ;;
        *) usage; die "unknown option: $1" ;;
    esac
    shift
done

(( EUID == 0 )) && die "run this as your normal user (sudo is used where needed)"

# ── packages ─────────────────────────────────────────────────────────────────
aur_helper() {
    local h
    for h in yay paru; do command -v "$h" >/dev/null && { echo "$h"; return 0; }; done
    return 1
}

bootstrap_yay() {
    confirm "No AUR helper found. Build yay from the AUR now?" || return 1
    local tmp; tmp="$(mktemp -d)"
    run sudo pacman -S --needed --noconfirm base-devel git
    run git clone --depth 1 https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
    (cd "$tmp/yay-bin" && run makepkg -si --noconfirm)
    rm -rf "$tmp"
}

install_packages() {
    [[ -f /etc/arch-release ]] || die "package installation only supports Arch-based systems"
    local flags=(--needed)
    (( YES )) && flags+=(--noconfirm)

    log "Installing official packages"
    mapfile -t repo_pkgs < <(read_list "$REPO/system/packages/pacman.txt")
    run sudo pacman -S "${flags[@]}" "${repo_pkgs[@]}"

    log "Installing AUR packages"
    local helper
    if ! helper="$(aur_helper)"; then
        bootstrap_yay || { warn "Skipping AUR packages (no helper)"; return 0; }
        helper=yay
        (( DRY )) || helper="$(aur_helper)"
    fi
    mapfile -t aur_pkgs < <(read_list "$REPO/system/packages/aur.txt")
    run "$helper" -S "${flags[@]}" "${aur_pkgs[@]}"
}

# ── symlinks ─────────────────────────────────────────────────────────────────
backup() {      # move an existing path out of the way
    local path="$1" rel="${1#"$HOME"/}"
    log "backing up ~/$rel"
    run mkdir -p "$(dirname "$BACKUP_DIR/$rel")"
    run mv "$path" "$BACKUP_DIR/$rel"
}

link_package() {
    local pkg="$1" root="$REPO/$1" src rel dest want
    [[ -d "$root" ]] || die "missing package directory: $pkg"
    while IFS= read -r -d '' src; do
        rel="${src#"$root"/}"
        dest="$HOME/$rel"
        if [[ -L "$src" ]]; then
            # theme switches inside the repo (colors.css -> colors.light.css) are
            # replicated as relative links; never reset one the user already flipped
            [[ -L "$dest" ]] && continue
            want="$(readlink "$src")"
        else
            want="$src"
            [[ -L "$dest" && "$(readlink "$dest")" == "$want" ]] && continue
        fi
        if [[ -e "$dest" || -L "$dest" ]]; then backup "$dest"; fi
        run mkdir -p "$(dirname "$dest")"
        run ln -s "$want" "$dest"
    done < <(find "$root" \( -type f -o -type l \) -print0 | sort -z)
}

link_all() {
    local pkg
    for pkg in "${PACKAGES[@]}"; do
        log "Linking package: $pkg"
        link_package "$pkg"
    done
    log "Creating wallpaper folder: $WALLPAPER_DIR"
    run mkdir -p "$WALLPAPER_DIR"
    run mkdir -p "$HOME/.config/themesw"
    if [[ -d "$BACKUP_DIR" ]]; then log "Previous files were saved in $BACKUP_DIR"; fi
}

# ── zsh ──────────────────────────────────────────────────────────────────────
install_zsh() {
    command -v git >/dev/null || die "git is required for --zsh"
    if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
        log "Installing oh-my-zsh"
        run git clone --depth 1 https://github.com/ohmyzsh/ohmyzsh.git "$HOME/.oh-my-zsh"
    fi
    local p10k="$HOME/.oh-my-zsh/custom/themes/powerlevel10k"
    if [[ ! -d "$p10k" ]]; then
        log "Installing powerlevel10k"
        run git clone --depth 1 https://github.com/romkatv/powerlevel10k.git "$p10k"
    fi
    if [[ "${SHELL##*/}" != "zsh" ]] && confirm "Make zsh your login shell?"; then
        run chsh -s "$(command -v zsh)"
    fi
}

# ── system files and services ────────────────────────────────────────────────
install_system() {
    local etc="$REPO/system/etc" file rel dest unit
    log "Installing system files (sudo)"
    while IFS= read -r -d '' file; do
        rel="${file#"$etc"/}"
        if [[ "$rel" == modprobe.d/* ]] && (( ! DO_HW )); then
            warn "skipping hardware-specific /etc/$rel (use --hardware to install it)"
            continue
        fi
        dest="/etc/$rel"
        if [[ -f "$dest" ]] && cmp -s "$file" "$dest"; then continue; fi
        if [[ -f "$dest" ]]; then run sudo cp -a "$dest" "$dest.dotfiles-bak"; fi
        log "installing $dest"
        run sudo install -Dm644 "$file" "$dest"
    done < <(find "$etc" -type f -print0 | sort -z)

    log "Enabling services"
    while IFS= read -r unit; do
        if systemctl cat "$unit" >/dev/null 2>&1; then
            run sudo systemctl enable --now "$unit"
        else
            warn "unit not found, skipping: $unit (install its package first)"
        fi
    done < <(read_list "$REPO/system/services.txt")
}

# ── go ───────────────────────────────────────────────────────────────────────
(( DRY )) && log "Dry run: nothing will be changed"
(( DO_PKG ))  && install_packages
(( DO_LINK )) && link_all
(( DO_ZSH ))  && install_zsh
(( DO_SYS ))  && install_system

log "Done."
(( DO_LINK )) && log "Log out and pick the Hyprland session, or run: hyprctl reload"
exit 0
