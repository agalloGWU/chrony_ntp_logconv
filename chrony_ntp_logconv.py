#!/usr/bin/env python3

# Convert chrony's tracking and statistics logs to something ntpsec's ntpviz can graph
# Assumes chrony's logs are in /var/log/chrony and outputs to /var/log/ntpstats
# See below and fill in an adapter from your local refid names for refclocks to NTPd style
# IPs for refclocks.

# agalloGWU modifications
# change location of files because we're going to be running this on a
# different machine than the one that generated the logs
# directory structure:
#   ./chrony-source = the files chronyd generates that are normally in /var/log/chrony
#   ./ntpconv = converted files


# adding reference clock Type 28 (Shared Memory driver) as 127.127.28.0
# see https://www.eecis.udel.edu/%7Emills/ntp/html/refclock.html#list

import shutil, os, math
from datetime import datetime, timezone

try:
    shutil.rmtree("./ntpconv")
except:
    pass
os.mkdir("./ntpconv")

# Chrony can sometimes print times out of order, which on day boundaries can result
# in us clearing logs completely, so we track which days we've covered and append
# if we see a day for a second time.
suffixes = {}
suffixes["loopstats"] = set()
suffixes["peerstats"] = set()
out = None
for f in os.listdir("./chrony-source"):
    if f.startswith("tracking.log"):
        out_ty = "loopstats"
    elif f.startswith("statistics.log"):
        out_ty = "peerstats"
    else:
        continue

    with open("./chrony-source/" + f) as fd:
        line = fd.readline()
        f = ""
        while line:
            if line.startswith("   ") or line.startswith("====="):
                line = fd.readline()
                continue
            s = line.split()
            t = datetime.fromisoformat(s[0] + " " + s[1])
            d = datetime.fromisoformat(s[0])
            mjs = (d.timestamp() + 3506716800)
            mjd = math.floor(mjs / 86400)
            secs = ((t.timestamp() - d.timestamp()))
            logsuf = d.strftime("%Y%m%d")


            if f != logsuf:
                f = logsuf
                if out is not None:
                    out.close()
                if f in suffixes[out_ty]:
                    out = open("./ntpconv/" + out_ty + "." + logsuf, "a")
                else:
                    out = open("./ntpconv/" + out_ty + "." + logsuf, "w")
                    suffixes[out_ty].add(f)

            if out_ty == "loopstats":
                # Bogus "clock discipline time constant"
                # Note that we don't have Allan Devitaion for freq, only "error bounds on the frequency", but we use that anyway
                out.write("%d %d %.9f %.3f %.9f %.9f 6\n" % (mjd, secs, -float(s[6]), -float(s[4]), float(s[9]), float(s[5])))
            elif out_ty == "peerstats":
                src = s[2]

                # These are my refclocks. You should fill in your own conversions here.
                if src == "NME0":
                    src = "127.127.20.0"
                elif src == "NME1":
                    src = "127.127.20.1"
                elif src == "NME2":
                    src = "127.127.20.2"
                elif src == "NME2":
                    src = "127.127.20.3"
                elif src == "GPS0":
                    src = "127.127.46.0"
                elif src == "GPS1":
                    src = "127.127.46.1"
                elif src == "GPS2":
                    src = "127.127.46.2"
                elif src == "PPS0":
                    src = "127.127.22.0"
                elif src == "PPS1":
                    src = "127.127.22.1"
                elif src == "PPS2":
                    src = "127.127.22.2"
                elif src == "PTP0":       # strictly speaking, this is the shared memory driver (SHM), but that's how we get PTP to sync with NTP
                    src = "127.127.28.0"


                # Bogus "status" and, sadly, missing "delay" (which is 0 here, its only in rawstats)
                out.write("%d %d %s 9014 %.9f 0 %.9f %.9f\n" % (mjd, secs, src, -float(s[4]), float(s[5]), float(s[3])))

            line = fd.readline()

out.close()

# don't this we need this anymore
"""
shutil.copyfile("/var/log/ntpstats/conv/peerstats." + logsuf, "/var/log/ntpstats/peerstats")
shutil.copyfile("/var/log/ntpstats/conv/loopstats." + logsuf, "/var/log/ntpstats/loopstats")
for f in os.listdir("/var/log/ntpstats/conv"):
    os.rename("/var/log/ntpstats/conv/" + f, "/var/log/ntpstats/" + f)
shutil.rmtree("/var/log/ntpstats/conv")
"""