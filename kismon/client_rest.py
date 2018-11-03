#!/usr/bin/env python3
"""
Copyright (c) 2018, Patrick Salecker
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
import os
import KismetRest

class RestClient:
    def __init__(self):
        self.debug = False
        self.uri = "http://127.0.0.1:2501"
        self.connector = None
        self.connected = False
        self.authenticated = False
        self.credentials = None
        self.timestamp = {
            'devices': 0,
            'messages': 0,
        }
        self.queue = {}
        self.empty_queue()
        self.error = []

    def empty_queue(self):
        self.queue = {
            'dot11': [],
            'status': None,
            'location': [],
            'messages': [],
            'datasources': {},
        }

    def start(self):
        """Open connection to the server
        """
        sessioncache_path = "~/.kismon/kismet-session-%s" % ''.join(e if e.isalnum() else '-' for e in self.uri)
        self.connector = KismetRest.KismetConnector(self.uri, sessioncache_path=sessioncache_path)
        print("Client: start %s" % self.uri)
        if not self.update_system_status():
            return False
        self.connected = True

    def stop(self):
        """Close connection to the server
        """
        print("Client: stop")
        self.connected = False

    def _callback(self, device):
        #print(device['dot11.device']['dot11.device.last_beaconed_ssid'])
        self.queue['dot11'].append(device)

    def get_updated_devices(self, queue_list=None):
        fields = [
            'dot11.device',
            'kismet.device.base.key',
            'kismet.device.base.macaddr',
            'kismet.device.base.first_time',
            'kismet.device.base.last_time',
            'kismet.device.base.channel',
            'kismet.device.base.manuf',
            'kismet.device.base.signal/kismet.common.signal.last_signal',
            'kismet.device.base.signal/kismet.common.signal.min_signal',
            'kismet.device.base.signal/kismet.common.signal.max_signal',
            'kismet.device.base.signal/kismet.common.signal.type',
            'kismet.device.base.location',
            'kismet.device.base.seenby',
        ]
        if queue_list:
            self.queue = queue_list

        new_timestamp = time.time()
        time_diff = int(self.timestamp['devices'] - new_timestamp - 1)
        self.connector.smart_device_list(callback=self._callback, fields=fields, ts=time_diff)
        self.timestamp['devices'] = new_timestamp

    def loop(self):
        while self.connected is True:
            self.get_updated_devices()
            self.update_system_status()
            self.update_location()
            self.queue_new_messages()
            self.update_datasources()
            for name in self.queue:
                print("'%s': " % name, self.queue[name])
            self.empty_queue()
            time.sleep(1)

    def update_system_status(self):
        try:
            status = self.connector.system_status()
        except Exception as e:
            self.connected = False
            print("Client: failed to connect")
            print(e)
            self.error.append("failed to connect: %s" % e)
            return False
        self.queue['status'] = status
        return True

    def update_location(self):
        self.queue['location'].append(self.connector.location())

    def queue_new_messages(self):
        messages = self.connector.messages(ts_sec=self.timestamp['messages'])
        self.timestamp['messages'] = int(time.time())
        self.queue['messages'].extend(messages['kismet.messagebus.list'])

    def update_datasources(self):
        self.queue['datasources'] = self.connector.datasources()

    def authenticate(self):
        print("authenticating...")
        if not self.credentials:
            print('no credentials')
            return False

        self.connector.set_login(self.credentials[0], self.credentials[1])
        response = self.connector.login()
        if response == False:
            self.authenticated = False
            print("login failed")
            return False
        self.authenticated = True
        print("authenticated")
        return True

    def set_channel(self, uuid, mode, value):
        print('set_channel', uuid, mode, value)
        if not self.connected:
            print('not connected')
            return False

        if not self.authenticated:
            if not self.authenticate():
                return False

        if mode == 'lock':
            self.connector.config_datasource_set_channel(uuid=uuid, channel=str(value))
        elif mode == 'hop':
            self.connector.config_datasource_set_hop_rate(uuid=uuid, rate=value)

class RestClientThread(threading.Thread):
    def __init__(self, uri=None):
        threading.Thread.__init__(self)
        self.debug = False
        self.client = RestClient()
        self.is_running = False
        if uri is not None:
            self.client.uri = uri

    def stop(self):
        self.is_running = None
        if self.client.connected is True:
            self.client.stop()

    def get_queue(self, name):
        try:
            return self.client.queue[name]
        except KeyError:
            print("queue %s absent" % name)
            return False

    def run(self):
        self.is_running = True
        self.client.error = []
        if self.client.start() is False:
            self.stop()
        while self.is_running is True and (self.client.connected is True):
            self.client.get_updated_devices()
            self.client.update_system_status()
            self.client.update_location()
            self.client.queue_new_messages()
            self.client.update_datasources()
            #print(self.client.queue)
            time.sleep(1)
        self.stop()


def get_crypt_list():
    """see packet_ieee80211.h from kismet-newcore
    """
    cryptsets = ["none", "unknown", "wep", "layer3 ", "wep40", "wep104",
                 "tkip", "wpa", "psk", "aes_ocb", "aes_ccm", "leap", "ttls",
                 "peap", "pptp", "fortress", "keyguard", "unknown_nonwep",
                 "wpa_migmode", "version_wpa", "version_wpa2"]

    return cryptsets


def encode_cryptset(crypts):
    cryptsets = get_crypt_list()
    bin_cryptset = []
    for crypt in cryptsets:
        if crypt in crypts:
            bit = "1"
        else:
            bit = "0"
        bin_cryptset.insert(0, bit)
    cryptset = int("".join(bin_cryptset[:-1]), 2)
    return cryptset


def decode_cryptset(cryptset, str=False):
    cryptsets = get_crypt_list()
    if cryptset == 0:
        if str is True:
            return cryptsets[cryptset]
        else:
            return [cryptsets[cryptset]]

    crypts = []
    pos = 1
    bin_cryptset = bin(cryptset)[2:][::-1]
    for bit in bin_cryptset:
        if bit == "1":
            try:
                crypts.append(cryptsets[pos])
            except IndexError:
                pass
        pos += 1

    if str is True:
        return ",".join(crypts).upper()
    else:
        return crypts


def decode_network_typeset(num):
    """see phy_80211.h from kismet
    """
    types = {0: 'generic', 1: 'infrastructure', 2: 'client', 3: 'infrastructure', 4: 'wired', 8: 'ad-hoc'}
    try:
        return types[num]
    except KeyError:
        print("fixme: unkown type num %s" % num)
        return False


if __name__ == "__main__":
    client = RestClient()
    client.debug = True
    client.start()
    try:
        client.loop()
    except KeyboardInterrupt:
        client.stop()
    print("end")
