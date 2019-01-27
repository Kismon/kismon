import time

from gi.repository import Gtk
from gi.repository import GObject


class SignalWindow:
    def __init__(self, mac, destroy, seconds=120):
        self.mac = mac
        self.history = {}
        self.sources = {}
        self.time_range = seconds

        self.colors = [
            (0, 1, 0),
            (1, 0, 0),
            (0, 0, 1),
            (1, 1, 0),
            (0, 1, 1),
            (0, 0.5, 0),
            (0.5, 0, 0),
            (0, 0, 0.5),
        ]

        self.graph_type = "signal"

        self.gtkwin = Gtk.Window()
        self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
        self.gtkwin.connect("destroy", destroy, mac)
        self.gtkwin.set_default_size(620, 320)
        self.gtkwin.set_title("Signal Graph: %s" % self.mac)

        self.graph = Gtk.DrawingArea()
        self.graph.connect("draw", self.on_draw_event)

        button_box = Gtk.HButtonBox()

        signal_button = Gtk.RadioButton(label='Signal strength')
        signal_button.connect("clicked", self.on_graph_type, "signal")
        signal_button.clicked()
        button_box.add(signal_button)

        packets_button = Gtk.RadioButton(group=signal_button, label='Packets per second')
        packets_button.connect("clicked", self.on_graph_type, "packets")
        button_box.add(packets_button)

        self.sources_list = Gtk.TreeView()

        tvcolumn = Gtk.TreeViewColumn("Color")
        cell = Gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        cell.set_property('background-set', True)
        tvcolumn.set_attributes(cell, text=0, background=9)

        self.sources_list.append_column(tvcolumn)

        num = 1
        for column in ("Name", "Type", "Signal (dbm)", "Min", "Max", "Packets/sec", "Packets", "Server"):
            tvcolumn = Gtk.TreeViewColumn(column)
            self.sources_list.append_column(tvcolumn)
            cell = Gtk.CellRendererText()
            tvcolumn.pack_start(cell, True)
            tvcolumn.add_attribute(cell, 'text', num)
            num += 1

        self.sources_list_store = Gtk.ListStore(
            GObject.TYPE_STRING,
            GObject.TYPE_STRING,
            GObject.TYPE_STRING,
            GObject.TYPE_INT,
            GObject.TYPE_INT,
            GObject.TYPE_INT,
            GObject.TYPE_INT,
            GObject.TYPE_INT,
            GObject.TYPE_INT,  # server
            GObject.TYPE_STRING,  # bg color
        )
        self.sources_list.set_model(self.sources_list_store)

        expander = Gtk.Expander()
        expander.set_label("Sources")
        expander.set_expanded(True)
        expander.add(self.sources_list)

        vbox = Gtk.VBox()
        vbox.pack_start(button_box, expand=False, fill=False, padding=0)
        vbox.add(self.graph)
        vbox.pack_end(expander, expand=False, fill=False, padding=0)
        self.gtkwin.add(vbox)

        self.gtkwin.show_all()

    def on_graph_type(self, widget, graph_type):
        if not widget.get_active():
            return

        self.graph_type = graph_type
        self.graph.queue_draw()

    def on_draw_event(self, widget, context):
        width = self.graph.get_allocated_width()
        height = self.graph.get_allocated_height()
        self.draw_graph(width, height, context)

        for uuid in self.sources:
            source = self.sources[uuid]

            line = ['#', source["name"], source["type"],
                    source["signal"], source["signal_min"], source["signal_max"],
                    source["pps"], source["packets"], source["server"], self.get_color(uuid, return_hex=True)]
            if "iter" in source:
                source_iter = source["iter"]
                num = 0
                for value in line:
                    self.sources_list_store.set_value(source_iter, num, value)
                    num += 1
            else:
                source["iter"] = self.sources_list_store.append(line)

    def draw_graph(self, width, height, ctx):
        border_left = 60
        border_right = 0
        border_bottom = 30

        graph_width = width - border_left - border_right
        graph_height = height - border_bottom

        if self.graph_type == "signal":
            index = 0
            data_min = -100
            data_max = -50
            data_step = 5
            text = "%s dbm"
        else:
            index = 1
            data_min = 0
            data_max = 20
            data_step = 2
            text = "%s p/s"

        if len(self.history) > 0:
            start_sec = max(self.history) - self.time_range
        else:
            start_sec = 0
        x_rel = 1.0 * graph_width / self.time_range

        for sec in self.history:
            if sec < start_sec:
                continue

            for uuid in self.history[sec]:
                data_min = min(data_min, self.history[sec][uuid][index])
                data_max = max(data_max, self.history[sec][uuid][index])

        data_max += 1
        data_range = data_max - data_min
        y_rel = 1.0 * graph_height / data_range

        # background
        ctx.set_source_rgb(0, 0, 0)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        ctx.stroke()

        # legend
        ctx.set_line_width(1)
        ctx.set_source_rgb(1, 1, 1)

        ctx.move_to(border_left, 0)
        ctx.line_to(border_left, graph_height + 5)
        ctx.move_to(border_left - 5, graph_height)
        ctx.line_to(width - border_right, height - border_bottom)
        ctx.line_to(width - border_right, 0)

        ctx.move_to(border_left - 55, graph_height + 4)
        ctx.show_text(text % data_min)

        while True:
            r = range(data_min, data_max, data_step)
            if len(r) > 6:  # max. 6 horizontal lines
                data_step = data_step * 2
            else:
                break

        for value in r:
            y = y_rel * (data_max - value)
            ctx.move_to(border_left - 5, y)
            ctx.line_to(width - border_right, y)
            ctx.move_to(border_left - 55, y + 4)
            ctx.show_text(text % value)

        ctx.move_to(border_left - 15, graph_height + 16)
        ctx.show_text("-%ss" % self.time_range)
        ctx.move_to(border_left + graph_width / 2, graph_height + 1)
        ctx.line_to(border_left + graph_width / 2, graph_height + 6)
        ctx.move_to(border_left + graph_width / 2 - 12, graph_height + 16)
        ctx.show_text("-%ss" % (self.time_range / 2))

        ctx.stroke()

        # graph
        ctx.set_line_width(2)
        ctx.set_source_rgb(0, 1, 0)

        if len(self.history) < 2:
            ctx.move_to(width / 2, height / 2)
            ctx.show_text("collecting data")
            ctx.stroke()
            return False

        for uuid in self.sources:
            start = False
            sec = 0

            color = self.get_color(uuid)
            ctx.set_source_rgb(*color)

            while True:
                if start_sec + sec in self.history and uuid in self.history[start_sec + sec]:
                    value = self.history[start_sec + sec][uuid][index]
                    x = x_rel * sec + border_left
                    y = y_rel * (data_max - value)
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

    def get_color(self, uuid, return_hex=False):
        try:
            color = self.colors[self.sources[uuid]["number"]]
        except ValueError:
            color = (1, 1, 1)

        if return_hex:
            color = "#%0.2X%0.2X%0.2X" % (color[0] * 255, color[1] * 255, color[2] * 255)

        return color

    def add_value(self, source_data, packets, signal, timestamp, server_id):
        uuid = "%i-%s" % (server_id, source_data["uuid"])
        if uuid not in self.sources:
            self.sources[uuid] = source_data
            source = source_data
            source["number"] = len(self.sources) - 1
            source["server"] = server_id + 1
            source["signal"] = signal
            source["signal_min"] = signal
            source["signal_max"] = signal
            source["packets"] = packets
            source["pps"] = 0
        else:
            source = self.sources[uuid]
            source["signal"] = signal
            source["signal_min"] = min(signal, source["signal_min"])
            source["signal_max"] = max(signal, source["signal_max"])
            source["pps"] = packets - source["packets"]
            source["packets"] = packets

        if timestamp not in self.history:
            self.history[timestamp] = {}
        self.history[timestamp][uuid] = (signal, source["pps"])
        self.graph.queue_draw()
