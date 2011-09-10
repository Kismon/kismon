import os

import gtk

class ConfigWindow:
	def __init__(self, main_window):
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.connect("destroy", self.on_destroy)
		self.gtkwin.set_size_request(640, 320)
		self.gtkwin.set_title("Kismon Preferences")
		self.main_window = main_window
		self.config = main_window.config
		self.map = main_window.map
		
		self.notebook = gtk.Notebook()
		self.gtkwin.add(self.notebook)
		
		general_page = gtk.Table(rows=2, columns=1)
		self.notebook.append_page(general_page)
		self.notebook.set_tab_label_text(general_page, "General")
		self.init_general_page(general_page)
		
		map_page = gtk.Table(rows=2, columns=1)
		self.notebook.append_page(map_page)
		self.notebook.set_tab_label_text(map_page, "Map")
		
		if self.map is None:
			label = gtk.Label("Map disabled")
			map_page.attach(label, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		else:
			self.init_map_page(map_page)
		
		self.gtkwin.show_all()
		
	def init_general_page(self, page):
		frame = gtk.Frame("Log List")
		page.attach(frame, 0, 1, 0, 1, yoptions=gtk.SHRINK)
		vbox = gtk.VBox()
		frame.add(vbox)
		hbox = gtk.HBox()
		vbox.add(hbox)
		
		label = gtk.Label("Max rows in the log list: ")
		label.set_alignment(xalign=0, yalign=0.5)
		label.set_justify(gtk.JUSTIFY_RIGHT)
		hbox.pack_start(label, False, False, 5)
		
		field = gtk.SpinButton()
		field.set_numeric(True)
		field.set_max_length(5)
		field.set_increments(1,100)
		field.set_range(-1,99999)
		field.set_value(self.config["window"]["log_list_max"])
		field.connect("output", self.on_change_log_list_max)
		hbox.pack_start(field, False, False, 5)
		
		label = gtk.Label("-1 = unlimited 0 = disable")
		label.set_alignment(xalign=0, yalign=0.5)
		hbox.pack_start(label, False, False, 5)
		
		frame = gtk.Frame("Autosave")
		page.attach(frame, 0, 1, 1, 2, yoptions=gtk.SHRINK)
		vbox = gtk.VBox()
		frame.add(vbox)
		hbox = gtk.HBox()
		vbox.add(hbox)
		label = gtk.Label("Save the networks every (in minutes):")
		hbox.pack_start(label, False, False, 5)
		
		field = gtk.SpinButton()
		field.set_numeric(True)
		field.set_max_length(5)
		field.set_increments(1,100)
		field.set_range(0,99999)
		field.set_value(self.config["networks"]["autosave"])
		field.connect("output", self.on_change_autosave)
		hbox.pack_start(field, False, False, 5)
		
		label = gtk.Label("0 = disable")
		label.set_alignment(xalign=0, yalign=0.5)
		hbox.pack_start(label, False, False, 5)
		
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
		
		first = None
		for name, source in (("Openstreetmap (default)", "openstreetmap"),
				("Openstreetmap Renderer", "openstreetmap-renderer"),
				("Custom tile source", "custom")):
			map_source = gtk.RadioButton(first, name)
			if first is None:
				first = map_source
			
			if self.config["map"]["source"] == source:
				map_source.clicked()
			map_source.connect("clicked", self.on_map_source, source)
			source_vbox.add(map_source)
		
		hbox = gtk.HBox()
		source_vbox.add(hbox)
		
		label = gtk.Label("     URL: ")
		label.set_alignment(xalign=0, yalign=0.5)
		label.set_justify(gtk.JUSTIFY_LEFT)
		hbox.pack_start(label, False, False, 5)
		
		entry = gtk.Entry()
		entry.set_width_chars(50)
		entry.set_text(self.config["map"]["custom_source_url"])
		entry.connect("changed", self.on_change_map_source_custom_url)
		hbox.pack_start(entry, False, False, 5)
		
		hbox = gtk.HBox()
		source_vbox.add(hbox)
		
		x=1
		for name in ("     Zoom Levels: ", " - "):
			label = gtk.Label(name)
			label.set_alignment(xalign=0, yalign=0.5)
			label.set_justify(gtk.JUSTIFY_LEFT)
			hbox.pack_start(label, False, False, 5)
			
			field = gtk.SpinButton()
			field.set_numeric(True)
			field.set_max_length(5)
			field.set_increments(1,3)
			field.set_range(1,18)
			if x == 1:
				name = "custom_source_min"
			else:
				name = "custom_source_max"
			field.set_value(self.config["map"][name])
			field.connect("output", self.on_change_map_source_custom_zoom, name)
			hbox.pack_start(field, False, False, 5)
			x += 1
		
		apply_button = gtk.Button(stock=gtk.STOCK_APPLY)
		apply_button.connect("clicked", self.on_map_source, "custom")
		hbox.pack_start(apply_button, False, False, 5)
		
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
		
	def on_map_source(self, widget, source):
		if (type(widget) == gtk.RadioButton and widget.get_active()) or type(widget) == gtk.Button:
			self.map.set_source(source)
			if self.config["window"]["map_position"] == "widget":
				self.main_window.on_map_widget(None, True)
			elif self.config["window"]["map_position"] == "window":
				self.main_window.map_window.gtkwin.add(self.main_window.map.widget)
				self.main_window.map_window.gtkwin.show_all()
		
	def on_change_map_source_custom_url(self, widget):
		print widget.get_text()
		self.config["map"]["custom_source_url"] = widget.get_text()
		
	def on_change_map_source_custom_zoom(self, widget, name):
		print name, int(widget.get_value())
		self.config["map"][name] = int(widget.get_value())
		
	def on_update_marker_positions(self, widget):
		self.config["map"]["update_marker_positions"] = widget.get_active()
		
