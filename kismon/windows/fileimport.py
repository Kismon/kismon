import os

import gtk
import gobject

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
		
		self.file_list = gtk.VBox()
		file_list_scroll = gtk.ScrolledWindow()
		file_list_scroll.add_with_viewport(self.file_list)
		file_list_scroll.get_children()[0].set_shadow_type(gtk.SHADOW_NONE)
		file_list_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
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
		
		self.progress_bar = gtk.ProgressBar()
		self.progress_bar.set_text("0 of %s Files" % len(self.files))
		self.progress_bar.set_fraction(0)
		main_box.pack_start(self.progress_bar, expand=False, fill=True, padding=0)
		
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
		
		self.progress_bar.set_text("%s of %s Files" % (pos, num_files))
		self.progress_bar.set_fraction(1.0 / num_files * pos)
		
		if len(self.parser_queue) == 0:
			self.close_button.set_sensitive(True)
		else:
			return True
		
	def on_close(self, widget):
		self.gtkwin.destroy()
