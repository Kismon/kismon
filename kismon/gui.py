#!/usr/bin/env python
"""
Copyright (c) 2010, Patrick Salecker
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the distribution.
    * Neither the name of the author nor the names of its
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

import client

import time
import os
import sys

import gtk
import gobject

class KismonWindows:
	def __init__(self):
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.connect("destroy", self.on_destroy)
		self.gtkwin.connect('key-press-event', self.on_key_press)
		
		self.is_fullscreen = False
		
	def fullscreen(self):
		if self.is_fullscreen is True:
			self.gtkwin.unfullscreen()
			self.is_fullscreen = False
		else:
			self.gtkwin.fullscreen()
			self.is_fullscreen = True
		
		#print "Fullscreen = ",self.is_fullscreen
		
	def on_key_press(self, widget, event):
		keyval = event.keyval
		name = gtk.gdk.keyval_name(keyval)
		if name == "F11":
			self.fullscreen()
		elif event.state & gtk.gdk.CONTROL_MASK:
			if self.map_widget is not None:
				if name == "i":
					self.map_widget.map.zoom_in()
				elif name == "o":
					self.map_widget.map.zoom_out()

class MainWindow(KismonWindows):
	def __init__(self, config, client_start, client_stop, map_widget, networks_on_map, networks):
		KismonWindows.__init__(self)
		self.config = config
		self.config_window = None
		self.client_start = client_start
		self.client_stop = client_stop
		self.networks_on_map = networks_on_map
		self.networks = networks
		
		self.gtkwin.set_title("Kismon")
		self.gtkwin.connect("window-state-event", self.on_window_state)
		self.gtkwin.connect('configure-event', self.on_configure_event)
		
		self.gtkwin.set_default_size(self.config["window"]["width"],
			self.config["window"]["height"])
		
		if self.config["window"]["maximized"] is True:
			self.gtkwin.maximize()
		
		self.map_widget = map_widget
		if self.map_widget is not None:
			self.map = map_widget.map
		self.network_list_types = []
		self.network_lines = {}
		self.network_iter = {}
		self.network_list_network_selected = None
		self.signal_graphs = {}
		
		self.network_scrolled = gtk.ScrolledWindow()
		self.network_scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		
		self.notebook = gtk.Notebook()
		
		vbox = gtk.VBox()
		self.gtkwin.add(vbox)
		
		vbox.pack_start(self.init_menu(), expand=False, fill=False, padding=0)
		
		vpaned_main = gtk.VPaned()
		vpaned_main.set_position(320)
		vbox.add(vpaned_main)
		hbox = gtk.HBox()
		vpaned_main.add1(hbox)
		
		network_frame = gtk.Frame("Networks")
		network_frame.add(self.network_scrolled)
		hbox.pack_start(network_frame, expand=True, fill=True, padding=0)
		self.init_network_list()
		
		right_table = gtk.Table(rows=3, columns=1)
		right_scrolled = gtk.ScrolledWindow()
		right_scrolled.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		right_scrolled.add_with_viewport(right_table)
		right_scrolled.set_size_request(160, -1)
		right_scrolled.get_children()[0].set_shadow_type(gtk.SHADOW_NONE)
		hbox.pack_end(right_scrolled, expand=False, fill=False, padding=2)
		
		self.info_expander = gtk.Expander("Infos")
		self.info_expander.set_expanded(True)
		right_table.attach(self.info_expander, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		self.init_info_table()
		
		self.gps_expander = gtk.Expander("GPS Data")
		self.gps_expander.set_expanded(True)
		right_table.attach(self.gps_expander, 0, 1, 1, 2, yoptions=gtk.SHRINK)
		self.init_gps_table()
		
		self.sources_expander = gtk.Expander("Sources")
		self.sources_expander.set_expanded(True)
		right_table.attach(self.sources_expander, 0, 1, 2, 3, yoptions=gtk.SHRINK)
		self.sources_table = None
		self.sources_table_sources = {}
		
		battery_expander = gtk.Expander("Battery")
		right_table.attach(battery_expander, 0, 1, 3, 4, yoptions=gtk.SHRINK)
		self.battery_bar = gtk.ProgressBar()
		battery_expander.add(self.battery_bar)
		self.set_battery_bar(100.0)
		
		self.create_log_list()
		log_scrolled = gtk.ScrolledWindow()
		log_scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		log_scrolled.set_shadow_type(gtk.SHADOW_NONE)
		log_scrolled.add(self.log_list)
		
		vpaned_main.add2(self.notebook)
		self.notebook.append_page(log_scrolled)
		self.notebook.set_tab_label_text(log_scrolled, "Log")
		
		self.gtkwin.show_all()
		self.apply_config()
		
	def apply_config(self):
		if self.map_widget is None:
			return
		if self.config["window"]["map_position"] == "widget":
			self.on_map_widget(None, True)
		elif self.config["window"]["map_position"] == "window":
			self.on_map_window(None, True)
		else:
			self.on_map_hide(None)
	
	def on_destroy(self, widget):
		print "Window destroyed"
		self.gtkwin = None
		gtk.main_quit()
		
	def init_menu(self):
		menubar = gtk.MenuBar()
		
		file_menu = gtk.Menu()
		file_menuitem = gtk.MenuItem("File")
		file_menuitem.set_submenu(file_menu)
		
		connect = gtk.ImageMenuItem(gtk.STOCK_CONNECT)
		connect.connect("activate", self.on_client_connect)
		file_menu.append(connect)
		
		disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
		disconnect.connect("activate", self.on_client_disconnect)
		file_menu.append(disconnect)
		
		sep = gtk.SeparatorMenuItem()
		file_menu.append(sep)
		
		file_import = gtk.ImageMenuItem(gtk.STOCK_OPEN)
		file_import.set_label("Import Networks")
		file_import.connect("activate", self.on_file_import)
		file_menu.append(file_import)
		
		sep = gtk.SeparatorMenuItem()
		file_menu.append(sep)
		
		exit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		exit.connect("activate", self.on_destroy)
		file_menu.append(exit)
		
		menubar.append(file_menuitem)
		
		view_menu = gtk.Menu()
		view_menuitem = gtk.MenuItem("View")
		view_menuitem.set_submenu(view_menu)
		menubar.append(view_menuitem)
		
		network_menu = gtk.Menu()
		network_menuitem = gtk.MenuItem("Network List")
		network_menuitem.set_submenu(network_menu)
		view_menu.append(network_menuitem)
		
		show_infrastructure = gtk.CheckMenuItem('Show Infrastructure Networks')
		show_infrastructure.connect("activate", self.on_network_list_filter_type)
		show_infrastructure.set_active(True)
		network_menu.append(show_infrastructure)
		
		show_probes = gtk.CheckMenuItem('Show Probe Networks')
		show_probes.connect("activate", self.on_network_list_filter_type)
		network_menu.append(show_probes)
		
		show_adhoc = gtk.CheckMenuItem('Show Ad-Hoc Networks')
		show_adhoc.connect("activate", self.on_network_list_filter_type)
		network_menu.append(show_adhoc)
		
		show_data = gtk.CheckMenuItem('Show Data Networks')
		show_data.connect("activate", self.on_network_list_filter_type)
		network_menu.append(show_data)
		
		config_menuitem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		config_menuitem.connect("activate", self.on_config_window)
		view_menu.append(config_menuitem)
		
		help_menu = gtk.Menu()
		help_menuitem = gtk.MenuItem("Help")
		help_menuitem.set_submenu(help_menu)
		menubar.append(help_menuitem)
		
		about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		about.connect("activate", self.on_about_dialog)
		help_menu.append(about)
		
		return menubar
	
	def init_network_list(self):
		if len(self.network_scrolled.get_children()) > 0:
			self.network_scrolled.remove(self.network_list)
		
		self.network_list = gtk.TreeView()
		self.network_list.connect("button-press-event", self.on_network_list_network_popup)
		num=0
		columns=("BSSID", "Type", "SSID", "Ch", "Crypt",
			"First Seen", "Last Seen", "Latitude", "Longitude",
			"Signal dbm")
		for column in columns:
			tvcolumn = gtk.TreeViewColumn(column)
			self.network_list.append_column(tvcolumn)
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			#tvcolumn.set_sort_column_id(num)
			tvcolumn.set_clickable(True)
			tvcolumn.set_resizable(True)
			tvcolumn.connect("clicked", self.on_column_clicked)
			tvcolumn.num = num
			num+=1
		self.network_list.show()
		
		self.network_list_treestore = gtk.ListStore(
			gobject.TYPE_STRING, #mac
			gobject.TYPE_STRING, #type
			gobject.TYPE_STRING, #ssid
			gobject.TYPE_INT, #channel
			gobject.TYPE_STRING, #cryptset
			gobject.TYPE_STRING, #firsttime
			gobject.TYPE_STRING, #lasttime
			gobject.TYPE_FLOAT, #lat
			gobject.TYPE_FLOAT, #lon
			gobject.TYPE_INT, #signal dbm
			)
		self.network_list.set_model(self.network_list_treestore)
		self.network_scrolled.add(self.network_list)
		
		network_menu = gtk.Menu()
		locate_item = gtk.MenuItem('Locate on map')
		network_menu.append(locate_item)
		locate_item.connect("activate", self.on_map_locate_marker)
		
		signal_item = gtk.MenuItem('Signal graph')
		network_menu.append(signal_item)
		signal_item.connect("activate", self.on_signal_graph)
		
		network_menu.show_all()
		self.network_list_network_menu = network_menu
	
	def add_to_network_list(self, bssid, ssid=None):
		mac = bssid["bssid"]
		network_type = client.decode_network_type(bssid["type"])
		if ssid is None:
			crypt = None
		else:
			try:
				crypt = self.crypt_cache[ssid["cryptset"]]
			except KeyError:
				crypt = client.decode_cryptset(ssid["cryptset"], True)
				self.crypt_cache[ssid["cryptset"]] = crypt
		if ssid is None:
			ssid_str = ""
		elif ssid["ssid"] == "":
			ssid_str = "<no ssid>"
		else:
			ssid_str = ssid["ssid"]
		line = [mac,
				network_type,
				ssid_str,
				bssid["channel"],
				crypt,
				show_timestamp(bssid["firsttime"]),
				show_timestamp(bssid["lasttime"]),
				bssid["bestlat"],
				bssid["bestlon"],
				bssid["signal_dbm"]
				]
		try:
			old_line = self.network_lines[mac]
		except:
			old_line = None
		self.network_lines[mac] = line
		storage = self.network_list_treestore
		if mac in self.network_iter:
			network_iter = self.network_iter[mac]
			storage.move_after(network_iter, None)
			num = 0
			for value in line:
				if old_line is not None and old_line.pop(0) == value:
					num += 1
					continue
				storage.set_value(network_iter, num, value)
				num += 1
		elif network_type in self.network_list_types:
			self.network_iter[mac] = storage.prepend(line)
		
		if mac in self.signal_graphs:
			self.signal_graphs[mac].add_value(bssid["signal_dbm"])
			
	def on_network_list_filter_type(self, widget):
		types = ("infrastructure", "ad-hoc", "probe", "data")
		label = widget.get_label().lower()
		for network_type in types:
			if network_type in label:
				if widget.get_active() is True:
					self.network_list_types.append(network_type)
				else:
					self.network_list_types.remove(network_type)
				break
		
		for mac in self.network_lines:
			line = self.network_lines[mac]
			network_type = line[1]
			if mac in self.network_iter:
				network_iter = self.network_iter[mac]
			else:
				network_iter = None
			
			if network_type not in self.network_list_types:
				if network_iter is not None:
					self.network_list_treestore.remove(network_iter)
					del(self.network_iter[mac])
			elif network_iter is None:
				self.network_iter[mac] = self.network_list_treestore.prepend(line)
				
	def on_network_list_network_popup(self, treeview, event):
		if event.button != 3: # right click
			return
		
		storage = self.network_list_treestore
		x = int(event.x)
		y = int(event.y)
		pthinfo = treeview.get_path_at_pos(x, y)
		if pthinfo is None:
			return
		
		path, col, cellx, celly = pthinfo
		treeview.grab_focus()
		treeview.set_cursor(path, col, 0)
		network_iter = storage.get_iter(path)
		mac = storage.get_value(network_iter, 0)
		self.network_list_network_selected = mac
		self.network_list_network_menu.popup(None, None, None, event.button, event.time)
		
	def on_column_clicked(self, widget):
		self.network_list.set_search_column(widget.num)
		
	def create_log_list(self):
		self.log_list = gtk.TreeView()
		num=0
		for column in ("Time", "Message"):
			tvcolumn = gtk.TreeViewColumn(column)
			self.log_list.append_column(tvcolumn)
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			num += 1
		
		self.log_list_treestore = gtk.TreeStore(
			gobject.TYPE_STRING,gobject.TYPE_STRING
			)
		self.log_list.set_model(self.log_list_treestore)
		
	def add_to_log_list(self, message):
		self.log_list_treestore.prepend(None, 
			[time.strftime("%H:%M:%S"), message])
	
	def init_info_table(self):
		table = gtk.Table(2, 2)
		
		networks_label = gtk.Label("Networks: ")
		networks_label.set_alignment(xalign=0, yalign=0)
		table.attach(networks_label, 0, 1, 0, 1)
		
		networks_value_label = gtk.Label()
		networks_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(networks_value_label, 1, 2, 0, 1)
		self.info_table_networks = networks_value_label
		
		packets_label = gtk.Label("Packets: ")
		packets_label.set_alignment(xalign=0, yalign=0)
		table.attach(packets_label, 0, 1, 1, 2)
		
		packets_value_label = gtk.Label()
		packets_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(packets_value_label, 1, 2, 1, 2)
		self.info_table_packets = packets_value_label
		
		table.show_all()
		self.info_table = table
		self.info_expander.add(self.info_table)
		
	def update_info_table(self, data):
		self.info_table_networks.set_text("%s" % data["networks"])
		self.info_table_packets.set_text("%s" % data["packets"])
	
	def init_gps_table(self):
		table = gtk.Table(3, 2)
		
		fix_label = gtk.Label("Fix: ")
		fix_label.set_alignment(xalign=0, yalign=0)
		table.attach(fix_label, 0, 1, 0, 1)
		
		fix_value_label = gtk.Label()
		fix_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(fix_value_label, 1, 2, 0, 1)
		self.gps_table_fix = fix_value_label
		
		lat_label = gtk.Label("Latitude: ")
		lat_label.set_alignment(xalign=0, yalign=0)
		table.attach(lat_label, 0, 1, 1, 2)
		
		lat_value_label = gtk.Label()
		lat_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(lat_value_label, 1, 2, 1, 2)
		self.gps_table_lat = lat_value_label
		
		lon_label = gtk.Label("Longitude: ")
		lon_label.set_alignment(xalign=0, yalign=0)
		table.attach(lon_label, 0, 1, 2, 3)
		
		lon_value_label = gtk.Label()
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
		
	def init_sources_table(self, sources):
		self.sources_table_sources = {}
		if self.sources_table is not None:
			self.sources_expander.remove(self.sources_table)
			
		table = gtk.Table(len(sources)*5-1, 2)
		for uuid in sources:
			self.init_sources_table_source(sources[uuid], table)
		
		table.show_all()
		self.sources_table = table
		self.sources_expander.add(self.sources_table)
	
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
				label = gtk.Label("%s: "%title)
				label.set_alignment(xalign=0, yalign=0)
				table.attach(label, 0, 1, row, row+1)
			
			label = gtk.Label(value)
			label.set_alignment(xalign=0, yalign=0)
			table.attach(label, 1, 2, row, row+1)
			self.sources_table_sources[source["uuid"]][title] = label
			row += 1
			
	def update_sources_table(self, sources):
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
		
	def on_client_connect(self, widget):
		dialog = gtk.Dialog("Connect", parent=self.gtkwin)
		entry = gtk.Entry()
		entry.set_text(self.config["kismet"]["server"])
		dialog.set_has_separator(False)
		dialog.add_action_widget(entry, 1)
		dialog.add_button(gtk.STOCK_CONNECT, 1)
		dialog.show_all()
		dialog.run()
		server = entry.get_text()
		dialog.destroy()
		self.config["kismet"]["server"] = server
		self.client_start()
		
	def on_client_disconnect(self, widget):
		self.client_stop()
		
	def on_map_hide(self, widget):
		self.config["window"]["map_position"] = "hide"
			
	def on_map_window(self, widget, override=False):
		if (widget is not None and widget.get_active()) or override is True:
			try:
				self.map_window.gtkwin.hide()
				self.map_window.gtkwin.show()
				return
			except:
				pass
			self.config["window"]["map_position"] = "window"
			self.map_window = MapWindow(self.map_widget)
			self.map_window.gtkwin.show_all()
		else:
			try:
				self.map_window.gtkwin.destroy()
			except AttributeError:
				pass
		
	def on_map_widget(self, widget, override=False):
		map_widget = self.map_widget.widget
		if (widget is not None and widget.get_active()) or override is True:
			self.config["window"]["map_position"] = "widget"
			self.notebook.append_page(map_widget)
			self.notebook.set_tab_label_text(map_widget, "Map")
			map_widget.show_all()
		else:
			page = self.notebook.page_num(map_widget)
			if page >= 0:
				self.notebook.remove_page(page)
			
	def on_map_locate_marker(self, widget):
		if self.map_widget is not None:
			self.map.locate_marker(self.network_list_network_selected)
		
	def on_about_dialog(self, widget):
		dialog = gtk.AboutDialog()
		dialog.set_name("Kismon")
		dialog.set_version("0.2")
		dialog.set_comments('PyGTK based kismet client')
		dialog.set_website('http://www.salecker.org/software/kismon/en')
		dialog.set_copyright("(c) 2010 Patrick Salecker")
		dialog.run()
		dialog.destroy()
		
	def on_window_state(self,window, event):
		if event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
			self.config["window"]["maximized"] = True
		else:
			self.config["window"]["maximized"] = False
			
	def on_configure_event(self, widget, event):
		width, height = self.gtkwin.get_size()
		self.config["window"]["width"] = width
		self.config["window"]["height"] = height
		
	def on_config_window(self, widget):
		if self.config_window is not None:
			try:
				self.config_window.gtkwin.hide()
				self.config_window.gtkwin.show()
				return
			except:
				pass
		
		self.config_window = ConfigWindow(self)
		
	def on_signal_graph(self, widget):
		mac = self.network_list_network_selected
		signal_window = SignalWindow(mac, self.on_signal_graph_destroy)
		self.signal_graphs[mac] = signal_window
		
	def on_signal_graph_destroy(self, window, mac):
		del self.signal_graphs[mac]
		
	def set_battery_bar(self, percent):
		self.battery_bar.set_text("%s%%" % percent)
		self.battery_bar.set_fraction(percent / 100)
	
	def on_file_import(self, widget):
		file_import_window = FileImportWindow(self.networks)
		file_import_window.gtkwin.set_transient_for(self.gtkwin)
		file_import_window.gtkwin.set_modal(True)
		
class MapWindow(KismonWindows):
	def __init__(self, map_widget):
		KismonWindows.__init__(self)
		self.gtkwin.set_title("Map")
		self.gtkwin.show()
		self.gtkwin.set_size_request(640, 480)
		self.map_widget = map_widget
		self.gtkwin.add(self.map_widget.widget)
		
	def on_destroy(self, window):
		self.remove_map()
		self.gtkwin = None
		
	def remove_map(self):
		if self.gtkwin is not None:
			self.gtkwin.remove(self.map_widget.widget)
		
	def hide(self):
		self.gtkwin.hide()
		
class ConfigWindow:
	def __init__(self, main_window):
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.connect("destroy", self.on_destroy)
		self.gtkwin.set_size_request(640, 480)
		self.gtkwin.set_title("Kismon Preferences")
		self.main_window = main_window
		self.config = main_window.config
		self.networks_on_map = main_window.networks_on_map
		self.map_widget = main_window.map_widget
		if self.map_widget is not None:
			self.map = self.map_widget.map
		
		self.notebook = gtk.Notebook()
		self.gtkwin.add(self.notebook)
		
		map_page = gtk.Table(rows=2, columns=1)
		self.notebook.append_page(map_page)
		self.notebook.set_tab_label_text(map_page, "Map")
		
		if self.map_widget is None:
			label = gtk.Label("Map disabled")
			map_page.attach(label, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		else:
			self.init_map_page(map_page)
		
		self.gtkwin.show_all()
	
	def init_map_page(self, map_page):
		position_frame = gtk.Frame("Position")
		map_page.attach(position_frame, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		position_vbox = gtk.VBox()
		position_frame.add(position_vbox)
		
		map_widget = gtk.RadioButton(None, 'In main window (default)')
		if self.config["window"]["map_position"] == "widget":
			map_widget.clicked()
		map_widget.connect("clicked", self.main_window.on_map_widget)
		position_vbox.add(map_widget)
		
		map_window = gtk.RadioButton(map_widget, 'In seperate window')
		if self.config["window"]["map_position"] == "window":
			map_window.clicked()
		map_window.connect("clicked", self.main_window.on_map_window)
		position_vbox.add(map_window)
		
		map_hide = gtk.RadioButton(map_widget, 'Hide')
		if self.config["window"]["map_position"] == "hide":
			map_hide.clicked()
		map_hide.connect("clicked", self.main_window.on_map_hide)
		position_vbox.add(map_hide)
		
		source_frame = gtk.Frame("Source")
		source_vbox = gtk.VBox()
		source_frame.add(source_vbox)
		map_page.attach(source_frame, 0, 1, 1, 2, yoptions=gtk.SHRINK)
		
		map_source_mapnik = gtk.RadioButton(None, 'OSM Mapnik (default)')
		
		if self.config["map"]["source"] == "osm-mapnik":
			map_source_mapnik.clicked()
		map_source_mapnik.connect("clicked", self.on_map_source_mapnik)
		source_vbox.add(map_source_mapnik)
		
		map_source_memphis = gtk.RadioButton(map_source_mapnik,
			'Memphis (local rendering)')
		
		if self.config["map"]["source"] == "memphis-local":
			map_source_memphis.clicked()
		map_source_memphis.connect("clicked", self.on_map_source_memphis)
		source_vbox.add(map_source_memphis)
		
		osm_frame = gtk.Frame("OSM File")
		osm_vbox = gtk.VBox()
		osm_frame.add(osm_vbox)
		dialog = gtk.FileChooserDialog(title="Select OSM File",
			parent=self.gtkwin, action=gtk.FILE_CHOOSER_ACTION_OPEN,
			buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,gtk.RESPONSE_ACCEPT)
			)
		dialog.connect("file-activated", self.on_osm_file_changed)
		osm_file_chooser_button = gtk.FileChooserButton(dialog)
		if self.config["map"]["osm_file"] != "":
			osm_file_chooser_button.set_filename(self.config["map"]["osm_file"])
		
		osm_vbox.add(osm_file_chooser_button)
		map_page.attach(osm_frame, 0, 1, 2, 3, yoptions=gtk.SHRINK)
		
		rules_frame = gtk.Frame("Memphis Rules")
		rules_vbox = gtk.VBox()
		rules_frame.add(rules_vbox)
		map_page.attach(rules_frame, 0, 1, 3, 4, yoptions=gtk.SHRINK)
		
		rules_default = gtk.RadioButton(None, 'Memphis default')
		if self.config["map"]["memphis_rules"] == "default":
			rules_default.clicked()
		rules_default.connect("toggled", self.on_memphis_rules, "default")
		rules_vbox.add(rules_default)
		
		rules_minimal = gtk.RadioButton(rules_default, 'Minimal')
		if self.config["map"]["memphis_rules"] == "minimal":
			rules_minimal.clicked()
		rules_minimal.connect("toggled", self.on_memphis_rules, "minimal")
		rules_vbox.add(rules_minimal)
		
		rules_night = gtk.RadioButton(rules_default, 'Night')
		if self.config["map"]["memphis_rules"] == "night":
			rules_night.clicked()
		rules_night.connect("toggled", self.on_memphis_rules, "night")
		rules_vbox.add(rules_night)
		
		perf_frame = gtk.Frame("Performance")
		perf_vbox = gtk.VBox()
		perf_frame.add(perf_vbox)
		map_page.attach(perf_frame, 0, 1, 4, 5, yoptions=gtk.SHRINK)
		
		perf_marker_positions = gtk.CheckButton("Update marker positions")
		if self.config["map"]["update_marker_positions"] == True:
			perf_marker_positions.clicked()
		perf_marker_positions.connect("clicked", self.on_update_marker_positions)
		perf_vbox.add(perf_marker_positions)
		
		networks_frame = gtk.Frame("Networks")
		networks_vbox = gtk.VBox()
		networks_frame.add(networks_vbox)
		map_page.attach(networks_frame, 0, 1, 5, 6, yoptions=gtk.SHRINK)
		
		networks_all = gtk.RadioButton(None, 'Show all networks on the map')
		
		if self.config["map"]["networks"] == "all":
			networks_all.clicked()
		networks_all.connect("clicked", self.on_map_networks, "all")
		networks_vbox.add(networks_all)
		
		networks_current = gtk.RadioButton(networks_all,
			'Show only the networks of the current session')
		
		if self.config["map"]["networks"] == "current":
			networks_current.clicked()
		networks_current.connect("clicked", self.on_map_networks, "current")
		networks_vbox.add(networks_current)
		
	def on_destroy(self, window):
		self.gtkwin = None
		
	def on_osm_file_changed(self, widget):
		filename = widget.get_filename()
		self.config["map"]["osm_file"] = filename
		if self.config["map"]["source"] == "memphis-local":
			self.map.load_osm_file()
		
	def on_map_source_mapnik(self, widget):
		if widget.get_active():
			self.config["map"]["source"] = "osm-mapnik"
			self.map.set_source("osm-mapnik")
		
	def on_map_source_memphis(self, widget):
		if not widget.get_active():
			return
		self.config["map"]["source"] = "memphis-local"
		
		if os.path.isfile(self.config["map"]["osm_file"]):
			self.map.set_source("memphis-local")
			
	def on_memphis_rules(self, widget, name):
		if widget.get_active():
			self.config["map"]["memphis_rules"] = name
			self.map.load_memphis_rules()
		
	def on_update_marker_positions(self, widget):
		self.config["map"]["update_marker_positions"] = widget.get_active()
		
	def on_map_networks(self, widget, show):
		self.networks_on_map(show)
		
class SignalWindow:
	def __init__(self, mac, destroy):
		self.mac = mac
		self.history = {}
		self.time_range = 60 * 2
		
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.connect("destroy", destroy, mac)
		self.gtkwin.set_default_size(480, 240)
		self.gtkwin.set_title("Signal Graph: %s" % self.mac)
		
		self.graph = gtk.DrawingArea()
		self.graph.connect("expose_event", self.on_expose_event)
		self.gtkwin.add(self.graph)
		
		self.gtkwin.show_all()
		
	def on_expose_event(self, widget, event):
		width = event.area.width
		height = event.area.height
		self.draw_graph(width, height)
		
	def draw_graph(self, width, height):
		ctx=self.graph.window.cairo_create()
		
		border_left = 60
		border_bottom = 30
		
		graph_width = width - border_left
		graph_height = height - border_bottom
		
		values = self.history.values()
		if len(values) > 1:
			signal_min = min(values)
			signal_max = max(values) + 1
		else:
			signal_min = -100
			signal_max = -50
		
		signal_min = min(signal_min, -100)
		signal_max = max(signal_max, -50)
		
		signal_range = signal_max - signal_min
		y_rel = 1.0 * graph_height / signal_range
		
		#background
		ctx.set_source_rgb(0, 0, 0)
		ctx.rectangle(0, 0, width, height)
		ctx.fill()
		ctx.stroke()
		
		#legend
		ctx.set_line_width(1)
		ctx.set_source_rgb(1, 1, 1)
		
		ctx.move_to(border_left, 0)
		ctx.line_to(border_left, graph_height + 5)
		ctx.move_to(border_left - 5, graph_height)
		ctx.line_to(width, height - border_bottom)
		
		ctx.move_to(border_left - 55, graph_height + 4)
		ctx.show_text("%s dbm" % signal_min)
		
		signal = (int((signal_min + 2) / 10)) * 10
		while True:
			signal += 10
			if signal >= signal_max:
				break
			
			y = y_rel * (signal_max - signal)
			ctx.move_to(border_left - 5, y)
			ctx.line_to(width, y)
			ctx.move_to(border_left - 55, y + 4)
			ctx.show_text("%s dbm" % signal)
		
		ctx.move_to(border_left - 15, graph_height + 16)
		ctx.show_text("-%ss" % self.time_range)
		ctx.move_to(border_left + graph_width / 2, graph_height + 1)
		ctx.line_to(border_left + graph_width / 2, graph_height + 6)
		ctx.move_to(border_left + graph_width / 2 - 12, graph_height + 16)
		ctx.show_text("-%ss" % (self.time_range / 2))
		
		ctx.stroke()
		
		#graph
		ctx.set_line_width(2)
		ctx.set_source_rgb(0, 1, 0)
		
		if len(self.history) < 2:
			ctx.move_to(width / 2, height / 2)
			ctx.show_text("collecting data")
			ctx.stroke()
			return False
		
		start_sec = max(self.history) - self.time_range
		x_rel = 1.0 * graph_width / self.time_range
		start = False
		sec = 0
		
		while True:
			if start_sec + sec in self.history:
				signal = self.history[start_sec + sec]
				x = x_rel * sec + border_left
				y = y_rel * (signal_max - signal)
				if not start:
					ctx.move_to(x, y)
					start = True
					sec += 1
				else:
					ctx.line_to(x, y)
			
			sec += 1
			if sec > self.time_range:
				break
		ctx.stroke()
		
		return False
		
	def add_value(self, value):
		self.history[int(time.time())] = value
		self.graph.queue_draw()

class FileImportWindow:
	def __init__(self, networks):
		self.networks = networks
		self.files = {}
		self.parser_queue = ()
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.set_default_size(600, 300)
		self.gtkwin.set_title("Kismon: File Import")
		self.gtkwin.set_border_width(5)
		
		self.main_box = gtk.VBox()
		
		file_list_scroll = gtk.ScrolledWindow()
		file_list_scroll.get_children()[0].set_shadow_type(gtk.SHADOW_NONE)
		file_list_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.file_list = gtk.VBox()
		file_list_scroll.add_with_viewport(self.file_list)
		self.main_box.add(file_list_scroll)
		
		button_box = gtk.HBox()
		add_file_button = gtk.Button("Add files")
		add_file_button.connect("clicked", self.on_add, "file")
		button_box.pack_start(add_file_button, expand=False, fill=False, padding=0)
		add_dir_button = gtk.Button("Add directories")
		add_dir_button.connect("clicked", self.on_add, "dir")
		button_box.pack_start(add_dir_button, expand=False, fill=False, padding=0)
		self.start_button = gtk.Button("Start Import")
		self.start_button.connect("clicked", self.on_start)
		button_box.pack_end(self.start_button, expand=False, fill=False, padding=0)
		
		self.main_box.pack_end(button_box, expand=False, fill=True, padding=0)
		self.gtkwin.add(self.main_box)
		self.gtkwin.show_all()
		
	def on_add(self, widget, add_type):
		if add_type == "dir":
			action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
		else:
			action = gtk.FILE_CHOOSER_ACTION_OPEN
		dialog = gtk.FileChooserDialog(title="", parent=self.gtkwin, action=action,
			buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_select_multiple(True)
		
		filter = gtk.FileFilter()
		filter.set_name("All supported files")
		filter.add_pattern("*.netxml")
		filter.add_pattern("*.csv")
		filter.add_pattern("*.json")
		dialog.add_filter(filter)
		
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dialog.add_filter(filter)
		
		response = dialog.run()
		filenames = dialog.get_filenames()
		dialog.destroy()
		if response != gtk.RESPONSE_OK:
			return
		
		if add_type == "file":
			for filename in filenames:
				self.add_file(filename)
		else:
			for dirname in filenames:
				for filename in os.listdir(dirname):
					full_filename = dirname + os.sep + filename
					if os.path.isfile(full_filename):
						self.add_file(full_filename)
		
		if len(self.files) > 0:
			self.start_button.set_sensitive(True)
		
	def add_file(self, filename):
		table = gtk.Table(columns=2)
		self.files[filename] = {}
		self.files[filename]["type"] = "unknown"
		
		combobox = gtk.combo_box_new_text()
		combobox.connect("changed", self.on_filetype_changed, filename)
		combobox.append_text("netxml")
		combobox.append_text("csv")
		combobox.append_text("networks")
		combobox.append_text("unknown")
		if filename.endswith(".netxml"):
			combobox.set_active(0)
		elif filename.endswith(".csv"):
			combobox.set_active(1)
		elif filename.endswith(".json"):
			combobox.set_active(2)
		else:
			combobox.set_active(3)
		table.attach(combobox, 0, 1, 0, 1, yoptions=gtk.SHRINK, xoptions=gtk.SHRINK)
		
		label = gtk.Label(filename)
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 1, 2, 0, 1, yoptions=gtk.SHRINK, xpadding=5)
		
		button = gtk.Button()
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU)
		button.set_image(image)
		button.connect("clicked", self.on_remove_file, filename)
		table.attach(button, 2, 3, 0, 1, yoptions=gtk.SHRINK, xoptions=gtk.SHRINK)
		
		frame = gtk.Frame()
		frame.add(table)
		self.files[filename]["widget"] = frame
		frame.show_all()
		self.file_list.pack_start(frame, expand=False, fill=False, padding=1)
		
	def on_filetype_changed(self, widget, filename):
		self.files[filename]["filetype"] = widget.get_active_text()
		
	def on_remove_file(self, widget, filename):
		self.file_list.remove(self.files[filename]["widget"])
		del self.files[filename]
		if len(self.files) == 0:
			self.start_button.set_sensitive(False)
		
	def on_start(self, widget):
		self.gtkwin.remove(self.main_box)
		main_box = gtk.VBox()
		self.gtkwin.add(main_box)
		
		self.file_list = gtk.TreeView()
		num=0
		for column in ("File", "Type", "Networks", "New", "Status"):
			tvcolumn = gtk.TreeViewColumn(column)
			self.file_list.append_column(tvcolumn)
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			num += 1
		
		self.file_list_treestore = gtk.ListStore(
			gobject.TYPE_STRING, # filename
			gobject.TYPE_STRING, # filetype
			gobject.TYPE_INT, # networks
			gobject.TYPE_INT, # new
			gobject.TYPE_STRING # status
			)
		self.file_list.set_model(self.file_list_treestore)
		
		file_scrolled = gtk.ScrolledWindow()
		file_scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		file_scrolled.set_shadow_type(gtk.SHADOW_NONE)
		file_scrolled.add(self.file_list)
		main_box.add(file_scrolled)
		
		self.battery_bar = gtk.ProgressBar()
		self.battery_bar.set_text("0 of %s Files" % len(self.files))
		self.battery_bar.set_fraction(0)
		main_box.pack_start(self.battery_bar, expand=False, fill=True, padding=0)
		
		button_box = gtk.VButtonBox()
		self.close_button = gtk.Button("Close")
		self.close_button.connect("clicked", self.on_close)
		self.close_button.set_sensitive(False)
		button_box.add(self.close_button)
		
		main_box.pack_end(button_box, expand=False, fill=True, padding=0)
		self.gtkwin.show_all()
		self.parser_queue = self.files.keys()
		gobject.timeout_add(20, self.parse_file)
		
	def parse_file(self):
		filename = self.parser_queue.pop()
		filetype = self.files[filename]["filetype"]
		num_new = 0 - len(self.networks.networks)
		if filetype != "unknown":
			try:
				num_networks = self.networks.import_networks(filetype, filename)
				status = "done"
			except:
				status = "failed"
				num_networks = 0
				print "%s: %s" % (filename, sys.exc_info()[1])
		else:
			num_networks = 0
			status = "skiped"
		
		num_new = num_new + len(self.networks.networks)
		
		self.file_list_treestore.append([filename, filetype, num_networks, num_new, status])
		
		num_files = len(self.files)
		pos = num_files - len(self.parser_queue)
		
		self.battery_bar.set_text("%s of %s Files" % (pos, num_files))
		self.battery_bar.set_fraction(1.0 / num_files * pos)
		
		if len(self.parser_queue) == 0:
			self.close_button.set_sensitive(True)
		else:
			return True
		
	def on_close(self, widget):
		self.gtkwin.destroy()

def show_timestamp(timestamp):
	time_format = "%H:%M:%S"
	return time.strftime(time_format, time.localtime(timestamp))
	
if __name__ == "__main__":
	import core
	core.main()
