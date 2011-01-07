import time

import gtk
import gobject

class SignalWindow:
	def __init__(self, mac, destroy):
		self.mac = mac
		self.history = {}
		self.sources = {}
		self.time_range = 60 * 2
		
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
		
		self.gtkwin = gtk.Window()
		self.gtkwin.set_position(gtk.WIN_POS_CENTER)
		self.gtkwin.connect("destroy", destroy, mac)
		self.gtkwin.set_default_size(620, 320)
		self.gtkwin.set_title("Signal Graph: %s" % self.mac)
		
		self.graph = gtk.DrawingArea()
		self.graph.connect("expose_event", self.on_expose_event)
		
		button_box = gtk.HButtonBox()
		
		signal_button = gtk.RadioButton(None, 'Signal strength')
		signal_button.connect("clicked", self.on_graph_type, "signal")
		signal_button.clicked()
		button_box.add(signal_button)
		
		packets_button = gtk.RadioButton(signal_button, 'Packets per second')
		packets_button.connect("clicked", self.on_graph_type, "packets")
		button_box.add(packets_button)
		
		self.sources_list = gtk.TreeView()
		
		tvcolumn = gtk.TreeViewColumn("Color")
		pixbuf = gtk.CellRendererPixbuf()
		tvcolumn.pack_start(pixbuf)
		tvcolumn.add_attribute(pixbuf, "pixbuf", 0)
		self.sources_list.append_column(tvcolumn)
		
		num=1
		for column in ("Name", "Type", "Signal (dbm)", "Min", "Max", "Packets/sec", "Packets"):
			tvcolumn = gtk.TreeViewColumn(column)
			self.sources_list.append_column(tvcolumn)
			cell = gtk.CellRendererText()
			tvcolumn.pack_start(cell, True)
			tvcolumn.add_attribute(cell, 'text', num)
			num += 1
		
		self.sources_list_store = gtk.ListStore(
			gtk.gdk.Pixbuf,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_INT,
			gobject.TYPE_INT,
			gobject.TYPE_INT,
			gobject.TYPE_INT,
			gobject.TYPE_INT,
			)
		self.sources_list.set_model(self.sources_list_store)
		
		expander = gtk.Expander("Sources")
		expander.set_expanded(True)
		expander.add(self.sources_list)
		
		vbox = gtk.VBox()
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
		
	def on_expose_event(self, widget, event):
		width = event.area.width
		height = event.area.height
		self.draw_graph(width, height)
		
		for uuid in self.sources:
			source = self.sources[uuid]
			
			line = [source["username"], source["type"],
				source["signal"], source["signal_min"], source["signal_max"],
				source["pps"], source["packets"]]
			if "iter" in source:
				source_iter = source["iter"]
				num = 1
				for value in line:
					self.sources_list_store.set_value(source_iter, num, value)
					num += 1
			else:
				width = 36
				height = 12
				
				pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
				drawable = gtk.gdk.Pixmap(None, width, height, 24)
				ctx = drawable.cairo_create()
				color = self.get_color(uuid)
				ctx.set_source_rgb(*color)
				ctx.rectangle(0, 0, width, height)
				ctx.fill()
				ctx.stroke()
				cmap = gtk.gdk.colormap_get_system()
				pixbuf.get_from_drawable(drawable, cmap, 0, 0, 0, 0, width, height)
				line.insert(0, pixbuf)
				source["iter"] = self.sources_list_store.append(line)
		
	def draw_graph(self, width, height):
		ctx=self.graph.window.cairo_create()
		
		border_left = 60
		border_right = 0
		border_bottom = 30
		
		graph_width = width - border_left - border_right
		graph_height = height - border_bottom
		
		if self.graph_type == "signal":
			index = 0
			data_min = -100
			data_max = -50
			text = "%s dbm"
		else:
			index = 1
			data_min = 0
			data_max = 20
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
		ctx.line_to(width - border_right, height - border_bottom)
		ctx.line_to(width - border_right, 0)
		
		ctx.move_to(border_left - 55, graph_height + 4)
		ctx.show_text(text % data_min)
		
		value = (int((data_min + 2) / 10)) * 10
		while True:
			value += int(float(data_range) / 6)
			if value >= data_max:
				break
			
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
		
		#graph
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
		
	def get_color(self, uuid):
		try:
			color = self.colors[self.sources[uuid]["number"]]
		except ValueError:
			color = (1, 1, 1)
		return color
		
	def add_value(self, source_data, bssidsrc, value):
		if source_data is None:
			source_data = {"username": "signal", "type": "all", "uuid": "all"}
		if source_data["uuid"] not in self.sources:
			self.sources[source_data["uuid"]] = source_data
			source = source_data
			source["number"] = len(self.sources) - 1
			source["signal"] = value
			source["signal_min"] = value
			source["signal_max"] = value
			if bssidsrc is None:
				source["packets"] = 0
				source["pps"] = 0
			else:
				source["packets"] = bssidsrc["numpackets"]
				source["pps"] = 0
		else:
			source = self.sources[source_data["uuid"]]
			source["signal"] = value
			source["signal_min"] = min(value, source["signal_min"])
			source["signal_max"] = max(value, source["signal_max"])
			if bssidsrc is not None:
				source["pps"] = bssidsrc["numpackets"] - source["packets"]
				source["packets"] = bssidsrc["numpackets"]
				
		sec = int(time.time())
		if sec not in self.history:
			self.history[sec] = {}
		self.history[sec][source["uuid"]] = (value, source["pps"])
		self.graph.queue_draw()
