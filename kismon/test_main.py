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

import time
import sys
import os
import tempfile
import unittest
import kismon.test_data
import kismon.logger
import copy

logger = kismon.logger.get_logger('warning')

def is_gi_available():
    try:
        import gi
        return True
    except ImportError:
        return False


def is_cairo_available():
    try:
        import cairo
        return True
    except ImportError:
        return False


gi_available = is_gi_available()
cairo_available = is_cairo_available()


def get_client_test_data():
    data = copy.deepcopy(kismon.test_data.data)
    return data


def core_tests(test_core):
    test_networks = networks()
    test_core.networks = test_networks
    test_core.client_threads[0].client.queue = get_client_test_data()
    test_core.queue_handler(0)
    test_core.queue_handler_networks(0)
    task = test_core.networks.notify_add_queue_process()
    while next(task):
        continue
    test_core.quit()


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

    def get_text(self):
        return self.text


class TestEvent:
    def __init__(self):
        from gi.repository import Gdk
        self.new_window_state = Gdk.WindowState.MAXIMIZED
        self.keyval = 0


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


def networks():
    from kismon.config import Config
    from kismon.networks import Networks
    from kismon.tracks import Tracks

    def dummy(bla):
        return

    test_data = get_client_test_data()
    test_config = Config(None, logger=logger).default_config

    networks = Networks(test_config, logger=logger)
    networks.notify_add_list["map"] = dummy
    networks.notify_add_list["network_list"] = dummy
    networks.notify_remove_list["map"] = dummy
    networks.notify_remove_list["network_list"] = dummy
    for device in test_data['dot11']:
        networks.add_device_data(device, server_id=0)

    tmp_csv_file = "%s%stest-%s.csv" % (tempfile.gettempdir(), os.sep, int(time.time()))
    tmp_csv = open(tmp_csv_file, "w")
    tmp_csv.write("""Network;NetType;ESSID;BSSID;Info;Channel;Cloaked;Encryption;Decrypted;MaxRate;MaxSeenRate;Beacon;LLC;Data;Crypt;Weak;Total;Carrier;Encoding;FirstTime;LastTime;BestQuality;BestSignal;BestNoise;GPSMinLat;GPSMinLon;GPSMinAlt;GPSMinSpd;GPSMaxLat;GPSMaxLon;GPSMaxAlt;GPSMaxSpd;GPSBestLat;GPSBestLon;GPSBestAlt;DataSize;IPType;IP;
1;infrastructure;asd;11:22:33:44:55:66;;3;No;WEP,WPA,PSK,AES-CCM;No;18.0;1000;25600;148;0;0;0;148;IEEE 802.11g;;Thu Jan 22 05:48:23 2009;Thu Jan 22 05:51:46 2009;0;65;-98;52.123456;13.123456;120.120003;0.000000;52.123456;13.123456;120.120003;2.934490;0.000000;0.000000;0.000000;0;None;0.0.0.0;""")
    tmp_csv.close()
    for x in range(2):
        networks.import_networks("csv", tmp_csv_file)
    networks.import_networks("netxml", "")

    tmp_tracks_file = "%s%stest-tracks-%s.json" % (tempfile.gettempdir(), os.sep, int(time.time()))
    test_tracks = Tracks(tmp_tracks_file)

    networks_file = "%s%snetworks-%s.json" % (tempfile.gettempdir(), os.sep, int(time.time()))
    networks.save(networks_file)
    networks.load(networks_file)
    networks.import_networks("networks", networks_file)
    networks.apply_filters()
    networks.save(networks_file)
    networks.export_networks_netxml(tempfile.gettempdir() + os.sep + "test.netxml", networks.networks)
    networks.import_networks("netxml", tempfile.gettempdir() + os.sep + "test.netxml")
    networks.export_networks_kmz(tempfile.gettempdir() + os.sep + "test.kmz", networks.networks, tracks=test_tracks,
                                 filtered=False)
    networks.export_networks_kmz(tempfile.gettempdir() + os.sep + "test.kmz", networks.networks, tracks=test_tracks,
                                 filtered=True)

    return networks


class TestKismon(unittest.TestCase):
    def test_client(self):
        from kismon.client_rest import RestClient, RestClientThread, encode_cryptset, decode_cryptset
        client = RestClient(logger=logger)
        client.uri = "invalid:xyz"
        client.start()

        client = RestClient(logger=logger)
        errors = 0

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
                print("decode_cryptset error: %s\n%s!=%s" % (cryptset, crypt_str, result))

            test_cryptset = encode_cryptset(crypt_str.lower().split(","))
            if test_cryptset != cryptset:
                print("encode_cryptset error: %s\n%s!=%s" % (crypt_str, test_cryptset, cryptset))

        if errors != 0:
            sys.exit("client test failed, %s errors" % errors)

        client_thread = RestClientThread(logger=logger)
        client_thread.client = client

    # client_thread.run()
    # client_thread.stop()

    def test_config(self):
        from kismon.config import Config
        config_file = tempfile.gettempdir() + os.sep + "testconfig.conf"
        conf = Config(config_file, logger=logger)
        conf.read()
        conf.write()
        conf = Config(config_file, logger=logger)
        conf.read()

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_core(self):
        from kismon.core import Core
        test_core = Core()
        core_tests(test_core)
        test_core.add_network_to_map("00:12:2A:03:B9:12")
        test_core.queues_handler()
        test_core.clients_stop()

        arg = "--disable-map"
        sys.argv.append(arg)
        test_core = Core()
        core_tests(test_core)
        sys.argv.remove(arg)

        test_core.clients_stop()

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_gui_main_window(self):
        from gi.repository import Gtk
        from kismon.config import Config
        from kismon.map import Map
        from kismon.gui import MainWindow
        from kismon.client_rest import RestClientThread
        from kismon.tracks import Tracks
        def dummy(server_id):
            return

        test_widget = TestWidget()

        test_config = Config(None, logger=logger).default_config
        test_map = Map(test_config["map"], logger=logger)
        test_networks = networks()
        test_networks.networks['00:12:2A:03:B9:12']['servers'] = "http://127.0.0.1:2501"
        test_client_threads = {0: RestClientThread(logger=logger)}
        tmp_tracks_file = "%s%stest-tracks-%s.json" % (tempfile.gettempdir(), os.sep, int(time.time()))
        test_tracks = Tracks(tmp_tracks_file)
        main_window = MainWindow(test_config, dummy, dummy, test_map, test_networks, test_tracks, {0: None, 1: None},
                                 test_client_threads, logger=logger)
        main_window.network_list.crypt_cache = {}

        for x in range(1, 202):
            main_window.log_list.add("Kismon", "test %s" % x)
        main_window.log_list.cleanup()
        main_window.network_list.add_network('11:22:33:44:55:66')
        main_window.network_list.network_selected = '11:22:33:44:55:66'
        main_window.network_list.add_network('00:12:2A:03:B9:12')
        main_window.network_list.add_network('00:12:2A:03:B9:12')
        main_window.network_list.column_selected = 2
        main_window.network_list.on_copy_field(None)
        main_window.network_list.on_copy_network(None)
        main_window.network_list.on_comment_editing_done(test_widget)
        main_window.network_list.remove_network('00:12:2A:03:B9:12')
        main_window.network_list.remove_column('Ch')
        main_window.network_list.add_column('Ch')
        main_window.network_list.on_locate_marker(None)
        main_window.network_list.pause()
        main_window.network_list.resume()
        main_window.server_tabs[0].update_info_table({"networks": 100, "packets": 200})
        main_window.server_tabs[0].update_gps_table(fix=3, lat=52.0, lon=13.0)
        sources = {"1": {"uuid": "1", "name": "test", "type": "bla",
                         "channel": 11, "packets": 100}}
        main_window.server_tabs[0].update_sources_table(sources)
        main_window.on_configure_event(None, None)
        main_window.on_config_window(None)
        main_window.on_config_window(None)
        main_window.on_signal_graph(None)
        main_window.on_signal_graph_destroy(None, "11:22:33:44:55:66")
        main_window.fullscreen()
        main_window.fullscreen()
        main_window.on_map_window(None, True)
        dummy_button = Gtk.Button()
        main_window.config_window.on_map_source(dummy_button, "custom")
        main_window.on_map_window(None, False)
        main_window.on_map_widget(None, True)
        main_window.config_window.on_map_source(dummy_button, "custom")
        main_window.on_map_widget(None, False)
        # main_window.on_server_disconnect(None, 0)
        test_event = TestEvent()
        main_window.on_window_state(None, test_event)

        main_window.on_file_import(None)

        main_window.networks_queue_progress()
        main_window.networks_queue_progress_update()

        test_widget.text = "Infrastructure"
        main_window.filter_tab.on_network_filter(test_widget, 'filter_type', 'infrastructure')
        main_window.filter_tab.on_toggle_limiter(test_widget, 'map', 'all')
        test_widget.text = 'something'
        main_window.filter_tab.on_regex_changed(test_widget, 'ssid')
        main_window.filter_tab.on_regex_changed(test_widget, 'ssid')

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_gui_channel_window(self):
        from kismon.gui import ChannelWindow
        from kismon.client_rest import RestClientThread
        sources = {
            "123": {"uuid": "123", "hop": 3, "name": "wlan0", "hop_rate": 3, "channel": 1},
            "234": {"uuid": "234", "hop": 0, "name": "wlan1", "hop_rate": 3, "channel": 6}
        }
        client_thread = RestClientThread(logger=logger)
        channel_window = ChannelWindow(sources, client_thread, parent=None)
        test_widget = TestWidget()
        channel_window.on_change_mode(test_widget, "123", "hop")
        channel_window.on_change_mode(test_widget, "123", "lock")
        channel_window.on_change_value(None, "123", "hop")
        channel_window.on_cancel(None)
        channel_window.on_apply(None)

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_gui_map_window(self):
        from kismon.config import Config
        from kismon.map import Map
        from kismon.gui import MapWindow
        test_config = Config(None, logger=logger).default_config["map"]
        test_map = Map(test_config, logger=logger)
        map_window = MapWindow(test_map)
        test_event = TestEvent()
        test_event.keyval = 65480  # F11
        map_window.on_key_release(None, test_event)
        map_window.on_key_release(None, test_event)
        test_event.keyval = 105  # i
        map_window.on_key_release(None, test_event)
        test_event.keyval = 111  # o
        map_window.on_key_release(None, test_event)
        map_window.hide()
        map_window.on_destroy(None)

    @unittest.skipUnless(cairo_available, "cairo module not available")
    def test_gui_signal_window(self):
        import cairo
        from kismon.gui import SignalWindow
        def destroy(obj, window):
            return

        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 600, 400)
        ctx = cairo.Context(surface)
        signal_window = SignalWindow("11:22:33:44:55:66", destroy)
        signal_window.on_draw_event(None, ctx)
        signal_window.history[-1] = {}
        test_source = {
            'uuid': '5fe308bd-0000-0000-0000-24050f73b68f',
            'name': 'wlan0',
            'type': 'iwtest'
        }
        signal_window.add_value(test_source, packets=1, signal=-30, timestamp=1, server_id=0)
        time.sleep(1)
        signal_window.add_value(test_source, packets=2, signal=-32, timestamp=2, server_id=0)
        time.sleep(1)
        signal_window.add_value(test_source, packets=3, signal=-34, timestamp=3, server_id=0)
        signal_window.draw_graph(600, 400, ctx)
        now = int(time.time())
        for signal in (-50, -60, -70, -80, -50):
            now -= 1
            signal_window.history[now] = {}
            signal_window.history[now]["test"] = (signal, signal * -1)
        signal_window.draw_graph(600, 400, ctx)
        signal_window.on_draw_event(None, ctx)
        test_widget = TestWidget()
        signal_window.on_graph_type(test_widget, "signal")
        signal_window.on_draw_event(None, ctx)
        signal_window.on_graph_type(test_widget, "packets")
        signal_window.on_draw_event(None, ctx)
        test_widget.active = False
        signal_window.on_graph_type(test_widget, "signal")
        signal_window.on_graph_type(test_widget, "packets")

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_file_import_window(self):
        from kismon.gui import FileImportWindow

        test_networks = networks()

        def dummy():
            return

        file_import_window = FileImportWindow(test_networks, dummy)
        file_import_window.create_file_chooser('file')
        file_import_window.create_file_chooser('dir')
        file_import_window.add_file('foo.bar')
        file_import_window.on_remove_file(None, 'foo.bar')
        file_import_window.add_file('foo.bar')
        file_import_window.add_file('kismet.netxml')
        file_import_window.add_file('kismet.csv')
        file_import_window.add_file('kismon.json')
        file_import_window.on_start(None)
        file_import_window.parse_file()
        file_import_window.parse_file()
        file_import_window.parse_file()
        file_import_window.on_close(None)

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_datasources_window(self):
        from gi.repository import Gtk
        from kismon.gui import DatasourcesWindow
        from kismon.client_rest import RestClientThread

        test_networks = networks()

        def dummy_datasources():
            return kismon.test_data.available_datasources

        test_window = Gtk.Window()
        client_thread = RestClientThread(logger=logger)
        client_thread.client.get_available_datasources = dummy_datasources
        datasources_window = DatasourcesWindow(client_thread,
                                               parent=test_window)
        datasources_window.on_refresh()
        datasources_window.on_destroy()

    @unittest.skipUnless(gi_available, "gi module not available")
    def test_map(self):
        from gi.repository import Gtk
        from kismon.config import Config
        from kismon.map import Map
        test_config = Config(None, logger=logger).default_config["map"]
        test_map = Map(test_config, logger=logger)

        test_map.set_zoom(16)
        test_map.set_position(52.513, 13.323)
        test_map.add_marker("111", "green", 52.513, 13.322)
        test_map.add_marker("222", "red", 52.512, 13.322)
        test_map.add_marker("333", "orange", 52.512, 13.322)
        test_map.locate_marker("111")
        test_map.add_marker("222", "red", 52.510, 13.321)
        test_map.add_marker("333", "orange", 52.511, 13.322)
        test_map.add_marker("444", "green", 52.511, 13.322)
        test_map.add_marker("server1", "server1", 52.511, 13.321)

        test_map.set_position(52.513, 13.323)
        test_map.zoom_out()
        test_map.zoom_in()
        test_map.on_map_pressed(None, None)
        test_map.change_source("openstreetmap")
        test_map.change_source("opencyclemap")
        test_map.remove_marker("333")

        test_map.add_track(52.513, 13.323, 'server1', color=(0, 16621, 19455))
        test_map.add_track(52.510, 13.321, 'server1')
        test_map.add_track(52.511, 13.321, 'server1')
        test_map.set_track_color('server1', (65535, 1, 65535))

        test_window = Gtk.Window()
        test_window.set_title("Kismon Test Map")
        test_window.connect("destroy", Gtk.main_quit)
        test_window.show()
        test_window.set_size_request(640, 480)
        test_window.add(test_map.widget)
        test_window.show_all()


if __name__ == "__main__":
    unittest.main()
