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

import ConfigParser

class Config:
	def __init__(self, config_file):
		self.config_file = config_file
		
		self.default_config={
			"kismet": {
				"server": "127.0.0.1:2501",
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
				"marker_style": "image",
				"follow_gps": True,
				"source": "osm-mapnik",
				"osm_file": "",
				"memphis_rules": "default",
				"update_marker_positions": True,
				"last_position": "0/0"
				},
			"networks": {
				"autosave": 5,
				},
			"filter_networks": {
				"network_list": "current",
				"map": "current",
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
				"other": True,
				},
			}
	
	def read(self):
		#print "reading config %s" % self.config_file
		self.config = self.default_config
		config = ConfigParser.RawConfigParser()
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
						print "Old config entry: %s" % key
						continue
					if valtype == bool:
						if value in ("True", "true"):
							value = True
						else:
							value = False
					elif valtype == int:
						value = int(value)
					self.config[section][key] = value
	
	def write(self):
		#print "writing config %s" % self.config_file
		config = ConfigParser.SafeConfigParser()
		
		for section in self.config:
			config.add_section(section)
			for key in self.config[section]:
				config.set(section, key, str(self.config[section][key]))
		
		configfile = open(self.config_file, 'wb')
		config.write(configfile)
		
	def show(self):
		txt="\n"
		for section in self.config:
			txt += section+" :\n"
			for key in self.config[section]:
				txt += "\t%s = %s\n" % (key, self.config[section][key])
		return txt
	
if __name__ == "__main__":
	import test
	test.config()
