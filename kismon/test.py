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
from networks import *

import gobject
gobject.threads_init()
import time
import gtk
import sys
import tempfile

def get_client_test_data():
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
	return (test_lines, result_split_line, result_parse_line)

def client():
	class TestClient(Client):
		def send(self, msg):
			return
			
	test_lines, result_split_line, result_parse_line = get_client_test_data()
	
	client = TestClient()
	client.server = "invalid:xyz"
	client.start()
	
	test_dump_name = "%s%skismet_dump_test-%s.dump" % (tempfile.gettempdir(), os.sep, int(time.time()))
	test_dump = open(test_dump_name, "w")
	
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
		test_dump.write(line)
		
	crypt_test = [
		(0, "none"),
		(2, "WEP"),
		(226, "WEP,TKIP,WPA,PSK"),
		(706, "WEP,WPA,PSK,AES_CCM"),
		(738, "WEP,TKIP,WPA,PSK,AES_CCM"),
	]
	for cryptset, result in crypt_test:
		crypt_str = decode_cryptset(cryptset, True)
		if crypt_str != result:
			print "decode_cryptset error: %s\n%s!=%s" % (cryptset, crypt_str, result)
		
		test_cryptset = encode_cryptset(crypt_str.lower().split(","))
		if test_cryptset != cryptset:
			print "encode_cryptset error: %s\n%s!=%s" % (crypt_str, test_cryptset, cryptset)
	
	if errors != 0:
		sys.exit("client test failed, %s errors" % errors)
		
	test_dump.close()
	
	client.load_dump(test_dump_name)
	client.loop()
	
	client_thread = ClientThread()
	client_thread.client = client
	client.load_dump(test_dump_name)
	client_thread.run()

def config():
	conf=Config(tempfile.gettempdir() + os.sep + "testconfig.conf")
	conf.read()
	conf.write()
	conf.read()
	conf.show()

def core():
	test_core = Core()
	core_tests(test_core)
	test_core.add_network_to_map("00:12:2A:03:B9:12")
	test_core.client_stop()
	
	arg = "--disable-map"
	sys.argv.append(arg)
	test_core = Core()
	core_tests(test_core)
	sys.argv.remove(arg)
	
	test_core.client_stop()
	
def core_tests(test_core):
	test_networks = networks()
	test_core.networks = test_networks
	test_data = get_client_test_data()[2]
	for line in test_data:
		if line is None:
			continue
		test_core.client_thread.queue[line[0]].append(line[1])
	test_core.queue_handler()
	test_core.queue_handler_networks()
	task = test_core.networks.notify_add_queue_process()
	while task.next():
		continue

class TestWidget:
		def __init__(self):
			self.active = True
			self.text = ""
		
		def get_active(self):
			return self.active
			
		def get_active_text(self):
			return self.text
			
		def get_label(self):
			return self.text

def gui_main_window():
	def dummy():
		return
	
	test_config = Config(None).default_config
	test_map = Map(test_config["map"])
	test_networks =  networks()
	
	main_window = MainWindow(test_config, dummy, dummy, test_map, test_networks, None, None)
	main_window.network_list.crypt_cache = {}
	
	main_window.log_list.add("test")
	main_window.network_list.network_selected = "11:22:33:44:55:66"
	main_window.network_list.add_network('00:12:2A:03:B9:12')
	main_window.network_list.add_network('00:12:2A:03:B9:12')
	main_window.network_list.remove_network('00:12:2A:03:B9:12')
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
	main_window.on_client_disconnect(None)
	
	test_widget = TestWidget()
	config_window = main_window.config_window
	
	main_window.on_file_import(None)
	
	test_widget.text = "Infrastructure"
	main_window.on_network_filter_type(test_widget)
	main_window.on_network_filter_networks(test_widget, "map", "all")
	
def gui_channel_window():
	sources = {"123":{"uuid": "123","hop": 3, "username": "123", "velocity": 3}}
	channel_window = ChannelWindow(sources, None)
	test_widget = TestWidget()
	channel_window.on_change_mode(test_widget, "123", "hop")
	channel_window.on_change_mode(test_widget, "123", "lock")
	channel_window.on_change_value(None, "123", "hop")
	channel_window.on_cancel(None)

def gui_file_import_window():
	test_widget = TestWidget()
	file_import_window = FileImportWindow(test_networks, main_window.networks_queue_progress)
	file_import_window.create_file_chooser("dir")
	filename = "%s%stest-networks-%s.json" % (tempfile.gettempdir(), os.sep, int(time.time()))
	test_networks.save(filename)
	file_import_window.add_file(filename)
	test_widget.text = "networks"
	file_import_window.on_filetype_changed(test_widget, filename)
	file_import_window.on_remove_file(None, filename)
	file_import_window.add_file(filename)
	file_import_window.on_start(None)
	file_import_window.parse_file()
	file_import_window.on_close(None)

def gui_map_window():
	test_config = Config(None).default_config["map"]
	test_map = Map(test_config)
	map_window = MapWindow(test_map)
	map_window.hide()
	map_window.on_destroy(None)

def gui_signal_window():
	def destroy(obj, window):
		return
	signal_window = SignalWindow("11:22:33:44:55:66", destroy)
	signal_window.add_value(None, None, -30)
	signal_window.add_value(None, None, -31)
	signal_window.draw_graph(600, 400)
	now = int(time.time())
	for signal in (-50, -60, -70, -80, -50):
		now -= 1
		signal_window.history[now] = {}
		signal_window.history[now]["test"] = (signal, signal * -1)
	signal_window.draw_graph(600, 400)
	class TestEvent:
		class TestArea:
			def __init__(self):
				self.width = 100
				self.height = 100
		def __init__(self):
			self.area = self.TestArea()
	signal_window.on_expose_event(None, TestEvent())
	signal_window.on_expose_event(None, TestEvent())

def map():
	test_config = Config(None).default_config["map"]
	test_map = Map(test_config)
	
	test_map.set_zoom(16)
	test_map.set_position(52.513, 13.323)
	test_map.add_marker("111", "green", 52.513, 13.322)
	test_map.add_marker("222", "red", 52.512, 13.322)
	test_map.add_marker("333", "orange", 52.512, 13.322)
	test_map.locate_marker("111")
	test_map.add_marker("222", "red", 52.510, 13.321)
	test_map.add_marker("333", "orange", 52.511, 13.322)
	
	test_map.set_position(52.513,13.323)
	test_map.zoom_out()
	test_map.zoom_in()
	test_map.on_map_pressed(None, None)
	test_map.set_source("openstreetmap")
	test_map.set_source("openstreetmap-renderer")
	test_map.remove_marker("333")
	
	test_window = gtk.Window()
	test_window.set_title("Kismon Test Map")
	test_window.connect("destroy", gtk.main_quit)
	test_window.show()
	test_window.set_size_request(640, 480)
	test_window.add(test_map.widget)
	test_window.show_all()

def networks():
	def dummy(bla):
		return
	test_data = get_client_test_data()[2]
	test_config = Config(None).default_config
	
	networks = Networks(test_config)
	networks.notify_add_list["map"] = dummy
	networks.notify_add_list["network_list"] = dummy
	networks.notify_remove_list["map"] = dummy
	networks.notify_remove_list["network_list"] = dummy
	for x in range(2):
		for data in test_data:
			if data is not None and data[0] == "bssid":
				networks.add_bssid_data(data[1])
				data[1]["lasttime"] = data[1]["lasttime"] + 1
		for data in test_data:
			if data is not None and data[0] == "ssid":
				networks.add_ssid_data(data[1])
				data[1]["lasttime"] = data[1]["lasttime"] + 1
	
	tmp_csv_file = "%s%stest-%s.csv" % (tempfile.gettempdir(), os.sep, int(time.time()))
	tmp_csv = open(tmp_csv_file, "w")
	tmp_csv.write("""Network;NetType;ESSID;BSSID;Info;Channel;Cloaked;Encryption;Decrypted;MaxRate;MaxSeenRate;Beacon;LLC;Data;Crypt;Weak;Total;Carrier;Encoding;FirstTime;LastTime;BestQuality;BestSignal;BestNoise;GPSMinLat;GPSMinLon;GPSMinAlt;GPSMinSpd;GPSMaxLat;GPSMaxLon;GPSMaxAlt;GPSMaxSpd;GPSBestLat;GPSBestLon;GPSBestAlt;DataSize;IPType;IP;
1;infrastructure;WsF;00:18:84:15:18:A5;;3;No;WEP,WPA,PSK,AES-CCM;No;18.0;1000;25600;148;0;0;0;148;IEEE 802.11g;;Thu Jan 22 05:48:23 2009;Thu Jan 22 05:51:46 2009;0;65;-98;52.549381;13.141430;120.120003;0.000000;52.549652;13.141682;120.120003;2.934490;0.000000;0.000000;0.000000;0;None;0.0.0.0;""")
	tmp_csv.close()
	for x in range(2):
		networks.import_networks("csv", tmp_csv_file)
	networks.import_networks("netxml", "")
	
	networks_file = "%s%snetworks-%s.json" % (tempfile.gettempdir(), os.sep, int(time.time()))
	networks.save(networks_file)
	networks.load(networks_file)
	networks.import_networks("networks",networks_file)
	networks.apply_filters()
	networks.save(networks_file)
	networks.export_networks_netxml(tempfile.gettempdir() + os.sep + "test.netxml", networks.networks)
	networks.import_networks("netxml", tempfile.gettempdir() + os.sep + "test.netxml")
	networks.export_networks_kmz(tempfile.gettempdir() + os.sep + "test.kmz", networks.networks)
	
	return networks

def test():
	client()
	core()
	config()
	gui_main_window()
	gui_channel_window()
	gui_map_window()
	gui_signal_window()
	map()

if __name__ == "__main__":
	test()
