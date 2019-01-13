from gi.repository import Gtk
from gi.repository import Gdk


class TemplateWindow:
    def __init__(self):
        self.gtkwin = Gtk.Window()
        self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
        self.gtkwin.connect("destroy", self.on_destroy)
        self.gtkwin.connect('key-release-event', self.on_key_release)
        self.is_fullscreen = False

    def fullscreen(self):
        if self.is_fullscreen is True:
            self.gtkwin.unfullscreen()
            self.is_fullscreen = False
        else:
            self.gtkwin.fullscreen()
            self.is_fullscreen = True

    def on_key_release(self, widget, event):
        keyval = event.keyval
        name = Gdk.keyval_name(keyval)
        if name == "F11":
            self.fullscreen()
        elif name in ('i', 'o') and self.map is not None:
            if name == "i":
                self.map.zoom_in()
            elif name == "o":
                self.map.zoom_out()
