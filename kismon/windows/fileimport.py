import os
import sys

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject


class FileImportWindow:
    def __init__(self, networks, networks_queue_progress):
        self.networks = networks
        self.networks_queue_progress = networks_queue_progress
        self.files = {}
        self.parser_queue = ()
        self.gtkwin = Gtk.Window()
        self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
        self.gtkwin.set_default_size(700, 300)
        self.gtkwin.set_title("Kismon: File Import")
        self.gtkwin.set_border_width(5)

        self.main_box = Gtk.VBox()

        self.file_list = Gtk.VBox()
        file_list_scroll = Gtk.ScrolledWindow()
        file_list_scroll.add(self.file_list)
        file_list_scroll.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)
        file_list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.main_box.add(file_list_scroll)

        button_box = Gtk.HBox()
        add_file_button = Gtk.Button.new_with_label("Add files")
        add_file_button.connect("clicked", self.on_add, "file")
        button_box.pack_start(add_file_button, expand=False, fill=False, padding=0)
        add_dir_button = Gtk.Button.new_with_label("Add directories")
        add_dir_button.connect("clicked", self.on_add, "dir")
        button_box.pack_start(add_dir_button, expand=False, fill=False, padding=0)
        self.start_button = Gtk.Button.new_with_label("Start")
        self.start_button.connect("clicked", self.on_start)
        button_box.pack_end(self.start_button, expand=False, fill=False, padding=0)

        self.main_box.pack_end(button_box, expand=False, fill=True, padding=0)
        self.gtkwin.add(self.main_box)
        self.gtkwin.show_all()

    def create_file_chooser(self, add_type):
        if add_type == "dir":
            action = Gtk.FileChooserAction.SELECT_FOLDER
        else:
            action = Gtk.FileChooserAction.OPEN
        dialog = Gtk.FileChooserDialog(title="", action=action)
        dialog.set_transient_for(self.gtkwin)
        dialog.add_button('gtk-cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('gtk-open', Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)

        if add_type == "file":
            filter = Gtk.FileFilter()
            filter.set_name("All supported files")
            filter.add_pattern("*.netxml")
            filter.add_pattern("*.csv")
            filter.add_pattern("*.json")
            dialog.add_filter(filter)

            filter = Gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            dialog.add_filter(filter)

        return dialog

    def on_add(self, widget, add_type):
        dialog = self.create_file_chooser(add_type)

        response = dialog.run()
        filenames = dialog.get_filenames()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
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
        table = Gtk.Table(n_columns=2)
        self.files[filename] = {}
        self.files[filename]["type"] = "unknown"

        combobox = Gtk.ComboBoxText()
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
        table.attach(combobox, 0, 1, 0, 1, yoptions=Gtk.AttachOptions.SHRINK, xoptions=Gtk.AttachOptions.SHRINK)

        label = Gtk.Label(label=filename)
        label.set_property("xalign", 0)
        label.set_property("yalign", 0.5)
        table.attach(label, 1, 2, 0, 1, yoptions=Gtk.AttachOptions.SHRINK, xpadding=5)

        button = Gtk.Button()
        image = Gtk.Image.new_from_icon_name('gtk-delete', size=Gtk.IconSize.MENU)
        button.set_image(image)
        button.connect("clicked", self.on_remove_file, filename)
        table.attach(button, 2, 3, 0, 1, yoptions=Gtk.AttachOptions.SHRINK, xoptions=Gtk.AttachOptions.SHRINK)

        frame = Gtk.Frame()
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
        main_box = Gtk.VBox()
        self.gtkwin.add(main_box)

        self.file_list = Gtk.TreeView()
        num = 0
        for column in ("File", "Type", "Networks", "New", "Status"):
            tvcolumn = Gtk.TreeViewColumn(column)
            self.file_list.append_column(tvcolumn)
            cell = Gtk.CellRendererText()
            tvcolumn.pack_start(cell, True)
            tvcolumn.add_attribute(cell, 'text', num)
            num += 1

        self.file_list_treestore = Gtk.ListStore(
            GObject.TYPE_STRING,  # filename
            GObject.TYPE_STRING,  # filetype
            GObject.TYPE_INT,  # networks
            GObject.TYPE_INT,  # new
            GObject.TYPE_STRING  # status
        )
        self.file_list.set_model(self.file_list_treestore)

        file_scrolled = Gtk.ScrolledWindow()
        file_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        file_scrolled.set_shadow_type(Gtk.ShadowType.NONE)
        file_scrolled.add(self.file_list)
        main_box.add(file_scrolled)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_text("0 of %s Files" % len(self.files))
        self.progress_bar.set_fraction(0)
        main_box.pack_start(self.progress_bar, expand=False, fill=True, padding=0)

        button_box = Gtk.VButtonBox()
        self.close_button = Gtk.Button(label="Finish")
        self.close_button.connect("clicked", self.on_close)
        self.close_button.set_sensitive(False)
        button_box.add(self.close_button)

        main_box.pack_end(button_box, expand=False, fill=True, padding=0)
        self.gtkwin.show_all()
        self.parser_queue = list(self.files.keys())
        if len(self.parser_queue) == 0:
            self.close_button.set_sensitive(True)
        else:
            self.networks.block_queue_start = True
            GLib.idle_add(self.parse_file)

    def parse_file(self):
        filename = self.parser_queue.pop()
        filetype = self.files[filename]["filetype"]
        print("Reading %s" % filename)
        num_new = 0 - len(self.networks.networks)
        if filetype != "unknown":
            try:
                num_networks = self.networks.import_networks(filetype, filename)
                status = "done"
            except:
                status = "failed"
                num_networks = 0
                print("%s: %s" % (filename, sys.exc_info()[1]))
        else:
            num_networks = 0
            status = "skiped"

        num_new = num_new + len(self.networks.networks)

        self.file_list_treestore.append([filename, filetype, num_networks, num_new, status])

        num_files = len(self.files)
        pos = num_files - len(self.parser_queue)

        self.progress_bar.set_text("%s of %s Files" % (pos, num_files))
        self.progress_bar.set_fraction(1.0 / num_files * pos)

        print("Parsing done")
        if len(self.parser_queue) == 0:
            self.close_button.set_sensitive(True)
        else:
            return True

    def on_close(self, widget):
        self.gtkwin.destroy()
        self.networks.block_queue_start = False
        self.networks.disable_refresh()
        self.networks.start_queue()
        self.networks_queue_progress()
