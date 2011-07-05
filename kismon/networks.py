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

import simplejson as json
import xml.parsers.expat
import time
import locale
import gobject
import zipfile

from client import *
from gui import show_timestamp

class Networks:
	def __init__(self, config):
		self.networks = {}
		self.config = config
		self.recent_networks = []
		self.notify_add_list = {}
		self.notify_add_queue = {}
		self.notify_remove_list = {}
		self.disable_refresh_functions = []
		self.refresh_disabled = False
		self.resume_refresh_functions = []
		self.queue_running = False
		self.block_queue_start = False
		self.temp_ssid_data = {}
		self.queue_task = None
		self.num_backups = 5
		self.autosave_task = None
		self.autosave_filename = None
		self.autosave_notify = None
		
	def get_network(self, mac):
		return self.networks[mac]
		
	def save(self, filename, notify=None):
		msg = "saving %s networks to %s" % (len(self.networks), filename)
		print msg
		if notify is not None:
			notify(msg)
		
		tmpfilename = filename + ".new"
		self.save_networks(tmpfilename, self.networks)
		
		for num in range(self.num_backups - 2, -1 , -1):
			backup_filename = "%s.%s" % (filename, num)
			if os.path.isfile(backup_filename):
				os.rename(backup_filename, "%s.%s" % (filename, num + 1))
		
		if os.path.isfile(filename):
			os.rename(filename, filename + ".0")
		os.rename(tmpfilename, filename)
		return True
		
	def save_networks_json(self, filename):
		f = open(filename, "w")
		json.dump(self.networks, f, sort_keys=True, indent=2)
		f.close()
		
	def save_networks(self, filename, networks):
		f = open(filename, "w")
		f.write('{\n')
		macs = sorted(networks)
		enc = json.JSONEncoder()
		for mac in macs:
			network = self.networks[mac]
			f.write('  "%s": {\n' % mac)
			f.write('    "channel": %s, \n' % network["channel"])
			f.write('    "cryptset": %s, \n' % network["cryptset"])
			f.write('    "firsttime": %s, \n'  % network["firsttime"])
			f.write('    "lasttime": %s, \n' % network["lasttime"])
			f.write('    "lat": %s, \n' % network["lat"])
			f.write('    "lon": %s, \n' % network["lon"])
			f.write('    "manuf": %s, \n' % enc.encode(network["manuf"]))
			if "signal_dbm" in network:
				f.write('    "signal_dbm": {\n')
				f.write('      "last": %s, \n' % network["signal_dbm"]["last"])
				f.write('      "max": %s, \n' % network["signal_dbm"]["max"])
				f.write('      "min": %s\n' % network["signal_dbm"]["min"])
				f.write('    }, \n')
			f.write('    "ssid": %s, \n' % enc.encode(network["ssid"]))
			f.write('    "type": "%s"\n' % network["type"])
			if mac != macs[-1]:
				f.write('  }, \n')
			else:
				f.write('  }\n')
		f.write('}')
		f.close()
		
	def set_autosave(self, minutes, filename=None, notify=None):
		if filename is not None:
			self.autosave_filename = filename
		if notify is not None:
			self.autosave_notify = notify
		
		if self.autosave_task is not None:
			gobject.source_remove(self.autosave_task)
		
		if minutes > 0:
			self.autosave_task = gobject.timeout_add(minutes * 60 * 1000, self.save, self.autosave_filename, self.autosave_notify)
		
	def load(self, filename):
		f = open(filename)
		self.networks = json.load(f)
		f.close()
		
	def apply_filters(self):
		self.stop_queue()
		self.apply_filters_on_networks()
		self.disable_refresh()
		self.start_queue()
		
	def check_filter(self, network):
		if self.config["filter_type"][network["type"]] == False:
			return False
		
		crypts = decode_cryptset(network["cryptset"])
		if crypts == ["none"]:
			crypt = "none"
		elif "wpa" in crypts:
			crypt = "wpa"
		elif "wep" in crypts:
			crypt = "wep"
		else:
			crypt = "other"
		if self.config["filter_crypt"][crypt] == False:
			return False
		
		return True
		
	def apply_filters_on_networks(self, networks=None):
		if networks is None:
			networks = self.networks
		
		targets = {}
		for target in self.config["filter_networks"]:
			if target in self.notify_add_list:
				targets[target] = self.config["filter_networks"][target]
		
		for mac in networks:
			network = self.networks[mac]
			if self.check_filter(network):
				for target in targets:
					show = targets[target]
					if show == "all" or (show == "current" and mac in self.recent_networks):
						if mac not in self.notify_add_queue:
							self.notify_add_queue[mac] =  {}
						self.notify_add_queue[mac][target] = True
					else:
						self.notify_remove_list[target](mac)
			else:
				for target in self.notify_remove_list:
					self.notify_remove_list[target](mac)
		
	def notify_add(self, mac):
		if mac not in self.recent_networks:
			self.recent_networks.append(mac)
		
		self.apply_filters_on_networks((mac,))
		
	def disable_refresh(self):
		if self.refresh_disabled is True:
			return
		self.refresh_disabled = True
		for function in self.disable_refresh_functions:
			function()
		
	def notify_add_queue_process(self):
		self.queue_running = True
		start_time = time.time()
		counter = 0
		
		while self.queue_running:
			for mac in self.notify_add_queue.keys():
				for target in self.notify_add_queue[mac]:
					self.notify_add_list[target](mac)
				
				del self.notify_add_queue[mac]
				
				counter += 1
				if time.time()-start_time > 0.9:
					print "%s networks added in %ssec, %s networks left" % (counter, round(time.time()-start_time,3), len(self.notify_add_queue))
					yield True
					start_time = time.time()
					counter = 0
			if len(self.notify_add_queue) == 0:
				break
			
		self.queue_running = False
		self.queue_task = None
		if self.refresh_disabled is True:
			for function in self.resume_refresh_functions:
				function()
			self.refresh_disabled = False
		
		yield False
		
	def start_queue(self):
		if self.queue_task is not None or self.block_queue_start:
			return
		task = self.notify_add_queue_process()
		self.queue_task = gobject.idle_add(task.next)
		
	def stop_queue(self):
		self.queue_running = False
		if self.queue_task is not None:
			gobject.source_remove(self.queue_task)
			self.queue_task = None
		self.notify_add_queue = {}
		
	def add_bssid_data(self, bssid):
		mac = bssid["bssid"]
		if mac not in self.networks:
			network = {
				"type": decode_network_type(bssid["type"]),
				"channel": bssid["channel"],
				"firsttime": bssid["firsttime"],
				"lasttime": bssid["lasttime"],
				"lat": bssid["bestlat"],
				"lon": bssid["bestlon"],
				"manuf": bssid["manuf"],
				"ssid": "",
				"cryptset": 0,
				"signal_dbm": {
					"min": bssid["minsignal_dbm"],
					"max": bssid["maxsignal_dbm"],
					"last": bssid["signal_dbm"]
				}
			}
			self.networks[mac] = network
			if mac in self.temp_ssid_data:
				data = self.temp_ssid_data[mac]
				self.add_ssid_data(data)
				del self.temp_ssid_data[mac]
		else:
			network = self.networks[mac]
			if "signal_dbm" not in network:
				network["signal_dbm"] = {
					"min": bssid["minsignal_dbm"],
					"max": bssid["maxsignal_dbm"],
					"last": bssid["signal_dbm"]
					}
			
			if bssid["lasttime"] > network["lasttime"]:
				if bssid["gpsfixed"] == 1 and \
					network["signal_dbm"]["max"] < bssid["maxsignal_dbm"]:
						network["lat"] = bssid["bestlat"]
						network["lon"] = bssid["bestlon"]
				
				network["channel"] = bssid["channel"]
				network["lasttime"] = bssid["lasttime"]
				network["signal_dbm"]["last"] = bssid["signal_dbm"]
				
			network["firsttime"] = min(network["firsttime"], bssid["firsttime"])
			network["signal_dbm"]["min"] = min(network["signal_dbm"]["min"], bssid["minsignal_dbm"])
			network["signal_dbm"]["max"] = min(network["signal_dbm"]["max"], bssid["maxsignal_dbm"])
		
		self.notify_add(mac)
		
	def add_ssid_data(self, ssid):
		mac = ssid["mac"]
		if mac not in self.networks:
			self.temp_ssid_data[mac] = ssid
			return
		
		network = self.networks[mac]
		if ssid["lasttime"] >= network["lasttime"] or \
			(network["ssid"] == "" and network["cryptset"] == 0):
			network["cryptset"] = ssid["cryptset"]
			network["ssid"] = str(ssid["ssid"])
		
	def add_network_data(self, mac, data):
		if len(mac) != 17 or mac == "00:00:00:00:00:00":
			return
		
		if mac not in self.networks:
			self.networks[mac] = data
			self.notify_add(mac)
			return
			
		network = self.networks[mac]
		signal = False
		data_signal = False
		for search, result in ((network, signal), (data, data_signal)):
			if "signal_dbm" in search:
				result = True
		
		if data["lasttime"] > network["lasttime"]:
			newer = True
			network["channel"] = data["channel"]
			network["lasttime"] = data["lasttime"]
			network["cryptset"] = data["cryptset"]
			if signal and data_signal:
				network["signal_dbm"]["last"] = data["signal_dbm"]["last"]
		else:
			newer = False
		if (network["lat"] == 0.0 and network["lon"] == 0.0) or \
			(((signal and data_signal and network["signal_dbm"]["max"] < data["signal_dbm"]["max"]) or \
			(not signal and data_signal)) and data["lat"] != 0.0 and data["lon"] != 0.0):
				network["lat"] = data["lon"]
				network["lon"] = data["lon"]
		if newer or network["ssid"] == "":
			network["ssid"] = data["ssid"]
		
		if network["manuf"] == "":
			network["manuf"] = data["manuf"]
		
		network["firsttime"] = min(network["firsttime"], data["firsttime"])
		if signal and data_signal:
			network["signal_dbm"]["min"] = min(network["signal_dbm"]["min"], data["signal_dbm"]["min"])
			network["signal_dbm"]["max"] = min(network["signal_dbm"]["max"], data["signal_dbm"]["max"])
		elif data_signal:
			network["signal_dbm"] = data["signal_dbm"]
			
		self.notify_add(mac)
		
	def import_networks(self, filetype, filename):
		if filetype == "networks":
			parser = Networks(None)
			parser.parse = parser.load
		if filetype == "netxml":
			parser = Netxml()
		elif filetype == "csv":
			parser = CSV()
		
		parser.parse(filename)
		
		for mac in parser.networks:
			self.add_network_data(mac, parser.networks[mac])
		
		return len(parser.networks)
		
	def export_networks(self, export_format, filename, networks=None):
		if networks is None:
			networks = self.networks
		if export_format == "kismon":
			self.save_networks(filename, networks)
		elif export_format == "kismet netxml":
			self.export_networks_netxml(filename, networks)
		elif export_format == "google earth kmz":
			self.export_networks_kmz(filename, networks)
		elif export_format == "mappoint csv":
			self.export_networks_mappoint(filename, networks)
		
	def export_networks_netxml(self, filename, networks):
		locale.setlocale(locale.LC_TIME, 'C');
		f = open(filename, "w")
		f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
		f.write('<!DOCTYPE detection-run SYSTEM "http://kismetwireless.net/kismet-3.1.0.dtd">\n')
		f.write('<detection-run kismet-version="2009.06.R1" start-time="Sat Oct 24 09:05:35 2009">\n\n')
		
		num = 0
		for mac in networks:
			network = self.networks[mac]
			firsttime = timestamp2timestring(network["firsttime"])
			lasttime = timestamp2timestring(network["lasttime"])
			ssid = network["ssid"].replace("<","&lt;").replace(">","&gt;").replace("&","&amp;")
			manuf = "Unknown" if network["manuf"] == "" else network["manuf"].replace("&", "&amp;")
			f.write('<wireless-network number="%s" type="%s" first-time="%s" last-time="%s">\n' % \
				(num, network["type"], firsttime, lasttime)
				)
			f.write(' <SSID first-time="%s" last-time="%s">\n' % (firsttime, lasttime))
			
			crypts = decode_cryptset(network["cryptset"])
			if network["cryptset"] == 0:
				f.write('  <encryption>None</encryption>\n')
			if crypts == ["wep"]:
				f.write('  <encryption>WEP</encryption>\n')
			if "layer3" in crypts:
				f.write('  <encryption>Layer3</encryption>\n')
			if "wpa_migmode" in crypts:
				f.write('  <encryption>WPA Migration Mode</encryption>\n')
			if "wep40" in crypts:
				f.write('  <encryption>WEP40</encryption>\n')
			if "wep104" in crypts:
				f.write('  <encryption>WEP104</encryption>\n')
			if "tkip" in crypts:
				f.write('  <encryption>WPA+TKIP</encryption>\n')
			if "psk" in crypts:
				f.write('  <encryption>WPA+PSK</encryption>\n')
			if "aes_ocb" in crypts:
				f.write('  <encryption>WPA+AES-OCB</encryption>\n')
			if "aes_ccm" in crypts:
				f.write('  <encryption>WPA+AES-CCM</encryption>\n')
			if "leap" in crypts:
				f.write('  <encryption>WPA+LEAP</encryption>\n')
			if "ttls" in crypts:
				f.write('  <encryption>WPA+TTLS</encryption>\n')
			if "tls" in crypts:
				f.write('  <encryption>WPA+TLS</encryption>\n')
			if "peap" in crypts:
				f.write('  <encryption>WPA+PEAP</encryption>\n')
			if "isakmp" in crypts:
				f.write('  <encryption>ISAKMP</encryption>\n')
			if "pptp" in crypts:
				f.write('  <encryption>PPTP</encryption>\n')
			if "tls" in crypts:
				f.write('  <encryption>Fortress</encryption>\n')
			if "fortress" in crypts:
				f.write('  <encryption>Keyguard</encryption>\n')
			
			f.write('  <essid cloaked="%s">%s</essid>\n' % (True if ssid == "" else False, ssid ))
			
			f.write(' </SSID>\n')
			f.write(' <BSSID>%s</BSSID>\n' % mac)
			f.write(' <manuf>%s</manuf>\n' % manuf)
			f.write(' <channel>%s</channel>\n' % network["channel"])
			if "signal_dbm" in network:
				f.write(' <snr-info>\n')
				f.write('  <last_signal_dbm>%s</last_signal_dbm>\n' % network["signal_dbm"]["last"])
				f.write('  <min_signal_dbm>%s</min_signal_dbm>\n' % network["signal_dbm"]["min"])
				f.write('  <max_signal_dbm>%s</max_signal_dbm>\n' % network["signal_dbm"]["max"])
				f.write(' </snr-info>\n')
			if network["lat"] != 0 and network["lon"] != 0:
				f.write(' <gps-info>\n')
				f.write('  <min-lat>%s</min-lat>\n' % network["lat"])
				f.write('  <min-lon>%s</min-lon>\n' % network["lon"])
				f.write('  <max-lat>%s</max-lat>\n' % network["lat"])
				f.write('  <max-lon>%s</max-lon>\n' % network["lon"])
				f.write('  <peak-lat>%s</peak-lat>\n' % network["lat"])
				f.write('  <peak-lon>%s</peak-lon>\n' % network["lon"])
				f.write('  <avg-lat>%s</avg-lat>\n' % network["lat"])
				f.write('  <avg-lon>%s</avg-lon>\n' % network["lon"])
				f.write(' </gps-info>\n')
			f.write('</wireless-network>\n')
			num += 1
		
		f.write('</detection-run>')
		f.close()
		locale.setlocale(locale.LC_TIME, '')
		
	def export_networks_kmz(self, filename, networks):
		kml_folder = """
<Folder>
<name>%s: %s APs</name>
<Style id="%s"><IconStyle><scale>0.5</scale>
<Icon>")
<href>http://files.salecker.org/kismon/images/%s.gif</href>
</Icon></IconStyle></Style>
%s
</Folder>"""
		data = []
		zip_output = zipfile.ZipFile(filename, "w")
		data.append("<?xml version='1.0' encoding='UTF-8'?>\r\n")
		data.append("<kml xmlns='http://earth.google.com/kml/2.1'>\r\n")
		data.append("<Document>\r\n")
		data.append("<name>Kismon</name>\r\n")
		data.append("<open>1</open>")
		
		count = {"WPA":0, "WEP":0, "None":0, "Other":0}
		folders = self.export_networks_kmz_folders(count, networks)
		
		for crypt in ("WPA", "WEP", "None", "Other"):
			if crypt == "WPA":
				pic = "WPA"
			elif crypt == "WEP":
				pic = "WEP"
			else:
				pic = "Open"
			
			data.append(kml_folder %(
				crypt,
				count[crypt],
				crypt,
				pic,
				"".join(folders[crypt])
			))
		data.append("\r\n</Document>\r\n</kml>")
		
		zinfo = zipfile.ZipInfo("kismon.kml")
		zinfo.compress_type = zipfile.ZIP_DEFLATED
		zip_output.writestr(zinfo, "".join(data))
		zip_output.close()
		
	def export_networks_kmz_folders(self, count, networks):
		kml_placemark = """<Placemark><styleUrl>#%s</styleUrl><name>%s</name>
<Point><coordinates>%s,%s</coordinates></Point>
<description><![CDATA[
SSID: %s<br />
MAC: %s<br />
Manuf: %s<br />
Type: %s<br />
Channel: %s<br />
Encryption: <FONT color=%s>%s</FONT><br />
Last time: %s<br />
GPS: %s,%s]]></description></Placemark>"""
		
		folders = {"WPA":[], "WEP":[], "None":[], "Other":[]}
		colors = {"WPA":"red", "WEP":"orange", "None":"green", "Other":"grey"}
		for mac in networks:
			network = self.networks[mac]
			if network["lat"] == 0 and network["lon"] == 0:
				continue
			
			ssid = network["ssid"].replace("<","&lt;").replace(">","&gt;").replace("&","&amp;")
			
			crypts = decode_cryptset(network["cryptset"])
			crypt = "Other"
			for c in crypts:
				if c.startswith("wpa"):
					crypt = "WPA"
			if crypt != "Other":
				pass
			elif "wep" in crypts:
				crypt = "WEP"
			elif "none" in crypts:
				crypt = "None"
			
			folders[crypt].append(kml_placemark %(
				crypt, ssid, network["lon"],network["lat"], ssid, mac,
				network["manuf"], network["type"], network["channel"],
				colors[crypt], ",".join(crypts).upper(), show_timestamp(network["lasttime"]),
				network["lat"], network["lat"],
			))
			count[crypt] += 1
		return folders
		
	def export_networks_mappoint(self, filename, networks):
		f = open(filename, "w")
		
		f.write('Latitude;Longitude;SSID;BSSID;Encryption;Channel;Last Seen;\n')
		for mac in networks:
			network = self.networks[mac]
			gps = "%s;%s" % (network["lat"], network["lon"])
			f.write('%s;%s;%s;%s;%s;%s;\n' % (
				gps.replace(".",","), network["ssid"].replace(";"," "),
				mac, print_cryptset(network["cryptset"]), network["channel"], show_timestamp(network["lasttime"])
				))
		f.close()
		
def print_cryptset(cryptset):
	crypts = decode_cryptset(cryptset)
	crypt = "Other"
	
	if "aes_ccm" in crypts:
		crypt = "WPA2"
	elif "wpa" in crypts:
		crypt = "WPA"
	elif "wep" in crypts:
		crypt = "WEP"
	elif "none" in crypts:
		crypt = "None"
	
	return crypt

class Netxml:
	def __init__(self):
		self.networks = {}
		
	def parse(self, filename):
		self.parser={
			"laststart": "",
			"parents": [],
			"network": None,
			"encryption": {}
			}
		locale.setlocale(locale.LC_TIME, 'C');
		
		p = xml.parsers.expat.ParserCreate()
		p.buffer_text = True #avoid chunked data
		p.returns_unicode = False #disabled Unicode support is much faster
		p.StartElementHandler = self.parse_start_element
		p.EndElementHandler = self.parse_end_element
		p.CharacterDataHandler = self.parse_char_data
		if os.path.isfile(filename):
			p.ParseFile(open(filename))
		else:
			print "Parser: filename is not a file (%s)" % filename
		
		locale.setlocale(locale.LC_TIME, '')
	
	def parse_start_element(self, name, attrs):
		"""<name attr="">
		"""
		if name == "wireless-network":
			self.parser["network"] = network = {
				"type": attrs["type"],
				"firsttime": timestring2timestamp(attrs["first-time"]),
				"lasttime": timestring2timestamp(attrs["last-time"]),
				"ssid": "",
				"cryptset": 0,
				"lat": 0.0,
				"lon": 0.0,
				"signal_dbm": {}
			}
		elif name == "SSID":
			self.parser["encryption"] = {}
			
		self.parser["parents"].insert(0, self.parser["laststart"])
		self.parser["laststart"] = name
		
	def parse_end_element(self, name):
		"""</name>
		"""
		if name == "wireless-network":
			mac = self.parser["network"]["mac"]
			del self.parser["network"]["mac"]
			self.networks[mac]=self.parser["network"]
		elif name == "SSID":
			if len(self.parser["encryption"]) > 0:
				if self.parser["parents"][0] =="wireless-network":
					crypts = []
					for crypt in self.parser["encryption"]:
						if crypt.startswith("WPA"):
							if "wpa" not in crypts:
								crypts.append("wpa")
							if crypt.startswith("WPA+"):
								crypts.append(crypt.split("+")[1].lower().replace("-","_"))
						else:
							crypts.append(crypt.lower().replace("-","_"))
					cryptset = encode_cryptset(crypts)
					self.parser["network"]["cryptset"] = cryptset
			del self.parser["encryption"]
		
		self.parser["laststart"] = self.parser["parents"].pop(0)
		
	def parse_char_data(self, data):
		"""<self.parser["laststart"]>data</self.parser["laststart"]>
		"""
		if data.strip() == "":
			return
		
		if self.parser["parents"][0] == "SSID":
			if self.parser["laststart"] == "encryption":
				self.parser["encryption"][data] = True
			elif self.parser["laststart"] == "essid":
				self.parser["network"]["ssid"] = data
		elif self.parser["parents"][1] == "wireless-network":
			if self.parser["parents"][0] == "gps-info":
				if self.parser["laststart"] == "peak-lat":
					self.parser["network"]["lat"] = float(data)
				elif self.parser["laststart"] == "peak-lon":
					self.parser["network"]["lon"] = float(data)
			elif self.parser["parents"][0]=="snr-info":
				if self.parser["laststart"] == "min_signal_dbm":
					self.parser["network"]["signal_dbm"]["min"] = int(data)
				elif self.parser["laststart"] == "max_signal_dbm":
					self.parser["network"]["signal_dbm"]["max"] = int(data)
				elif self.parser["laststart"] == "last_signal_dbm":
					self.parser["network"]["signal_dbm"]["last"] = int(data)
		elif self.parser["parents"][0] == "wireless-network":
			if self.parser["laststart"] == "BSSID":
				self.parser["network"]["mac"] = data
			elif self.parser["laststart"] == "channel":
				self.parser["network"]["channel"] = int(data)
			elif self.parser["laststart"] == "manuf":
				self.parser["network"]["manuf"] = data

class CSV:
	def __init__(self):
		self.networks = {}
		
	def parse(self, filename):
		locale.setlocale(locale.LC_TIME, 'C');
		f = open(filename)
		head = f.readline().split(";")[:-1]
		for line in f.readlines():
			x = 0
			data = {}
			for column in line.split(";")[:-1]:
				data[head[x]] = column
				x += 1
			
			crypts = []
			for crypt in data["Encryption"].split(","):
				crypts.append(crypt.lower().replace("-","_"))
				
			self.networks[data["BSSID"]] = {
				"type": data["NetType"],
				"channel": int(data["Channel"]),
				"firsttime": timestring2timestamp(data["FirstTime"]),
				"lasttime": timestring2timestamp(data["LastTime"]),
				"lat": float(data["GPSBestLat"]),
				"lon": float(data["GPSBestLon"]),
				"manuf": "",
				"ssid": data["ESSID"],
				"cryptset": encode_cryptset(crypts)
			}
		locale.setlocale(locale.LC_TIME, '')

def timestring2timestamp(timestring):
	return int(time.mktime(time.strptime(timestring)))
	
def timestamp2timestring(timestamp):
	return time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(timestamp))

if __name__ == "__main__":
	import test
	test.networks()
