from gi.repository import Gtk


class FilterTab:
    def __init__(self, config, networks, networks_queue_progress):
        self.config = config
        self.networks = networks
        self.networks_queue_progress = networks_queue_progress

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(10)
        self.grid.set_property('margin', 5)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.grid)
        self.widget = scrolled

        x = 0
        y = 0
        crypt_kv = (
            ('Open', 'none'),
            ('WEP', 'wep'),
            ('WPA', 'wpa'),
            ('WPA2', 'wpa2'),
            ('Other', 'other')
        )

        self.add_checkbox_list(config_key='filter_crypt', title='Encryption', kv=crypt_kv, x=x, y=y)

        type_kv = []
        for network_type in self.config['filter_type'].keys():
            type_kv.append((network_type.capitalize(), network_type))

        x += 1
        self.add_checkbox_list(config_key='filter_type', title='Network type', kv=type_kv, x=x, y=y)

        x += 1
        self.add_limiter_radiobuttons(main_x=x, main_y=y)

        x += 1
        self.add_regex_filters(main_x=x, main_y=y)

    def add_checkbox_list(self, config_key, title, kv, x, y):
        frame = Gtk.Frame()
        frame.set_label(title)
        self.grid.attach(frame, x, y, 1, 1)

        box = Gtk.Box()
        box.set_property('orientation', Gtk.Orientation.VERTICAL)
        frame.add(box)

        for key, value in kv:
            checkbox = Gtk.CheckButton.new_with_label(key)
            if self.config[config_key][value]:
                checkbox.set_active(True)
            checkbox.connect('toggled', self.on_network_filter, config_key, value)
            box.pack_start(checkbox, True, True, 0)

    def add_limiter_radiobuttons(self, main_x, main_y):
        frame = Gtk.Frame()
        frame.set_label("Limit networks")
        self.grid.attach(frame, main_x, main_y, 1, 1)

        limiter_grid = Gtk.Grid()
        limiter_grid.set_column_spacing(5)
        limiter_grid.set_row_spacing(5)
        limiter_grid.set_property('margin', 5)
        frame.add(limiter_grid)

        y = 1

        groups = {}
        for name, key in (("Network List", "network_list"), ("Map", "map"), ("Export", "export")):
            x = 0
            label = Gtk.Label(label=name)
            label.set_property("xalign", 0)
            limiter_grid.attach(label, x, y, 1, 1)

            for text, value in (('Disable', 'none'), ('Only current session', 'current'), ('All Networks', 'all')):
                x += 1
                if y == 1:
                    label = Gtk.Label(label=text)
                    label.set_property("xalign", 0)

                    limiter_grid.attach(label, x, 0, 1, 1)

                if key not in groups:
                    radiobutton = Gtk.RadioButton.new_from_widget(None)
                    groups[key] = radiobutton
                else:
                    radiobutton = Gtk.RadioButton.new_from_widget(groups[key])

                if self.config["filter_networks"][key] == value:
                    radiobutton.set_active(True)

                radiobutton.connect('toggled', self.on_toggle_limiter, key, value)
                limiter_grid.attach(radiobutton, x, y, 1, 1)

            y += 1
        y = 0

    def add_regex_filters(self, main_x, main_y):
        frame = Gtk.Frame()
        frame.set_label("Regular expression")
        self.grid.attach(frame, main_x, main_y, 1, 1)

        box = Gtk.Box()
        box.set_property('orientation', Gtk.Orientation.VERTICAL)
        box.set_property('margin', 5)
        frame.add(box)

        for key in ('ssid', 'bssid'):
            entry = Gtk.Entry()
            entry.set_width_chars(30)
            entry.set_text(self.config["filter_regexpr"][key])
            entry.connect('changed', self.on_regex_changed, key)
            label = Gtk.Label(label="%s:" % key.upper())
            hbox = Gtk.Box()
            hbox.pack_start(label, False, False, 0)
            hbox.pack_end(entry, False, False, 10)
            box.pack_start(hbox, False, False, 0)

    def apply(self):
        self.networks.apply_filters()
        self.networks_queue_progress()

    def on_network_filter(self, widget, config_key, filter_key):
        active = widget.get_active()
        self.config[config_key][filter_key] = active
        self.apply()

    def on_toggle_limiter(self, widget, key, value):
        if not widget.get_active():
            return
        self.config["filter_networks"][key] = value
        self.apply()

    def on_regex_changed(self, widget, key):
        text = widget.get_text()
        if text == self.config["filter_regexpr"][key]:
            return

        self.config["filter_regexpr"][key] = text
        self.apply()
