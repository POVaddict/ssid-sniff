#!/usr/bin/python
# run "ssid_prepare.sh" before using this script

import subprocess
import re
import os
import sys
import time

maxssid = 100
rows = 20
columns = 80
ssids = []

# terminal colors
class tcolors:
	N = '\033[0;39m'
	R = '\033[1;31m'
	G = '\033[1;32m'
	B = '\033[1;34m'
	W = '\033[1;37m'

# init SSID list
for cnt in range(maxssid):
	ssids.append({})
	ssids[cnt]["name"] = ""
	ssids[cnt]["lastseen"] = 0

# SSID blacklist (sort out local SSIDs)
blacklist = []
blacklist.append("C3D2")
blacklist.append("C3D2.anybert")

def is_blacklisted(name):
	cnt = 0
	while cnt < len(blacklist):
		if blacklist[cnt] == name:
			return 1
		cnt += 1
	return 0

def findfree():
	cnt = 0
	while cnt < maxssid:
		if ssids[cnt]["lastseen"] == 0:
			return cnt
		cnt += 1
	return -1

def findssid(name):
	cnt = 0
	while cnt < maxssid:
		if ssids[cnt]["name"] == name:
			return cnt
		cnt += 1
	return -1

def findoldest():
	cnt = 0
	ret = 0
	oldest = ssids[cnt]["lastseen"]
	while cnt < maxssid:
		if ssids[cnt]["lastseen"] < oldest:
			oldest = ssids[cnt]["lastseen"]
			ret = cnt
		cnt += 1
	return ret

def print_ssids():
	rows, columns = os.popen('stty size', 'r').read().split()
	rows, columns = int(rows),int(columns)
	
	if True:
		cur_ssids = sorted(ssids,key=lambda k: k["lastseen"], reverse=True)
	else:
		cur_ssids = ssids
	
	# move cursor to 1,1
	sys.stdout.write('\033[H')
	for cnt in range(rows-1):
		age = time.time()-cur_ssids[cnt]["lastseen"]
		# color code age of SSIDs
		if age > 120:
			agecol = tcolors.B
		elif age > 60:
			agecol = tcolors.R
		elif age > 30:
			agecol = tcolors.G
		else:
			agecol = tcolors.W
		name = cur_ssids[cnt]["name"]
		# limit to width -6 (** name **)
		if len(name) > columns-6:
			name = name[0:columns-1-6]
		# pad to columns chars, centered
		name = name.center(columns - 6)
		print agecol+'** '+name+' **'+tcolors.N

FNULL = open(os.devnull, 'w')
proc = subprocess.Popen(['/tmp/tcpdump', '-plni', 'mon0', 'type', 'mgt', 'subtype', 'probe-req'], stdout=subprocess.PIPE, stderr=FNULL)

while True:
	ssid_re = re.compile("^.*Probe Request \((.+)\).*$")
	line = proc.stdout.readline()
	if line != '':
		# extract SSID from probe request
		res = ssid_re.match(line)
		if res:
			#print "SSID:", res.group(1), "seen:", time.time()
			# skip blacklisted SSIDs
			if is_blacklisted(res.group(1)) == 1:
				continue
			ind = findssid(res.group(1))
			if ind == -1:
				# new SSID, find free slot
				ind = findfree()
				if ind == -1:
					# no free slot, replace oldest
					oind = findoldest()
					ssids[oind]["name"] = res.group(1)
					ssids[oind]["lastseen"] = time.time()
				else:
					# fill free slot
					ssids[ind]["name"] = res.group(1)
					ssids[ind]["lastseen"] = time.time()
			else:
				# old SSID, update timestamp
				ssids[ind]["lastseen"] = time.time()
			print_ssids()
	else:
		break

