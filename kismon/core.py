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

from client import *
from gui import MainWindow, MapWindow, show_timestamp
from config import Config

import os
import sys

import gtk
import gobject

try:
	import champlaingtk
	import champlain
except:
	champlain_error = sys.exc_info()[1]
	champlain = None
if champlain is not None:
	try:
		champlain.Marker().set_image(None)
	except TypeError:
		champlain_error = "libchamplain older than 0.6.1"
		champlain = None
if champlain is not None:
	from map import MapWidget
else:
	print champlain_error
	print "Map disabled"

class Core:
	def __init__(self):
		user_dir = "%s%s.kismon%s" % (os.path.expanduser("~"), os.sep, os.sep)
		if not os.path.isdir(user_dir):
			print "Creating Kismon user directory %s" % user_dir
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
		
		self.init_client_thread()
		if self.config["kismet"]["connect"] is True:
			self.client_start()
		
		if champlain is None:
			self.map_widget = None
		else:
			self.map_widget = MapWidget(self.config["map"])
			self.map = self.map_widget.map
			self.map.set_zoom(16)
		
		self.main_window = MainWindow(self.config,
			self.client_start,
			self.client_stop,
			self.map_widget)
		self.main_window.add_to_log_list("Kismon started")
		if champlain is None:
			self.main_window.add_to_log_list(champlain_error)
			self.main_window.add_to_log_list("Map diabled")
		
		self.sources = {}
		self.bssids = {}
		self.ssids = {}
		self.crypt_cache = {}
		self.main_window.crypt_cache = self.crypt_cache
		
		if os.path.isdir("/proc/acpi/battery/BAT0"):
			f = open("/proc/acpi/battery/BAT0/info")
			for line in f.readlines():
				if line.startswith("last full capacity:"):
					max = line.split(":")[1].strip()
					self.battery_max = int(max.split()[0])
					break
			self.update_battery_bar()
			gobject.timeout_add(30000, self.update_battery_bar)
		else:
			self.battery_max = None
		
		gobject.threads_init()
		gobject.timeout_add(self.config["core"]["refresh_rate"], self.queue_handler)
		
	def init_client_thread(self):
		self.client_thread = ClientThread(self.config["kismet"]["server"])
		self.client_thread.client.set_capabilities(
			('status', 'source', 'info', 'gps', 'bssid', 'ssid'))
		if "--create-kismet-dump" in sys.argv:
			self.client_thread.client.enable_dump()
		
	def client_start(self):
		if self.client_thread.is_running is True:
			self.client_stop()
		self.init_client_thread()
		if "--load-kismet-dump" in sys.argv:
			self.client_thread.client.load_dump(sys.argv[2])
		self.client_thread.start()
		
	def client_stop(self):
		self.client_thread.stop()
		
	def queue_handler(self):
		if self.main_window.gtkwin is None:
			self.quit()
			
		if len(self.client_thread.client.error) > 0:
			for error in self.client_thread.client.error:
				self.main_window.add_to_log_list(error)
			self.client_thread.client.error = []
		
		queue = self.client_thread.queue
		self.client_thread.queue=[]
		for cap, data in queue:
			if cap == "status":
				self.main_window.add_to_log_list(data["text"])
			
			elif cap == "gps":
				self.main_window.update_gps_table(data)
				if data["fix"] > 1 and self.map_widget is not None:
					self.map.set_position(data["lat"], data["lon"])
			
			elif cap == "info":
				self.main_window.update_info_table(data)
			
			elif cap == "source":
				self.sources[data["uuid"]] = data
				self.main_window.update_sources_table(self.sources)
			
			elif cap == "bssid":
				mac = data["bssid"]
				self.bssids[mac] = data
				
				if mac in self.ssids:
					self.main_window.add_to_network_list(self.bssids[mac], self.ssids[mac])
					
					if self.map_widget is None:
						continue
						
					try:
						crypt = self.crypt_cache[self.ssids[mac]["cryptset"]]
					except KeyError:
						crypt = decode_cryptset(self.ssids[mac]["cryptset"], True)
						self.crypt_cache[self.ssids[mac]["cryptset"]] = crypt
					
					if "WPA" in crypt:
						color = "red"
					elif "WEP" in crypt:
						color = "orange"
					else:
						color = "green"
					
					ssid = str(self.ssids[mac]["ssid"])
					if ssid == "":
						ssid = "<no ssid>"
					evils = (("&", "&amp;"),("<", "&lt;"),(">", "&gt;"))
					for evil, good in evils:
						ssid = ssid.replace(evil, good)
					
					text = self.marker_text % (crypt, mac, data["manuf"],
						decode_network_type(data["type"]), data["channel"],
						show_timestamp(data["firsttime"]),
						show_timestamp(data["lasttime"])
						)
					text = text.replace("&", "&amp;")
					
					if decode_network_type(data["type"]) == "infrastructure":
						self.map.add_marker(mac, ssid, text, color,
							data["bestlat"], data["bestlon"])
				else:
					self.main_window.add_to_network_list(self.bssids[mac])
			
			elif cap == "ssid":
				mac = data["mac"]
				self.ssids[mac] = data
				
			else:
				pass
				#print cap, data
				
		return True
		
	def quit(self):
		self.client_thread.stop()
		self.config_handler.write()
		
	def get_battery_capacity(self):
		filename = "/proc/acpi/battery/BAT0/state"
		if not os.path.isfile(filename):
			return False
		f = open(filename)
		for line in f.readlines():
			if line.startswith("remaining capacity:"):
				current = line.split(":")[1].strip()
				current = int(current.split()[0])
				return round(100.0 / self.battery_max * current, 1)
		
	def update_battery_bar(self):
		battery = self.get_battery_capacity()
		if battery is not False:
			self.main_window.set_battery_bar(battery)
		return True

def main():
	core = Core()
	try:
		gtk.main()
	except KeyboardInterrupt:
		pass
	core.quit()

if __name__ == "__main__":
	main()
