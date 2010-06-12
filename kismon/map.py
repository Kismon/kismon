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

import gtk
import champlaingtk
import champlain
import clutter

import os

class Map:
	def __init__(self, config):
		self.config = config
		self.markers = {}
		self.marker_text = "%s\n<span size=\"small\">%s</span>"
		self.marker_font = "Serif 10"
		self.selected_marker = None
		self.next_position = None
		self.colors = {
			"red": clutter.Color(255, 0, 0, 187),
			"green": clutter.Color(0, 255, 0, 187),
			"orange":clutter.Color(243, 148, 7, 187),
			"black": clutter.Color(0, 0, 0, 255)
			}
		if os.path.isdir("/usr/share/kismon"):
			image_folder = "/usr/share/kismon/"
		else:
			image_folder = "..%sfiles%s" % (os.sep, os.sep)
		self.images = {
			"green": "%sopen.png" % image_folder,
			"orange": "%swep.png" % image_folder,
			"red": "%swpa.png" % image_folder,
			"position": "%sposition.png" % image_folder
			}
		
		self.marker_layer = champlain.Layer()
		self.init_position_marker()
		
		self.vbox = gtk.VBox()
		self.init_menu()
		
		self.embed = champlaingtk.ChamplainEmbed()
		self.embed.connect("button-press-event", self.on_map_pressed)
		self.embed.connect("button-release-event", self.on_map_released)
		self.vbox.add(self.embed)
		self.view = self.embed.get_view()
		self.view.add_layer(self.marker_layer)
		self.view.add_layer(self.position_layer)
		
		self.widget = self.vbox
		
	def init_position_marker(self):
		"""show a marker at the current position
		"""
		self.position_layer = champlain.Layer()
		self.position_marker = champlain.marker_new_from_file(self.images["position"])
		self.position_marker.set_draw_background(False)
		self.position_layer.add_marker(self.position_marker)
		
	def init_menu(self):
		hbox = gtk.HBox()
		self.vbox.pack_start(hbox, expand=False, fill=False, padding=0)
		
		button = gtk.Button(stock=gtk.STOCK_ZOOM_IN)
		button.connect("clicked", self.on_zoom_in)
		button.show()
		hbox.add(button)
		
		button = gtk.Button(stock=gtk.STOCK_ZOOM_OUT)
		button.connect("clicked", self.on_zoom_out)
		button.show()
		hbox.add(button)
		
		self.toggle_moving_button = gtk.ToggleButton("Follow GPS")
		self.toggle_moving_button.connect("clicked", self.on_toggle_moving)
		self.toggle_moving_button.show()
		self.toggle_moving_button.set_active(True)
		hbox.add(self.toggle_moving_button)
		
		label = gtk.Label("Marker style:")
		hbox.add(label)
		
		combobox = gtk.combo_box_new_text()
		combobox.connect("changed", self.on_change_marker_style)
		combobox.append_text('Names')
		combobox.append_text('Images')
		if self.config["map"]["markerstyle"] == "name":
			combobox.set_active(0)
		else:
			combobox.set_active(1)
		hbox.add(combobox)
		
	def set_zoom(self, zoom):
		self.view.set_property("zoom-level", zoom)
		
	def on_zoom_in(self, widget=None):
		self.view.zoom_in()
		
	def on_zoom_out(self, widget=None):
		self.view.zoom_out()
		
	def set_osm_file(self, filename):
		print "set_osm_file stub!",filename
		
	def set_position(self, lat, lon):
		if self.config["map"]["followgps"] is True:
			self.view.center_on(lat, lon)
		else:
			self.next_position = (lat, lon)
		
		self.position_marker.set_position(lat, lon)
		
	def add_marker(self, key, name, text, color, lat, lon):
		"""add a new marker to the marker_layer
		
		key: a unique key
		name: the name, shown when marker_style is 'name'
		text: shown after click on the marker
		color: a color from self.colors
		lat: latitude
		lon: longitude
		"""
		if key in self.markers:
			self.update_marker(key, name, text, lat, lon)
			return
		
		marker = champlain.Marker()
		marker.set_position(lat, lon)
		marker.set_use_markup(True)
		marker.set_reactive(True)
		marker.set_color(self.colors[color])
		marker.set_font_name(self.marker_font)
		marker.set_text_color(self.colors["black"])
		marker.set_name(name)
		marker.connect("button-press-event", self.on_marker_clicked)
		
		marker.long_text = text
		marker.color_name = color
		
		if self.selected_marker is not None:
			marker.hide()
		
		self.marker_layer.add_marker(marker)
		self.markers[key] = marker
		
		if self.config["map"]["markerstyle"] == "image":
			self.marker_style_image(marker)
		else:
			self.marker_style_name(marker)
		
	def update_marker(self, key, name, text, lat, lon):
		marker = self.markers[key]
		marker.set_position(lat, lon)
		marker.long_text = text
		marker.set_name(name)
		if self.config["map"]["markerstyle"] == "marker":
			marker.set_text(name)
	
	def on_marker_clicked(self, marker, event=None):
		"""hide all markers and create a new marker with the long text
		"""
		if self.selected_marker is None:
			text = self.marker_text % (marker.get_name(), marker.long_text)
			lat = marker.get_latitude()
			lon = marker.get_longitude()
			
			self.selected_marker = champlain.marker_new_with_text(text,
				self.marker_font, self.colors["black"], self.colors[marker.color_name])
			self.selected_marker.connect("button-press-event", self.on_marker_clicked)
			self.selected_marker.set_position(lat, lon)
			self.selected_marker.set_use_markup(True)
			self.selected_marker.set_reactive(True)
			self.marker_layer.hide_all_markers()
			self.marker_layer.add_marker(self.selected_marker)
			
		else:
			self.marker_layer.remove_marker(marker)
			self.selected_marker = None
			self.marker_layer.show_all_markers()
			
	def on_change_marker_style(self, widget):
		style = widget.get_active_text()
		self.config["map"]["markerstyle"] = style.lower()[:-1]
		
		if self.selected_marker is not None:
			self.on_marker_clicked(self.selected_marker)
		if self.config["map"]["markerstyle"] == "name":
			for key in self.markers:
				marker = self.markers[key]
				self.marker_style_name(marker)
		elif self.config["map"]["markerstyle"] == "image":
			for key in self.markers:
				marker = self.markers[key]
				self.marker_style_image(marker)
				
	def marker_style_name(self, marker):
		"""show the name on the map and remove the image
		"""
		marker.set_text(marker.get_name())
		marker.set_draw_background(True)
		#marker.set_image(None)
		#FIXME: set_image(None) is not fixed yet, so hide it
		for child in marker.get_children():
			if type(child) == clutter.Texture:
				child.hide()

	
	def marker_style_image(self, marker):
		"""show the image on the map and remove the text and background
		"""
		marker.set_draw_background(False)
		texture = clutter.texture_new_from_file(self.images[marker.color_name])
		marker.set_image(texture)
		marker.set_text(" ")
		
	def on_map_pressed(self, widget, event):
		"""disable set_position if the map is pressed
		"""
		if self.config["map"]["followgps"] is True:
			self.stop_moving()
		
	def on_map_released(self, widget, event):
		active = self.toggle_moving_button.get_active()
		if self.config["map"]["followgps"] is False and active is True:
			self.start_moving()
		
	def stop_moving(self):
		self.config["map"]["followgps"] = False
	
	def start_moving(self):
		self.config["map"]["followgps"] = True
		
		if self.next_position is None:
			return
		
		lat, lon = self.next_position
		self.set_position(lat, lon)
		self.next_position = None
		
	def on_toggle_moving(self, widget):
		active = widget.get_active()
		if active is True:
			self.start_moving()
		else:
			self.stop_moving()

if __name__ == "__main__":
	test_config = {"map": {"markerstyle": "name", "followgps": True}}
	
	test_map = Map(test_config)
	test_map.set_zoom(16)
	test_map.set_position(52.513,13.323)
	test_map.add_marker("111", "marker 1", "long description\nbla\nblub", "green", 52.513, 13.322)
	test_map.add_marker("222", "marker 2", "blablabla", "red", 52.512, 13.322)
	test_map.add_marker("222", "blablub", "asdasdasd", "red", 52.512, 13.322)
	
	test_window = gtk.Window()
	test_window.set_title("Kismon Test Map")
	test_window.connect("destroy", gtk.main_quit)
	test_window.show()
	test_window.set_size_request(640, 480)
	test_window.add(test_map.widget)
	test_window.show_all()
	
	gtk.main()
