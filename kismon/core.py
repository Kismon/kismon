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
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib

from kismon.client_rest import *
from kismon.gui import MainWindow
from kismon.config import Config
from kismon.networks import Networks
from kismon.tracks import Tracks
import kismon.utils as utils


def check_osmgpsmap():
    try:
        gi.require_version('OsmGpsMap', '1.0')
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

        self.sources = {}
        self.crypt_cache = {}
        self.networks = Networks(self.config)
        self.client_threads = {}
        self.init_client_threads()
        self.tracks = Tracks("%stracks.json" % user_dir)
        self.tracks.load()

        if "--disable-map" in sys.argv:
            self.map_error = "--disable-map used"
        else:
            self.map_error = check_osmgpsmap()

        if self.map_error is not None:
            self.map_error = "%s\nMap disabled" % self.map_error
            print(self.map_error, "\n")

        self.init_map()

        self.main_window = MainWindow(self.config,
                                      self.client_start,
                                      self.client_stop,
                                      self.map,
                                      self.networks,
                                      self.sources,
                                      self.tracks,
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
                dialog_message = "Could not read the networks file '%s':\n%s\n\nDo you want to continue?" % (
                self.networks_file, error)
                dialog = Gtk.MessageDialog(self.main_window.gtkwin, Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                           Gtk.MessageType.ERROR, Gtk.ButtonsType.YES_NO, dialog_message)

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
        self.networks.set_autosave(self.config["networks"]["autosave"], self.networks_file,
                                   self.main_window.log_list.add)

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
            from kismon.map import Map
            user_agent = 'kismon/%s' % utils.get_version()
            self.map = Map(self.config["map"], user_agent=user_agent)
            self.map.set_last_from_config()

    def init_client_thread(self, server_id):
        server = self.config["servers"][server_id]
        server['id'] = server_id
        self.client_threads[server_id] = RestClientThread(server['uri'])
        if server['username'] != '' and server['password'] != '':
            self.client_threads[server_id].client.credentials = (server['username'], server['password'])

    def init_client_threads(self):
        server_id = 0
        for server in self.config["servers"]:
            self.init_client_thread(server_id)
            server_id += 1

    def client_start(self, server_id):
        if server_id in self.client_threads and self.client_threads[server_id].is_running:
            self.client_stop(server_id)
        self.sources[server_id] = {}
        self.init_client_thread(server_id)
        self.client_threads[server_id].start()

    def client_stop(self, server_id):
        self.client_threads[server_id].stop()

    def clients_stop(self):
        for server_id in self.client_threads:
            self.client_stop(server_id)
        return True

    def queue_handler(self, server_id):
        server = self.config['servers'][server_id]
        if self.main_window.gtkwin is None:
            return False

        thread = self.client_threads[server_id]
        if len(thread.client.error) > 0:
            for error in thread.client.error:
                self.main_window.log_list.add(server['uri'], error)
            thread.client.error = []
            self.main_window.server_tabs[server_id].server_switch.set_active(False)
            page_num = self.main_window.notebook.page_num(self.main_window.log_list.widget)
            self.main_window.notebook.set_current_page(page_num)

        # info
        status = thread.get_queue('status')
        if status:
            self.main_window.server_tabs[server_id].update_info_table(devices=status['kismet.system.devices.count'])

        # gps
        gps = None
        gps_queue = thread.get_queue("location")

        while len(gps_queue) > 0:
            data = gps_queue.pop(0)
            if not data:
                continue

            if data['kismet.common.location.valid'] == 0:
                continue
            gps = {'lat': data['kismet.common.location.lat'],
                   'lon': data['kismet.common.location.lon'],
                   'alt': data['kismet.common.location.alt'],
                   'fix': data['kismet.common.location.fix'],
                   }
            if data['kismet.common.location.fix'] > 1:
                if self.config['tracks']['store']:
                    self.tracks.add_point_to_track(server['uri'], gps['lat'], gps['lon'], gps['alt'])
                if self.map:
                    self.map.add_track(gps['lat'], gps['lon'], server_id)
        if gps:
            self.main_window.server_tabs[server_id].update_gps_table(lat=gps['lat'], lon=gps['lon'], fix=gps['fix'])
            if gps['fix'] > 1 and self.map:
                server_key = "server%s" % (server_id + 1)
                if server_id == 0:
                    self.map.set_position(gps['lat'], gps['lon'])
                else:
                    self.map.add_marker(server_key, server_key, gps['lat'], gps['lon'])

        message_queue = thread.get_queue("messages")
        while len(message_queue) > 0:
            message = message_queue.pop(0)
            self.main_window.log_list.add(origin=server['uri'], message=message['kismet.messagebus.message_string'],
                                          timestamp=message['kismet.messagebus.message_time'])

        datasources = thread.get_queue('datasources')
        if len(datasources) == 0:
            # print("no active datasources")
            if type(self.main_window.server_tabs[server_id].datasources_dialog_answer) == bool:
                # question was already asked
                pass
            elif not thread.client.connected:
                # not connected
                pass
            elif self.datasources_dialog(server_id):
                self.main_window.server_tabs[server_id].on_manage_datasources()

        sources_updated = False
        for ds in datasources:
            uuid = ds['kismet.datasource.uuid']
            source = {
                'type': ds['kismet.datasource.hardware'],
                'packets': ds['kismet.datasource.num_packets'],
                'channel': ds['kismet.datasource.channel'],
                'hop': ds['kismet.datasource.hopping'],
                'hop_rate': ds['kismet.datasource.hop_rate'],
                'running': ds['kismet.datasource.running'],
                'name': ds['kismet.datasource.name'],
                'uuid': uuid,
            }
            # print(source)
            if uuid in self.sources[server_id] and source['packets'] != self.sources[server_id][uuid]['packets']:
                sources_updated = True
            self.sources[server_id][uuid] = source

        if sources_updated is True:
            self.main_window.server_tabs[server_id].update_sources_table(self.sources[server_id])

    def datasources_dialog(self, server_id):
        dialog_message = "The Kismet instance %s seems to have no active interfaces.\nDo you want to activate them now? *\n\n* Requires authentification" % (
        self.config["servers"][server_id]['uri'])
        dialog = Gtk.MessageDialog(self.main_window.gtkwin, Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.QUESTION,
                                   Gtk.ButtonsType.YES_NO, dialog_message)

        def dialog_response(dialog, response_id):
            answer = False
            if response_id == -8:
                answer = True
                print("yes")
            else:
                print("no", response_id)
            self.main_window.server_tabs[server_id].datasources_dialog_answer = answer

        dialog.connect("response", dialog_response)
        dialog.run()
        dialog.destroy()
        return self.main_window.server_tabs[server_id].datasources_dialog_answer

    def queues_handler(self):
        for server_id in self.client_threads:
            self.queue_handler(server_id)
        return True

    def queue_handler_networks(self, server_id):
        thread = self.client_threads[server_id]

        queue = thread.get_queue("dot11")
        for x in range(0, len(queue)):
            device = queue.pop(0)
            self.networks.add_device_data(device, server_id)
            mac = device['kismet.device.base.macaddr']

            for sid in device['kismet.device.base.seenby']:
                source = device['kismet.device.base.seenby'][sid]
                source_uuid = source['kismet.common.seenby.uuid']
                if source_uuid not in self.sources[server_id]:
                    continue
                if mac not in self.main_window.signal_graphs:
                    continue

                if source['kismet.common.seenby.signal']['kismet.common.signal.type'] != 'dbm':
                    continue
                self.main_window.signal_graphs[mac].add_value(source_data=self.sources[server_id][source_uuid],
                                                              packets=source['kismet.common.seenby.num_packets'],
                                                              signal=source['kismet.common.seenby.signal'][
                                                                  'kismet.common.signal.last_signal'],
                                                              timestamp=source['kismet.common.seenby.last_time'],
                                                              server_id=server_id)

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

        if self.map is not None:
            lat = self.map.osm.get_property("latitude")
            lon = self.map.osm.get_property("longitude")
            self.config["map"]["last_position"] = "%.6f/%.6f" % (lat, lon)

        while None in self.config['servers']:
            self.config['servers'].remove(None)
        self.config_handler.write()
        self.networks.save(self.networks_file, force=True)
        if self.config['tracks']['store']:
            self.tracks.save()

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

        self.map.add_marker(mac, color, network["lat"], network["lon"])


def main():
    core = Core()
    if core.main_window.gtkwin is None:
        sys.exit()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    core.quit()


if __name__ == "__main__":
    main()
