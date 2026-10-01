#!/bin/bash
# Theme picker in the same tofi overlay style as the clipboard / app picker
CUR=$(~/.local/bin/themesw --current)
mark() { [ "$CUR" = "$1" ] && echo " (current)"; }
CHOICE=$(printf '%s\n%s\n' "  Light$(mark light)" "  Dark$(mark dark)" \
  | tofi -c ~/.config/tofi/configV --prompt-text " theme : ")
case "$CHOICE" in
  *Light*) exec ~/.local/bin/themesw light ;;
  *Dark*)  exec ~/.local/bin/themesw dark ;;
esac
