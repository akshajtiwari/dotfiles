#!/usr/bin/env python3
"""Fullscreen wallpaper picker with thumbnails, styled like the tofi clipboard / app picker.

Type to filter · arrows to move · Enter to apply · Ctrl+R random · Esc to close
"""
import hashlib
import os
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

LIB = "/usr/lib/libgtk4-layer-shell.so"
if LIB not in os.environ.get("LD_PRELOAD", "") and os.path.exists(LIB):
    env = dict(os.environ, LD_PRELOAD=(LIB + ":" + os.environ.get("LD_PRELOAD", "")).rstrip(":"))
    os.execve(sys.executable, [sys.executable] + sys.argv, env)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf, Gtk4LayerShell as LS  # noqa: E402

WALL_DIR = os.path.expanduser("~/Pictures/Wallpapers/Walls-main/Wallpapers")
CACHE = os.path.expanduser("~/.cache/wallpaper-picker")
SETTER = os.path.expanduser("~/.config/scripts/set_wallpaper.sh")
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
COLS = 5
THUMB_W, THUMB_H = 270, 152

CSS = """
window.wp { background: rgba(17, 17, 27, 0.95); }
.wp-root { font-family: "JetBrainsMono Nerd Font", "CaskaydiaCove Nerd Font"; }
.prompt { font-size: 24px; color: #4e4e5f; }
entry.search {
  all: unset; font-size: 24px; color: #cdd6f4; min-height: 40px;
}
entry.search text { color: #cdd6f4; }
entry.search placeholder { color: #4e4e5f; }
.count { color: #4e4e5f; font-size: 14px; }
gridview { background: transparent; }
gridview > child {
  all: unset; margin: 6px; padding: 6px; border-radius: 14px;
  transition: 120ms;
}
gridview > child:hover { background: alpha(#83A4E7, 0.12); }
gridview > child:selected { background: alpha(#83A4E7, 0.30); }
.thumb { border-radius: 10px; background: alpha(#ffffff, 0.05); }
.name { color: #8a8aa0; font-size: 12px; margin-top: 4px; }
gridview > child:selected .name { color: #cdd6f4; }
scrolledwindow undershoot, scrolledwindow overshoot { all: unset; }
scrollbar { all: unset; }
scrollbar slider { all: unset; min-width: 5px; border-radius: 99px; background: alpha(#83A4E7, 0.35); margin: 2px; }
"""

pool = ThreadPoolExecutor(max_workers=4)


def thumb_path(src):
    st = os.stat(src)
    key = hashlib.md5(f"{src}:{st.st_mtime_ns}".encode()).hexdigest()
    return os.path.join(CACHE, key + ".jpg")


def make_thumb(src, dst):
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(src, THUMB_W * 2, THUMB_H * 2, True)
        pb.savev(dst, "jpeg", ["quality"], ["82"])
        return True
    except GLib.Error:
        pass
    # formats gdk-pixbuf can't read (webp here): fall back to ImageMagick
    try:
        r = subprocess.run(["magick", src + "[0]", "-thumbnail", f"{THUMB_W * 2}x{THUMB_H * 2}",
                            "-quality", "82", dst], capture_output=True, timeout=30)
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


class Picker(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.quickpanel.wallpicker", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        os.makedirs(CACHE, exist_ok=True)
        prov = Gtk.CssProvider()
        prov.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def do_activate(self):
        if self.win:
            self.win.close()
            self.win = None
            return
        files = []
        for root, _d, names in os.walk(WALL_DIR):
            for n in names:
                if n.lower().endswith(EXTS):
                    files.append(os.path.join(root, n))
        files.sort(key=lambda p: os.path.basename(p).lower())
        self.files = files

        w = self.win = Gtk.Window(application=self)
        w.add_css_class("wp")
        w.set_decorated(False)
        LS.init_for_window(w)
        LS.set_layer(w, LS.Layer.OVERLAY)
        LS.set_namespace(w, "tofi")  # reuses your existing tofi layer rules (ignore-alpha)
        for e in (LS.Edge.TOP, LS.Edge.BOTTOM, LS.Edge.LEFT, LS.Edge.RIGHT):
            LS.set_anchor(w, e, True)
        LS.set_exclusive_zone(w, -1)
        LS.set_keyboard_mode(w, LS.KeyboardMode.EXCLUSIVE)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root.add_css_class("wp-root")
        root.set_margin_top(60)
        root.set_margin_bottom(40)
        root.set_margin_start(150)
        root.set_margin_end(150)

        bar = Gtk.Box(spacing=8)
        bar.append(Gtk.Label(label=" wallpaper :", css_classes=["prompt"]))
        self.entry = Gtk.Entry(hexpand=True, css_classes=["search"])
        self.entry.set_placeholder_text("type to filter…")
        self.entry.connect("changed", self.on_changed)
        self.entry.connect("activate", lambda *_: self.apply_selected())
        bar.append(self.entry)
        self.count = Gtk.Label(css_classes=["count"])
        bar.append(self.count)
        root.append(bar)

        store = Gio.ListStore(item_type=Gtk.StringObject)
        for f in files:
            store.append(Gtk.StringObject.new(f))
        self.filter = Gtk.CustomFilter.new(self.match)
        self.filtered = Gtk.FilterListModel(model=store, filter=self.filter)
        self.sel = Gtk.SingleSelection(model=self.filtered)
        self.sel.set_autoselect(True)

        fac = Gtk.SignalListItemFactory()
        fac.connect("setup", self.on_setup)
        fac.connect("bind", self.on_bind)
        self.grid = Gtk.GridView(model=self.sel, factory=fac)
        self.grid.set_min_columns(COLS)
        self.grid.set_max_columns(COLS)
        self.grid.set_single_click_activate(True)
        self.grid.connect("activate", lambda _g, pos: self.apply_pos(pos))

        sc = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        sc.set_child(self.grid)
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        root.append(sc)
        w.set_child(root)

        keys = Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.on_key)
        w.add_controller(keys)
        w.connect("close-request", lambda *_: setattr(self, "win", None))

        self.update_count()
        w.present()
        self.entry.grab_focus()

    # -- filtering ----------------------------------------------------------------
    def match(self, item):
        q = self.entry.get_text().strip().lower() if hasattr(self, "entry") else ""
        if not q:
            return True
        name = os.path.basename(item.get_string()).lower()
        return all(t in name for t in q.split())

    def on_changed(self, *_):
        self.filter.changed(Gtk.FilterChange.DIFFERENT)
        self.update_count()
        if self.filtered.get_n_items():
            self.sel.set_selected(0)
            self.grid.scroll_to(0, Gtk.ListScrollFlags.NONE, None)

    def update_count(self):
        self.count.set_text(f"{self.filtered.get_n_items()} / {len(self.files)}")

    # -- cells --------------------------------------------------------------------
    def on_setup(self, _f, li):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        pic = Gtk.Picture(css_classes=["thumb"])
        pic.set_size_request(THUMB_W, THUMB_H)
        pic.set_content_fit(Gtk.ContentFit.COVER)
        pic.set_can_shrink(True)
        pic.set_overflow(Gtk.Overflow.HIDDEN)
        name = Gtk.Label(css_classes=["name"], xalign=0.5)
        name.set_ellipsize(3)
        name.set_max_width_chars(28)
        box.append(pic)
        box.append(name)
        li.set_child(box)

    def on_bind(self, _f, li):
        box = li.get_child()
        pic, name = box.get_first_child(), box.get_last_child()
        src = li.get_item().get_string()
        box.token = src
        name.set_text(os.path.splitext(os.path.basename(src))[0].replace("_", " "))
        pic.set_paintable(None)
        try:
            dst = thumb_path(src)
        except OSError:
            return
        if os.path.exists(dst):
            self.set_thumb(box, pic, src, dst)
            return

        def job():
            if getattr(box, "token", None) != src:   # recycled while queued
                return
            ok = make_thumb(src, dst)
            if ok:
                GLib.idle_add(lambda: (self.set_thumb(box, pic, src, dst), False)[1])
        pool.submit(job)

    @staticmethod
    def set_thumb(box, pic, src, dst):
        if getattr(box, "token", None) != src:
            return
        try:
            pic.set_paintable(Gdk.Texture.new_from_filename(dst))
        except GLib.Error:
            pass

    # -- actions --------------------------------------------------------------------
    def on_key(self, _c, keyval, _code, state):
        n = self.filtered.get_n_items()
        cur = self.sel.get_selected()
        move = {Gdk.KEY_Right: 1, Gdk.KEY_Left: -1, Gdk.KEY_Down: COLS, Gdk.KEY_Up: -COLS}.get(keyval)
        if keyval == Gdk.KEY_Escape:
            self.win.close()
            return True
        if keyval == Gdk.KEY_r and state & Gdk.ModifierType.CONTROL_MASK and n:
            self.apply_pos(random.randrange(n))
            return True
        if move is not None and n:
            if cur == Gtk.INVALID_LIST_POSITION:
                cur = 0
            new = max(0, min(n - 1, cur + move))
            self.sel.set_selected(new)
            self.grid.scroll_to(new, Gtk.ListScrollFlags.NONE, None)
            return True
        return False

    def apply_selected(self):
        pos = self.sel.get_selected()
        if pos != Gtk.INVALID_LIST_POSITION:
            self.apply_pos(pos)

    def apply_pos(self, pos):
        item = self.filtered.get_item(pos)
        if not item:
            return
        subprocess.Popen([SETTER, item.get_string()], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.win.close()


if __name__ == "__main__":
    sys.exit(Picker().run([sys.argv[0]]))
