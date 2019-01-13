import time
from gi.repository import Gtk
from gi.repository import GObject

import kismon.utils as utils


class LogList:
    def __init__(self, config):
        self.rows = []
        self.config = config
        self.treeview = Gtk.TreeView()
        num = 0
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
            GObject.TYPE_STRING,  # time
            GObject.TYPE_STRING,  # origin
            GObject.TYPE_STRING,  # message
        )
        self.treeview.set_model(self.store)

        log_scrolled = Gtk.ScrolledWindow()
        log_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_scrolled.set_shadow_type(Gtk.ShadowType.NONE)
        log_scrolled.add(self.treeview)

        self.widget = log_scrolled

    def add(self, origin, message, timestamp=time.time()):
        if not self.cleanup():
            return
        row = self.store.append([utils.format_timestamp(timestamp), origin, message])
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
