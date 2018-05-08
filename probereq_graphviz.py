#!/usr/bin/python
# prepare wlan interface:
# iwconfig wlan0 mode monitor
# ip link set wlan0 up

import subprocess
import re
import os
import sys
import time

# SSID limit
ssid_limit = 50

# Wireless clients
stations = {}

# SSID blacklist (sort out local SSIDs)
blacklist = []
blacklist.append("C3D2")
blacklist.append("C3D2.anybert")

class preqest:
	ssid = ""
	lastseen = 0

def is_blacklisted(name):
	cnt = 0
	while cnt < len(blacklist):
		if blacklist[cnt] == name:
			return 1
		cnt += 1
	return 0

def color_hash(s):
	h = 0
	for i in range(len(s)):
		h = ord(s[i]) + ((h << 5) - h)
	h = h & 0x00ffffff
	return h

def have_seen(hssid, now):
	for mac in stations:
		for req in stations[mac]:
			if hssid == req.ssid:
				# update lastseen time
				req.lastseen = now
				return True
	return False

def delete_old():
	repeat = 1
	while repeat > 0:
		count = 0
		oldest = time.time()
		for mac in stations:
			for req in stations[mac]:
				count = count + 1
				if req.lastseen < oldest:
					oldest = req.lastseen
					dmac = mac
					dreq = req
		# remove request from station
		stations[dmac].remove(dreq)
		count = count - 1
		print "del [", dmac, "/", dreq.ssid, "]"
		# remove station if empty
		if len(stations[dmac]) == 0:
			del stations[dmac]
		if count <= ssid_limit:
			repeat = 0

def write_dot():
	ssids_cnt = 0
	f = open("/tmp/ssids.dot", 'w')
	print >>f, "digraph ssids {"
	print >>f, "margin=\"0\";"
	print >>f, "bgcolor=\"#333333\";"
	print >>f, "node [ shape=none ];"
	scnt = 0
	for mac in stations:
		hashcol = color_hash(mac)
		col = "#%0.6X" % hashcol
		fillcol = "style=\"rounded,filled\"; color=\"black\"; fillcolor=\"" + col + "\";"
		cpref = "c"+str(scnt)
		clustername = "cluster_" + cpref
		print >>f, fillcol
		print >>f, "subgraph", clustername, "{"
		# calculate luminosity to determine font color
		grey = 0.21 * ((hashcol & 0x00ff0000) >> 16) / 255
		grey = grey + 0.72 * ((hashcol & 0x0000ff00) >> 8) / 255
		grey = grey + 0.07 * (hashcol & 0x000000ff) / 255
		if grey < 0.5:
			fontcol = "white"
		else:
			fontcol = "black"
		idcnt = 0
		for req in stations[mac]:
			ssidline = cpref + "_" + str(idcnt) + " [fontcolor=\"" + fontcol + "\"; label=\"" + req.ssid + "\"];"
			print >>f, ssidline
			idcnt = idcnt + 1
			ssids_cnt = ssids_cnt + 1
		print >>f, "}"
		scnt = scnt + 1
	print >>f, "}"
	f.close()
	return ssids_cnt

def render_dot():
	subprocess.call(["fdp", "-Tpdf", "-o/tmp/ssids.pdf", "/tmp/ssids.dot"])
	#subprocess.call(["aplay", "/usr/share/sounds/arpeg64.wav"])

FNULL = open(os.devnull, 'w')
proc = subprocess.Popen(['/tmp/tcpdump', '-leni', 'wlan0', 'type', 'mgt', 'subtype', 'probe-req'], stdout=subprocess.PIPE, stderr=FNULL)
#proc = subprocess.Popen(['/bin/cat', '/tmp/ssid_probereq.log'], stdout=subprocess.PIPE, stderr=FNULL)

# initial graph
req = preqest()
req.ssid = "please wait..."
req.lastseen = 0
stations["init"] = set()
stations["init"].add(req)
write_dot()
render_dot()
stations["init"].remove(req)
del stations["init"]
#time.sleep(10)

last = 0
while True:
	ssid_re = re.compile("^.*SA:(..:..:..:..:..:..).*Probe Request \((.+)\).*$")
	#time.sleep(0.1)
	line = proc.stdout.readline()
	if line != '':
		# extract SSID from probe request
		res = ssid_re.match(line)
		if res:
			now = time.time()
			pmac = res.group(1)
			pssid = res.group(2)
			# remove any double quote chars
			pssid = pssid.translate(None, '"')
			#print "MAC:", pmac, "SSID:", pssid, "time:", now
			# skip blacklisted SSIDs
			if is_blacklisted(pssid) == 1:
				continue
			# check if SSID was already seen
			if have_seen(pssid, now):
				continue
			# new station
			if not pmac in stations:
				stations[pmac] = set()
			# check if SSID was already seen for this station
			#if pssid in stations[pmac]:
			#	continue
			req = preqest()
			req.ssid = pssid
			req.lastseen = now
			stations[pmac].add(req)
			print "add [", pmac, "/", pssid, "]"
			# rate limit
			if (now - last) >= 2:
				last = now
				total_ssids = write_dot()
				render_dot()
				if total_ssids > ssid_limit:
					# limit reached, delete old requests
					delete_old()
	else:
		break

