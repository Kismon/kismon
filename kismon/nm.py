#!/usr/bin/python3

import NetworkManager
from pprint import pprint
import time


# https://developer.gnome.org/NetworkManager/1.2/gdbus-org.freedesktop.NetworkManager.AccessPoint.html

def decode_security_flags(num):
    hex_str = '%02x' % num
    # print(hex_str)
    flags = []

    if hex_str[-1] == '0':
        flags.append('NONE')
        crypt = "None"
    elif hex_str[-1] == '1':
        flags.append('PAIR_WEP40')
        crypt = "WEP"
    elif hex_str[-1] == '2':
        flags.append('PAIR_WEP104')
        crypt = "WEP"
    elif hex_str[-1] == '4':
        flags.append('PAIR_TKIP')
        crypt = "WPA"
    elif hex_str[-1] == '8':
        flags.append('PAIR_CCMP')
        crypt = "WPA2"
    else:
        crypt = "None"

    if hex_str[-2] == '1':
        flags.append('GROUP_WEP40')
    elif hex_str[-2] == '2':
        flags.append('GROUP_WEP104')
    elif hex_str[-2] == '4':
        flags.append('GROUP_TKIP')
    elif hex_str[-2] == '8':
        flags.append('GROUP_CCMP')

    if hex_str[-3] == '1':
        flags.append('KEY_MGMT_PSK')
    elif hex_str[-3] == '2':
        flags.append('KEY_MGMT_802_1X')

    return flags, crypt


modes = {0: 'unkown', 1: 'adhoc', 2: 'infrastructure', 3: 'infrastructure'}

channels = {
    # 2.4 GHz
    2412: 1, 2417: 2, 2422: 3, 2427: 4, 2432: 5, 2437: 6, 2442: 7,
    2447: 8, 2452: 9, 2457: 10, 2462: 11, 2467: 12, 2472: 13, 2484: 14,
    # 5 GHz
    5160: 32, 5170: 34, 5180: 36, 5190: 38, 5200: 40, 5210: 42, 5220: 44, 5230: 46,
    5240: 48, 5250: 50, 5260: 52, 5270: 52, 5280: 56, 5290: 58, 5300: 60, 5310: 62,
    5320: 64, 5340: 68, 5480: 96, 5500: 100, 5510: 102, 5520: 104, 5530: 106, 5540: 108,
    5550: 110, 5560: 112, 5570: 114, 5580: 116, 5590: 118, 5600: 120, 5610: 122, 5620: 124,
    5630: 126, 5640: 128, 5660: 132, 5670: 134, 5680: 136, 5690: 138, 5700: 140, 5710: 142,
    5720: 144,
}


class NetworkManagerScanner:
    def __init__(self):
        self.last_clock = 0

    def get_networks(self, only_new=True):
        networks = {}
        # https://pythonhosted.org/python-networkmanager/
        aps = NetworkManager.AccessPoint()
        clock_now = time.clock_gettime(time.CLOCK_MONOTONIC)
        for ap in aps.all():

            if ap.LastSeen < self.last_clock and only_new:
                continue
            last_seen = int(time.time() - (clock_now - ap.LastSeen))

            security_flags, crypt = decode_security_flags(ap.RsnFlags)

            network = {
                'mac': ap.HwAddress,
                'ssid': ap.Ssid,
                'signal': ap.Strength,
                'firsttime': last_seen,
                'lasttime': last_seen,
                'crypt': crypt,
                'cryptset': 0,
                'type': modes[ap.Mode],
                'channel': channels[ap.Frequency]
            }
            if ap.HwAddress not in networks:
                networks[ap.HwAddress] = network
            elif last_seen > networks[ap.HwAddress]['lasttime']:
                networks[ap.HwAddress] = network

        self.last_clock = clock_now
        return networks


if __name__ == "__main__":
    nms = NetworkManagerScanner()
    while True:
        try:
            networks = nms.get_networks()
        except Exception as e:
            print('error', e)
            continue
        if len(networks) > 0:
            pprint(networks)
        time.sleep(5)
