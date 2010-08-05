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

from core import *
from config import Config
from map import *
from gui import *
from client import *

import gobject
gobject.threads_init()
import time
import gtk

def config():
	conf=Config("/tmp/testconfig.conf")
	conf.read()
	conf.write()
	conf.read()
	conf.show()

def core():
	core = Core()
	core.queue_handler()

def gui_main_window():
	def client_start():
		return
	def client_stop():
		return
	
	test_config = Config(None).default_config
	test_map = MapWidget(test_config["map"])
	
	main_window = MainWindow(test_config, client_start, client_stop, test_map)
	main_window.crypt_cache = {}
	
	main_window.add_to_log_list("test")
	now = int(time.time())
	bssid = {"bssid": "11:22:33:44:55:66", "type": 0, "channel": 11,
		"firsttime": now, "lasttime": now, "bestlat": 52.0, "bestlon": 13.0,
		"signal_dbm": -70}
	ssid = {"cryptset": 706, "ssid": "test"}
	main_window.add_to_network_list(bssid, ssid)
	main_window.add_to_network_list(bssid, ssid)
	main_window.network_list_network_selected = "11:22:33:44:55:66"
	main_window.update_info_table({"networks":100, "packets":200})
	main_window.update_gps_table({"fix": 3, "lat": 52.0, "lon": 13.0})
	sources = {"1": {"uuid": "1", "username": "test", "type": "bla",
		"channel": 11, "packets": 100}}
	main_window.update_sources_table(sources)
	main_window.on_configure_event(None, None)
	main_window.on_config_window(None)
	main_window.on_config_window(None)
	main_window.on_signal_graph(None)
	main_window.on_signal_graph_destroy(None, "11:22:33:44:55:66")
	main_window.fullscreen()
	main_window.fullscreen()
	main_window.on_map_window(None, True)
	main_window.on_map_window(None, False)
	main_window.on_map_widget(None, True)
	main_window.on_map_widget(None, False)
	
	class TestWidget:
		def __init__(self):
			self.active = True
		
		def get_active(self):
			return self.active
	
	test_widget = TestWidget()
	config_window = main_window.config_window
	config_window.on_map_source_mapnik(test_widget)
	config_window.on_map_source_memphis(test_widget)
	config_window.on_memphis_rules(test_widget, "default")

def gui_map_window():
	test_config = Config(None).default_config["map"]
	test_map = MapWidget(test_config)
	map_window = MapWindow(test_map)
	map_window.hide()
	map_window.on_destroy(None)

def gui_signal_window():
	def destroy(obj, window):
		return
	signal_window = SignalWindow("11:22:33:44:55:66", destroy)
	signal_window.add_value(-30)
	signal_window.draw_graph(600, 400)
	now = int(time.time())
	for signal in (-50, -60, -70, -80, -50):
		now -= 1
		signal_window.history[now] = signal
	signal_window.draw_graph(600, 400)

def map():
	test_config = Config(None).default_config["map"]
	test_map_widget = MapWidget(test_config)
	test_map = test_map_widget.map
	
	test_map.set_zoom(16)
	test_map.set_position(52.513, 13.323)
	test_map.add_marker("111", "marker 1", "long description\nbla\nblub", "green", 52.513, 13.322)
	test_map.add_marker("222", "marker 2", "bla", "red", 52.512, 13.322)
	test_map.add_marker("222", "marker 2 test1", "foobar", "red", 52.512, 13.322)
	test_map.locate_marker("111")
	test_map.set_marker_style("name")
	test_map.add_marker("222", "marker 2 test2", "blub", "red", 52.512, 13.321)
	test_map.add_marker("333", "marker 3", "test", "orange", 52.511, 13.322)
	test_map.set_marker_style("image")
	test_map_widget.toggle_moving_button.set_active(False)
	test_map.set_position(52.513,13.323)
	test_map_widget.toggle_moving_button.set_active(True)
	test_map_widget.on_zoom_out(None)
	test_map_widget.on_zoom_in(None)
	test_map_widget.on_map_pressed(None, None)
	test_map_widget.on_map_released(None, None)
	test_map.set_source("osm-mapnik")
	
	tmp_osm_file = "/tmp/test-%s.osm" % int(time.time())
	tmp_osm = open(tmp_osm_file, "w")
	tmp_osm.write('''
	<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="OpenStreetMap server">
</osm>
	''')
	tmp_osm.close()
	test_config["osm_file"] = tmp_osm_file
	test_map.set_source("memphis-local")
	
	test_window = gtk.Window()
	test_window.set_title("Kismon Test Map")
	test_window.connect("destroy", gtk.main_quit)
	test_window.show()
	test_window.set_size_request(640, 480)
	test_window.add(test_map_widget.widget)
	test_window.show_all()

def test():
	core()
	config()
	gui_main_window()
	gui_map_window()
	gui_signal_window()
	map()

if __name__ == "__main__":
	test()
