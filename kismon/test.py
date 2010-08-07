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
import sys

def client():
	class TestClient(Client):
		def send(self, msg):
			return
			
	test_lines = [
	'*KISMET: 0.0.0 1276329809 \x01Kismet_2009\x01 \x01netxml\x01 0 ',
	'*PROTOCOLS: KISMET,ERROR,ACK,PROTOCOLS,CAPABILITY,TERMINATE,TIME,PACKET,STATUS,PLUGIN,SOURCE,ALERT,WEPKEY,STRING,GPS,BSSID,SSID,CLIENT,BSSIDSRC,CLISRC,NETTAG,CLITAG,REMOVE,CHANNEL,INFO,BATTERY',
	'*CAPABILITY: INFO networks,packets,crypt,noise,dropped,rate,filtered,clients,llcpackets,datapackets,numsources,numerrorsources',
	'*CAPABILITY: STATUS text,flags',
	'*CAPABILITY: SSID mac,checksum,type,ssid,beaconinfo,cryptset,cloaked,firsttime,lasttime,maxrate,beaconrate,packets,beacons,dot11d',
	'*CAPABILITY: BSSID bssid,type,llcpackets,datapackets,cryptpackets,manuf,channel,firsttime,lasttime,atype,rangeip,netmaskip,gatewayip,gpsfixed,minlat,minlon,minalt,minspd,maxlat,maxlon,maxalt,maxspd,signal_dbm,noise_dbm,minsignal_dbm,minnoise_dbm,maxsignal_dbm,maxnoise_dbm,signal_rssi,noise_rssi,minsignal_rssi,minnoise_rssi,maxsignal_rssi,maxnoise_rssi,bestlat,bestlon,bestalt,agglat,agglon,aggalt,aggpoints,datasize,turbocellnid,turbocellmode,turbocellsat,carrierset,maxseenrate,encodingset,decrypted,dupeivpackets,bsstimestamp,cdpdevice,cdpport,fragments,retries,newpackets,freqmhz,datacryptset',
	'*CAPABILITY: SOURCE interface,type,username,channel,uuid,packets,hop,velocity,dwell,hop_time_sec,hop_time_usec,channellist,error,warning',
	'*CAPABILITY: GPS lat,lon,alt,spd,heading,fix,satinfo,hdop,vdop,connected',
	'*SSID: 00:09:5B:D5:50:10 3604535 0 \x01\x01 \x01 \x01 226 1 1276329814 1276329814 54 10 3 0  ',
	'*SSID: 00:12:2A:03:B9:12 566756343 0 \x01bla 123\x01 \x01 \x01 706 0 1276329811 1276329811 54 10 1 0  ',
	'*SSID: 00:23:08:B4:AF:1C 399639338 0 \x01WLAN-123\x01 \x01 \x01 738 0 1276329819 1276329819 54 10 4 0 \x01DE :2-13-20:\x01 ',
	'*BSSID: 00:12:2A:03:B9:12 0 1 0 0 \x01VtechTelec\x01 6 1276329811 1276329811 0 0.0.0.0 0.0.0.0 0.0.0.0 1 52.1234 13.1232 25.578 0 52.1234 13.1232 25.578 0 -75 0 -75 0 -75 -256 0 0 1024 1024 0 0 52.1234 13.1232 25.578 52.1234 13.1232 25.578 1 0 0 0 0 1 10 0 0 0 5750318387682 \x01 \x01 \x01 \x01 0 0 0 2437:1* 0 ',
	'*BSSID: 00:23:08:23:F6:19 0 2 0 0 \x01ArcadyanTe\x01 1 1276329809 1276329809 0 0.0.0.0 0.0.0.0 0.0.0.0 1 52.1232 13.1231 25.905 0 52.1232 13.1231 25.905 0 -74 0 -76 0 -74 -256 0 0 1024 1024 0 0 52.1232 13.1231 25.905 105.086 26.3162 51.81 2 0 0 0 0 1 10 0 0 0 1084647629116 \x01 \x01 \x01 \x01 0 0 0 2412:2* 0 ',
	'*STATUS: \x01Detected new managed network "test", BSSID 00:26:4D:4A:1C:11, encryption yes, channel 1, 54.00 mbit\x01 2 ',
	'*INFO: 13 58 2 0 0 0 0 0 56 2 1 0 ',
	]
	result_split_line = [
		['0.0.0', '1276329809', 'Kismet_2009', 'netxml', '0'],
		['KISMET,ERROR,ACK,PROTOCOLS,CAPABILITY,TERMINATE,TIME,PACKET,STATUS,PLUGIN,SOURCE,ALERT,WEPKEY,STRING,GPS,BSSID,SSID,CLIENT,BSSIDSRC,CLISRC,NETTAG,CLITAG,REMOVE,CHANNEL,INFO,BATTERY'],
		['INFO', 'networks,packets,crypt,noise,dropped,rate,filtered,clients,llcpackets,datapackets,numsources,numerrorsources'],
		['STATUS', 'text,flags'],
		['SSID', 'mac,checksum,type,ssid,beaconinfo,cryptset,cloaked,firsttime,lasttime,maxrate,beaconrate,packets,beacons,dot11d'],
		['BSSID', 'bssid,type,llcpackets,datapackets,cryptpackets,manuf,channel,firsttime,lasttime,atype,rangeip,netmaskip,gatewayip,gpsfixed,minlat,minlon,minalt,minspd,maxlat,maxlon,maxalt,maxspd,signal_dbm,noise_dbm,minsignal_dbm,minnoise_dbm,maxsignal_dbm,maxnoise_dbm,signal_rssi,noise_rssi,minsignal_rssi,minnoise_rssi,maxsignal_rssi,maxnoise_rssi,bestlat,bestlon,bestalt,agglat,agglon,aggalt,aggpoints,datasize,turbocellnid,turbocellmode,turbocellsat,carrierset,maxseenrate,encodingset,decrypted,dupeivpackets,bsstimestamp,cdpdevice,cdpport,fragments,retries,newpackets,freqmhz,datacryptset'],
		['SOURCE', 'interface,type,username,channel,uuid,packets,hop,velocity,dwell,hop_time_sec,hop_time_usec,channellist,error,warning'],
		['GPS', 'lat,lon,alt,spd,heading,fix,satinfo,hdop,vdop,connected'],
		['00:09:5B:D5:50:10', '3604535', '0', '', ' ', '226', '1', '1276329814', '1276329814', '54', '10', '3', '0'],
		['00:12:2A:03:B9:12', '566756343', '0', 'bla 123', ' ', '706', '0', '1276329811', '1276329811', '54', '10', '1', '0'],
		['00:23:08:B4:AF:1C', '399639338', '0', 'WLAN-123', ' ', '738', '0', '1276329819', '1276329819', '54', '10', '4', '0', 'DE :2-13-20:'],
		['00:12:2A:03:B9:12', '0', '1', '0', '0', 'VtechTelec', '6', '1276329811', '1276329811', '0', '0.0.0.0', '0.0.0.0', '0.0.0.0', '1', '52.1234', '13.1232', '25.578', '0', '52.1234', '13.1232', '25.578', '0', '-75', '0', '-75', '0', '-75', '-256', '0', '0', '1024', '1024', '0', '0', '52.1234', '13.1232', '25.578', '52.1234', '13.1232', '25.578', '1', '0', '0', '0', '0', '1', '10', '0', '0', '0', '5750318387682', ' ', ' ', '0', '0', '0', '2437:1*', '0'],
		['00:23:08:23:F6:19', '0', '2', '0', '0', 'ArcadyanTe', '1', '1276329809', '1276329809', '0', '0.0.0.0', '0.0.0.0', '0.0.0.0', '1', '52.1232', '13.1231', '25.905', '0', '52.1232', '13.1231', '25.905', '0', '-74', '0', '-76', '0', '-74', '-256', '0', '0', '1024', '1024', '0', '0', '52.1232', '13.1231', '25.905', '105.086', '26.3162', '51.81', '2', '0', '0', '0', '0', '1', '10', '0', '0', '0', '1084647629116', ' ', ' ', '0', '0', '0', '2412:2*', '0'],
		['Detected new managed network "test", BSSID 00:26:4D:4A:1C:11, encryption yes, channel 1, 54.00 mbit', '2'],
		['13', '58', '2', '0', '0', '0', '0', '0', '56', '2', '1', '0'],
	]
	result_parse_line = [
		None, None, None, None, None, None, None, None,
		('ssid', {'firsttime': 1276329814, 'ssid': '', 'beacons': 0, 'checksum': 3604535, 'packets': 3, 'beaconrate': 10, 'mac': '00:09:5B:D5:50:10', 'maxrate': 54, 'cloaked': 1, 'type': 0, 'beaconinfo': ' ', 'lasttime': 1276329814, 'cryptset': 226}),
		('ssid', {'firsttime': 1276329811, 'ssid': 'bla 123', 'beacons': 0, 'checksum': 566756343, 'packets': 1, 'beaconrate': 10, 'mac': '00:12:2A:03:B9:12', 'maxrate': 54, 'cloaked': 0, 'type': 0, 'beaconinfo': ' ', 'lasttime': 1276329811, 'cryptset': 706}),
		('ssid', {'firsttime': 1276329819, 'ssid': 'WLAN-123', 'beacons': 0, 'checksum': 399639338, 'dot11d': 'DE :2-13-20:', 'packets': 4, 'beaconrate': 10, 'mac': '00:23:08:B4:AF:1C', 'maxrate': 54, 'cloaked': 0, 'type': 0, 'beaconinfo': ' ', 'lasttime': 1276329819, 'cryptset': 738}),
		('bssid', {'manuf': 'VtechTelec', 'maxalt': 25.577999999999999, 'encodingset': 0, 'agglon': 13.123200000000001, 'minnoise_dbm': 0, 'maxseenrate': 10, 'bssid': '00:12:2A:03:B9:12', 'maxspd': 0, 'maxsignal_dbm': -75, 'minlat': 52.123399999999997, 'cryptpackets': 0, 'llcpackets': 1, 'signal_rssi': 0, 'aggalt': 25.577999999999999, 'newpackets': 0, 'minsignal_dbm': -75, 'noise_dbm': 0, 'noise_rssi': 0, 'aggpoints': 1, 'cdpdevice': ' ', 'maxnoise_rssi': 0, 'maxnoise_dbm': -256, 'retries': 0, 'bsstimestamp': 5750318387682, 'turbocellnid': 0, 'bestlon': 13.123200000000001, 'dupeivpackets': 0, 'minalt': 25.577999999999999, 'fragments': 0, 'datasize': 0, 'type': 0, 'channel': 6, 'agglat': 52.123399999999997, 'maxlon': 13.123200000000001, 'decrypted': 0, 'turbocellmode': 0, 'gatewayip': '0.0.0.0', 'signal_dbm': -75, 'maxlat': 52.123399999999997, 'freqmhz': '2437:1*', 'lasttime': 1276329811, 'minspd': 0, 'bestalt': 25.577999999999999, 'bestlat': 52.123399999999997, 'firsttime': 1276329811, 'minlon': 13.123200000000001, 'carrierset': 1, 'datapackets': 0, 'turbocellsat': 0, 'atype': 0, 'datacryptset': 0, 'gpsfixed': 1, 'rangeip': '0.0.0.0', 'minsignal_rssi': 1024, 'maxsignal_rssi': 0, 'netmaskip': '0.0.0.0', 'minnoise_rssi': 1024, 'cdpport': ' '}),
		('bssid', {'manuf': 'ArcadyanTe', 'maxalt': 25.905000000000001, 'encodingset': 0, 'agglon': 26.316199999999998, 'minnoise_dbm': 0, 'maxseenrate': 10, 'bssid': '00:23:08:23:F6:19', 'maxspd': 0, 'maxsignal_dbm': -74, 'minlat': 52.123199999999997, 'cryptpackets': 0, 'llcpackets': 2, 'signal_rssi': 0, 'aggalt': 51.810000000000002, 'newpackets': 0, 'minsignal_dbm': -76, 'noise_dbm': 0, 'noise_rssi': 0, 'aggpoints': 2, 'cdpdevice': ' ', 'maxnoise_rssi': 0, 'maxnoise_dbm': -256, 'retries': 0, 'bsstimestamp': 1084647629116, 'turbocellnid': 0, 'bestlon': 13.123100000000001, 'dupeivpackets': 0, 'minalt': 25.905000000000001, 'fragments': 0, 'datasize': 0, 'type': 0, 'channel': 1, 'agglat': 105.086, 'maxlon': 13.123100000000001, 'decrypted': 0, 'turbocellmode': 0, 'gatewayip': '0.0.0.0', 'signal_dbm': -74, 'maxlat': 52.123199999999997, 'freqmhz': '2412:2*', 'lasttime': 1276329809, 'minspd': 0, 'bestalt': 25.905000000000001, 'bestlat': 52.123199999999997, 'firsttime': 1276329809, 'minlon': 13.123100000000001, 'carrierset': 1, 'datapackets': 0, 'turbocellsat': 0, 'atype': 0, 'datacryptset': 0, 'gpsfixed': 1, 'rangeip': '0.0.0.0', 'minsignal_rssi': 1024, 'maxsignal_rssi': 0, 'netmaskip': '0.0.0.0', 'minnoise_rssi': 1024, 'cdpport': ' '}),
		('status', {'text': 'Detected new managed network "test", BSSID 00:26:4D:4A:1C:11, encryption yes, channel 1, 54.00 mbit', 'flags': 2}),
		('info', {'noise': 0, 'datapackets': 2, 'crypt': 2, 'clients': 0, 'packets': 58, 'rate': 0, 'llcpackets': 56, 'dropped': 0, 'numerrorsources': 0, 'numsources': 1, 'filtered': 0, 'networks': 13}),
	]
	
	client = TestClient()
	client.set_capabilities(["bssid", "ssid"])
	pos = 0
	errors = 0
	for line in test_lines:
		result = client.split_line(line.split(":", 1)[1])
		if result != result_split_line[pos]:
			print "split_line error %s" % pos
			print "%s\n!=\n%s" % (result, result_split_line[pos])
			errors += 1
		
		result = client.parse_line(line)
		if result != result_parse_line[pos]:
			print "parse_line error %s" % pos
			print "%s\n!=\n%s" % (result, result_parse_line[pos])
			errors += 1
		pos += 1
	
	if errors != 0:
		sys.exit("client test failed, %s errors" % errors)

def config():
	conf=Config("/tmp/testconfig.conf")
	conf.read()
	conf.write()
	conf.read()
	conf.show()

def core():
	core = Core()
	core.queue_handler()
	core.queue_handler_networks()
	core.client_stop()

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
	test_map.marker_layer_add_new_markers()
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
	tmp_osm.write('''<?xml version="1.0" encoding="UTF-8"?>
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
	client()
	core()
	config()
	gui_main_window()
	gui_map_window()
	gui_signal_window()
	map()

if __name__ == "__main__":
	test()
