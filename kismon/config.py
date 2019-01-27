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

import json
import os


class Config:
    def __init__(self, config_file, logger):
        self.config_file = config_file
        self.logger = logger

        self.default_config = {
            "servers": [
                {
                    'uri': 'http://127.0.0.1:2501',
                    'username': '',
                    'password': '',
                    'connect': True
                },
            ],
            "window": {
                "maximized": False,
                "width": 800,
                "height": 600,
                "map_position": "hide",
                "log_list_max": 200,
                "signal_window_seconds": 120,
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
                "num_backups": 5,
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
                "unknown": True,
                "client": False,
                "infrastructure": True,
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
            },
            "network_list_columns": []
        }

    def read(self):
        self.config = self.default_config
        if not os.path.isfile(self.config_file):
            self.logger.info("config file %s not found, continuing with default settings" % self.config_file)
            return

        with open(self.config_file, 'r') as f:
            first_line = f.readline()
        if first_line.startswith('['):
            self.logger.info('skipping old ini config, using default')
            return
        elif first_line.startswith('{'):
            # new json config
            self.logger.info('loading json config')
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
            for key in self.config:
                if key not in loaded_config:
                    # doesn't exist before
                    continue
                if type(self.config[key]) != type(loaded_config[key]):
                    # type has changed
                    continue
                if type(self.config[key]) == dict:
                    self.config[key].update(loaded_config[key])
                elif type(self.config[key]) == list:
                    self.config[key] = loaded_config[key]
        else:
            self.logger.warning('unknown config format, using default')
            return

    def write(self):
        self.logger.info('writing json config')
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)


if __name__ == "__main__":
    from test import TestKismon

    TestKismon.test_config(True)
