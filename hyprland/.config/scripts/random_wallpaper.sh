#!/bin/bash

WALLPAPER_DIR="$HOME/Pictures/Wallpapers/Walls-main/Wallpapers"

RANDOM_WALLPAPER=$(find "$WALLPAPER_DIR" -type f \( \
  -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" -o -iname "*.webp" \
\) | shuf -n 1)

[ -z "$RANDOM_WALLPAPER" ] && exit 1

exec "$HOME/.config/scripts/set_wallpaper.sh" "$RANDOM_WALLPAPER"
