from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib


try:
	from kismon.client import decode_cryptset
	import kismon.utils as utils
except ImportError:
	from client import decode_cryptset
	import utils

class NetworkList:
	def __init__(self, networks, locate_network_on_map, on_signal_graph):
		self.network_lines = {}
		self.network_iter = {}
		self.network_selected = None
		self.locate_network_on_map = locate_network_on_map
		self.on_signal_graph = on_signal_graph
		self.networks = networks
		self.value_cache = {}
		for key in ('time', 'crypt', 'server', 'type', 'channel', 'signal', 'ssid'):
			self.value_cache[key] = {}
		
		self.networks.notify_add_list["network_list"] = self.add_network
		self.networks.notify_remove_list["network_list"] = self.remove_network
		self.networks.disable_refresh_functions.append(self.pause)
		self.networks.resume_refresh_functions.append(self.resume)
		
		self.treeview = Gtk.TreeView()
		self.treeview.connect("button-press-event", self.on_treeview_clicked)
		num=0
		self.columns=("BSSID", "Type", "SSID", "Ch", "Crypt",
			"First Seen", "Last Seen", "Latitude", "Longitude",
			"Signal dbm", "Comment", "Servers")
		for column in self.columns:
			renderer = Gtk.CellRendererText()
			if column == "Comment":
				renderer.set_property('editable', True)
				renderer.connect("editing-started", self.on_comment_editing_started)
			elif column == "Signal dbm":
				renderer = Gtk.CellRendererProgress()
			
			tvcolumn = Gtk.TreeViewColumn(column, renderer, text=num)
			self.treeview.append_column(tvcolumn)
			cell = Gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.set_sort_column_id(num)
			tvcolumn.set_clickable(True)
			tvcolumn.set_resizable(True)
			tvcolumn.connect("clicked", self.on_column_clicked)
			tvcolumn.num = num
			if column == "Signal dbm":
				tvcolumn.add_attribute(renderer, "value", 12)
			num+=1
		self.treeview.show()
		
		self.store = Gtk.ListStore(
			GObject.TYPE_STRING, #mac
			GObject.TYPE_STRING, #type
			GObject.TYPE_STRING, #ssid
			GObject.TYPE_INT, #channel
			GObject.TYPE_STRING, #cryptset
			GObject.TYPE_STRING, #firsttime
			GObject.TYPE_STRING, #lasttime
			GObject.TYPE_FLOAT, #lat
			GObject.TYPE_FLOAT, #lon
			GObject.TYPE_INT, #signal dbm
			GObject.TYPE_STRING, #comment
			GObject.TYPE_STRING, #servers
			GObject.TYPE_INT, #signal dbm + 100 (progressbar)
			)
		self.treeview.set_model(self.store)
		
		scrolled = Gtk.ScrolledWindow()
		scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		scrolled.add(self.treeview)
		
		frame = Gtk.Frame()
		frame.set_label("Networks")
		frame.add(scrolled)
		
		self.widget = frame
		
		self.store.set_sort_column_id(6, Gtk.SortType.DESCENDING)
		
		network_popup = Gtk.Menu()
		locate_item = Gtk.MenuItem.new_with_label('Copy field')
		network_popup.append(locate_item)
		locate_item.connect("activate", self.on_copy_field)
		locate_item = Gtk.MenuItem.new_with_label('Copy network')
		network_popup.append(locate_item)
		locate_item.connect("activate", self.on_copy_network)
		
		locate_item = Gtk.MenuItem.new_with_label('Locate on map')
		network_popup.append(locate_item)
		locate_item.connect("activate", self.on_locate_marker)
		
		signal_item = Gtk.MenuItem.new_with_label('Signal graph')
		network_popup.append(signal_item)
		signal_item.connect("activate", self.on_signal_graph)
		
		network_popup.show_all()
		self.network_popup = network_popup
		
		self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
	
	def on_column_clicked(self, widget):
		self.treeview.set_search_column(widget.num)
	
	def on_comment_editing_started(self, widget, editable, path):
		editable.connect("editing-done", self.on_comment_editing_done)
	
	def on_comment_editing_done(self, widget):
		network = self.networks.get_network(self.network_selected)
		network['comment'] = widget.get_text()
		self.add_network(self.network_selected)
	
	def prepare_network_servers(self, value):
		if len(value) == 0 or value is None:
			servers = None
		else:
			servers = []
			for server in value:
				if server.endswith(':2501'): # remove the default port
					server = server.rsplit(':', 1)[0]
				servers.append(server)
			servers_str = ", ".join(sorted(servers))
			
			try:
				servers = self.value_cache['server'][servers_str]
			except KeyError:
				servers = GObject.Value(GObject.TYPE_STRING, servers_str)
				self.value_cache['server'][servers_str] = servers
		return servers
		
	def prepare_network_time(self, value):
		try:
			result = self.value_cache['time'][value]
		except KeyError:
			result = GObject.Value(GObject.TYPE_STRING, utils.format_timestamp(value))
			self.value_cache['time'][value] = result
		return result
		
	def prepare_network_crypt(self, value):
		try:
			crypt = self.value_cache['crypt'][value]
		except KeyError:
			crypt = GObject.Value(GObject.TYPE_STRING, decode_cryptset(value, True))
			self.value_cache['crypt'][value] = crypt
		return crypt
		
	def prepare_network_channel(self, value):
		try:
			channel = self.value_cache['channel'][value]
		except KeyError:
			channel = GObject.Value(GObject.TYPE_INT, value)
			self.value_cache['channel'][value] = channel
		return channel
		
	def prepare_network_type(self, value):
		try:
			network_type = self.value_cache['type'][value]
		except KeyError:
			network_type = GObject.Value(GObject.TYPE_STRING, value)
			self.value_cache['type'][value] = network_type
		return network_type
		
	def prepare_network_signal(self, value):
		try:
			return self.value_cache['signal'][value]
		except KeyError:
			pass
		
		""" Wifi cards report different ranges for the signal, some use
		-1xx to 0 and others 0 to 100. The CellRendererProgress needs a
		percentage value between 0 and 100, so we convert the value if
		necessary.
		"""
		if -100 <= value <= 0:
			signal_strength = value + 100
		elif value < -100:
			signal_strength = 0
		elif 1 <= value <= 100:
			signal_strength = value
		else:
			signal_strength = 0
		
		signal = GObject.Value(GObject.TYPE_INT, value)
		signal_strength = GObject.Value(GObject.TYPE_INT, signal_strength)
		self.value_cache['signal'][value] = (signal, signal_strength)
		
		return signal, signal_strength
		
	def prepare_network_ssid(self, value):
		if value == "":
			ssid_str = "<no ssid>"
		else:
			ssid_str = value
		
		try:
			ssid = self.value_cache['ssid'][ssid_str]
		except KeyError:
			ssid = GObject.Value(GObject.TYPE_STRING, ssid_str)
			self.value_cache['ssid'][ssid_str] = ssid
		return ssid
	
	@staticmethod
	def prepare_network_coordinate(value):
		if value == 0.0:
			return None
		else:
			return value
		
	def add_network(self, mac):
		network = self.networks.get_network(mac)
		
		""" The Gtk.ListStore will convert every Python-type value to its
		GObject equivalent. Most of the prepare_network_* functions cache
		and return the value as a GObject, this speed things up as we have
		a lot of duplicate values. Furthermore a None value is faster then
		an zero size string, so we replace it where possible.
		"""
		
		if "signal_dbm" not in network or len(network["signal_dbm"]) != 3:
			signal = 0
		else:
			signal = network["signal_dbm"]["last"]
		signal, signal_strength = self.prepare_network_signal(signal)
		
		if network['comment'] == '':
			comment = None
		else:
			comment = network['comment']
		
		line = [mac,
				self.prepare_network_type(network["type"]),
				self.prepare_network_ssid(network["ssid"]),
				self.prepare_network_channel(network["channel"]),
				self.prepare_network_crypt(network["cryptset"]),
				self.prepare_network_time(network["firsttime"]),
				self.prepare_network_time(network["lasttime"]),
				self.prepare_network_coordinate(network["lat"]),
				self.prepare_network_coordinate(network["lon"]),
				signal,
				comment,
				self.prepare_network_servers(network["servers"]),
				signal_strength
				]
		try:
			old_line = self.network_lines[mac]
		except:
			old_line = None
		self.network_lines[mac] = line
		
		if mac in self.network_iter:
			network_iter = self.network_iter[mac]
			num = 0
			for value in line:
				if old_line is not None and old_line.pop(0) == value:
					num += 1
					continue
				self.store.set_value(network_iter, num, value)
				num += 1
		else:
			self.network_iter[mac] = self.store.append(line)
			
			adj = self.treeview.get_vadjustment()
			self.scroll_value = int(adj.get_value())
			if self.scroll_value == 0:
				GLib.idle_add(self.treeview.scroll_to_point, -1, 0)
		
	def remove_network(self, mac):
		try:
			network_iter = self.network_iter[mac]
		except KeyError:
			return
		
		self.store.remove(network_iter)
		del(self.network_iter[mac])
		
	def pause(self):
		self.treeview.freeze_child_notify()
		self.treeview.set_model(None)
		
	def resume(self):
		self.treeview.set_model(self.store)
		self.treeview.thaw_child_notify()
		
	def on_treeview_clicked(self, treeview, event):
		x = int(event.x)
		y = int(event.y)
		pthinfo = treeview.get_path_at_pos(x, y)
		if pthinfo is None:
			return
		
		path, col, cellx, celly = pthinfo
		treeview.grab_focus()
		treeview.set_cursor(path, col, 0)
		network_iter = self.store.get_iter(path)
		mac = self.store.get_value(network_iter, 0)
		self.network_selected = mac
		self.column_selected = self.columns.index(col.get_title())
		
		if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS: # double click
			self.on_locate_marker(None)
		elif event.button == 3: # right click
			self.network_popup.popup(None, None, None, 0, event.button, event.time, )
		
	def on_locate_marker(self, widget):
		if self.locate_network_on_map is not None:
			self.locate_network_on_map(self.network_selected)
		
	def on_copy_field(self, widget):
		selected_text = self.get_value_from_cell(self.network_selected, self.column_selected)
		self.set_clipboard(selected_text)
		
	def on_copy_network(self, widget):
		text = []
		num = 0
		for column in self.columns:
			value = self.get_value_from_cell(self.network_selected, num)
			text.append("%s: %s" % (column, value))
			num += 1
		self.set_clipboard('\n'.join(text))
		
	def set_clipboard(self, text):
		self.clipboard.set_text("%s" % text, -1)
		self.clipboard.store()

	def get_value_from_cell(self, mac, column):
		value = self.network_lines[mac][column]
		try:
			value = value.get_value()
		except AttributeError:
			pass
		return value
