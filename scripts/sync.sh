#!/usr/bin/env bash
# sync.sh — copy the live configuration into this repository.
#
# Everything is driven by an explicit allowlist (see the bottom of the file), so
# runtime state, caches, history and credentials can never sneak in. The script
# is idempotent: run it as often as you like, then `git diff` to review.
#
#   scripts/sync.sh            # sync everything
#   scripts/sync.sh --dry-run  # show what would change
#   SRC_HOME=/some/home scripts/sync.sh   # sync from another home directory
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${SRC_HOME:-$HOME}"
RSYNC=(rsync -a --delete --prune-empty-dirs)
DRY=0
if [[ "${1:-}" == "--dry-run" ]]; then DRY=1; RSYNC+=(-n -i); fi

log() { printf '  %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
command -v rsync >/dev/null || die "rsync is required"

# Always-excluded junk, wherever it appears.
COMMON_EXCLUDES=(--exclude='__pycache__/' --exclude='*.pyc' --exclude='*.bak' --exclude='*.swp'
                 --exclude='.DS_Store' --exclude='*.log')

# sync_dir <package> <path-relative-to-home> [extra rsync args...]
sync_dir() {
    local pkg="$1" rel="$2"; shift 2
    [[ -d "$SRC/$rel" ]] || { log "skip   $rel (not found)"; return 0; }
    mkdir -p "$REPO/$pkg/$rel"
    log "dir    $rel"
    "${RSYNC[@]}" "${COMMON_EXCLUDES[@]}" "$@" "$SRC/$rel/" "$REPO/$pkg/$rel/"
}

# sync_file <package> <path-relative-to-home>
sync_file() {
    local pkg="$1" rel="$2"
    [[ -e "$SRC/$rel" ]] || { log "skip   $rel (not found)"; return 0; }
    mkdir -p "$(dirname "$REPO/$pkg/$rel")"
    log "file   $rel"
    "${RSYNC[@]}" "$SRC/$rel" "$REPO/$pkg/$rel"
}

# sync_system <absolute-source> <path-under-system/etc>
sync_system() {
    local abs="$1" rel="$2"
    [[ -f "$abs" ]] || { log "skip   $abs (not found)"; return 0; }
    mkdir -p "$(dirname "$REPO/system/etc/$rel")"
    log "system $abs"
    "${RSYNC[@]}" "$abs" "$REPO/system/etc/$rel"
}

# Rewrite absolute symlinks (pointing inside the live home) as relative ones, and
# drop symlinks that dangle or point outside the home directory.
fix_symlinks() {
    local pkg link target live resolved
    for pkg in hyprland config; do
        [[ -d "$REPO/$pkg" ]] || continue
        while IFS= read -r -d '' link; do
            target="$(readlink "$link")"
            live="$SRC/${link#"$REPO/$pkg/"}"
            if [[ "$target" == /* ]]; then
                if [[ "$target" == "$SRC"/* && -e "$target" ]]; then
                    ln -sfn "$(realpath -m --relative-to="$(dirname "$live")" "$target")" "$link"
                else
                    log "drop   dangling/external symlink ${link#"$REPO/"}"
                    rm -f "$link"
                fi
            elif [[ ! -e "$(dirname "$live")/$target" ]]; then
                log "drop   dangling symlink ${link#"$REPO/"}"
                rm -f "$link"
            fi
        done < <(find "$REPO/$pkg" -type l -print0)
    done
}

# The repository always ships the light variant of every theme switch.
normalize_theme_links() {
    local h="$REPO/hyprland/.config" c="$REPO/config/.config"
    [[ -d "$h/waybar/colors" ]]          && ln -sfn colors.light.css "$h/waybar/colors/colors.css"
    [[ -d "$h/swaync/colors" ]]          && ln -sfn colors.light.css "$h/swaync/colors/colors.css"
    [[ -d "$h/nwg-dock-hyprland/colors" ]] && ln -sfn colors.light.css "$h/nwg-dock-hyprland/colors/colors.css"
    [[ -d "$c/nvim/lua/colors" ]]        && ln -sfn colors.light.lua "$c/nvim/lua/colors/colors.lua"
    [[ -d "$c/gtk-3.0" ]] && { ln -sfn gtk/light.css "$c/gtk-3.0/gtk.css"; ln -sfn settings/light.ini "$c/gtk-3.0/settings.ini"; }
    [[ -d "$c/gtk-4.0" ]] && ln -sfn settings/light.ini "$c/gtk-4.0/settings.ini"
    return 0
}

# Remove machine-specific bits from text files that were copied.
sanitize() {
    local user; user="$(basename "$SRC")"
    local f
    # wlogout: make image urls relative to the stylesheet instead of absolute
    f="$REPO/hyprland/.config/wlogout/style.css"
    [[ -f "$f" ]] && sed -i -E 's#url\("'"$SRC"'/\.config/assets/#url("../assets/#g' "$f"
    # scripts: no hard-coded home directory
    while IFS= read -r -d '' f; do
        sed -i "s#$SRC#\$HOME#g" "$f"
    done < <(find "$REPO/hyprland/.config/scripts" -type f -name '*.sh' -print0 2>/dev/null)
    # btop: its "current" theme is a symlink managed elsewhere, fall back to a stock one
    f="$REPO/config/.config/btop/btop.conf"
    [[ -f "$f" ]] && sed -i 's#^color_theme = "current"#color_theme = "Default"#' "$f"
    # zsh: portable paths, and never export API keys / odd leftovers
    f="$REPO/config/.zshrc"
    if [[ -f "$f" ]]; then
        sed -i -E \
            -e '/(API_KEY|_TOKEN|_SECRET|PASSWORD)=/d' \
            -e '/API key$/d' \
            -e "/^alias logoutt /d" \
            -e "s#$SRC#\$HOME#g" "$f"
    fi
    f="$REPO/config/.p10k.zsh"
    [[ -f "$f" ]] && sed -i "s#$SRC#\$HOME#g" "$f"
    return 0
}

echo "Syncing from $SRC into $REPO"

# ───────────────────────────── hyprland package ─────────────────────────────
H=hyprland
sync_dir  $H .config/hypr --include='hyprland.lua' --include='hypridle.conf' --include='hyprlock.conf' --exclude='*'
sync_dir  $H .config/waybar --exclude='README.md'
sync_dir  $H .config/swaync --exclude='README.md'
sync_dir  $H .config/tofi
sync_dir  $H .config/wlogout --exclude='icons/'
sync_dir  $H .config/assets/wlogout
sync_dir  $H .config/nwg-dock-hyprland
sync_dir  $H .config/quickpanel
sync_dir  $H .config/scripts
sync_dir  $H .config/themesw/units --include='10-gtk' --include='20-waybar' --include='30-dock' \
          --include='30-nvim' --include='30-swaync' --exclude='*'
sync_file $H .config/xdg-desktop-portal/portals.conf
for b in qp wallpicker powerprofile caffeine mictoggle themesw toggle_bluetooth brightness volume \
         playerctl_volume cycle_layout refreshrate screenrec screenshot powersafe hotspot; do
    sync_file $H ".local/bin/$b"
done

# ────────────────────────────── config package ──────────────────────────────
C=config
sync_dir  $C .config/kitty
sync_dir  $C .config/btop
sync_dir  $C .config/cava
sync_dir  $C .config/fastfetch
sync_dir  $C .config/nvim
sync_dir  $C .config/yazi
sync_dir  $C .config/Kvantum
sync_dir  $C .config/qt6ct
sync_dir  $C .config/wireplumber
sync_dir  $C .config/gtk-3.0 --exclude='bookmarks'
sync_dir  $C .config/gtk-4.0
sync_file $C .zshrc
sync_file $C .p10k.zsh

# ──────────────────────────── system (needs root to install) ────────────────
sync_system /etc/tlp.conf                       tlp.conf
sync_system /etc/modprobe.d/nvidia-power.conf   modprobe.d/nvidia-power.conf
sync_system /etc/modprobe.d/hid_apple.conf      modprobe.d/hid_apple.conf

if (( DRY )); then echo "Dry run: post-processing skipped."; exit 0; fi
fix_symlinks
normalize_theme_links
sanitize
echo "Done. Review with: git -C \"$REPO\" status && git -C \"$REPO\" diff"
