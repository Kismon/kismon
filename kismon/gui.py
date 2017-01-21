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
	from .widgets import *
	import kismon.utils as utils
except SystemError:
	from client import Client, decode_cryptset
	from windows import *
	from widgets import *
	import utils

import time
import os
import sys

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib

class MainWindow(TemplateWindow):
	def __init__(self, config, client_start, client_stop, map, networks, sources, tracks, client_threads):
		TemplateWindow.__init__(self)
		self.config = config
		self.config_window = None
		self.progress_bar_win = None
		self.client_start = client_start
		self.client_stop = client_stop
		self.networks = networks
		self.map = map
		self.tracks = tracks

		if map is not None:
			self.locate_marker = map.locate_marker
		else:
			self.locate_marker = None
		
		self.export_networks = {}
		self.networks.notify_add_list["export"] = self.export_add_network
		self.networks.notify_remove_list["export"] = self.export_remove_network
		
		self.network_list = NetworkList(self.networks, self.locate_marker, self.on_signal_graph)
		
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
		vpaned_main.set_position(400)
		vbox.add(vpaned_main)
		hbox = Gtk.HBox()
		vpaned_main.add1(hbox)
		hbox.pack_start(self.network_list.widget, expand=True, fill=True, padding=0)
		
		self.server_notebook = Gtk.Notebook()
		frame = Gtk.Frame()
		frame.set_label("Servers")
		frame.add(self.server_notebook)
		hbox.pack_end(frame, expand=False, fill=False, padding=2)
		
		image = Gtk.Image.new_from_icon_name('list-add', Gtk.IconSize.MENU)
		button = Gtk.Button()
		button.props.focus_on_click = False
		button.add(image)
		button.show_all()
		button.set_tooltip_text('Add server')
		button.connect("clicked", self.on_add_server_clicked)
		self.server_notebook.set_action_widget(button, Gtk.PackType.END)
		
		self.server_tabs = {}
		for server_id in self.client_threads:
			self.add_server_tab(server_id)
		
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
		
		for crypt in ("None", "WEP", "WPA", "WPA2", "Other"):
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
			self.progress_bar.set_show_text(True)
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
		
	def add_server_tab(self, server_id):
		self.server_tabs[server_id] = ServerTab(server_id, self.map, self.config, self.client_threads, self.client_start, self.client_stop, self.set_server_tab_label, self.on_server_remove_clicked)
		self.server_notebook.append_page(self.server_tabs[server_id].widget)
		self.server_tabs[server_id].set_active()
		
	def set_server_tab_label(self, server_id, icon, tooltip):
		table = self.get_server_tab_widget(server_id)
		hbox = Gtk.HBox()
		label = Gtk.Label()
		image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
		image.set_tooltip_text(tooltip)
		hbox.add(label)
		hbox.add(image)
		hbox.show_all()
		label.set_text("%s " % (server_id + 1))
		label.set_tooltip_text(tooltip)
		notebook = table.get_parent()
		notebook.set_tab_label(table, hbox)
		
	def get_server_tab_widget(self, server_id):
		return self.server_tabs[server_id].widget
		
	def on_server_remove_clicked(self, widget, server_id):
		if self.server_notebook.get_n_pages() == 1:
			# last connection
			dialog = Gtk.Dialog("Info", parent=self.gtkwin)
			label = Gtk.Label("You can't remove the last connection!")
			area = dialog.get_content_area()
			area.add(label)
			dialog.add_button('gtk-cancel', 1)
			dialog.show_all()
			dialog.run()
			dialog.destroy()
			return
		
		table = self.get_server_tab_widget(server_id)
		page_num = self.server_notebook.page_num(table)
		self.server_notebook.remove_page(page_num)
		self.client_stop(server_id)
		self.config['kismet']['servers'][server_id] = None
		self.map.remove_track(server_id)
		self.map.remove_marker("server%s" % (server_id + 1))
		
	def on_add_server_clicked(self, widget):
		server_id = len(self.client_threads)
		print("adding server", server_id+1)
		self.config['kismet']['servers'].append("server%s:2501" % (server_id+1))
		self.client_start(server_id)
		self.add_server_tab(server_id)
		
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
			if self.config["window"]["map_position"] == "widget" and self.notebook.page_num(map_widget) != -1:
				# the widget is already attached
				return
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
		dialog.set_version(utils.get_version())
		dialog.set_comments('PyGTK based kismet client')
		dialog.set_website('https://www.salecker.org/software/kismon.html')
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
		dialog.add_button('gtk-save', Gtk.ResponseType.OK)
		dialog.add_button('gtk-cancel', Gtk.ResponseType.CANCEL)
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
			filtered = True
		else:
			networks = None
			filtered = False

		self.networks.export_networks(export_format, filename, networks, self.tracks, filtered)

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

if __name__ == "__main__":
	try:
		from . import core
	except SystemError:
		import core
	core.main()
