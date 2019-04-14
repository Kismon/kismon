from gi.repository import Gtk


class ConfigWindow:
    def __init__(self, main_window):
        self.gtkwin = Gtk.Window()
        self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
        self.gtkwin.connect("destroy", self.on_destroy)
        self.gtkwin.set_size_request(640, 320)
        self.gtkwin.set_title("Kismon Preferences")
        self.main_window = main_window
        self.config = main_window.config
        self.map = main_window.map

        self.notebook = Gtk.Notebook()
        self.gtkwin.add(self.notebook)

        general_page = Gtk.Table(n_rows=2, n_columns=1)
        general_page.set_property('margin', 5)
        self.notebook.append_page(general_page)
        self.notebook.set_tab_label_text(general_page, "General")
        self.init_general_page(general_page)

        map_page = Gtk.Table(n_rows=2, n_columns=1)
        map_page.set_property('margin', 5)
        self.notebook.append_page(map_page)
        self.notebook.set_tab_label_text(map_page, "Map")

        if self.map is None:
            label = Gtk.Label(label="Map disabled")
            map_page.attach(label, 0, 1, 0, 1, yoptions=Gtk.AttachOptions.SHRINK)
        else:
            self.init_map_page(map_page)

        self.gtkwin.show_all()

    def init_general_page(self, page):
        frame = Gtk.Frame()
        frame.set_label("Log List")
        page.attach(frame, 0, 1, 0, 1, yoptions=Gtk.AttachOptions.SHRINK)
        vbox = Gtk.VBox()
        frame.add(vbox)
        hbox = Gtk.HBox()
        vbox.add(hbox)

        label = Gtk.Label(label="Max rows in the log list: ")
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)

        label.set_justify(Gtk.Justification.RIGHT)
        hbox.pack_start(label, False, False, 5)

        field = Gtk.SpinButton()
        field.set_numeric(True)
        field.set_max_length(5)
        field.set_increments(1, 100)
        field.set_range(-1, 99999)
        field.set_value(self.config["window"]["log_list_max"])
        field.connect("output", self.on_change_log_list_max)
        hbox.pack_start(field, False, False, 5)

        label = Gtk.Label(label="-1 = unlimited 0 = disable")
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        hbox.pack_start(label, False, False, 5)

        frame = Gtk.Frame()
        frame.set_label("Autosave")
        page.attach(frame, 0, 1, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)
        vbox = Gtk.VBox()
        frame.add(vbox)
        hbox = Gtk.HBox()
        vbox.add(hbox)
        label = Gtk.Label(label="Save the networks every (in minutes):")
        hbox.pack_start(label, False, False, 5)

        field = Gtk.SpinButton()
        field.set_numeric(True)
        field.set_max_length(5)
        field.set_increments(1, 100)
        field.set_range(0, 99999)
        field.set_value(self.config["networks"]["autosave"])
        field.connect("output", self.on_change_autosave)
        hbox.pack_start(field, False, False, 5)

        label = Gtk.Label(label="0 = disable")
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        hbox.pack_start(label, False, False, 5)

        frame = Gtk.Frame()
        frame.set_label("Tracks")
        page.attach(frame, 0, 1, 2, 3, yoptions=Gtk.AttachOptions.SHRINK)
        hbox = Gtk.HBox()
        frame.add(hbox)

        checkbox = Gtk.CheckButton.new_with_label("Store GPS Tracks")
        if 'tracks' in self.config and self.config['tracks']['store'] is True:
            checkbox.clicked()
        checkbox.connect("clicked", self.on_change_tracks_store)
        hbox.add(checkbox)

    def on_change_log_list_max(self, widget):
        if self.config["window"]["log_list_max"] == int(widget.get_value()):
            return
        self.config["window"]["log_list_max"] = int(widget.get_value())
        self.main_window.log_list.cleanup(0)

    def on_change_autosave(self, widget):
        if self.config["networks"]["autosave"] == int(widget.get_value()):
            return
        self.config["networks"]["autosave"] = int(widget.get_value())
        self.main_window.networks.set_autosave(self.config["networks"]["autosave"])

    def on_change_tracks_store(self, widget):
        self.config["tracks"]["store"] = widget.get_active()

    def init_map_page(self, map_page):
        position_frame = Gtk.Frame()
        position_frame.set_label("Position")
        map_page.attach(position_frame, 0, 1, 0, 1, yoptions=Gtk.AttachOptions.SHRINK)
        position_vbox = Gtk.VBox()
        position_frame.add(position_vbox)

        map_widget = Gtk.RadioButton(group=None, label='In main window (default)')
        if self.config["window"]["map_position"] == "widget":
            map_widget.clicked()
        map_widget.connect("clicked", self.main_window.on_map_widget)
        position_vbox.add(map_widget)

        map_window = Gtk.RadioButton(group=map_widget, label='In seperate window')
        if self.config["window"]["map_position"] == "window":
            map_window.clicked()
        map_window.connect("clicked", self.main_window.on_map_window)
        position_vbox.add(map_window)

        map_hide = Gtk.RadioButton(group=map_widget, label='Hide')
        if self.config["window"]["map_position"] == "hide":
            map_hide.clicked()
        map_hide.connect("clicked", self.main_window.on_map_hide)
        position_vbox.add(map_hide)

        source_frame = Gtk.Frame()
        source_frame.set_label("Source")
        source_vbox = Gtk.VBox()
        source_frame.add(source_vbox)
        map_page.attach(source_frame, 0, 1, 1, 2, yoptions=Gtk.AttachOptions.SHRINK)

        first = None
        for name, source in (("OpenStreetMap (default)", "openstreetmap"),
                             ("OpenCycleMap", "opencyclemap"),
                             ("Custom tile source", "custom")):
            map_source = Gtk.RadioButton(group=first, label=name)
            if first is None:
                first = map_source

            if self.config["map"]["source"] == source:
                map_source.clicked()
            map_source.connect("clicked", self.on_map_source, source)
            source_vbox.add(map_source)

        hbox = Gtk.HBox()
        source_vbox.add(hbox)

        label = Gtk.Label(label="     URL: ")
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        label.set_justify(Gtk.Justification.LEFT)
        hbox.pack_start(label, False, False, 5)

        entry = Gtk.Entry()
        entry.set_width_chars(50)
        entry.set_text(self.config["map"]["custom_source_url"])
        entry.connect("changed", self.on_change_map_source_custom_url)
        hbox.pack_start(entry, False, False, 5)

        hbox = Gtk.HBox()
        source_vbox.add(hbox)

        x = 1
        for name in ("     Zoom Levels: ", " - "):
            label = Gtk.Label(label=name)
            label.set_property("xalign", 0)
            label.set_property("yalign", 0.5)
            label.set_justify(Gtk.Justification.LEFT)
            hbox.pack_start(label, False, False, 5)

            field = Gtk.SpinButton()
            field.set_numeric(True)
            field.set_max_length(5)
            field.set_increments(1, 3)
            field.set_range(1, 18)
            if x == 1:
                name = "custom_source_min"
            else:
                name = "custom_source_max"
            field.set_value(self.config["map"][name])
            field.connect("output", self.on_change_map_source_custom_zoom, name)
            hbox.pack_start(field, False, False, 5)
            x += 1

        apply_button = Gtk.Button.new_with_mnemonic('_Apply')
        apply_button.connect("clicked", self.on_map_source, "custom")
        hbox.pack_start(apply_button, False, False, 5)

        perf_frame = Gtk.Frame()
        perf_frame.set_label("Performance")
        perf_vbox = Gtk.VBox()
        perf_frame.add(perf_vbox)
        map_page.attach(perf_frame, 0, 1, 4, 5, yoptions=Gtk.AttachOptions.SHRINK)

        perf_marker_positions = Gtk.CheckButton.new_with_label("Update marker positions")
        if self.config["map"]["update_marker_positions"] is True:
            perf_marker_positions.clicked()
        perf_marker_positions.connect("clicked", self.on_update_marker_positions)
        perf_vbox.add(perf_marker_positions)

    def on_destroy(self, window):
        self.gtkwin = None

    def on_map_source(self, widget, source):
        if (type(widget) == Gtk.RadioButton and widget.get_active()) or type(widget) == Gtk.Button:
            self.map.change_source(source)
            if self.config["window"]["map_position"] == "widget":
                self.main_window.on_map_widget(None, True)
            elif self.config["window"]["map_position"] == "window":
                self.main_window.map_window.gtkwin.add(self.main_window.map.widget)
                self.main_window.map_window.gtkwin.show_all()

    def on_change_map_source_custom_url(self, widget):
        self.config["map"]["custom_source_url"] = widget.get_text()

    def on_change_map_source_custom_zoom(self, widget, name):
        self.config["map"][name] = int(widget.get_value())

    def on_update_marker_positions(self, widget):
        self.config["map"]["update_marker_positions"] = widget.get_active()
