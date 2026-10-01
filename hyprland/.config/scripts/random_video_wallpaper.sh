#!/bin/bash

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export WAYLAND_DISPLAY="wayland-1"

VIDEO_DIR="$HOME/Videos/Wallpapers"

RANDOM_WALLPAPER=$(find "$VIDEO_DIR" -type f -iname "*.mp4" | shuf -n 1)

[ -z "$RANDOM_WALLPAPER" ] && exit 1

pkill mpvpaper 2>/dev/null

# mpvpaper -o "--no-audio --loop" ALL "$RANDOM_WALLPAPER"
mpvpaper -o "--loop" ALL "$RANDOM_WALLPAPER"
