#!/usr/bin/env python3
"""
Copyright (c) 2016, Patrick Salecker
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
import json
import os
import collections


class Tracks:
    def __init__(self, tracks_file):
        self.tracks = {}
        self.tracks_file = tracks_file
        self.starttime = int(time.time())

    def load(self):
        if not os.path.isfile(self.tracks_file):
            return

        with open(self.tracks_file, 'r') as f:
            self.tracks = json.load(f)

    def save(self):
        new_file = "%s.new" % self.tracks_file
        with open(new_file, 'w') as f:
            json.dump(self.tracks, f)
        os.rename(new_file, self.tracks_file)

    def add_point_to_track(self, track_name, lat, lon, alt):
        if track_name not in self.tracks:
            self.tracks[track_name] = {}

        timestamp = int(time.time())
        self.tracks[track_name][str(timestamp)] = (lat, lon, alt)

    def group_to_sessions(self, filter_time):
        sessions = {}
        timeout = 600
        for track_name in self.tracks:
            sessions[track_name] = collections.OrderedDict()
            track = self.tracks[track_name]
            timestamps = list(track.keys())
            timestamps.sort()
            first_timestamp = 0
            previous_timestamp = 0
            session = collections.OrderedDict()
            for timestamp in timestamps:
                point = track[timestamp]
                timestamp = int(timestamp)
                if timestamp < filter_time:
                    continue
                if timestamp - previous_timestamp > timeout:
                    if len(session) > 0:
                        sessions[track_name][first_timestamp] = session
                    session = collections.OrderedDict()
                    first_timestamp = timestamp
                session[timestamp] = point
                previous_timestamp = timestamp
            if len(session) > 0:
                sessions[track_name][first_timestamp] = session
        return sessions

    def export_kml(self, export_filter):
        if export_filter == 'current':
            filter_time = self.starttime
        else:
            filter_time = 0
        output = ["<Folder><name>Tracks</name>"]
        sessions = self.group_to_sessions(filter_time)
        time_format = "%a %b %d %H:%M:%S %Y"
        for track_name in sessions:
            output.append("<Folder><name>%s</name>" % track_name)
            for session_start in sessions[track_name]:
                output.append(
                    "<Placemark><Style><LineStyle><color>7f00ff00</color><width>3</width></LineStyle></Style><LineString><coordinates>\n")
                for timestamp in sessions[track_name][session_start]:
                    lat, lon, alt = sessions[track_name][session_start][timestamp]
                    output.append("%s,%s \n" % (lon, lat))
                output.append("</coordinates></LineString>")

                output.append("<name>Session %s - %s</name></Placemark>\n" % (
                    time.strftime(time_format, time.gmtime(session_start)),
                    time.strftime(time_format, time.gmtime(timestamp)),
                ))
            output.append("</Folder>")
        output.append("</Folder>")
        return "".join(output)
