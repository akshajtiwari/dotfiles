#!/bin/bash
# Waybar audio visualizer: prints bars while audio plays, empty line (hides module) when silent
CFG="${XDG_RUNTIME_DIR:-/tmp}/waybar-cava.conf"
pkill -f "cava -p $CFG" 2>/dev/null

cat > "$CFG" <<CONF
[general]
bars = 14
framerate = 30
[input]
method = pulse
source = auto
[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7
bar_delimiter = 59
CONF

cava -p "$CFG" | while IFS= read -r l; do
  l=${l//;/}
  if [[ $l =~ ^0*$ ]]; then echo ""; continue; fi
  l=${l//0/▁}; l=${l//1/▂}; l=${l//2/▃}; l=${l//3/▄}
  l=${l//4/▅}; l=${l//5/▆}; l=${l//6/▇}; l=${l//7/█}
  echo "$l"
done
