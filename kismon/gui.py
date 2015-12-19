#!/usr/bin/env python3
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

try:
	from .client import Client, decode_cryptset
	from .windows import *
except SystemError:
	from client import Client, decode_cryptset
	from windows import *

import time
import os
import sys

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib

class KismonWindows:
	def __init__(self):
		self.gtkwin = Gtk.Window()
		self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
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
		name = Gdk.keyval_name(keyval)
		if name == "F11":
			self.fullscreen()
		elif event.get_state() & Gdk.ModifierType.CONTROL_MASK:
			if self.map is not None:
				if name == "i":
					self.map.zoom_in()
				elif name == "o":
					self.map.zoom_out()

class MainWindow(KismonWindows):
	def __init__(self, config, client_start, client_stop, map, networks, sources, client_threads):
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
		
		self.export_networks = {}
		self.networks.notify_add_list["export"] = self.export_add_network
		self.networks.notify_remove_list["export"] = self.export_remove_network
		
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
		self.client_threads = client_threads
		
		self.notebook = Gtk.Notebook()
		
		vbox = Gtk.VBox()
		self.gtkwin.add(vbox)
		vbox.pack_start(self.init_menu(), False, False, 0)
		
		vpaned_main = Gtk.VPaned()
		vpaned_main.set_position(320)
		vbox.add(vpaned_main)
		hbox = Gtk.HBox()
		vpaned_main.add1(hbox)
		hbox.pack_start(self.network_list.widget, expand=True, fill=True, padding=0)
		
		self.server_notebook = Gtk.Notebook()
		frame = Gtk.Frame()
		frame.set_label("Servers")
		frame.add(self.server_notebook)
		hbox.pack_end(frame, expand=False, fill=False, padding=2)
		
		image = Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.MENU)
		button = Gtk.Button()
		button.props.focus_on_click = False
		button.add(image)
		button.show_all()
		button.set_tooltip_text('Add server')
		button.connect("clicked", self.on_add_server_clicked)
		self.server_notebook.set_action_widget(button, Gtk.PackType.END)
		
		self.info_expanders = {}
		self.gps_expanders = {}
		self.sources_expanders = {}
		self.info_table_networks = {}
		self.info_table_packets = {}
		self.gps_table_fix = {}
		self.gps_table_lat = {}
		self.gps_table_lon = {}
		self.sources_table_sources = {}
		self.sources_tables = {}
		self.server_switches = {}
		for server_id in self.client_threads:
			self.init_server_tab(server_id)
		
		self.log_list = LogList(self.config["window"])
		vpaned_main.add2(self.notebook)
		self.notebook.append_page(self.log_list.widget)
		self.notebook.set_tab_label_text(self.log_list.widget, "Log")
		
		self.statusbar = Gtk.Statusbar()
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
		print("Window destroyed")
		self.gtkwin = None
		Gtk.main_quit()
		
	def init_menu(self):
		menubar = Gtk.MenuBar()
		
		file_menu = Gtk.Menu()
		file_menuitem = Gtk.MenuItem.new_with_label("File")
		file_menuitem.set_submenu(file_menu)
		
		channel_config = Gtk.MenuItem.new_with_mnemonic('_Preferences')
		channel_config.set_label("Configure Channels")
		channel_config.connect("activate", self.on_channel_config)
		file_menu.append(channel_config)
		
		sep = Gtk.SeparatorMenuItem()
		file_menu.append(sep)
		
		file_import = Gtk.MenuItem.new_with_mnemonic('_Open')
		file_import.set_label("Import Networks")
		file_import.connect("activate", self.on_file_import)
		file_menu.append(file_import)
		
		export_menu = Gtk.Menu()
		export_menuitem = Gtk.MenuItem.new_with_mnemonic('Save _As')
		export_menuitem.set_label("Export Networks")
		export_menuitem.set_submenu(export_menu)
		file_menu.append(export_menuitem)
		
		for export_format, extension in (("Kismon", "json"),("Kismet netxml", "netxml"),
				("Google Earth KMZ", "kmz"), ("MapPoint csv", "csv")):
			
			menu = Gtk.Menu()
			menuitem = Gtk.MenuItem.new_with_mnemonic('Save _As')
			menuitem.set_label(export_format)
			menuitem.set_submenu(menu)
			export_menu.append(menuitem)
			
			for amount in ("All", "Filtered"):
				item = Gtk.MenuItem.new_with_label(amount)
				item.connect("activate", self.on_file_export, export_format.lower(), extension, amount)
				menu.append(item)
		
		sep = Gtk.SeparatorMenuItem()
		file_menu.append(sep)
		
		exit = Gtk.MenuItem.new_with_mnemonic('_Quit')
		exit.connect("activate", self.on_destroy)
		file_menu.append(exit)
		
		menubar.append(file_menuitem)
		
		view_menu = Gtk.Menu()
		view_menuitem = Gtk.MenuItem.new_with_label("View")
		view_menuitem.set_submenu(view_menu)
		menubar.append(view_menuitem)
		
		networks_menu = Gtk.Menu()
		networks_menuitem = Gtk.MenuItem.new_with_label("Amount of networks")
		networks_menuitem.set_submenu(networks_menu)
		view_menu.append(networks_menuitem)
		
		for name, key in (("Network List", "network_list"), ("Map", "map"), ("Export", "export")):
			menu = Gtk.Menu()
			menuitem = Gtk.MenuItem.new_with_label(name)
			menuitem.set_submenu(menu)
			networks_menu.append(menuitem)
			
			show_none = Gtk.RadioMenuItem(label='Disable')
			if key != "export":
				menu.append(show_none)
			show_current = Gtk.RadioMenuItem(group=show_none, label='Networks from the current session')
			menu.append(show_current)
			show_all = Gtk.RadioMenuItem(group=show_none, label='All Networks')
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
		
		network_type_menu = Gtk.Menu()
		network_menuitem = Gtk.MenuItem.new_with_label("Network Type")
		network_menuitem.set_submenu(network_type_menu)
		view_menu.append(network_menuitem)
		
		for network_type, key in (("Infrastructure", "infrastructure"),("Data", "data"), ("Probe", "probe"), ("Ad-Hoc", "ad-hoc")):
			item = Gtk.CheckMenuItem.new_with_label('%s Networks' % network_type)
			if self.config["filter_type"][key]:
				item.set_active(True)
			item.connect("activate", self.on_network_filter_type)
			network_type_menu.append(item)
		
		crypt_menu = Gtk.Menu()
		crypt_menuitem = Gtk.MenuItem.new_with_label("Encryption")
		crypt_menuitem.set_submenu(crypt_menu)
		view_menu.append(crypt_menuitem)
		
		for crypt in ("None", "WEP", "WPA", "Other"):
			crypt_item = Gtk.CheckMenuItem.new_with_label(crypt)
			if self.config["filter_crypt"][crypt.lower()]:
				crypt_item.set_active(True)
			crypt_item.connect("activate", self.on_network_filter_crypt)
			crypt_menu.append(crypt_item)
		
		for key in ("ssid", "bssid"):
			regexpr_menuitem = Gtk.MenuItem.new_with_label("%s (regular expression)" % key.upper())
			regexpr_menuitem.connect("activate", self.on_network_filter_regexpr, key)
			view_menu.append(regexpr_menuitem)
		
		sep = Gtk.SeparatorMenuItem()
		view_menu.append(sep)
		
		config_menuitem = Gtk.MenuItem.new_with_mnemonic('_Preferences')
		config_menuitem.connect("activate", self.on_config_window)
		view_menu.append(config_menuitem)
		
		help_menu = Gtk.Menu()
		help_menuitem = Gtk.MenuItem.new_with_label("Help")
		help_menuitem.set_submenu(help_menu)
		menubar.append(help_menuitem)
		
		about = Gtk.MenuItem.new_with_mnemonic('_About')
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
		
	def on_network_filter_regexpr(self, widget, key):
		dialog = Gtk.Dialog("%s (regular expression)" % key.upper(), parent=self.gtkwin)
		entry = Gtk.Entry()
		entry.set_width_chars(100)
		entry.set_text(self.config["filter_regexpr"][key])
		hbox = Gtk.HBox()
		hbox.pack_start(Gtk.Label("Regular expression:", True, True, 0), False, 5, 5)
		hbox.pack_end(entry, True, True, 0)
		dialog.vbox.pack_end(hbox, True, True, 0)
		dialog.add_button("Apply", 1)
		dialog.show_all()
		dialog.run()
		regexpr = entry.get_text()
		dialog.destroy()
		self.config["filter_regexpr"][key] = regexpr
		self.networks.apply_filters()
		self.networks_queue_progress()
		
	def networks_queue_progress(self):
		if self.progress_bar_win is not None:
			return
		
		self.progress_bar_max = float(len(self.networks.notify_add_queue))
		if self.networks.queue_task:
			self.progress_bar = Gtk.ProgressBar()
			self.progress_bar.set_text("0.0%%, %s networks left" % len(self.networks.notify_add_queue))
			self.progress_bar.set_fraction(0)
			
			self.progress_bar_win = Gtk.Window()
			self.progress_bar_win.set_title("Adding networks")
			self.progress_bar_win.set_position(Gtk.WindowPosition.CENTER)
			self.progress_bar_win.set_default_size(300, 30)
			self.progress_bar_win.set_modal(True)
			self.progress_bar_win.set_transient_for(self.gtkwin)
			self.progress_bar_win.add(self.progress_bar)
			self.progress_bar_win.show_all()
			def on_delete_event(widget, event):
				return True
			self.progress_bar_win.connect("delete-event",on_delete_event)
			self.progress_bar_win.connect("destroy", self.on_destroy_progress_bar_win)
			
			GLib.idle_add(self.networks_queue_progress_update)
			
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
		
	def init_server_tab(self, server_id):
		right_table = Gtk.Table(n_rows=3, n_columns=1)
		right_scrolled = Gtk.ScrolledWindow()
		right_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		right_scrolled.add(right_table)
		right_scrolled.set_size_request(160, -1)
		right_scrolled.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)
		self.server_notebook.append_page(right_scrolled)
		self.server_notebook.set_tab_label_text(right_scrolled, "%s" % (server_id + 1))
		row = 0
		
		hbox = Gtk.HBox()
		switch = Gtk.Switch()
		switch.connect("notify::active", self.on_server_switch, server_id)
		hbox.add(switch)
		self.server_switches[server_id] = switch
		switch.set_active(True)
		
		image = Gtk.Image.new_from_stock(Gtk.STOCK_EDIT, size=Gtk.IconSize.MENU)
		button = Gtk.Button(image=image)
		button.connect("clicked", self.on_server_edit, server_id)
		button.set_tooltip_text('Edit connection')
		hbox.add(button)
		right_table.attach(hbox, 0, 1, row, row+1, yoptions=Gtk.AttachOptions.SHRINK)
		row += 1
		
		image = Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE, size=Gtk.IconSize.MENU)
		button = Gtk.Button(image=image)
		button.set_tooltip_text('Remove server')
		button.connect("clicked", self.on_server_remove_clicked, server_id)
		hbox.add(button)
		
		info_expander = Gtk.Expander()
		info_expander.set_label("Infos")
		info_expander.set_expanded(True)
		right_table.attach(info_expander, 0, 1, row, row+1, yoptions=Gtk.AttachOptions.SHRINK)
		row += 1
		self.info_expanders[server_id] = info_expander
		self.init_info_table(server_id)
		
		gps_expander = Gtk.Expander()
		gps_expander.set_label("GPS Data")
		gps_expander.set_expanded(True)
		right_table.attach(gps_expander, 0, 1, row, row+1, yoptions=Gtk.AttachOptions.SHRINK)
		row += 1
		self.gps_expanders[server_id] = gps_expander
		self.init_gps_table(server_id)
		
		sources_expander = Gtk.Expander()
		sources_expander.set_label("Sources")
		sources_expander.set_expanded(True)
		right_table.attach(sources_expander, 0, 1, row, row+1, yoptions=Gtk.AttachOptions.SHRINK)
		row += 1
		self.sources_expanders[server_id] = sources_expander
		self.sources_tables[server_id] = None
		self.sources_table_sources[server_id] = {}
		right_scrolled.show_all()
		
	def init_info_table(self, server_id):
		table = Gtk.Table(n_rows=4, n_columns=2)
		row = 0
		
		server_host, server_port = self.config['kismet']['servers'][server_id].split(':')
		label = Gtk.Label(label="Host: ")
		label.set_alignment(xalign=0, yalign=0)
		table.attach(label, 0, 1, row, row+1)
		value_label = Gtk.Label(label="%s" % server_host)
		value_label.set_alignment(xalign=0, yalign=0)
		table.attach(value_label, 1, 2, row, row+1)
		row += 1
		
		label = Gtk.Label(label="Port: ")
		label.set_alignment(xalign=0, yalign=0)
		table.attach(label, 0, 1, row, row+1)
		value_label = Gtk.Label(label="%s" % server_port)
		value_label.set_alignment(xalign=0, yalign=0)
		table.attach(value_label, 1, 2, row, row+1)
		row += 1
		
		networks_label = Gtk.Label(label="Networks: ")
		networks_label.set_alignment(xalign=0, yalign=0)
		table.attach(networks_label, 0, 1, row, row+1)
		
		networks_value_label = Gtk.Label()
		networks_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(networks_value_label, 1, 2, row, row+1)
		self.info_table_networks[server_id] = networks_value_label
		row += 1
		
		packets_label = Gtk.Label(label="Packets: ")
		packets_label.set_alignment(xalign=0, yalign=0)
		table.attach(packets_label, 0, 1, row, row+1)
		
		packets_value_label = Gtk.Label()
		packets_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(packets_value_label, 1, 2, row, row+1)
		self.info_table_packets[server_id] = packets_value_label
		row += 1
		
		table.show_all()
		self.info_table = table
		self.info_expanders[server_id].add(self.info_table)
		
	def update_info_table(self, server_id, data):
		self.info_table_networks[server_id].set_text("%s" % data["networks"])
		self.info_table_packets[server_id].set_text("%s" % data["packets"])
	
	def init_gps_table(self, server_id):
		table = Gtk.Table(n_rows=3, n_columns=2)
		
		fix_label = Gtk.Label(label="Fix: ")
		fix_label.set_alignment(xalign=0, yalign=0)
		table.attach(fix_label, 0, 1, 0, 1)
		
		fix_value_label = Gtk.Label()
		fix_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(fix_value_label, 1, 2, 0, 1)
		self.gps_table_fix[server_id] = fix_value_label
		
		lat_label = Gtk.Label(label="Latitude: ")
		lat_label.set_alignment(xalign=0, yalign=0)
		table.attach(lat_label, 0, 1, 1, 2)
		
		lat_value_label = Gtk.Label()
		lat_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(lat_value_label, 1, 2, 1, 2)
		self.gps_table_lat[server_id] = lat_value_label
		
		lon_label = Gtk.Label(label="Longitude: ")
		lon_label.set_alignment(xalign=0, yalign=0)
		table.attach(lon_label, 0, 1, 2, 3)
		
		lon_value_label = Gtk.Label()
		lon_value_label.set_alignment(xalign=0, yalign=0)
		table.attach(lon_value_label, 1, 2, 2, 3)
		self.gps_table_lon[server_id] = lon_value_label
		
		table.show_all()
		self.gps_table = table
		self.gps_expanders[server_id].add(self.gps_table)
		
	def update_gps_table(self, server_id, data):
		if data["fix"] == -1:
			data["fix"] = "None"
		elif data["fix"] == 2:
			data["fix"] = "2D"
		elif data["fix"] == 3:
			data["fix"] = "3D"
		
		self.gps_table_fix[server_id].set_text("%s" % data["fix"])
		self.gps_table_lat[server_id].set_text("%s" % data["lat"])
		self.gps_table_lon[server_id].set_text("%s" % data["lon"])
		
	def init_sources_table(self, server_id, sources):
		self.sources_table_sources[server_id] = {}
		if self.sources_tables[server_id] is not None:
			self.sources_expanders[server_id].remove(self.sources_tables[server_id])
			
		table = Gtk.Table(n_rows=(len(sources)*5-1), n_columns=2)
		for uuid in sources:
			self.init_sources_table_source(server_id, sources[uuid], table)
		
		table.show_all()
		self.sources_tables[server_id] = table
		self.sources_expanders[server_id].add(table)
	
	def init_sources_table_source(self, server_id, source, table):
		self.sources_table_sources[server_id][source["uuid"]] = {}
		
		rows = []
		if len(self.sources_table_sources[server_id]) != 1:
			rows.append((None, None))
		rows.append((source["username"], ""))
		rows.append(("Type", source["type"]))
		rows.append(("Channel", source["channel"]))
		rows.append(("Packets", source["packets"]))
		
		row = len(self.sources_table_sources[server_id]) * 5
		for title, value in rows:
			if title is not None:
				label = Gtk.Label(label="%s: "%title)
				label.set_alignment(xalign=0, yalign=0)
				table.attach(label, 0, 1, row, row+1)
			
			label = Gtk.Label(label=value)
			label.set_alignment(xalign=0, yalign=0)
			table.attach(label, 1, 2, row, row+1)
			self.sources_table_sources[server_id][source["uuid"]][title] = label
			row += 1
			
	def update_sources_table(self, server_id, sources):
		for source in sources:
			if source not in self.sources_table_sources:
				self.init_sources_table(server_id, sources)
				break
			
		for uuid in sources:
			source = sources[uuid]
			sources_table_source = self.sources_table_sources[server_id][uuid]
			sources_table_source["Type"].set_text("%s" % source["type"])
			sources_table_source["Channel"].set_text("%s" % source["channel"])
			sources_table_source["Packets"].set_text("%s" % source["packets"])
		
	def on_server_edit(self, widget, server_id):
		dialog = Gtk.Dialog("Connect", parent=self.gtkwin)
		entry = Gtk.Entry()
		entry.set_text(self.config["kismet"]["servers"][server_id])
		dialog.add_action_widget(entry, 1)
		dialog.add_button(Gtk.STOCK_CONNECT, 1)
		dialog.show_all()
		dialog.run()
		server = entry.get_text()
		dialog.destroy()
		self.config["kismet"]["servers"][server_id] = server
		self.on_server_connect(None, server_id, True)
		
	def on_server_connect(self, widget, server_id, force_connect=False):
		if self.client_threads[server_id].is_running and not force_connect:
			return
		self.client_start(server_id)
		
	def on_server_disconnect(self, widget, server_id):
		if not self.client_threads[server_id].is_running:
			return
		self.client_stop(server_id)
		
	def on_server_switch(self, widget, data, server_id):
		if widget.get_active():
			self.on_server_connect(None, server_id)
		else:
			self.on_server_disconnect(None, server_id)
		
	def on_server_remove_clicked(self, widget, server_id):
		if self.server_notebook.get_n_pages() == 1:
			# last connection
			dialog = Gtk.Dialog("Info", parent=self.gtkwin)
			label = Gtk.Label("You can't remove the last connection!")
			area = dialog.get_content_area()
			area.add(label)
			dialog.add_button(Gtk.STOCK_CANCEL, 1)
			dialog.show_all()
			dialog.run()
			dialog.destroy()
			return
		
		# HBox -> Table -> Viewport -> ScrolledWindow
		table = self.server_switches[server_id].get_parent().get_parent().get_parent().get_parent()
		page_num = self.server_notebook.page_num(table)
		self.server_notebook.remove_page(page_num)
		self.client_stop(server_id)
		self.config['kismet']['servers'][server_id] = None
		
	def on_add_server_clicked(self, widget):
		server_id = len(self.client_threads)
		print("adding server", server_id+1)
		self.config['kismet']['servers'].append("server%s:2501" % (server_id+1))
		self.client_start(server_id)
		self.init_server_tab(server_id)
		
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
			page_num = self.notebook.page_num(map_widget)
			self.notebook.set_tab_label_text(map_widget, "Map")
			map_widget.show_all()
			self.map.set_last_from_config()
			self.notebook.set_current_page(page_num)
		else:
			page = self.notebook.page_num(map_widget)
			if page >= 0:
				self.notebook.remove_page(page)
			
	def on_about_dialog(self, widget):
		dialog = Gtk.AboutDialog()
		dialog.set_program_name("Kismon")
		dialog.set_version("0.7")
		dialog.set_comments('PyGTK based kismet client')
		dialog.set_website('http://www.salecker.org/software/kismon/en')
		dialog.set_copyright("(c) 2010-2015 Patrick Salecker")
		dialog.run()
		dialog.destroy()
		
	def on_window_state(self,window, event):
		if event.new_window_state == Gdk.WindowState.MAXIMIZED:
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
		
	def on_file_import(self, widget):
		file_import_window = FileImportWindow(self.networks, self.networks_queue_progress)
		file_import_window.gtkwin.set_transient_for(self.gtkwin)
		file_import_window.gtkwin.set_modal(True)
		
	def on_file_export(self, widget, export_format, extension, amount):
		dialog = Gtk.FileChooserDialog(title="Export as %s" % (export_format),
			parent=self.gtkwin, action=Gtk.FileChooserAction.SAVE)
		dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
		dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		dialog.set_do_overwrite_confirmation(True)
		dialog.set_current_name("kismon.%s" % extension)
		
		filename = False
		if dialog.run() == Gtk.ResponseType.OK:
			filename = dialog.get_filename()
		dialog.destroy()
		if filename == False:
			return
		
		if amount == "Filtered":
			networks = []
			for mac in self.export_networks:
				if self.export_networks[mac] is True:
					networks.append(mac)
		else:
			networks = None
		
		self.networks.export_networks(export_format, filename, networks)
		
	def export_add_network(self, mac):
		self.export_networks[mac] = True
		
	def export_remove_network(self, mac):
		self.export_networks[mac] = False
		
	def update_statusbar(self):
		if self.map is not None:
			on_map = len(self.map.markers)
		else:
			on_map = 0
		
		text = "Networks: %s in the current session, %s total, %s in the network list, %s on the map" % \
			(len(self.networks.recent_networks), len(self.networks.networks), len(self.network_list.network_iter), on_map)
		self.statusbar.push(self.statusbar_context, text)
		
	def on_channel_config(self, widget, server_id):
		win = ChannelWindow(self.sources[server_id], self.client_threads[server_id])
		
class LogList:
	def __init__(self, config):
		self.rows = []
		self.config = config
		self.treeview = Gtk.TreeView()
		num=0
		for column in ("Time", "From", "Message"):
			tvcolumn = Gtk.TreeViewColumn(column)
			self.treeview.append_column(tvcolumn)
			cell = Gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			tvcolumn.set_sort_column_id(num)
			tvcolumn.set_clickable(True)
			num += 1
		
		self.store = Gtk.ListStore(
			GObject.TYPE_STRING, #time
			GObject.TYPE_STRING, #origin
			GObject.TYPE_STRING, #message
			)
		self.treeview.set_model(self.store)
		
		log_scrolled = Gtk.ScrolledWindow()
		log_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		log_scrolled.set_shadow_type(Gtk.ShadowType.NONE)
		log_scrolled.add(self.treeview)
		
		self.widget = log_scrolled
		
	def add(self, origin, message):
		if not self.cleanup():
			return
		row = self.store.append([show_timestamp(time.time()), origin, message])
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
		
	def add_network(self, mac):
		network = self.networks.get_network(mac)
		try:
			crypt = self.crypt_cache[network["cryptset"]]
		except KeyError:
			crypt = decode_cryptset(network["cryptset"], True)
			self.crypt_cache[network["cryptset"]] = crypt
		
		if network["ssid"] == "":
			ssid_str = "<no ssid>"
		else:
			ssid_str = network["ssid"]
			
		if "signal_dbm" in network and len(network["signal_dbm"]) == 3:
			signal = network["signal_dbm"]["last"]
		else:
			signal = 0
		
		servers = []
		for server in network["servers"]:
			if server.endswith(':2501'):
				server = server.rsplit(':', 1)[0]
			servers.append(server)
		
		line = [mac,
				network["type"],
				ssid_str,
				network["channel"],
				crypt,
				show_timestamp(network["firsttime"]),
				show_timestamp(network["lasttime"]),
				network["lat"],
				network["lon"],
				signal,
				network['comment'],
				", ".join(servers),
				signal+100
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
		selected_text = self.network_lines[self.network_selected][self.column_selected]
		self.set_clipboard(selected_text)
		
	def on_copy_network(self, widget):
		text = []
		num = 0
		for column in self.columns:
			text.append("%s: %s" % (column, self.network_lines[self.network_selected][num]))
			num += 1
		self.set_clipboard('\n'.join(text))
		
	def set_clipboard(self, text):
		self.clipboard.set_text("%s" % text, -1)
		self.clipboard.store()

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
	try:
		from . import core
	except SystemError:
		import core
	core.main()
