from .template import TemplateWindow


class MapWindow(TemplateWindow):
    def __init__(self, map):
        TemplateWindow.__init__(self)
        self.gtkwin.set_title("Map")
        self.gtkwin.show()
        self.gtkwin.set_size_request(320, 240)
        self.gtkwin.resize(640, 480)
        self.map = map
        self.gtkwin.add(self.map.widget)

    def on_destroy(self, window):
        self.remove_map()
        self.gtkwin = None

    def remove_map(self):
        if self.gtkwin is not None:
            self.gtkwin.remove(self.map.widget)

    def hide(self):
        self.gtkwin.hide()
