-- #######################################################################################
-- CONVERTED FROM hyprland.conf (hyprlang) TO hyprland.lua FOR HYPRLAND 0.55+
-- Place this at ~/.config/hypr/hyprland.lua
-- Your old ~/.config/hypr/hyprland.conf can stay there as a backup, but once this
-- .lua file exists, Hyprland loads it INSTEAD of the .conf on the next full restart.
-- #######################################################################################

----------------
---- MONITORS ----
----------------
-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
-- old: monitor=,preferred,auto,1,mirror,DP-1
hl.monitor({
  output   = "",
  mode     = "preferred",
  position = "auto",
  scale    = 1,
  mirror   = "DP-1",
})

---------------------
---- MY PROGRAMS ----
---------------------
local terminal   = "kitty"
local fileManager = "dolphin"
local menu       = "tofi-drun -c ~/.config/tofi/configA --drun-launch=true"
local browser    = "zen"
local notes      = "obsidian"
local editor     = "code"
local colorPicker = "hyprpicker"
local spotifyApp = "spotify-launcher"

-------------------
---- AUTOSTART ----
-------------------
-- See https://wiki.hypr.land/Configuring/Basics/Autostart/
hl.on("hyprland.start", function()
  hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1") -- Polkit to manage passwords
  hl.exec_cmd("swaync") -- notifications + control center (dunst removed: two daemons fight over the bus name)
  hl.exec_cmd("waybar") -- topbar
  hl.exec_cmd("awww-daemon") -- wallpaper daemon
  -- hl.exec_cmd("swww img ~/.config/assets/backgrounds/cat_leaves.png --transition-fps 255 --transition-type outer --transition-duration 0.8")
  hl.exec_cmd("wl-paste --type text --watch cliphist store") -- clipboard
  hl.exec_cmd("wl-paste --type image --watch cliphist store")
  hl.exec_cmd("hypridle")
  hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
end)

-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Nvidia
hl.env("LIBVA_DRIVER_NAME", "nvidia")
hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("GBM_BACKEND", "nvidia-drm")
hl.env("__GLX_VENDOR_LIBRARY_NAME", "nvidia") -- remove if firefox crashes
hl.env("NVD_BACKEND", "direct")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")

-- QT
hl.env("QT_QPA_PLATFORM", "wayland")
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
hl.env("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
hl.env("QT_STYLE_OVERRIDE", "kvantum")

-- Toolkit Backend Variables
hl.env("GDK_BACKEND", "wayland,x11,*")
hl.env("SDL_VIDEODRIVER", "wayland")
hl.env("CLUTTER_BACKEND", "wayland")

-- XDG Specifications
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")

-----------------------
---- LOOK AND FEEL ----
-----------------------
-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
  general = {
    gaps_in = 5,
    gaps_out = 5,
    border_size = 2,
    col = {
      -- old: col.active_border = rgb(8aadf4) rgb(24273A) rgb(24273A) rgb(8aadf4) 45deg
      active_border = {
        colors = { "rgb(8aadf4)", "rgb(24273A)", "rgb(24273A)", "rgb(8aadf4)" },
        angle = 45,
      },
      -- old: col.inactive_border = rgb(24273A) rgb(24273A) rgb(24273A) rgb(27273A) 45deg
      inactive_border = {
        colors = { "rgb(24273A)", "rgb(24273A)", "rgb(24273A)", "rgb(27273A)" },
        angle = 45,
      },
    },
    resize_on_border = true,
    allow_tearing = false,
    layout = "dwindle",
  },

  decoration = {
    rounding = 10,
    active_opacity = 1.0,
    inactive_opacity = 1.0,
    blur = {
      enabled = true,
      size = 3,
      passes = 3,
      new_optimizations = true,
      vibrancy = 0.1696,
      ignore_opacity = true,
    },
  },

  animations = {
    enabled = true,
  },
})

-- Bezier curves
-- old: bezier = wind, 0.05, 0.9, 0.1, 1.05
hl.curve("wind",   { type = "bezier", points = { {0.05, 0.9}, {0.1, 1.05} } })
-- old: bezier = winIn, 0.1, 1.1, 0.1, 1.1
hl.curve("winIn",  { type = "bezier", points = { {0.1, 1.1}, {0.1, 1.1} } })
-- old: bezier = winOut, 0.3, -0.3, 0, 1
hl.curve("winOut", { type = "bezier", points = { {0.3, -0.3}, {0, 1} } })
-- old: bezier = liner, 1, 1, 1, 1
hl.curve("liner",  { type = "bezier", points = { {1, 1}, {1, 1} } })

-- Animations
hl.animation({ leaf = "windows",      enabled = true, speed = 6,  bezier = "wind",   style = "slide" })
hl.animation({ leaf = "windowsIn",    enabled = true, speed = 6,  bezier = "winIn",  style = "slide" })
hl.animation({ leaf = "windowsOut",   enabled = true, speed = 5,  bezier = "winOut", style = "slide" })
hl.animation({ leaf = "windowsMove",  enabled = true, speed = 5,  bezier = "wind",   style = "slide" })
hl.animation({ leaf = "border",       enabled = true, speed = 1,  bezier = "liner" })
hl.animation({ leaf = "borderangle",  enabled = true, speed = 30, bezier = "liner",  style = "loop" })
hl.animation({ leaf = "fade",         enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "workspaces",   enabled = true, speed = 5,  bezier = "wind" })

-- Dwindle layout
-- See https://wiki.hypr.land/Configuring/Layouts/Dwindle-Layout/
hl.config({
  dwindle = {
    preserve_split = true,
  },
})
-- NOTE: dwindle.pseudotile was removed entirely in Hyprland 0.55 ("wasn't doing
-- anything", per the changelog). Pseudotiling is now purely per-window via the
-- pseudo dispatcher, which your SUPER+P bind below already calls.

-- Misc
hl.config({
  misc = {
    force_default_wallpaper = 0,  -- 0 or 1 disables the anime mascot wallpapers
    disable_hyprland_logo = true,
    disable_splash_rendering = true,
    vrr = 0,
  },
})

---------------
---- INPUT ----
---------------
hl.config({
  input = {
    kb_layout = "us",
    kb_variant = "",
    kb_model = "",
    kb_options = "",
    kb_rules = "",
    follow_mouse = 1,
    sensitivity = 0,
    touchpad = {
      natural_scroll = true,
    },
  },
})

hl.gesture({ fingers = 4, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 4, direction = "vertical",   action = "close" })

-- Example per-device config
hl.device({
  name = "epic-mouse-v1",
  sensitivity = -0.5,
})

---------------------
---- KEYBINDINGS ----
---------------------
local mainMod = "SUPER"

-- NOTE: your original .conf bound SUPER+S twice (spotify, then editor-alt).
-- You've since pointed SUPER+S at spotify directly and moved special-workspace
-- toggle to SUPER+P (which is free now that dwindle pseudotile is gone).

hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(browser))
hl.bind(mainMod .. " + O", hl.dsp.exec_cmd(notes))
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd(editor))
hl.bind(mainMod .. " + S", hl.dsp.exec_cmd(spotifyApp))
hl.bind(mainMod .. " + Q", hl.dsp.window.close())
hl.bind(mainMod .. " + F", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + W", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + A", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit")) -- dwindle only

hl.bind("SUPER + E", hl.dsp.exec_cmd("jome -d | wl-copy")) -- Emoji picker + clipboard copy

-- Move focus with mainMod + arrow keys
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- Move window position with mainMod + SHIFT + arrow keys
hl.bind(mainMod .. " + SHIFT + left",  hl.dsp.window.move({ direction = "left" }))
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.move({ direction = "right" }))
hl.bind(mainMod .. " + SHIFT + up",    hl.dsp.window.move({ direction = "up" }))
hl.bind(mainMod .. " + SHIFT + down",  hl.dsp.window.move({ direction = "down" }))

-- Switch workspaces with mainMod + [0-9], move window to workspace with + SHIFT
for i = 1, 10 do
  local key = i % 10 -- 10 maps to key 0
  hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i }))
  hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

-- Special workspace (scratchpad)
hl.bind(mainMod .. " + P", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Move/resize windows with mainMod + Z/X (kept from your original bindm lines)
hl.bind(mainMod .. " + Z", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + X", hl.dsp.window.resize(), { mouse = true })

-- Resize active window with mainMod+ALT + arrow keys (binde, repeating)
hl.bind(mainMod .. " + ALT + right", hl.dsp.window.resize({ x = 30,  y = 0 }),   { repeating = true })
hl.bind(mainMod .. " + ALT + left",  hl.dsp.window.resize({ x = -30, y = 0 }),   { repeating = true })
hl.bind(mainMod .. " + ALT + up",    hl.dsp.window.resize({ x = 0,   y = -30 }), { repeating = true })
hl.bind(mainMod .. " + ALT + down",  hl.dsp.window.resize({ x = 0,   y = 30 }),  { repeating = true })

-- Clipboard
hl.bind("SUPER + V", hl.dsp.exec_cmd("cliphist list | tofi -c ~/.config/tofi/configV | cliphist decode | wl-copy"))

-- Colour Picker
-- hl.bind(mainMod .. " + P", hl.dsp.exec_cmd(colorPicker .. " | wl-copy")) -- now conflicts with special-workspace toggle on P, pick a different key if you want this back

-- Screen locking
hl.bind("SUPER + L", hl.dsp.exec_cmd("hyprlock"))

-- wlogout
hl.bind("SUPER + ESCAPE", hl.dsp.exec_cmd("wlogout"))

-- Screenshots (add --cursor to include cursor, --freeze to freeze before selection)
hl.bind("Print",        hl.dsp.exec_cmd("grimblast --notify copysave screen"))
hl.bind("SUPER + Print", hl.dsp.exec_cmd("grimblast --notify copysave active"))
hl.bind("SUPER + ALT + Print", hl.dsp.exec_cmd("grimblast --notify copysave area"))

-- Volume and media control
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("pamixer -i 3"), { locked = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("pamixer -d 3"), { locked = true })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("pamixer --default-source -m"), { locked = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("pamixer -t"), { locked = true })
hl.bind("XF86AudioPlay",        hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPause",       hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioNext",        hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPrev",        hl.dsp.exec_cmd("playerctl previous"), { locked = true })

-- Screen brightness
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl s +3%"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl s 3%-"), { locked = true, repeating = true })

-- Wi-Fi / Bluetooth overlay panels
hl.bind(mainMod .. " + CTRL + W", hl.dsp.exec_cmd("~/.local/bin/qp wifi"))
hl.bind(mainMod .. " + CTRL + B", hl.dsp.exec_cmd("~/.local/bin/qp bluetooth"))

-- Random wallpaper (static)
hl.bind(mainMod .. " + k", hl.dsp.exec_cmd("~/.config/scripts/random_wallpaper.sh"))

-- Wallpaper picker (thumbnails) / theme picker
hl.bind(mainMod .. " + SHIFT + K", hl.dsp.exec_cmd("~/.local/bin/wallpicker"))
hl.bind(mainMod .. " + SHIFT + T", hl.dsp.exec_cmd("~/.config/scripts/theme_picker.sh"))

-- Random wallpaper (video)
hl.bind("ALT + k", hl.dsp.exec_cmd("~/.config/scripts/random_video_wallpaper.sh"))

-- Kill video wallpaper
hl.bind("ALT + SHIFT + K", hl.dsp.exec_cmd("~/.config/scripts/stop_video_wallpaper.sh"))

--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------
-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/

hl.window_rule({
  name = "thorium-opacity",
  match = { class = "^(Thorium-browser)$" },
  opacity = "0.90 0.90",
})

hl.window_rule({
  name = "code-opacity",
  match = { class = "^(Code)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "arduino-ide-opacity",
  match = { class = "^(Arduino IDE)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "warp-opacity",
  match = { class = "^(dev.warp.Warp)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "obsidian-opacity",
  match = { class = "^(obsidian)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "code-url-handler-opacity",
  match = { class = "^(code-url-handler)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "code-insiders-url-handler-opacity",
  match = { class = "^(code-insiders-url-handler)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "kitty-opacity",
  match = { class = "^(kitty)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "nautilus-opacity",
  match = { class = "^(org.gnome.Nautilus)$" },
  opacity = "0.80 0.80",
})

hl.window_rule({
  name = "ark-float",
  match = { class = "^(org.kde.ark)$" },
  opacity = "0.80 0.80",
  float = true,
})

hl.window_rule({
  name = "nwg-look-float",
  match = { class = "^(nwg-look)$" },
  opacity = "0.80 0.80",
  float = true,
})

hl.window_rule({
  name = "qt5ct-float",
  match = { class = "^(qt5ct)$" },
  opacity = "0.80 0.80",
  float = true,
})

hl.window_rule({
  name = "qt6ct-float",
  match = { class = "^(qt6ct)$" },
  opacity = "0.80 0.80",
  float = true,
})

hl.window_rule({
  name = "kvantummanager-float",
  match = { class = "^(kvantummanager)$" },
  opacity = "0.80 0.80",
  float = true,
})

hl.window_rule({
  name = "pavucontrol-float",
  match = { class = "^(pavucontrol)$" },
  opacity = "0.80 0.70",
  float = true,
})

hl.window_rule({
  name = "blueman-manager-float",
  match = { class = "^(blueman-manager)$" },
  opacity = "0.80 0.70",
  float = true,
})

hl.window_rule({
  name = "nm-applet-float",
  match = { class = "^(nm-applet)$" },
  opacity = "0.80 0.70",
  float = true,
})

hl.window_rule({
  name = "spotify-opacity",
  match = { class = "^(Spotify)$" },
  opacity = "0.70 0.70",
})

hl.window_rule({
  name = "spotify-free-opacity",
  match = { initial_title = "^(Spotify Free)$" },
  opacity = "0.70 0.70",
})

hl.window_rule({
  name = "nm-connection-editor-float",
  match = { class = "^(nm-connection-editor)$" },
  opacity = "0.80 0.70",
  float = true,
})

hl.window_rule({
  name = "polkit-kde-float",
  match = { class = "^(org.kde.polkit-kde-authentication-agent-1)$" },
  opacity = "0.80 0.70",
  float = true,
})

hl.window_rule({
  name = "polkit-gnome-opacity",
  match = { class = "^(polkit-gnome-authentication-agent-1)$" },
  opacity = "0.80 0.70",
})

hl.window_rule({
  name = "portal-gtk-opacity",
  match = { class = "^(org.freedesktop.impl.portal.desktop.gtk)$" },
  opacity = "0.80 0.70",
})

hl.window_rule({
  name = "portal-hyprland-opacity",
  match = { class = "^(org.freedesktop.impl.portal.desktop.hyprland)$" },
  opacity = "0.80 0.70",
})

hl.window_rule({
  name = "suppress-maximize-events",
  match = { class = ".*" }, -- You'll probably like this.
  suppress_event = "maximize",
})

----------------------
---- LAYER RULES -----
----------------------
hl.layer_rule({
  name = "tofi-ignore-alpha",
  match = { namespace = "tofi" },
  ignore_alpha = 0,
})

hl.layer_rule({
  name = "dunst-blur",
  match = { namespace = "dunst" },
  ignore_alpha = 0,
  blur = true,
})

-- QuickShell Layer Rules
-- require("hyprland-layer-config") -- if you port this file over too, convert it to lua and require() it here
-----------------------------------
---- PANELS, DOCK (NEW BINDS) ----
-----------------------------------
-- Notification / control center panel (same swaync panel as the waybar icon)
hl.bind(mainMod .. " + N",         hl.dsp.exec_cmd("swaync-client -t"))  -- toggle panel
hl.bind(mainMod .. " + SHIFT + N", hl.dsp.exec_cmd("swaync-client -d"))  -- toggle do-not-disturb
hl.bind(mainMod .. " + CTRL + N",  hl.dsp.exec_cmd("swaync-client -C"))  -- clear all notifications

-- Dock (nwg-dock-hyprland) show/hide
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd("pkill -SIGRTMIN+1 -f nwg-dock-hyprland"))