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

from config import Config
from map import *
from gui import *
from client import *

import gobject
gobject.threads_init()

def config():
	conf=Config("/tmp/testconfig.conf")
	conf.read()
	conf.write()
	conf.read()
	conf.show()

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
	
	test_window = gtk.Window()
	test_window.set_title("Kismon Test Map")
	test_window.connect("destroy", gtk.main_quit)
	test_window.show()
	test_window.set_size_request(640, 480)
	test_window.add(test_map_widget.widget)
	test_window.show_all()

def test():
	config()
	map()

if __name__ == "__main__":
	test()
