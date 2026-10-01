#!/bin/bash
# set_wallpaper.sh FILE — apply a wallpaper, regenerate pywal colors, restart waybar
FILE="$1"
[ -f "$FILE" ] || exit 1

awww img "$FILE" \
  --transition-fps 255 \
  --transition-type outer \
  --transition-duration 0.8

# optional: regenerate terminal colours when pywal is installed
command -v wal >/dev/null && wal -i "$FILE" -n

# SIGUSR2 live-reload crashes waybar, so restart it cleanly
pkill -x waybar
while pgrep -x waybar >/dev/null; do sleep 0.05; done
setsid -f waybar >/dev/null 2>&1
