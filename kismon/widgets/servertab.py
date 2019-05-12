from gi.repository import Gtk

from kismon.windows import ChannelWindow, DatasourcesWindow


class ServerTab:
    def __init__(self, server_id, map, config, client_threads, client_start, client_stop, set_server_tab_label,
                 on_server_remove_clicked, window, logger):
        self.server_id = server_id
        self.config = config
        self.map = map
        self.client_threads = client_threads
        self.client_start = client_start
        self.client_stop = client_stop
        self.set_server_tab_label = set_server_tab_label
        self.on_server_remove_clicked = on_server_remove_clicked
        self.window = window
        self.logger = logger
        self.sources = {}
        self.sources_tables = {}
        self.sources_table_sources = {}
        right_table = Gtk.VBox()
        right_scrolled = Gtk.ScrolledWindow()
        right_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        right_scrolled.add(right_table)
        right_scrolled.set_size_request(160, -1)
        right_scrolled.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)
        self.widget = right_scrolled

        row = 0

        connection_expander = Gtk.Expander()
        connection_expander.set_label("Control")
        connection_expander.set_expanded(True)
        right_table.pack_start(connection_expander, False, False, 0)
        connection_table = self.init_control_table()
        connection_expander.add(connection_table)
        row += 1

        info_expander = Gtk.Expander()
        info_expander.set_label("Infos")
        info_expander.set_expanded(True)
        right_table.pack_start(info_expander, False, False, 0)
        row += 1
        self.info_expander = info_expander
        self.init_info_table(server_id)

        gps_expander = Gtk.Expander()
        gps_expander.set_label("GPS Data")
        gps_expander.set_expanded(True)
        right_table.pack_start(gps_expander, False, False, 0)
        row += 1
        self.gps_expander = gps_expander
        self.init_gps_table()

        if self.map is not None:
            track_expander = Gtk.Expander()
            track_expander.set_label("GPS Track")
            table = self.init_track_table()
            track_expander.add(table)
            right_table.pack_start(track_expander, False, False, 0)
            row += 1

        sources_expander = Gtk.Expander()
        sources_expander.set_label("Sources")
        sources_expander.set_expanded(True)
        right_table.pack_start(sources_expander, False, False, 0)
        row += 1
        self.sources_expander = sources_expander
        self.sources_table = None
        self.sources_table_source = {}
        right_scrolled.show_all()

        self.datasources_dialog_answer = None

    def init_control_table(self):
        table = Gtk.Table(n_rows=4, n_columns=2)
        row = 0

        label = Gtk.Label(label='Active:')
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        table.attach(label, 0, 1, row, row + 1)

        checkbutton = Gtk.CheckButton()
        checkbutton.connect("toggled", self.on_server_switch)
        table.attach(checkbutton, 1, 2, row, row + 1)
        self.server_switch = checkbutton
        row += 1

        label = Gtk.Label(label='Configure:')
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        table.attach(label, 0, 1, row, row + 1)

        box = Gtk.Box()
        menubutton = Gtk.MenuButton()
        menubutton.connect("clicked", self.on_control_menubutton_clicked)
        box.pack_start(menubutton, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        popover = Gtk.Popover()
        popover.add(vbox)
        self.control_popover = popover
        menubutton.set_popover(popover)
        image = Gtk.Image.new_from_icon_name('document-properties', Gtk.IconSize.MENU)
        menubutton.add(image)

        edit_button = Gtk.ModelButton(label='Edit connection')
        edit_button.connect('clicked', self.on_server_edit)
        vbox.pack_start(edit_button, False, True, 5)

        channel_button = Gtk.ModelButton(label='Change channel')
        channel_button.connect('clicked', self.on_channel_config)
        vbox.pack_start(channel_button, False, True, 5)

        datasource_button = Gtk.ModelButton(label='Add data source')
        datasource_button.connect('clicked', self.on_manage_datasources)
        vbox.pack_start(datasource_button, False, True, 5)

        label = Gtk.Label(label='-')
        vbox.pack_start(label, False, True, 5)

        remove_button = Gtk.ModelButton(label='Remove server')
        remove_button.connect('clicked', self.on_server_remove_clicked, self.server_id)
        vbox.pack_start(remove_button, False, True, 5)

        table.attach(box, 1, 2, row, row + 1)
        row += 1

        return table

    def on_control_menubutton_clicked(self, button):
        self.control_popover.set_relative_to(button)
        self.control_popover.show_all()

    def init_info_table(self, server_id):
        self.info_table = {}
        table = Gtk.Table(n_rows=4, n_columns=2)
        row = 0

        label = Gtk.Label(label="URI: ")
        label.set_property("xalign", 0)
        label.set_property("yalign", 0)
        table.attach(label, 0, 1, row, row + 1)
        row += 1
        value_label = Gtk.Label(label="%s" % self.config['servers'][server_id]['uri'])
        value_label.set_property("xalign", 0)
        value_label.set_property("yalign", 0)
        table.attach(value_label, 0, 2, row, row + 1)
        self.info_table['uri'] = value_label
        row += 1

        networks_label = Gtk.Label(label="Devices: ")
        networks_label.set_property("xalign", 0)
        networks_label.set_property("yalign", 0)
        table.attach(networks_label, 0, 1, row, row + 1)

        networks_value_label = Gtk.Label()
        label.set_property("xalign", 0)
        label.set_property("yalign", 0)
        table.attach(networks_value_label, 1, 2, row, row + 1)
        self.info_table['devices'] = networks_value_label
        row += 1

        table.show_all()
        self.info_expander.add(table)

    def update_info_table(self, devices):
        self.info_table['devices'].set_text("%s" % devices)

    def init_gps_table(self):
        table = Gtk.Table(n_rows=3, n_columns=2)

        fix_label = Gtk.Label(label="Fix: ")
        fix_label.set_property("xalign", 0)
        fix_label.set_property("yalign", 0)
        table.attach(fix_label, 0, 1, 0, 1)

        fix_value_label = Gtk.Label()
        fix_value_label.set_property("xalign", 0)
        fix_value_label.set_property("yalign", 0)
        table.attach(fix_value_label, 1, 2, 0, 1)
        self.gps_table_fix = fix_value_label

        lat_label = Gtk.Label(label="Latitude: ")
        lat_label.set_property("xalign", 0)
        lat_label.set_property("yalign", 0)
        table.attach(lat_label, 0, 1, 1, 2)

        lat_value_label = Gtk.Label()
        lat_value_label.set_property("xalign", 0)
        lat_value_label.set_property("yalign", 0)
        table.attach(lat_value_label, 1, 2, 1, 2)
        self.gps_table_lat = lat_value_label

        lon_label = Gtk.Label(label="Longitude: ")
        lon_label.set_property("xalign", 0)
        lon_label.set_property("yalign", 0)
        table.attach(lon_label, 0, 1, 2, 3)

        lon_value_label = Gtk.Label()
        lon_value_label.set_property("xalign", 0)
        lon_value_label.set_property("yalign", 0)
        table.attach(lon_value_label, 1, 2, 2, 3)
        self.gps_table_lon = lon_value_label

        table.show_all()
        self.gps_table = table
        self.gps_expander.add(self.gps_table)

    def update_gps_table(self, lat, lon, fix):
        if fix == -1:
            fix_text = "None"
        elif fix == 2:
            fix_text = "2D"
        elif fix == 3:
            fix_text = "3D"
        else:
            fix_text = fix

        self.gps_table_fix.set_text("%s" % fix_text)
        self.gps_table_lat.set_text("%s" % lat)
        self.gps_table_lon.set_text("%s" % lon)

    def init_track_table(self):
        table = Gtk.Table(n_rows=2, n_columns=2)
        row = 0

        label = Gtk.Label(label='Show:')
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        table.attach(label, 0, 1, row, row + 1)

        checkbutton = Gtk.CheckButton()
        checkbutton.connect("toggled", self.on_track_switch)
        checkbutton.set_active(True)
        table.attach(checkbutton, 1, 2, row, row + 1)
        row += 1

        label = Gtk.Label(label='Reset:')
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        table.attach(label, 0, 1, row, row + 1)

        box = Gtk.Box()
        image = Gtk.Image.new_from_icon_name('gtk-cancel', size=Gtk.IconSize.MENU)
        button = Gtk.Button(image=image)
        button.connect('clicked', self.on_track_reset_clicked)
        box.pack_start(button, False, False, 0)
        table.attach(box, 1, 2, row, row + 1)
        row += 1

        label = Gtk.Label(label='Jump to:')
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        table.attach(label, 0, 1, row, row + 1)

        box = Gtk.Box()
        image = Gtk.Image.new_from_icon_name('gtk-home', size=Gtk.IconSize.MENU)
        button = Gtk.Button(image=image)
        button.connect('clicked', self.on_server_locate_clicked)
        box.pack_start(button, False, False, 0)
        table.attach(box, 1, 2, row, row + 1)
        row += 1

        table.show_all()
        return table

    def init_sources_table(self, sources):
        self.sources_table_sources = {}
        if self.sources_table is not None:
            self.sources_expander.remove(self.sources_table)

        table = Gtk.Table(n_rows=(len(sources) * 5) + 1, n_columns=2)
        for uuid in sources:
            self.init_sources_table_source(sources[uuid], table)

        table.show_all()
        self.sources_table = table
        self.sources_expander.add(table)

    def init_sources_table_source(self, source, table):
        self.sources_table_sources[source["uuid"]] = {}

        rows = []
        if len(self.sources_table_sources) != 1:
            rows.append((None, None))
        rows.append((source['name'], ''))
        rows.append(("Type", source["type"]))
        rows.append(("Packets", source["packets"]))

        row = len(self.sources_table_sources) * 5
        for title, value in rows:
            if title is not None:
                label = Gtk.Label(label="%s: " % title)
                label.set_property("xalign", 0)
                label.set_property("yalign", 0)
                table.attach(label, 0, 1, row, row + 1)

            label = Gtk.Label(label=value)
            label.set_property("xalign", 0)
            label.set_property("yalign", 0)
            table.attach(label, 1, 2, row, row + 1)
            self.sources_table_sources[source["uuid"]][title] = label
            row += 1
        return row

    def update_sources_table(self, sources):
        self.sources = sources
        for source in sources:
            if source not in self.sources_table_sources:
                self.init_sources_table(sources)
                break

        for uuid in sources:
            source = sources[uuid]
            sources_table_source = self.sources_table_sources[uuid]
            sources_table_source["Type"].set_text("%s" % source["type"])
            sources_table_source["Packets"].set_text("%s" % source["packets"])

    def set_active(self, active=True):
        self.server_switch.set_active(active)

    def on_server_edit(self, widget):
        self.control_popover.hide()
        dialog = Gtk.Dialog(title="Edit server")
        dialog.set_transient_for(self.window)
        box = dialog.get_content_area()
        row = 0
        table = Gtk.Table(n_rows=4, n_columns=2)

        label = Gtk.Label("URI: ")
        table.attach(label, 0, 1, row, row + 1)

        uri_entry = Gtk.Entry()
        uri_entry.set_text(self.config["servers"][self.server_id]['uri'])
        table.attach(uri_entry, 1, 2, row, row + 1)
        row += 1

        label = Gtk.Label()
        label.set_markup("<b>Username</b>: ")

        table.attach(label, 0, 1, row, row + 1)

        username_entry = Gtk.Entry()
        username_entry.set_placeholder_text("Default: kismet")
        current_username = self.config["servers"][self.server_id]['username']
        if current_username == "":
            current_username = "kismet"
        username_entry.set_text(current_username)
        table.attach(username_entry, 1, 2, row, row + 1)

        row += 1

        label = Gtk.Label()
        label.set_markup("<b>Password*</b>: ")

        table.attach(label, 0, 1, row, row + 1)

        password_entry = Gtk.Entry()
        password_entry.set_visibility(False)
        password_entry.set_placeholder_text("Password")
        password_entry.set_text(self.config["servers"][self.server_id]['password'])
        table.attach(password_entry, 1, 2, row, row + 1)
        row += 1

        label = Gtk.Label()
        label.set_markup("<b>* Required, see kismet_httpd.conf</b>")
        table.attach(label, 0, 2, row, row + 1)
        row += 1

        box.add(table)
        dialog.add_button('gtk-cancel', 0)
        dialog.add_button('gtk-connect', 1)

        dialog.show_all()
        response = dialog.run()
        if response < 1:
            self.logger.info("dialog canceled (%s)" % response)
            dialog.destroy()
            return False
        uri = uri_entry.get_text()
        username = username_entry.get_text()
        password = password_entry.get_text()
        dialog.destroy()

        self.config['servers'][self.server_id]['uri'] = uri
        self.config['servers'][self.server_id]['username'] = username
        self.config['servers'][self.server_id]['password'] = password
        self.client_threads[self.server_id].client.credentials = (username, password)
        self.set_active(False)
        self.set_active(True)
        self.info_table['uri'].set_text(uri)
        self.update_info_table(devices=0)
        self.update_gps_table(lat='', lon='', fix='')
        self.sources = {}
        return True

    def on_server_connect(self, widget, force_connect=False):
        if self.client_threads[self.server_id].is_running and not force_connect:
            return
        self.client_start(self.server_id)

    def on_server_disconnect(self, widget):
        if not self.client_threads[self.server_id].is_running:
            return
        self.client_stop(self.server_id)

    def on_server_switch(self, widget):
        if widget.get_active():
            self.on_server_connect(None)
            state = 'connected'
            icon = 'gtk-connect'
            widget.set_tooltip_text('Disconnect')
        else:
            self.on_server_disconnect(None)
            state = 'disconnected'
            icon = 'gtk-disconnect'
            widget.set_tooltip_text('Connect')

        self.set_server_tab_label(self.server_id, icon, "Server %s %s" % ((self.server_id + 1), state))

    def on_server_locate_clicked(self, widget):
        if not self.map:
            return

        if self.server_id == 0:
            self.map.start_moving()
        else:
            server = "server%s" % (self.server_id + 1)
            self.map.locate_marker(server)

    def on_track_switch(self, widget):
        if widget.get_active():
            self.map.show_track(self.server_id)
        else:
            self.map.hide_track(self.server_id)

    def on_track_reset_clicked(self, widget):
        self.map.remove_track(self.server_id)

    def on_channel_config(self, widget):
        self.control_popover.hide()

        if not self.try_authentification():
            return
        ChannelWindow(sources=self.sources,
                      client_thread=self.client_threads[self.server_id],
                      parent=self.window)

    def on_manage_datasources(self, widget=None):
        self.try_authentification()
        DatasourcesWindow(client_thread=self.client_threads[self.server_id],
                          parent=self.window)

    def try_authentification(self):
        client = self.client_threads[self.server_id].client
        while not client.authenticate():
            response = self.on_server_edit(widget=None)
            if not response:  # if the dialog was canceled
                return False
            self.logger.info("next try")
        return True
