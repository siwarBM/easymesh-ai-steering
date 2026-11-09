#!/usr/bin/env python
"""Baseline EasyMesh-style topology: 2 APs + 1 moving station.

    ap1 (ch 1) ======== wired backhaul ======== ap2 (ch 6)
      (30,50)                                   (90,50)
         sta1 walks  (10,50) ----------------------------> (110,50)

Both APs advertise the same SSID, as in an EasyMesh network. Roaming is left to
wpa_supplicant's background scanning (bgscan), i.e. the classic RSSI-threshold
behaviour that the ML steering model is meant to improve on.

Usage (Mininet-WiFi needs root):
    sudo ~/mininet-wifi-env/bin/python simulation/topology_2ap.py            # interactive CLI
    sudo ~/mininet-wifi-env/bin/python simulation/topology_2ap.py --no-cli   # run walk, log, exit
"""

import argparse
import re
import time

from mininet.log import info, setLogLevel
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

SSID = "easymesh"
PASSWD = "easymesh123"  # lab-only simulation passphrase
MESH_FREQS = "2412 2437"  # MHz: ch 1 (ap1), ch 6 (ap2); space-separated for wpa_supplicant
AP_MACS = {"00:00:00:00:00:01": "ap1", "00:00:00:00:00:02": "ap2"}
WALK_START, WALK_END = 1, 31  # seconds into the simulation


def build_network(plot=False, wpa_log=None):
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    # WPA2 is required, not just realistic: Mininet-WiFi only runs
    # wpa_supplicant (and therefore bgscan roaming) for encrypted APs;
    # open APs get a one-shot `iw connect` and the station never roams.
    ap1 = net.addAccessPoint("ap1", mac="00:00:00:00:00:01", ssid=SSID,
                             mode="g", channel="1", position="30,50,0",
                             encrypt="wpa2", passwd=PASSWD,
                             failMode="standalone")
    ap2 = net.addAccessPoint("ap2", mac="00:00:00:00:00:02", ssid=SSID,
                             mode="g", channel="6", position="90,50,0",
                             encrypt="wpa2", passwd=PASSWD,
                             failMode="standalone")
    sta1 = net.addStation("sta1", mac="00:00:00:00:00:10", ip="10.0.0.10/8",
                          position="10,50,0", bgscan_threshold=-60,
                          # "s_inverval" (sic) is the spelling Mininet-WiFi reads
                          s_inverval=2, l_interval=5, bgscan_module="simple",
                          # Scan only the mesh channels (1 and 6), as an 802.11k
                          # neighbor report would. hwsim otherwise sweeps every
                          # 2.4/5/6 GHz and S1G channel: ~20 s per scan, so the
                          # station never gets a fresh scan during the walk.
                          scan_freq=MESH_FREQS, freq_list=MESH_FREQS,
                          # optional wpa_supplicant debug log, for roaming analysis
                          wpasup_flags=("-dd -t -f %s" % wpa_log) if wpa_log else "")

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=3.5)

    info("*** Configuring nodes\n")
    net.configureNodes()

    info("*** Creating backhaul link\n")
    net.addLink(ap1, ap2)

    if plot:
        net.plotGraph(max_x=120, max_y=100)

    info("*** Scheduling mobility\n")
    net.startMobility(time=0)
    net.mobility(sta1, "start", time=WALK_START, position="10,50,0")
    net.mobility(sta1, "stop", time=WALK_END, position="110,50,0")
    net.stopMobility(time=WALK_END + 1)

    info("*** Starting network\n")
    net.build()
    ap1.start([])
    ap2.start([])
    return net


def link_state(sta):
    """Return (ap_name, rssi_dbm) as seen by the station's driver."""
    out = sta.cmd("iw dev %s-wlan0 link" % sta.name)
    bssid = re.search(r"Connected to ([0-9a-f:]{17})", out)
    signal = re.search(r"signal:\s*(-?\d+)", out)
    ap = AP_MACS.get(bssid.group(1), bssid.group(1)) if bssid else "-"
    return ap, int(signal.group(1)) if signal else None


def log_walk(net, debug=False):
    """Print association and RSSI once per second during the walk."""
    sta1 = net.get("sta1")
    info("t(s)  x(m)   AP    RSSI(dBm)\n")
    for t in range(WALK_END + 2):
        ap, rssi = link_state(sta1)
        x = float(sta1.position[0])
        info("%4d %6.1f   %-4s  %s\n" % (t, x, ap, rssi if rssi is not None else "-"))
        if debug and t % 5 == 0:
            # which BSSes wpa_supplicant currently sees, and how strong
            scan = sta1.cmd("wpa_cli -i %s-wlan0 scan_results" % sta1.name)
            info("".join("      | %s\n" % line for line in scan.splitlines()[1:]))
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-cli", action="store_true",
                        help="run the walk, log association/RSSI, then exit")
    parser.add_argument("--plot", action="store_true",
                        help="show the live position plot (needs a display)")
    parser.add_argument("--wpa-log", metavar="PATH",
                        help="write a wpa_supplicant debug log to PATH and "
                             "print scan results every 5 s (with --no-cli)")
    args = parser.parse_args()

    setLogLevel("info")
    net = build_network(plot=args.plot, wpa_log=args.wpa_log)
    try:
        if args.no_cli:
            log_walk(net, debug=bool(args.wpa_log))
        else:
            CLI(net)
    finally:
        info("*** Stopping network\n")
        net.stop()


if __name__ == "__main__":
    main()
