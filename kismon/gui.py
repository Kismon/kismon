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

from windows import *

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
		
	def on_key_press(self, widget, event):
		keyval = event.keyval
		name = gtk.gdk.keyval_name(keyval)
		if name == "F11":
			self.fullscreen()
		elif event.state & gtk.gdk.CONTROL_MASK:
			if self.map is not None:
				if name == "i":
					self.map.zoom_in()
				elif name == "o":
					self.map.zoom_out()

class MainWindow(KismonWindows):
	def __init__(self, config, client_start, client_stop, map, networks, sources, client):
		KismonWindows.__init__(self)
		self.config = config
		self.config_window = None
		self.progress_bar_win = None
		self.client_start = client_start
		self.client_stop = client_stop
		self.networks = networks
		self.map = map
		
		if map is not None:
			locate_marker = map.locate_marker
		else:
			locate_marker = None
		
		self.network_list = NetworkList(self.networks, locate_marker, self.on_signal_graph)
		
		self.gtkwin.set_title("Kismon")
		self.gtkwin.connect("window-state-event", self.on_window_state)
		self.gtkwin.connect('configure-event', self.on_configure_event)
		
		self.gtkwin.set_default_size(self.config["window"]["width"],
			self.config["window"]["height"])
		
		if self.config["window"]["maximized"] is True:
			self.gtkwin.maximize()
		
		self.network_filter = {}
		self.signal_graphs = {}
		self.sources = sources
		self.client = client
		
		self.notebook = gtk.Notebook()
		
		vbox = gtk.VBox()
		self.gtkwin.add(vbox)
		vbox.pack_start(self.init_menu(), expand=False, fill=False, padding=0)
		
		vpaned_main = gtk.VPaned()
		vpaned_main.set_position(320)
		vbox.add(vpaned_main)
		hbox = gtk.HBox()
		vpaned_main.add1(hbox)
		hbox.pack_start(self.network_list.widget, expand=True, fill=True, padding=0)
		
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
		
		self.log_list = LogList(self.config["window"])
		vpaned_main.add2(self.notebook)
		self.notebook.append_page(self.log_list.widget)
		self.notebook.set_tab_label_text(self.log_list.widget, "Log")
		
		self.statusbar = gtk.Statusbar()
		self.statusbar_context = self.statusbar.get_context_id("Starting...")
		vbox.pack_end(self.statusbar, expand=False, fill=False, padding=0)
		
		self.gtkwin.show_all()
		self.apply_config()
		
	def apply_config(self):
		if self.map is None:
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
		
		channel_config = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		channel_config.set_label("Configure Channels")
		channel_config.connect("activate", self.on_channel_config)
		file_menu.append(channel_config)
		
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
		
		networks_menu = gtk.Menu()
		networks_menuitem = gtk.MenuItem("Amount of networks")
		networks_menuitem.set_submenu(networks_menu)
		view_menu.append(networks_menuitem)
		
		for name, key in (("Network List", "network_list"), ("Map", "map")):
			menu = gtk.Menu()
			menuitem = gtk.MenuItem(name)
			menuitem.set_submenu(menu)
			networks_menu.append(menuitem)
			
			show_none = gtk.RadioMenuItem(None, 'Disable')
			menu.append(show_none)
			show_current = gtk.RadioMenuItem(show_none, 'Networks from the current session')
			menu.append(show_current)
			show_all = gtk.RadioMenuItem(show_none, 'All Networks')
			menu.append(show_all)
			
			if self.config["filter_networks"][key] == "none":
				show_none.set_active(True)
			if self.config["filter_networks"][key] == "current":
				show_current.set_active(True)
			if self.config["filter_networks"][key] == "all":
				show_all.set_active(True)
			
			show_none.connect("activate", self.on_network_filter_networks, key, "none")
			show_current.connect("activate", self.on_network_filter_networks, key, "current")
			show_all.connect("activate", self.on_network_filter_networks, key, "all")
		
		network_type_menu = gtk.Menu()
		network_menuitem = gtk.MenuItem("Network Type")
		network_menuitem.set_submenu(network_type_menu)
		view_menu.append(network_menuitem)
		
		for network_type, key in (("Infrastructure", "infrastructure"),("Data", "data"), ("Probe", "probe"), ("Ad-Hoc", "ad-hoc")):
			item = gtk.CheckMenuItem('%s Networks' % network_type)
			if self.config["filter_type"][key]:
				item.set_active(True)
			item.connect("activate", self.on_network_filter_type)
			network_type_menu.append(item)
		
		crypt_menu = gtk.Menu()
		crypt_menuitem = gtk.MenuItem("Encryption")
		crypt_menuitem.set_submenu(crypt_menu)
		view_menu.append(crypt_menuitem)
		
		for crypt in ("None", "WEP", "WPA", "Other"):
			crypt_item = gtk.CheckMenuItem(crypt)
			if self.config["filter_crypt"][crypt.lower()]:
				crypt_item.set_active(True)
			crypt_item.connect("activate", self.on_network_filter_crypt)
			crypt_menu.append(crypt_item)
		
		sep = gtk.SeparatorMenuItem()
		view_menu.append(sep)
		
		marker_menu = gtk.Menu()
		marker_menuitem = gtk.MenuItem("Marker Style")
		marker_menuitem.set_submenu(marker_menu)
		view_menu.append(marker_menuitem)
		if self.map == None:
			marker_menu.set_sensitive(False)
		else:
			parent = None
			for style in ("Point", "Name"):
				item = gtk.RadioMenuItem(parent, style)
				if self.config["map"]["marker_style"] == style.lower():
					item.set_active(True)
				item.connect("activate", self.map.on_set_marker_style, style.lower())
				marker_menu.append(item)
				parent = item
			
		sep = gtk.SeparatorMenuItem()
		view_menu.append(sep)
			
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
	
	def on_network_filter_type(self, widget):
		types = ("infrastructure", "ad-hoc", "probe", "data")
		label = widget.get_label().lower()
		
		for network_type in types:
			if network_type in label:
				self.config["filter_type"][network_type] = widget.get_active()
				break
		self.networks.apply_filters()
		self.networks_queue_progress()
		
	def on_network_filter_networks(self, widget, target, show):
		if not widget.get_active():
			return
		
		self.config["filter_networks"][target] = show
		self.networks.apply_filters()
		self.networks_queue_progress()
		
	def on_network_filter_crypt(self, widget):
		crypt = widget.get_label().lower()
		self.config["filter_crypt"][crypt] = widget.get_active()
		self.networks.apply_filters()
		self.networks_queue_progress()
		
	def networks_queue_progress(self):
		if self.progress_bar_win is not None:
			return
		
		self.progress_bar_max = float(len(self.networks.notify_add_queue))
		if self.networks.queue_task:
			self.progress_bar = gtk.ProgressBar()
			self.progress_bar.set_text("0.0%%, %s networks left" % len(self.networks.notify_add_queue))
			self.progress_bar.set_fraction(0)
			
			self.progress_bar_win = gtk.Window()
			self.progress_bar_win.set_title("Adding networks")
			self.progress_bar_win.set_position(gtk.WIN_POS_CENTER)
			self.progress_bar_win.set_default_size(300, 30)
			self.progress_bar_win.set_modal(True)
			self.progress_bar_win.set_transient_for(self.gtkwin)
			self.progress_bar_win.add(self.progress_bar)
			self.progress_bar_win.show_all()
			def on_delete_event(widget, event):
				return True
			self.progress_bar_win.connect("delete-event",on_delete_event)
			self.progress_bar_win.connect("destroy", self.on_destroy_progress_bar_win)
			
			gobject.idle_add(self.networks_queue_progress_update)
			
	def networks_queue_progress_update(self):
		if self.networks.queue_task is None:
			self.progress_bar_win.destroy()
			return False
		progress = 100 / self.progress_bar_max * (self.progress_bar_max - len(self.networks.notify_add_queue))
		self.progress_bar.set_text("%s%%, %s networks left" % (round(progress, 1), len(self.networks.notify_add_queue)))
		self.progress_bar.set_fraction(progress/100)
		return True
		
	def on_destroy_progress_bar_win(self, window):
		self.progress_bar_win = None
		
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
			self.map_window = MapWindow(self.map)
			self.map_window.gtkwin.show_all()
		else:
			try:
				self.map_window.gtkwin.destroy()
			except AttributeError:
				pass
		
	def on_map_widget(self, widget, override=False):
		map_widget = self.map.widget
		if (widget is not None and widget.get_active()) or override is True:
			self.config["window"]["map_position"] = "widget"
			self.notebook.append_page(map_widget)
			self.notebook.set_tab_label_text(map_widget, "Map")
			map_widget.show_all()
		else:
			page = self.notebook.page_num(map_widget)
			if page >= 0:
				self.notebook.remove_page(page)
			
	def on_about_dialog(self, widget):
		dialog = gtk.AboutDialog()
		dialog.set_name("Kismon")
		dialog.set_version("0.3")
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
		mac = self.network_list.network_selected
		signal_window = SignalWindow(mac, self.on_signal_graph_destroy)
		self.signal_graphs[mac] = signal_window
		
	def on_signal_graph_destroy(self, window, mac):
		del self.signal_graphs[mac]
		
	def set_battery_bar(self, percent):
		if percent is not False:
			self.battery_bar.set_text("%s%%" % percent)
			self.battery_bar.set_fraction(percent / 100)
		else:
			self.battery_bar.set_text("-")
			self.battery_bar.set_fraction(0)
	
	def on_file_import(self, widget):
		file_import_window = FileImportWindow(self.networks, self.networks_queue_progress)
		file_import_window.gtkwin.set_transient_for(self.gtkwin)
		file_import_window.gtkwin.set_modal(True)
		
	def update_statusbar(self):
		text = "Networks: %s in the current session, %s total" % \
			(len(self.networks.recent_networks), len(self.networks.networks))
		self.statusbar.push(self.statusbar_context, text)
		
	def on_channel_config(self, widget):
		win = ChannelWindow(self.sources, self.client)
		
class LogList:
	def __init__(self, config):
		self.rows = []
		self.config = config
		self.treeview = gtk.TreeView()
		num=0
		for column in ("Time", "Message"):
			tvcolumn = gtk.TreeViewColumn(column)
			self.treeview.append_column(tvcolumn)
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			tvcolumn.set_sort_column_id(num)
			tvcolumn.set_clickable(True)
			num += 1
		
		self.store = gtk.ListStore(
			gobject.TYPE_STRING, #time
			gobject.TYPE_STRING, #message
			)
		self.treeview.set_model(self.store)
		
		log_scrolled = gtk.ScrolledWindow()
		log_scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		log_scrolled.set_shadow_type(gtk.SHADOW_NONE)
		log_scrolled.add(self.treeview)
		
		self.widget = log_scrolled
		
	def add(self, message):
		if not self.cleanup():
			return
		
		row = self.store.append([show_timestamp(time.time()), message])
		path = self.store.get_path(row)
		self.treeview.scroll_to_cell(path)
		self.rows.append(row)
		
	def cleanup(self, new=1):
		max_rows = self.config["log_list_max"]
		num_rows = len(self.rows)
		
		if max_rows == -1:
			return True
		if num_rows == 0 and max_rows == 0:
			return False
		
		if max_rows - new < 0:
			stop = 0
		else:
			stop = max_rows - new
		
		while num_rows > stop:
			row = self.rows.pop(0)
			self.store.remove(row)
			num_rows -= 1
		
		if max_rows == 0:
			return False
		
		return True
		
class NetworkList:
	def __init__(self, networks, locate_network_on_map, on_signal_graph):
		self.network_lines = {}
		self.network_iter = {}
		self.network_selected = None
		self.locate_network_on_map = locate_network_on_map
		self.on_signal_graph = on_signal_graph
		self.networks = networks
		
		self.networks.notify_add_list["network_list"] = self.add_network
		self.networks.notify_remove_list["network_list"] = self.remove_network
		self.networks.disable_refresh_functions.append(self.pause)
		self.networks.resume_refresh_functions.append(self.resume)
		
		self.treeview = gtk.TreeView()
		self.treeview.connect("button-press-event", self.on_popup)
		num=0
		columns=("BSSID", "Type", "SSID", "Ch", "Crypt",
			"First Seen", "Last Seen", "Latitude", "Longitude",
			"Signal dbm")
		for column in columns:
			tvcolumn = gtk.TreeViewColumn(column)
			self.treeview.append_column(tvcolumn)
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			tvcolumn.set_sort_column_id(num)
			tvcolumn.set_clickable(True)
			tvcolumn.set_resizable(True)
			tvcolumn.connect("clicked", self.on_column_clicked)
			tvcolumn.num = num
			num+=1
		self.treeview.show()
		
		self.store = gtk.ListStore(
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
		self.treeview.set_model(self.store)
		
		scrolled = gtk.ScrolledWindow()
		scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled.add(self.treeview)
		
		frame = gtk.Frame("Networks")
		frame.add(scrolled)
		
		self.widget = frame
		
		self.store.set_sort_column_id(6, gtk.SORT_DESCENDING)
		
		network_popup = gtk.Menu()
		locate_item = gtk.MenuItem('Locate on map')
		network_popup.append(locate_item)
		locate_item.connect("activate", self.on_locate_marker)
		
		signal_item = gtk.MenuItem('Signal graph')
		network_popup.append(signal_item)
		signal_item.connect("activate", self.on_signal_graph)
		
		network_popup.show_all()
		self.network_popup = network_popup
	
	def on_column_clicked(self, widget):
		self.treeview.set_search_column(widget.num)
	
	def add_network(self, mac):
		network = self.networks.get_network(mac)
		try:
			crypt = self.crypt_cache[network["cryptset"]]
		except KeyError:
			crypt = client.decode_cryptset(network["cryptset"], True)
			self.crypt_cache[network["cryptset"]] = crypt
		
		if network["ssid"] == "":
			ssid_str = "<no ssid>"
		else:
			ssid_str = network["ssid"]
			
		if "signal_dbm" in network and len(network["signal_dbm"]) == 3:
			signal = network["signal_dbm"]["last"]
		else:
			signal = 0
		
		line = [mac,
				network["type"],
				ssid_str,
				network["channel"],
				crypt,
				show_timestamp(network["firsttime"]),
				show_timestamp(network["lasttime"]),
				network["lat"],
				network["lon"],
				signal
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
				gobject.idle_add(self.treeview.scroll_to_point, -1, 0)
		
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
		
	def on_popup(self, treeview, event):
		if event.button != 3: # right click
			return
		
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
		self.network_popup.popup(None, None, None, event.button, event.time)
		
	def on_locate_marker(self, widget):
		if self.locate_network_on_map is not None:
			self.locate_network_on_map(self.network_selected)
		
		
class MapWindow(KismonWindows):
	def __init__(self, map_widget):
		KismonWindows.__init__(self)
		self.gtkwin.set_title("Map")
		self.gtkwin.show()
		self.gtkwin.set_size_request(640, 480)
		self.map_widget = map_widget.widget
		self.gtkwin.add(self.map_widget)
		
	def on_destroy(self, window):
		self.remove_map()
		self.gtkwin = None
		
	def remove_map(self):
		if self.gtkwin is not None:
			self.gtkwin.remove(self.map_widget)
		
	def hide(self):
		self.gtkwin.hide()

def show_timestamp(timestamp):
	time_format = "%Y/%m/%d %H:%M:%S"
	return time.strftime(time_format, time.localtime(timestamp))
	
if __name__ == "__main__":
	import core
	core.main()
