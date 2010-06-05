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

import socket
import sys
import threading
import time

class Client:
	def __init__(self):
		self.debug = False
		self.server = "127.0.0.1:25011"
		self.connected = False
		self.response_id = 1
		self.error = []
		self.dump = None
		self.replay_dump = None
		self.s = None
		
	def set_capabilities(self, capabilities):
		"""
		'ERROR', 'TERMINATE', 'TIME', 'PACKET', 'STATUS', 'PLUGIN',
		'SOURCE', 'ALERT', 'WEPKEY', 'STRING', 'GPS', 'SPECTRUM',
		'BSSID', 'SSID', 'CLIENT', 'BSSIDSRC', 'CLISRC', 'REMOVE',
		'CHANNEL', 'INFO'
		"""
		self.capabilities = {}
		for cap in capabilities:
			self.capabilities[cap.lower()] = ()
			
	def enable_dump(self):
		filename = "/tmp/kismet-rawdump-%s.dump" % int(time.time())
		print "Client: Dump %s" % filename
		self.dump = open(filename, "w")
		return filename
		
	def load_dump(self, filename):
		print "Client: replay dump %s" % filename
		self.replay_dump = open(filename, "r")
		self.stop()
		
	def start(self):
		"""Open connection to the server
		"""
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print "Client: start %s" % self.server
		try:
			host, port = self.server.split(":")
			port = int(port)
		except ValueError:
			self.error.append("Invalid server %s" % self.server)
			print "Client: %s" % self.error[-1]
			self.stop()
			return False
		try:
			self.s.connect((host, port))
			self.connected = True
			return True
		except socket.error:
			self.error.append("Open connection to %s failed: %s" % \
				(self.server, sys.exc_info()[1]))
			print "Client: %s" % self.error[-1]
			self.stop()
			return False
	
	def stop(self):
		"""Close connection to the server
		"""
		print "Client: stop"
		self.connected = False
		if self.s is not None:
			self.s.close()
		if self.dump is not None:
			self.dump.close()
			self.dump = None
		
	def send(self, msg):
		"""Send a message to the server
		"""
		if self.connected is False:
			return
		
		self.s.send(msg)
		if self.debug is True:
			print "Send: %s" % msg
	
	def loop(self):
		while self.connected is True or self.replay_dump is not None:
			data = self.receive_data()
			for line in data:
				if line == "":
					continue
				result = self.parse_line(line)
				if result is False:
					break
				elif result is not None and self.debug is True:
					print '("%s", %s),' % (result[0], result[1])
	
	def receive_data(self):
		if self.replay_dump is not None:
			data = self.replay_dump.readline()
			return data.split("\n")
		
		data = self.s.recv(0x10000)
		if data == "":
			print "Client: no data recieved from kismet server"
			self.stop()
			return False
		
		while not data.endswith("\n") and self.connected is True:
			data += self.s.recv(0x10000)
		
		if self.dump is not None:
			self.dump.write(data)
		
		return data.split("\n")
		
	def split_line(self, line):
		data = line[1].split()
		columns = []
		combine = False
		
		while len(data) > 0:
			row = data[0]
			if row == "\x01\x01":
				columns.append("<empty>")
				
			elif combine is False:
				if row == "\x01" or (row.startswith("\x01") and not row.endswith("\x01")):
					string = row
					combine = True
				else:
					columns.append(row.strip("\x01"))
					
			elif combine is True:
				string += " " + row
				if "\x01" in row:
					columns.append(string.strip("\x01"))
					combine = False
			del data[0]
			
		return columns
	
	def parse_line(self, line):
		line = line.split(": ", 1)
		cap = line[0][1:].lower()
		data = {}
		if cap in self.capabilities:
			columns = self.split_line(line)
			
			y = 0
			for column in columns:
				if column == "":
					continue
					
				try:
					column = float(column)
					if column == int(column):
						column = int(column)
				except:
					pass
				if y < len(self.capabilities[cap]):
					data[self.capabilities[cap][y]] = column
				else:
					print "Parser error:", cap, y, len(columns), \
						len(self.capabilities[cap]), data
				y += 1
			
			return cap, data
				
		elif line[0] == "*TERMINATE":
			print "Client: Server shutdown"
			return "stop", True
			
		elif line[0] == "*PROTOCOLS":
			response = ""
			for cap in self.capabilities:
				response += "!%i CAPABILITY %s\n" % (self.response_id, cap.upper())
				self.response_id += 1
			self.send(response)
			
		elif line[0] == "*CAPABILITY":
			# get column headers and enable capabilities
			foo = line[1].split()
			self.capabilities[foo[0].lower()] = foo[1].split(",")
			response = "!%i ENABLE %s %s\n" % \
				(self.response_id, foo[0] ,",".join(self.capabilities[foo[0].lower()]))
			self.response_id += 1
			self.send(response)
		
class ClientThread(threading.Thread):
	def __init__ (self, server=None):
		threading.Thread.__init__(self)
		self.debug = False
		self.client = Client()
		self.is_running = False
		self.queue = []
		if server != None:
			self.client.server = server
	
	def stop(self):
		self.is_running = None
		if self.client.connected is True:
			self.client.stop()
		self.queue.append(("stop", True))
	
	def run(self):
		self.is_running = True
		self.client.error = []
		if self.client.start() is False and self.client.replay_dump is None:
			self.stop()
		while self.is_running is True and (self.client.connected is True or self.client.replay_dump is not None):
			data = self.client.receive_data()
			if data is False:
				self.stop()
				break
			for line in data:
				if line == "":
					continue
				
				result = self.client.parse_line(line)
				if result is None:
					continue
				elif result[0] == "stop":
					self.stop()
				if self.debug is True:
					print "%s: %s" % (result[0], result[1])
				self.queue.append(result)
			
def decode_cryptset(cryptset):
	"""see packet_ieee80211.h from kismet-newcore
	"""
	cryptsets=["none", "unknown", "wep", "layer3 ", "wep40", "wep104",
		"tkip", "wpa", "psk", "aes_ocb", "aes_ccm", "leap", "ttls",
		"peap", "pptp", "fortress", "keyguard"]
	try:
		cryptset = int(cryptset)
	except:
		return False
	crypts = []
	binlist = []
	if cryptset == 0:
		return [cryptsets[cryptset]]
	#byte shifting (>>)
	while cryptset>0:
		binlist.append(cryptset % 2)
		cryptset = cryptset >> 1
	pos = 1
	for bit in binlist:
		if bit == 1:
			if len(cryptsets) > pos:
				crypts.append(cryptsets[pos])
		pos += 1
	return crypts
	
def decode_network_type(num):
	"""see netracker.h from kismet-newcore
	"""
	types = {0:"infrastructure", 1:"ad-hoc", 2:"probe", 4:"data"}
	if num in types:
		return types[num]
	else:
		return False
	
if __name__ == "__main__":
	client = Client()
	client.debug = True
	client.set_capabilities(('status', 'source', 'info', 'bssid', 'ssid', 'gps'))
	dumpfile = client.enable_dump()
	client.start()
	try:
		client.loop()
	except KeyboardInterrupt:
		client.stop()
		print "Client: dump %s" % dumpfile
