from gi.repository import Gtk

try:
	from kismon.windows import ChannelWindow
except ImportError:
	from windows import ChannelWindow

class ServerTab():
	def __init__(self, server_id, map, config, client_threads, client_start, client_stop, set_server_tab_label, on_server_remove_clicked):
		self.server_id = server_id
		self.config = config
		self.map = map
		self.client_threads = client_threads
		self.client_start = client_start
		self.client_stop = client_stop
		self.set_server_tab_label = set_server_tab_label
		self.on_server_remove_clicked = on_server_remove_clicked
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
		connection_table = self.init_control_table(server_id)
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
		self.init_gps_table(server_id)
		
		if self.map != None:
			track_expander = Gtk.Expander()
			track_expander.set_label("GPS Track")
			table = self.init_track_table(server_id)
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
		
	def init_control_table(self, server_id):
		table = Gtk.Table(n_rows=4, n_columns=2)
		row = 0
		
		label = Gtk.Label(label='Active:')
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, row, row+1)
		
		checkbutton = Gtk.CheckButton()
		checkbutton.connect("toggled", self.on_server_switch)
		table.attach(checkbutton, 1, 2, row, row+1)
		self.server_switch = checkbutton
		row += 1
		
		box = Gtk.Box()
		label = Gtk.Label(label='Edit:')
		label.set_alignment(xalign=0, yalign=0.5)
		box.pack_start(label, True, True, 0)
		table.attach(box, 0, 1, row, row+1)
		
		box = Gtk.Box()
		image = Gtk.Image.new_from_icon_name(Gtk.STOCK_EDIT, size=Gtk.IconSize.MENU)
		button = Gtk.Button(image=image)
		button.connect("clicked", self.on_server_edit)
		button.set_tooltip_text('Edit connection')
		box.pack_start(button, False, False, 0)
		table.attach(box, 1, 2, row, row+1)
		row += 1
		
		label = Gtk.Label(label='Remove:')
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, row, row+1)
		
		box = Gtk.Box()
		image = Gtk.Image.new_from_icon_name(Gtk.STOCK_REMOVE, size=Gtk.IconSize.MENU)
		button = Gtk.Button(image=image)
		button.set_tooltip_text('Remove server')
		button.connect("clicked", self.on_server_remove_clicked, self.server_id)
		box.pack_start(button, False, False, 0)
		table.attach(box, 1, 2, row, row+1)
		row += 1
		
		return table
		
	def init_info_table(self, server_id):
		self.info_table = {}
		table = Gtk.Table(n_rows=4, n_columns=2)
		row = 0
		
		server_host, server_port = self.config['kismet']['servers'][server_id].split(':')
		label = Gtk.Label(label="Host: ")
		label.set_alignment(xalign=0, yalign=0)
		table.attach(label, 0, 1, row, row+1)
		value_label = Gtk.Label(label="%s" % server_host)
		value_label.set_alignment(xalign=0, yalign=0)
		table.attach(value_label, 1, 2, row, row+1)
		self.info_table['host'] = value_label
		row += 1
		
		label = Gtk.Label(label="Port: ")
		label.set_alignment(xalign=0, yalign=0)
		table.attach(label, 0, 1, row, row+1)
		value_label = Gtk.Label(label="%s" % server_port)
		value_label.set_alignment(xalign=0, yalign=0)
		table.attach(value_label, 1, 2, row, row+1)
		self.info_table['port'] = value_label
		row += 1
		
		networks_label = Gtk.Label(label="Networks: ")
		networks_label.set_alignment(xalign=0, yalign=0)
		table.attach(networks_label, 0, 1, row, row+1)
		
		networks_value_label = Gtk.Label()
		networks_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(networks_value_label, 1, 2, row, row+1)
		self.info_table['networks'] = networks_value_label
		row += 1
		
		packets_label = Gtk.Label(label="Packets: ")
		packets_label.set_alignment(xalign=0, yalign=0)
		table.attach(packets_label, 0, 1, row, row+1)
		
		packets_value_label = Gtk.Label()
		packets_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(packets_value_label, 1, 2, row, row+1)
		self.info_table['packets'] = packets_value_label
		row += 1
		
		table.show_all()
		self.info_expander.add(table)
		
	def update_info_table(self, data):
		self.info_table['networks'].set_text("%s" % data["networks"])
		self.info_table['packets'].set_text("%s" % data["packets"])
	
	def init_gps_table(self, server_id):
		table = Gtk.Table(n_rows=3, n_columns=2)
		
		fix_label = Gtk.Label(label="Fix: ")
		fix_label.set_alignment(xalign=0, yalign=0)
		table.attach(fix_label, 0, 1, 0, 1)
		
		fix_value_label = Gtk.Label()
		fix_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(fix_value_label, 1, 2, 0, 1)
		self.gps_table_fix = fix_value_label
		
		lat_label = Gtk.Label(label="Latitude: ")
		lat_label.set_alignment(xalign=0, yalign=0)
		table.attach(lat_label, 0, 1, 1, 2)
		
		lat_value_label = Gtk.Label()
		lat_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(lat_value_label, 1, 2, 1, 2)
		self.gps_table_lat = lat_value_label
		
		lon_label = Gtk.Label(label="Longitude: ")
		lon_label.set_alignment(xalign=0, yalign=0)
		table.attach(lon_label, 0, 1, 2, 3)
		
		lon_value_label = Gtk.Label()
		lon_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(lon_value_label, 1, 2, 2, 3)
		self.gps_table_lon = lon_value_label
		
		table.show_all()
		self.gps_table = table
		self.gps_expander.add(self.gps_table)
		
	def update_gps_table(self, data):
		if data["fix"] == -1:
			data["fix"] = "None"
		elif data["fix"] == 2:
			data["fix"] = "2D"
		elif data["fix"] == 3:
			data["fix"] = "3D"
		
		self.gps_table_fix.set_text("%s" % data["fix"])
		self.gps_table_lat.set_text("%s" % data["lat"])
		self.gps_table_lon.set_text("%s" % data["lon"])
		
	def init_track_table(self, server_id):
		table = Gtk.Table(n_rows=2, n_columns=2)
		row = 0
		
		label = Gtk.Label(label='Show:')
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, row, row+1)
		
		checkbutton = Gtk.CheckButton()
		checkbutton.connect("toggled", self.on_track_switch)
		checkbutton.set_active(True)
		table.attach(checkbutton, 1, 2, row, row+1)
		row += 1
		
		label = Gtk.Label(label='Reset:')
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, row, row+1)
		
		box = Gtk.Box()
		image = Gtk.Image.new_from_icon_name(Gtk.STOCK_CANCEL, size=Gtk.IconSize.MENU)
		button = Gtk.Button(image=image)
		button.connect('clicked', self.on_track_reset_clicked)
		box.pack_start(button, False, False, 0)
		table.attach(box, 1, 2, row, row+1)
		row += 1
		
		label = Gtk.Label(label='Jump to:')
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, row, row+1)
		
		box = Gtk.Box()
		image = Gtk.Image.new_from_icon_name(Gtk.STOCK_HOME, size=Gtk.IconSize.MENU)
		button = Gtk.Button(image=image)
		button.connect('clicked', self.on_server_locate_clicked)
		box.pack_start(button, False, False, 0)
		table.attach(box, 1, 2, row, row+1)
		row += 1
		
		table.show_all()
		return table
		
	def init_sources_table(self, sources):
		self.sources_table_sources = {}
		if self.sources_table is not None:
			self.sources_expander.remove(self.sources_tables)
			
		table = Gtk.Table(n_rows=(len(sources)*5)+1, n_columns=2)
		for uuid in sources:
			row = self.init_sources_table_source(sources[uuid], table)
		
		button = Gtk.Button(label='Channel Settings')
		button.connect('clicked', self.on_channel_config)
		table.attach(button, 0, 2, row, row+1)
		
		table.show_all()
		self.sources_table = table
		self.sources_expander.add(table)
	
	def init_sources_table_source(self, source, table):
		self.sources_table_sources[source["uuid"]] = {}
		
		rows = []
		if len(self.sources_table_sources) != 1:
			rows.append((None, None))
		rows.append((source["username"], ""))
		rows.append(("Type", source["type"]))
		rows.append(("Channel", source["channel"]))
		rows.append(("Packets", source["packets"]))
		
		row = len(self.sources_table_sources) * 5
		for title, value in rows:
			if title is not None:
				label = Gtk.Label(label="%s: "%title)
				label.set_alignment(xalign=0, yalign=0)
				table.attach(label, 0, 1, row, row+1)
			
			label = Gtk.Label(label=value)
			label.set_alignment(xalign=0, yalign=0)
			table.attach(label, 1, 2, row, row+1)
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
			sources_table_source["Channel"].set_text("%s" % source["channel"])
			sources_table_source["Packets"].set_text("%s" % source["packets"])
		
	def set_active(self):
		self.server_switch.set_active(True)
		
	def on_server_edit(self, widget):
		dialog = Gtk.Dialog("Connect")
		entry = Gtk.Entry()
		entry.set_text(self.config["kismet"]["servers"][self.server_id])
		dialog.add_action_widget(entry, 1)
		dialog.add_button(Gtk.STOCK_CONNECT, 1)
		dialog.show_all()
		dialog.run()
		server = entry.get_text()
		dialog.destroy()
		self.config["kismet"]["servers"][self.server_id] = server
		self.on_server_connect(None, True)
		host, port = server.split(':')
		self.info_table['host'].set_text(host)
		self.info_table['port'].set_text(port)
		
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
			icon = Gtk.STOCK_CONNECT
			widget.set_tooltip_text('Disconnect')
		else:
			self.on_server_disconnect(None)
			state = 'disconnected'
			icon = Gtk.STOCK_DISCONNECT
			widget.set_tooltip_text('Connect')
		
		self.set_server_tab_label(self.server_id, icon, "Server %s %s" %((self.server_id+1), state))
		
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
		win = ChannelWindow(self.sources, self.client_threads[self.server_id])
