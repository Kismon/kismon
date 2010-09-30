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

import json
from client import *

class Networks:
	def __init__(self):
		self.networks = {}
		
	def get_network(self, mac):
		return self.networks[mac]
		
	def save(self, filename):
		f = open(filename, "w")
		json.dump(self.networks, f, sort_keys=True, indent=2)
		f.close()
		
	def load(self, filename):
		f = open(filename)
		self.networks = json.load(f)
		f.close()
		
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
					"last": bssid["maxsignal_dbm"]
				}
			}
			self.networks[mac] = network
		else:
			network = self.networks[mac]
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
			
		
	def add_ssid_data(self, ssid):
		mac = ssid["mac"]
		if mac not in self.networks:
			return
		
		network = self.networks[mac]
		if ssid["lasttime"] >= network["lasttime"] or \
			(network["ssid"] == "" and network["cryptset"] == 0):
			network["cryptset"] = ssid["cryptset"]
			network["ssid"] = str(ssid["ssid"])

if __name__ == "__main__":
	import test
	test.networks()
