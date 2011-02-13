import os

import gtk

class ConfigWindow:
	def __init__(self, main_window):
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.connect("destroy", self.on_destroy)
		self.gtkwin.set_size_request(640, 480)
		self.gtkwin.set_title("Kismon Preferences")
		self.main_window = main_window
		self.config = main_window.config
		self.map_widget = main_window.map_widget
		if self.map_widget is not None:
			self.map = self.map_widget.map
		
		self.notebook = gtk.Notebook()
		self.gtkwin.add(self.notebook)
		
		general_page = gtk.Table(rows=2, columns=1)
		self.notebook.append_page(general_page)
		self.notebook.set_tab_label_text(general_page, "General")
		self.init_general_page(general_page)
		
		map_page = gtk.Table(rows=2, columns=1)
		self.notebook.append_page(map_page)
		self.notebook.set_tab_label_text(map_page, "Map")
		
		if self.map_widget is None:
			label = gtk.Label("Map disabled")
			map_page.attach(label, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		else:
			self.init_map_page(map_page)
		
		self.gtkwin.show_all()
		
	def init_general_page(self, page):
		table = gtk.Table()
		page.attach(table, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		
		label = gtk.Label("<b>Log List</b>")
		label.set_use_markup(True)
		label.set_alignment(xalign=0, yalign=0)
		table.attach(label, 0, 1, 0, 1)
		
		label = gtk.Label("Max rows in the log list: ")
		label.set_alignment(xalign=0, yalign=0.5)
		label.set_justify(gtk.JUSTIFY_RIGHT)
		table.attach(label, 0, 1, 1, 2, xoptions=gtk.FILL)
		
		field = gtk.SpinButton()
		field.set_numeric(True)
		field.set_max_length(5)
		field.set_increments(1,100)
		field.set_range(-1,99999)
		field.set_value(self.config["window"]["log_list_max"])
		field.connect("output", self.on_change_log_list_max)
		table.attach(field, 1, 2, 1, 2, xoptions=gtk.SHRINK)
		
		label = gtk.Label("-1 = unlimited 0 = disable")
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, 2, 3)
		
		table.set_row_spacing(2,10)
		
		label = gtk.Label("<b>Autosave</b>")
		label.set_use_markup(True)
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, 3, 4)
		
		label = gtk.Label("Save the networks every (in minutes):")
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, 4, 5, xoptions=gtk.FILL)
		
		field = gtk.SpinButton()
		field.set_numeric(True)
		field.set_max_length(5)
		field.set_increments(1,100)
		field.set_range(0,99999)
		field.set_value(self.config["networks"]["autosave"])
		field.connect("output", self.on_change_autosave)
		table.attach(field, 1, 2, 4, 5, xoptions=gtk.SHRINK)
		
		label = gtk.Label("0 = disable")
		label.set_alignment(xalign=0, yalign=0.5)
		table.attach(label, 0, 1, 5, 6)
		
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
		
		memphis = self.main_window.map.memphis
		
		map_source_mapnik = gtk.RadioButton(None, 'OSM Mapnik (default)')
		
		if self.config["map"]["source"] == "osm-mapnik" or not memphis:
			map_source_mapnik.clicked()
		map_source_mapnik.connect("clicked", self.on_map_source_mapnik)
		source_vbox.add(map_source_mapnik)
		
		map_source_memphis = gtk.RadioButton(map_source_mapnik,
			'Memphis (local rendering)')
			
		if not memphis:
			map_source_memphis.set_sensitive(False)
		elif self.config["map"]["source"] == "memphis-local":
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
		if self.config["map"]["update_marker_positions"] is True:
			perf_marker_positions.clicked()
		perf_marker_positions.connect("clicked", self.on_update_marker_positions)
		perf_vbox.add(perf_marker_positions)
		
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
		
