#!/usr/bin/env python3
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

import os
import sys
import subprocess

try:
	from .client import *
	from .gui import show_timestamp
	from .config import Config
	from .networks import Networks
except SystemError:
	from client import *
	from gui import MainWindow, show_timestamp
	from config import Config
	from networks import Networks

from gi.repository import Gtk
from gi.repository import GLib

def check_osmgpsmap():
	try:
		from gi.repository import OsmGpsMap
	except:
		return sys.exc_info()[1]

class Core:
	def __init__(self):
		user_dir = "%s%s.kismon%s" % (os.path.expanduser("~"), os.sep, os.sep)
		if not os.path.isdir(user_dir):
			print("Creating Kismon user directory %s" % user_dir)
			os.mkdir(user_dir)
		config_file = "%skismon.conf" % user_dir
		self.config_handler = Config(config_file)
		self.config_handler.read()
		self.config = self.config_handler.config
		
		self.marker_text = """Encryption: %s
MAC: %s
Manuf: %s
Type: %s
Channel: %s
First seen: %s
Last seen: %s"""
		
		self.sources = {}
		self.crypt_cache = {}
		self.networks = Networks(self.config)
		self.client_threads = {}
		self.init_client_threads()
		
		if "--disable-map" in sys.argv:
			self.map_error = "--disable-map used"
		else:
			self.map_error = check_osmgpsmap()
		
		if self.map_error is not None:
			self.map_error =  "%s\nMap disabled" % self.map_error
			print(self.map_error, "\n")
		
		self.init_map()
		
		self.main_window = MainWindow(self.config,
			self.client_start,
			self.client_stop,
			self.map,
			self.networks,
			self.sources,
			self.client_threads)
		self.main_window.log_list.add("Kismon", "started")
		if self.map_error is not None:
			self.main_window.log_list.add("Kismon", self.map_error)
		
		self.networks_file = "%snetworks.json" % user_dir
		if os.path.isfile(self.networks_file):
			try:
				self.networks.load(self.networks_file)
			except:
				error = sys.exc_info()[1]
				print(error)
				dialog_message = "Could not read the networks file '%s':\n%s\n\nDo you want to continue?" % (self.networks_file, error)
				dialog = Gtk.MessageDialog(self.main_window.gtkwin, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR, Gtk.ButtonsType.YES_NO, dialog_message)
				def dialog_response(dialog, response_id):
					self.dialog_response = response_id
				dialog.connect("response", dialog_response)
				dialog.run()
				dialog.destroy()
				if self.dialog_response == -9:
					print("exit")
					self.clients_stop()
					self.main_window.gtkwin = None
					return
		self.networks.set_autosave(self.config["networks"]["autosave"], self.networks_file, self.main_window.log_list.add)
		
		if self.map is not None:
			self.networks.notify_add_list["map"] = self.add_network_to_map
			self.networks.notify_remove_list["map"] = self.map.remove_marker
			GLib.timeout_add(100, self.map.set_last_from_config)
		
		self.main_window.network_list.crypt_cache = self.crypt_cache
		
		GLib.timeout_add(500, self.queues_handler)
		GLib.timeout_add(300, self.queues_handler_networks)
		GLib.idle_add(self.networks.apply_filters)
		
	def init_map(self):
		if self.map_error is not None:
			self.map = None
		else:
			try:
				from .map import Map
			except SystemError:
				from map import Map
			self.map = Map(self.config["map"])
			self.map.set_last_from_config()
		
	def init_client_thread(self, server_id):
		server = self.config["kismet"]["servers"][server_id]
		self.client_threads[server_id] = ClientThread(server)
		self.client_threads[server_id].client.set_capabilities(
			('status', 'source', 'info', 'gps', 'bssid', 'bssidsrc', 'ssid'))
		if "--create-kismet-dump" in sys.argv:
			self.client_threads[server_id].client.enable_dump()
		
	def init_client_threads(self):
		server_id=0
		for server in self.config["kismet"]["servers"]:
			self.init_client_thread(server_id)
			server_id += 1
		
	def client_start(self, server_id):
		if server_id in self.client_threads and self.client_threads[server_id].is_running:
			self.client_stop(server_id)
		self.sources[server_id] = {}
		self.init_client_thread(server_id)
		if "--load-kismet-dump" in sys.argv:
			self.client_threads[server_id].client.load_dump(sys.argv[2])
		self.client_threads[server_id].start()
		
	def client_stop(self, server_id):
		if self.client_threads[server_id].client.connecting:
			# kill connecting sockets, don't wait for the timeout
			self.client_threads[server_id].client.s.shutdown(socket.SHUT_RDWR)
		self.client_threads[server_id].stop()
		
	def clients_stop(self):
		for server_id in self.client_threads:
			self.client_stop(server_id)
		return True
		
	def queue_handler(self, server_id):
		server_name = self.config['kismet']['servers'][server_id]
		if self.main_window.gtkwin is None:
			return False
		
		thread = self.client_threads[server_id]
		if len(thread.client.error) > 0:
			for error in thread.client.error:
				self.main_window.log_list.add(server_name, error)
			thread.client.error = []
			self.main_window.server_tabs[server_id].server_switch.set_active(False)
			page_num = self.main_window.notebook.page_num(self.main_window.log_list.widget)
			self.main_window.notebook.set_current_page(page_num)
		
		#gps
		gps = None
		fix = None
		gps_queue = thread.get_queue("gps")
		while True:
			try:
				data = gps_queue.pop()
				if gps is None:
					gps = data
				if data["fix"] > 1:
					fix = (data["lat"], data["lon"])
					break
			except IndexError:
				break
		if gps is not None:
			self.main_window.server_tabs[server_id].update_gps_table(gps)
			if fix is not None and self.map is not None:
				server = "server%s" % (server_id + 1)
				if server_id == 0:
					self.map.set_position(fix[0], fix[1])
				else:
					self.map.add_marker(server, server, fix[0], fix[1])
				self.map.add_track(fix[0], fix[1], server_id)
		
		#status
		for data in thread.get_queue("status"):
			self.main_window.log_list.add(server_name, data["text"])
		
		#info
		info_queue = thread.get_queue("info")
		try:
			data = info_queue.pop()
			self.main_window.server_tabs[server_id].update_info_table(data)
		except IndexError:
			pass
			
		#source
		update = False
		for data in thread.get_queue("source"):
			uuid = data["uuid"]
			if uuid == "00000000-0000-0000-0000-000000000000":
				continue
			self.sources[server_id][uuid] = data
			
			update = True
		if update is True:
			self.main_window.server_tabs[server_id].update_sources_table(self.sources[server_id])
		
	def queues_handler(self):
		for server_id in self.client_threads:
			self.queue_handler(server_id)
		return True
		
	def queue_handler_networks(self, server_id):
		thread = self.client_threads[server_id]
		
		#ssid
		for data in thread.get_queue("ssid"):
			self.networks.add_ssid_data(data)
		
		#bssid
		bssids = {}
		for data in thread.get_queue("bssid"):
			mac = data["bssid"]
			self.networks.add_bssid_data(data, server_id)
			if mac in self.main_window.signal_graphs and "signal_dbm" not in thread.client.capabilities["bssidsrc"]:
				self.main_window.signal_graphs[mac].add_value(None, None, data["signal_dbm"], server_id)
			
			bssids[mac] = True
			
		#bssidsrc
		for data in thread.get_queue("bssidsrc"):
			if "signal_dbm" not in data or data["uuid"] not in self.sources[server_id]:
				continue
			
			mac = data["bssid"]
			if mac in self.main_window.signal_graphs:
				self.main_window.signal_graphs[mac].add_value(self.sources[server_id][data["uuid"]], data, data["signal_dbm"], server_id)
		
		if len(self.networks.notify_add_queue) > 0:
			self.networks.start_queue()
			if len(self.networks.notify_add_queue) > 500:
				self.networks.disable_refresh()
				self.main_window.networks_queue_progress()
		
		self.main_window.update_statusbar()
		
	def queues_handler_networks(self):
		for server_id in self.client_threads:
			self.queue_handler_networks(server_id)
		return True
		
	def quit(self):
		self.clients_stop()

		lat = self.map.osm.get_property("latitude")
		lon = self.map.osm.get_property("longitude")
		self.config["map"]["last_position"] = "%.6f/%.6f" % (lat, lon)

		while None in self.config['kismet']['servers']:
			self.config['kismet']['servers'].remove(None)
		self.config_handler.write()
		self.networks.save(self.networks_file)
		
	def add_network_to_map(self, mac):
		network = self.networks.get_network(mac)
		
		try:
			crypt = self.crypt_cache[network["cryptset"]]
		except KeyError:
			crypt = decode_cryptset(network["cryptset"], True)
			self.crypt_cache[network["cryptset"]] = crypt
		
		if "AES_CCM" in crypt or "AES_OCB" in crypt:
			color = "red"
		elif "WPA" in crypt:
			color = "orange"
		elif "WEP" in crypt:
			color = "yellow"
		else:
			color = "green"
		
		ssid = network["ssid"]
		if ssid == "":
			ssid = "<no ssid>"
		evils = (("&", "&amp;"),("<", "&lt;"),(">", "&gt;"))
		for evil, good in evils:
			ssid = ssid.replace(evil, good)
		
		time_format = "%d.%m.%Y %H:%M:%S"
		
		text = self.marker_text % (crypt, mac, network["manuf"],
			network["type"], network["channel"],
			time.strftime(time_format, time.localtime(network["firsttime"])),
			time.strftime(time_format, time.localtime(network["lasttime"]))
			)
		text = text.replace("&", "&amp;")
		
		self.map.add_marker(mac, color, network["lat"], network["lon"])
		
def main():
	core = Core()
	if core.main_window.gtkwin == None:
		sys.exit()
	try:
		Gtk.main()
	except KeyboardInterrupt:
		pass
	core.quit()

if __name__ == "__main__":
	main()
