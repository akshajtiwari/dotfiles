#!/usr/bin/env python3
"""Wi-Fi and Bluetooth overlay panels (GTK4 + layer-shell).

Usage: quickpanel.py wifi|bluetooth     (running it again toggles the panel off)
"""
import os
import sys
import subprocess
import threading

LIB = "/usr/lib/libgtk4-layer-shell.so"
if LIB not in os.environ.get("LD_PRELOAD", "") and os.path.exists(LIB):
    env = dict(os.environ, LD_PRELOAD=(LIB + ":" + os.environ.get("LD_PRELOAD", "")).rstrip(":"))
    os.execve(sys.executable, [sys.executable] + sys.argv, env)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Gtk4LayerShell as LS  # noqa: E402

CONFIG = os.path.expanduser("~/.config")
COLORS = os.path.join(CONFIG, "swaync/colors/colors.css")  # follows the light/dark theme symlink

# Nerd Font (material design) glyphs
G = dict(
    wifi_off="\U000f05aa", lock="\U000f033e", refresh="\U000f0450", close="\U000f0156",
    check="\U000f012c", cog="\U000f0493", ethernet="\U000f0200", trash="\U000f01b4",
    bt="\U000f00af", bt_on="\U000f00b1", bt_off="\U000f00b2", battery="\U000f0079",
)
WIFI_SIGNAL = ["\U000f091f", "\U000f0922", "\U000f0925", "\U000f0928"]
BT_ICONS = {
    "audio-headphones": "\U000f02cb", "audio-headset": "\U000f02ce", "audio-card": "\U000f04c3",
    "input-keyboard": "\U000f030c", "input-mouse": "\U000f037d", "input-gaming": "\U000f0297",
    "phone": "\U000f011c", "computer": "\U000f0322", "video-display": "\U000f0379",
    "printer": "\U000f042a",
}

CSS = """
window.qp { background: transparent; }
.panel {
  background: @center-notification-bg;
  color: @text;
  border-radius: 18px;
  border: 1px solid alpha(@text, 0.14);
  padding: 14px;
  font-family: "CaskaydiaCove Nerd Font Propo";
  font-weight: 700;
}
.panel label { color: @text; }
.title { font-size: 1.25rem; font-weight: 800; }
.dim, .panel label.dim { color: @text-alt; font-size: 0.82rem; }
.section { color: @text-alt; font-size: 0.78rem; font-weight: 800; margin: 10px 4px 2px 4px; }
.glyph { font-size: 1.35rem; min-width: 2rem; }
.iconbtn {
  all: unset;
  padding: 6px 9px; border-radius: 10px; background: alpha(@text, 0.08);
  font-size: 1.05rem; transition: 150ms;
}
.iconbtn:hover { background: alpha(@text, 0.18); }
.iconbtn.danger:hover { background: alpha(#e0556a, 0.35); }
.rowbtn {
  all: unset;
  padding: 9px 10px; border-radius: 14px; transition: 150ms;
}
.rowbtn:hover { background: alpha(@text, 0.09); }
.rowbtn.active { background: alpha(@text, 0.14); }
.rowname { font-size: 0.98rem; font-weight: 800; }
.tag {
  font-size: 0.72rem; padding: 2px 8px; border-radius: 99px;
  background: alpha(@text, 0.14);
}
.tag.on { background: @text; }
.tag.on label, label.tag.on { color: @center-notification-bg; }
.drawer { padding: 4px 10px 10px 10px; }
.action {
  all: unset;
  padding: 8px 14px; border-radius: 12px; background: alpha(@text, 0.12);
  transition: 150ms; font-size: 0.9rem;
}
.action:hover { background: alpha(@text, 0.22); }
.action.primary { background: @text; }
.action.primary label { color: @center-notification-bg; }
.action.primary:hover { background: alpha(@text, 0.85); }
.action.danger:hover { background: alpha(#e0556a, 0.4); }
.panel entry {
  all: unset; padding: 8px 12px; border-radius: 12px;
  background: alpha(@text, 0.1); color: @text; min-height: 1.2rem;
  border: 1px solid alpha(@text, 0.12);
}
.panel entry:focus-within { border-color: alpha(@text, 0.5); }
.panel entry text { color: @text; }
.error { color: #e0556a; font-size: 0.8rem; margin: 2px 4px; }
.banner {
  background: alpha(@text, 0.12); border-radius: 14px; padding: 10px 12px; margin: 8px 0 2px 0;
}
.empty { color: @text-alt; padding: 30px 0; }
.panel switch {
  all: unset; min-width: 46px; min-height: 26px; border-radius: 99px;
  background: alpha(@text, 0.2); transition: 150ms;
}
.panel switch:checked { background: @text; }
.panel switch slider {
  all: unset; min-width: 20px; min-height: 20px; margin: 3px; border-radius: 99px;
  background: @center-notification-bg; box-shadow: 0 1px 3px rgba(0,0,0,0.35);
}
.panel switch:not(:checked) slider { background: @text; }
.panel scrolledwindow undershoot, .panel scrolledwindow overshoot { all: unset; }
.panel scrollbar { all: unset; }
.panel scrollbar slider { all: unset; min-width: 4px; border-radius: 99px; background: alpha(@text, 0.25); margin: 2px; }
"""

COMPAT = """
@define-color center-notification-bg rgba(214,216,223,1.0);
@define-color text #343B58;
@define-color text-alt #707280;
"""


def run_async(cmd, callback, stdin=None):
    """Run cmd in a thread; callback(rc, stdout, stderr) is invoked on the main loop."""
    def work():
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, input=stdin, timeout=90)
            res = (p.returncode, p.stdout, p.stderr)
        except Exception as e:  # noqa: BLE001
            res = (1, "", str(e))
        GLib.idle_add(lambda: (callback(*res), False)[1])
    threading.Thread(target=work, daemon=True).start()


def nm_split(line):
    """Split an `nmcli -t` line on unescaped colons."""
    out, cur, esc = [], "", False
    for ch in line:
        if esc:
            cur += ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def label(text, css=None, xalign=0.0, ellipsize=True):
    l = Gtk.Label(label=text, xalign=xalign)
    if css:
        for c in css.split():
            l.add_css_class(c)
    if ellipsize:
        l.set_ellipsize(3)  # Pango.EllipsizeMode.END
    return l


def clear(box):
    child = box.get_first_child()
    while child:
        nxt = child.get_next_sibling()
        box.remove(child)
        child = nxt


def action_button(text, cb, css=""):
    b = Gtk.Button()
    b.set_child(label(text))
    b.add_css_class("action")
    for c in css.split():
        b.add_css_class(c)
    b.connect("clicked", lambda *_: cb())
    return b


def icon_button(glyph, cb, css="", tip=None):
    b = Gtk.Button()
    b.set_child(label(glyph))
    b.add_css_class("iconbtn")
    for c in css.split():
        b.add_css_class(c)
    if tip:
        b.set_tooltip_text(tip)
    b.connect("clicked", lambda *_: cb())
    return b


class Panel:
    """Shared window chrome: layer-shell overlay, header, scrolling list, footer."""

    title = ""
    width = 380

    def __init__(self, app):
        self.app = app
        self.win = Gtk.Window(application=app)
        self.win.add_css_class("qp")
        self.win.set_decorated(False)
        self.win.set_default_size(self.width, -1)
        LS.init_for_window(self.win)
        LS.set_layer(self.win, LS.Layer.OVERLAY)
        LS.set_namespace(self.win, "quickpanel")
        LS.set_anchor(self.win, LS.Edge.TOP, True)
        LS.set_anchor(self.win, LS.Edge.RIGHT, True)
        LS.set_margin(self.win, LS.Edge.TOP, 8)
        LS.set_margin(self.win, LS.Edge.RIGHT, 10)
        LS.set_keyboard_mode(self.win, LS.KeyboardMode.ON_DEMAND)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.win.add_controller(keys)
        self._armed = False
        self.win.connect("notify::is-active", self._on_active)
        self.win.connect("close-request", self._on_close)
        GLib.timeout_add(500, self._arm)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        root.add_css_class("panel")
        root.set_size_request(self.width, -1)

        self.header = Gtk.Box(spacing=10)
        self.header_title = label(self.title, "title")
        self.header_title.set_hexpand(True)
        self.header.append(self.header_title)
        self.header_extra = Gtk.Box(spacing=8)
        self.header.append(self.header_extra)
        self.switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self._switch_guard = False
        self.switch.connect("notify::active", self._on_switch)
        self.header.append(self.switch)
        root.append(self.header)

        self.status = label("", "dim")
        self.status.set_margin_start(2)
        root.append(self.status)

        self.banner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(self.banner_box)

        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_child(self.list)
        self.scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_propagate_natural_height(True)
        self.scroller.set_max_content_height(430)
        self.scroller.set_min_content_height(120)
        root.append(self.scroller)

        self.footer = Gtk.Box(spacing=8)
        self.footer.set_margin_top(8)
        root.append(self.footer)

        self.win.set_child(root)

    # -- window lifecycle ---------------------------------------------------
    def _arm(self):
        self._armed = True
        return False

    def _on_key(self, _c, keyval, *_):
        if keyval == Gdk.KEY_Escape:
            self.win.close()
            return True
        return False

    def _on_active(self, *_):
        if self._armed and not self.win.is_active():
            GLib.timeout_add(120, self._close_if_inactive)

    def _close_if_inactive(self):
        if not self.win.is_active() and not self.keep_open():
            self.win.close()
        return False

    def keep_open(self):
        return False

    def _on_close(self, *_):
        self.on_close()
        return False

    def on_close(self):
        pass

    def present(self):
        self.win.present()

    # -- hooks ----------------------------------------------------------------
    def set_switch(self, state, sensitive=True):
        self._switch_guard = True
        self.switch.set_active(state)
        self.switch.set_sensitive(sensitive)
        self._switch_guard = False

    def _on_switch(self, sw, _p):
        if not self._switch_guard:
            self.on_switch(sw.get_active())

    def on_switch(self, state):
        pass

    def show_empty(self, glyph, text):
        clear(self.list)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("empty")
        g = label(glyph, "glyph", 0.5)
        g.set_markup(f'<span size="xx-large">{glyph}</span>')
        box.append(g)
        box.append(label(text, "dim", 0.5, ellipsize=False))
        self.list.append(box)

    def keep_scroll(self, fn):
        adj = self.scroller.get_vadjustment()
        v = adj.get_value()
        fn()
        GLib.idle_add(lambda: (adj.set_value(v), False)[1])


# ============================================================================
# Wi-Fi
# ============================================================================
class WifiPanel(Panel):
    title = "Wi-Fi"

    def __init__(self, app):
        super().__init__(app)
        self.dev = None
        self.radio = True
        self.networks = []
        self.saved = set()
        self.expanded = None
        self.busy = None       # ssid currently connecting
        self.errors = {}       # ssid -> message
        self.entry = None
        self.scanning = False
        self.dirty = False
        self.header_extra.append(icon_button(G["refresh"], lambda: self.refresh(rescan=True), tip="Rescan"))
        self.footer.append(action_button(f'{G["cog"]}  Network settings', self.open_settings))
        self.refresh(rescan=False)
        GLib.timeout_add_seconds(7, self._tick)

    def _tick(self):
        if self.win.get_visible():
            self.refresh(rescan=True)
            return True
        return False

    def open_settings(self):
        subprocess.Popen(["nm-connection-editor"], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.win.close()

    def keep_open(self):
        return self.busy is not None

    # -- data -------------------------------------------------------------------
    def refresh(self, rescan):
        if self.scanning and rescan:
            return
        self.scanning = rescan or self.scanning
        script = [
            ("radio", ["nmcli", "radio", "wifi"]),
            ("dev", ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"]),
            ("saved", ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]),
            ("list", ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list",
                      "--rescan", "yes" if rescan else "no"]),
        ]
        results = {}

        def step(i=0):
            if i == len(script):
                self.scanning = False
                self.apply(results)
                return
            key, cmd = script[i]
            run_async(cmd, lambda rc, out, err: (results.__setitem__(key, out if rc == 0 else ""), step(i + 1)))
        step()

    def apply(self, r):
        self.radio = r["radio"].strip() == "enabled"
        wifi_dev, eth = None, None
        for line in r["dev"].splitlines():
            f = nm_split(line)
            if len(f) < 4:
                continue
            if f[1] == "wifi" and not wifi_dev:
                wifi_dev = f
            if f[1] == "ethernet" and f[2] == "connected" and not eth:
                eth = f
        self.dev = wifi_dev[0] if wifi_dev else None
        self.saved = {nm_split(l)[0] for l in r["saved"].splitlines()
                      if len(nm_split(l)) > 1 and nm_split(l)[1] == "802-11-wireless"}
        nets = {}
        for line in r["list"].splitlines():
            f = nm_split(line)
            if len(f) < 4 or not f[1]:
                continue
            n = dict(active=f[0] == "*", ssid=f[1], signal=int(f[2] or 0), sec=f[3] not in ("", "--"))
            old = nets.get(n["ssid"])
            if not old or n["active"] or (not old["active"] and n["signal"] > old["signal"]):
                nets[n["ssid"]] = n
        self.networks = sorted(nets.values(), key=lambda n: (not n["active"], n["ssid"] not in self.saved, -n["signal"]))

        parts = []
        if wifi_dev and wifi_dev[2] == "connected":
            parts.append(f"Connected to {wifi_dev[3]}")
        if eth:
            parts.append(f"{G['ethernet']} Ethernet")
        self.status.set_text("  ·  ".join(parts) if parts else ("Not connected" if self.radio else ""))
        self.set_switch(self.radio, self.dev is not None)
        self.render()

    # -- ui -----------------------------------------------------------------------
    def render(self):
        if self.entry is not None and (self.entry.get_text() or self.busy):
            return  # don't blow away a half-typed password
        self.entry = None
        if self.dev is None:
            return self.show_empty(G["wifi_off"], "No Wi-Fi adapter found")
        if not self.radio:
            return self.show_empty(G["wifi_off"], "Wi-Fi is turned off")
        if not self.networks:
            return self.show_empty(WIFI_SIGNAL[0], "Searching for networks…")
        self.keep_scroll(self._build_list)

    def _build_list(self):
        clear(self.list)
        for n in self.networks:
            self.list.append(self.make_row(n))

    def make_row(self, n):
        ssid = n["ssid"]
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        btn = Gtk.Button()
        btn.add_css_class("rowbtn")
        if self.expanded == ssid:
            btn.add_css_class("active")
        row = Gtk.Box(spacing=10)
        row.append(label(WIFI_SIGNAL[min(3, n["signal"] // 25)], "glyph"))
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.set_hexpand(True)
        col.append(label(ssid, "rowname"))
        if self.busy == ssid:
            sub = "Connecting…"
        elif n["active"]:
            sub = "Connected"
        elif ssid in self.saved:
            sub = "Saved"
        else:
            sub = "Secured" if n["sec"] else "Open"
        col.append(label(f'{sub}  ·  {n["signal"]}%', "dim"))
        row.append(col)
        if n["sec"]:
            row.append(label(G["lock"], "dim"))
        if n["active"]:
            t = label(G["check"], "tag on")
            row.append(t)
        btn.set_child(row)
        btn.connect("clicked", lambda *_: self.on_row(n))
        outer.append(btn)

        drawer = self.make_drawer(n)
        if drawer:
            outer.append(drawer)
        return outer

    def make_drawer(self, n):
        ssid = n["ssid"]
        err = self.errors.get(ssid)
        if self.expanded != ssid and not err:
            return None
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("drawer")
        if err:
            box.append(label(err, "error", ellipsize=False))
        if self.expanded != ssid:
            return box
        if n["active"]:
            acts = Gtk.Box(spacing=8)
            acts.append(action_button("Disconnect", lambda: self.disconnect(n)))
            acts.append(action_button("Forget", lambda: self.forget(n), "danger"))
            box.append(acts)
        elif n["sec"] and ssid not in self.saved:
            e = Gtk.Entry()
            e.set_visibility(False)
            e.set_placeholder_text("Password")
            e.set_hexpand(True)
            e.set_sensitive(self.busy is None)
            e.connect("activate", lambda *_: self.connect(n, e.get_text()))
            self.entry = e
            line = Gtk.Box(spacing=8)
            line.append(e)
            line.append(action_button("Connect", lambda: self.connect(n, e.get_text()), "primary"))
            box.append(line)
            GLib.idle_add(lambda: (e.grab_focus(), False)[1])
        elif ssid in self.saved:
            acts = Gtk.Box(spacing=8)
            acts.append(action_button("Connect", lambda: self.connect(n, None), "primary"))
            acts.append(action_button("Forget", lambda: self.forget(n), "danger"))
            box.append(acts)
        return box

    # -- actions ----------------------------------------------------------------
    def on_row(self, n):
        ssid = n["ssid"]
        if self.busy:
            return
        self.errors.pop(ssid, None)
        if self.expanded == ssid:
            self.expanded = None
        elif not n["active"] and not n["sec"] and ssid not in self.saved:
            self.expanded = ssid
            return self.connect(n, None)  # open network: just join it
        elif not n["active"] and ssid in self.saved:
            return self.connect(n, None)  # known network: one click
        else:
            self.expanded = ssid
        self.entry = None
        self.render()

    def on_switch(self, state):
        run_async(["nmcli", "radio", "wifi", "on" if state else "off"],
                  lambda *_: GLib.timeout_add(600, lambda: (self.refresh(rescan=state), False)[1]))

    def connect(self, n, password):
        ssid = n["ssid"]
        if password == "":
            return
        self.busy, self.entry = ssid, None
        self.errors.pop(ssid, None)
        self.render()
        was_saved = ssid in self.saved
        if was_saved:
            cmd = ["nmcli", "connection", "up", "id", ssid]
        else:
            cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", self.dev]
            if password:
                cmd += ["password", password]

        def done(rc, out, err):
            self.busy = None
            if rc == 0:
                self.expanded = None
                self.errors.pop(ssid, None)
            else:
                msg = (err or out).strip().splitlines()
                msg = msg[-1] if msg else "Could not connect"
                if "Secrets were required" in err or "password" in err.lower():
                    msg = "Wrong password or the network rejected it."
                self.errors[ssid] = msg
                if not was_saved:  # don't leave a broken profile behind
                    run_async(["nmcli", "connection", "delete", "id", ssid], lambda *_: None)
            self.refresh(rescan=False)
        run_async(cmd, done)

    def disconnect(self, n):
        self.expanded = None
        run_async(["nmcli", "device", "disconnect", self.dev], lambda *_: self.refresh(rescan=False))

    def forget(self, n):
        self.expanded = None
        run_async(["nmcli", "connection", "delete", "id", n["ssid"]], lambda *_: self.refresh(rescan=False))


# ============================================================================
# Bluetooth
# ============================================================================
BLUEZ = "org.bluez"
AGENT_PATH = "/dev/quickpanel/agent"
AGENT_XML = """<node><interface name="org.bluez.Agent1">
<method name="Release"/>
<method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
<method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
<method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
<method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/></method>
<method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
<method name="RequestAuthorization"><arg type="o" direction="in"/></method>
<method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
<method name="Cancel"/></interface></node>"""
NOISY = {"RSSI", "ManufacturerData", "ServiceData", "TxPower", "AdvertisingData", "AdvertisingFlags"}


class BluetoothPanel(Panel):
    title = "Bluetooth"

    def __init__(self, app):
        super().__init__(app)
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM)
        self.adapter = None
        self.devices = {}
        self.busy = {}         # path -> status text
        self.errors = {}
        self.discovering = False
        self.prompt_inv = None
        self._debounce = 0
        self.header_extra.append(icon_button(G["refresh"], self.restart_scan, tip="Scan again"))
        self.footer.append(action_button(f'{G["cog"]}  All settings', self.open_settings))
        for iface, sig in (("org.freedesktop.DBus.Properties", "PropertiesChanged"),
                           ("org.freedesktop.DBus.ObjectManager", "InterfacesAdded"),
                           ("org.freedesktop.DBus.ObjectManager", "InterfacesRemoved")):
            self.bus.signal_subscribe(BLUEZ, iface, sig, None, None, Gio.DBusSignalFlags.NONE, self._on_signal)
        self.agent_reg = False
        self.read_state()
        self.register_agent()
        self.start_scan()

    def open_settings(self):
        subprocess.Popen(["blueman-manager"], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.win.close()

    def keep_open(self):
        return self.prompt_inv is not None or bool(self.busy)

    def on_close(self):
        if self.discovering and self.adapter:
            try:
                self.bus.call_sync(BLUEZ, self.adapter, "org.bluez.Adapter1", "StopDiscovery",
                                   None, None, 0, 1000, None)
            except GLib.Error:
                pass

    # -- D-Bus helpers --------------------------------------------------------
    def call(self, path, iface, method, params=None, cb=None, timeout=30000, reply=None):
        def done(conn, res):
            try:
                out = conn.call_finish(res)
                err = None
            except GLib.Error as e:
                out, err = None, e.message
            if cb:
                cb(out, err)
        self.bus.call(BLUEZ, path, iface, method, params, reply, Gio.DBusCallFlags.NONE, timeout, None, done)

    def set_prop(self, path, iface, prop, variant, cb=None):
        self.call(path, "org.freedesktop.DBus.Properties", "Set",
                  GLib.Variant("(ssv)", (iface, prop, variant)), cb)

    def read_state(self):
        try:
            r = self.bus.call_sync(BLUEZ, "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects",
                                   None, GLib.VariantType("(a{oa{sa{sv}}})"), 0, 3000, None)
            objs = r.unpack()[0]
        except GLib.Error:
            objs = None
        self.adapter, self.devices = None, {}
        if objs is not None:
            for path, ifaces in objs.items():
                if "org.bluez.Adapter1" in ifaces and not self.adapter:
                    self.adapter = path
                    self.adapter_props = ifaces["org.bluez.Adapter1"]
                if "org.bluez.Device1" in ifaces:
                    d = dict(ifaces["org.bluez.Device1"])
                    d["Battery"] = ifaces.get("org.bluez.Battery1", {}).get("Percentage")
                    self.devices[path] = d
        self.render()

    def _on_signal(self, _c, _s, path, iface, sig, params, *_):
        if sig == "PropertiesChanged":
            changed = params.unpack()[1]
            if set(changed) <= NOISY:
                return
        self.schedule_refresh()

    def schedule_refresh(self):
        if self._debounce:
            return

        def go():
            self._debounce = 0
            self.read_state()
            return False
        self._debounce = GLib.timeout_add(250, go)

    # -- scanning ------------------------------------------------------------
    def start_scan(self):
        if not self.adapter or not self.adapter_props.get("Powered"):
            return
        self.call(self.adapter, "org.bluez.Adapter1", "StartDiscovery",
                  cb=lambda o, e: setattr(self, "discovering", e is None or "InProgress" in (e or "")))

    def restart_scan(self):
        if not self.adapter:
            return
        self.call(self.adapter, "org.bluez.Adapter1", "StopDiscovery",
                  cb=lambda *_: GLib.timeout_add(300, lambda: (self.start_scan(), False)[1]))

    # -- pairing agent ----------------------------------------------------------
    def register_agent(self):
        try:
            info = Gio.DBusNodeInfo.new_for_xml(AGENT_XML)
            self.bus.register_object(AGENT_PATH, info.interfaces[0], self._agent_call, None, None)
        except GLib.Error:
            return
        self.call("/org/bluez", "org.bluez.AgentManager1", "RegisterAgent",
                  GLib.Variant("(os)", (AGENT_PATH, "KeyboardDisplay")),
                  cb=lambda o, e: self.call("/org/bluez", "org.bluez.AgentManager1", "RequestDefaultAgent",
                                            GLib.Variant("(o)", (AGENT_PATH,))))

    def _name_of(self, path):
        d = self.devices.get(path, {})
        return d.get("Alias") or d.get("Name") or d.get("Address", "device")

    def _agent_call(self, _c, _sender, _path, _iface, method, params, inv):
        args = params.unpack()
        dev = args[0] if args else ""
        name = self._name_of(dev)
        if method in ("Release", "Cancel"):
            self.clear_prompt()
            inv.return_value(None)
        elif method in ("RequestAuthorization", "AuthorizeService"):
            inv.return_value(None)
        elif method == "DisplayPinCode":
            self.show_prompt(f"Enter this PIN on {name}", args[1])
            inv.return_value(None)
        elif method == "DisplayPasskey":
            self.show_prompt(f"Type this code on {name}", f"{args[1]:06d}")
            inv.return_value(None)
        elif method == "RequestConfirmation":
            self.show_prompt(f"Does {name} show this code?", f"{args[1]:06d}", inv=inv, kind="confirm")
        elif method == "RequestPinCode":
            self.show_prompt(f"PIN for {name}", None, inv=inv, kind="pin")
        elif method == "RequestPasskey":
            self.show_prompt(f"Passkey for {name}", None, inv=inv, kind="passkey")
        else:
            inv.return_dbus_error("org.bluez.Error.Rejected", "unsupported")

    def clear_prompt(self):
        if self.prompt_inv is not None:
            try:
                self.prompt_inv.return_dbus_error("org.bluez.Error.Canceled", "cancelled")
            except Exception:  # noqa: BLE001
                pass
        self.prompt_inv = None
        clear(self.banner_box)

    def show_prompt(self, text, code, inv=None, kind=None):
        clear(self.banner_box)
        self.prompt_inv = inv
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.add_css_class("banner")
        box.append(label(text, "rowname", ellipsize=False))
        if code:
            big = Gtk.Label()
            big.set_markup(f'<span size="xx-large" letter_spacing="4000">{GLib.markup_escape_text(str(code))}</span>')
            box.append(big)

        def answer(ok, value=None):
            i, self.prompt_inv = self.prompt_inv, None
            clear(self.banner_box)
            if i is None:
                return
            if not ok:
                i.return_dbus_error("org.bluez.Error.Rejected", "rejected")
            elif kind == "pin":
                i.return_value(GLib.Variant("(s)", (value,)))
            elif kind == "passkey":
                i.return_value(GLib.Variant("(u)", (int(value or 0),)))
            else:
                i.return_value(None)

        if kind == "confirm":
            row = Gtk.Box(spacing=8)
            row.append(action_button("Confirm", lambda: answer(True), "primary"))
            row.append(action_button("Cancel", lambda: answer(False)))
            box.append(row)
        elif kind in ("pin", "passkey"):
            e = Gtk.Entry()
            e.set_placeholder_text("0000" if kind == "pin" else "000000")
            row = Gtk.Box(spacing=8)
            e.set_hexpand(True)
            e.connect("activate", lambda *_: answer(True, e.get_text()))
            row.append(e)
            row.append(action_button("OK", lambda: answer(True, e.get_text()), "primary"))
            row.append(action_button("Cancel", lambda: answer(False)))
            box.append(row)
            GLib.idle_add(lambda: (e.grab_focus(), False)[1])
        self.banner_box.append(box)

    # -- ui --------------------------------------------------------------------
    def on_switch(self, state):
        if not self.adapter:
            return
        if state:
            subprocess.run(["rfkill", "unblock", "bluetooth"])
        self.set_prop(self.adapter, "org.bluez.Adapter1", "Powered", GLib.Variant("b", state),
                      lambda *_: GLib.timeout_add(400, lambda: (self.read_state(), self.start_scan() if state else None, False)[2]))

    def render(self):
        if not self.adapter:
            self.set_switch(False, False)
            self.status.set_text("")
            return self.show_empty(G["bt_off"], "No Bluetooth adapter available")
        powered = bool(self.adapter_props.get("Powered"))
        self.set_switch(powered)
        conn = [d for d in self.devices.values() if d.get("Connected")]
        self.status.set_text(f"{len(conn)} connected" if conn else ("On" if powered else ""))
        if not powered:
            return self.show_empty(G["bt_off"], "Bluetooth is turned off")
        self.keep_scroll(self._build_list)

    def _build_list(self):
        clear(self.list)
        mine = [(p, d) for p, d in self.devices.items() if d.get("Paired")]
        new = [(p, d) for p, d in self.devices.items() if not d.get("Paired") and d.get("Name")]
        key = lambda pd: (not pd[1].get("Connected"), (pd[1].get("Alias") or "").lower())  # noqa: E731
        mine.sort(key=key)
        new.sort(key=lambda pd: -(pd[1].get("RSSI") or -200))
        if mine:
            self.list.append(label("MY DEVICES", "section"))
            for p, d in mine:
                self.list.append(self.make_row(p, d))
        self.list.append(label("AVAILABLE DEVICES" + ("  ·  searching…" if self.discovering else ""), "section"))
        if new:
            for p, d in new:
                self.list.append(self.make_row(p, d))
        else:
            self.list.append(label("Nothing new found yet. Put your device in pairing mode.", "dim", ellipsize=False))

    def make_row(self, path, d):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        head = Gtk.Box(spacing=4)
        btn = Gtk.Button()
        btn.set_hexpand(True)
        btn.add_css_class("rowbtn")
        row = Gtk.Box(spacing=10)
        row.append(label(BT_ICONS.get(d.get("Icon", ""), G["bt"]), "glyph"))
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.set_hexpand(True)
        col.append(label(d.get("Alias") or d.get("Name") or d.get("Address"), "rowname"))
        if path in self.busy:
            sub = self.busy[path]
        elif d.get("Connected"):
            sub = "Connected" + (f'  ·  {G["battery"]} {d["Battery"]}%' if d.get("Battery") is not None else "")
        elif d.get("Paired"):
            sub = "Paired"
        else:
            sub = "Click to pair"
        col.append(label(sub, "dim"))
        row.append(col)
        if d.get("Connected"):
            row.append(label(G["check"], "tag on"))
        btn.set_child(row)
        btn.connect("clicked", lambda *_: self.primary(path, d))
        head.append(btn)
        if d.get("Paired") and path not in self.busy:
            head.append(icon_button(G["trash"], lambda: self.forget(path), "danger", "Forget device"))
        outer.append(head)
        err = self.errors.get(path)
        if err:
            outer.append(label(err, "error", ellipsize=False))
        return outer

    # -- actions ----------------------------------------------------------------
    def primary(self, path, d):
        if path in self.busy:
            return
        self.errors.pop(path, None)

        def finish(out, err, what):
            self.busy.pop(path, None)
            if err:
                msg = err.split(":")[-1].strip() or "Failed"
                self.errors[path] = f"{what} failed: {msg}"
            self.read_state()

        def connect():
            self.busy[path] = "Connecting…"
            self.read_state()
            self.call(path, "org.bluez.Device1", "Connect", cb=lambda o, e: finish(o, e, "Connection"), timeout=40000)

        if d.get("Connected"):
            self.busy[path] = "Disconnecting…"
            self.read_state()
            self.call(path, "org.bluez.Device1", "Disconnect", cb=lambda o, e: finish(o, e, "Disconnect"))
        elif d.get("Paired"):
            connect()
        else:
            self.busy[path] = "Pairing…"
            self.read_state()

            def paired(o, e):
                if e and "AlreadyExists" not in e:
                    return finish(o, e, "Pairing")
                self.set_prop(path, "org.bluez.Device1", "Trusted", GLib.Variant("b", True))
                connect()
            self.call(path, "org.bluez.Device1", "Pair", cb=paired, timeout=75000)

    def forget(self, path):
        self.call(self.adapter, "org.bluez.Adapter1", "RemoveDevice", GLib.Variant("(o)", (path,)),
                  cb=lambda *_: self.read_state())


class App(Gtk.Application):
    def __init__(self, mode):
        super().__init__(application_id=f"dev.quickpanel.{mode}", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.mode = mode
        self.panel = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        css = ""
        try:
            with open(COLORS) as f:
                css = f.read()
        except OSError:
            css = COMPAT
        # aliases the stylesheet relies on, in case the theme file lacks them
        for name, fallback in (("center-notification-bg", "rgba(214,216,223,1)"), ("text", "#343B58"),
                               ("text-alt", "#707280")):
            if f"@define-color {name} " not in css:
                css += f"\n@define-color {name} {fallback};"
        prov = Gtk.CssProvider()
        prov.load_from_string(css + CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def do_activate(self):
        if self.panel is not None:       # second launch = toggle off
            self.panel.win.close()
            self.panel = None
            return
        cls = WifiPanel if self.mode == "wifi" else BluetoothPanel
        self.panel = cls(self)
        self.panel.win.connect("close-request", lambda *_: setattr(self, "panel", None))
        self.panel.present()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "wifi"
    if mode not in ("wifi", "bluetooth"):
        sys.exit("usage: quickpanel.py wifi|bluetooth")
    sys.exit(App(mode).run([sys.argv[0]]))
