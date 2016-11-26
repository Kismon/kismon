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

import configparser
import json
import os

class Config:
	def __init__(self, config_file):
		self.config_file = config_file
		
		self.default_config={
			"kismet": {
				"servers": ["127.0.0.1:2501"],
				"connect": True
				},
			"window": {
				"maximized": False,
				"width": 800,
				"height": 600,
				"map_position": "hide",
				"log_list_max": 50,
				},
			"map": {
				"source": "openstreetmap",
				"update_marker_positions": True,
				"last_position": "0/0",
				"last_zoom": 12,
				"custom_source_url": "http://localhost:8080/#Z/#X/#Y.png",
				"custom_source_min": 12,
				"custom_source_max": 17,
				},
			"networks": {
				"autosave": 5,
				},
			"tracks": {
				"store": False,
				},
			"filter_networks": {
				"network_list": "current",
				"map": "current",
				"export": "all"
				},
			"filter_type": {
				"infrastructure": True,
				"probe": False,
				"data": False,
				"ad-hoc": False,
				},
			"filter_crypt": {
				"none": True,
				"wep": True,
				"wpa": True,
				"wpa2": True,
				"other": True,
				},
			"filter_regexpr": {
				"ssid": "",
				"bssid": "",
				}
			}
	
	def read_ini(self):
		#print "reading config %s" % self.config_file
		self.config = self.default_config
		config = configparser.RawConfigParser()
		config.read(self.config_file)
		config_sections = config.sections()
		
		for section in self.config:
			if section in config_sections:
				items = config.items(section)
				if len(items) == 0:
					continue
				for key, value in items:
					try:
						valtype = type(self.config[section][key])
					except KeyError:
						print("Old config entry: %s" % key)
						continue
					if valtype == bool:
						if value in ("True", "true"):
							value = True
						else:
							value = False
					elif valtype == int:
						value = int(value)
					elif valtype == list:
						value = [v.strip() for v in value.split(",")]
					self.config[section][key] = value
	
	def read(self):
		self.config = self.default_config
		if not os.path.isfile(self.config_file):
			print("config file %s not found, continuing with default settings" % self.config_file)
			return

		with open(self.config_file, 'r') as f:
			first_line = f.readline()
		if first_line.startswith('['):
			# old ini style config
			print('loading ini config')
			self.read_ini()
		elif first_line.startswith('{'):
			# new json config
			print('loading json config')
			with open(self.config_file, 'r') as f:
				loaded_config = json.load(f)
			self.config.update(loaded_config)
		else:
			print('unknown config format, using default')
			return

	def write(self):
		print('writing json config')
		with open(self.config_file, 'w') as f:
			json.dump(self.config, f, indent=2)

if __name__ == "__main__":
	from test import TestKismon
	TestKismon.test_config(True)
