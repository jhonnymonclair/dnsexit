#!/usr/bin/env python3
###################################################
##
##  DnsExit.Com Dynamic IP update script
##  based on original 1.6 Perl version
##
###################################################

import os
import sys
import time
from datetime import datetime
import urllib.request
import re

cfile = "/etc/dnsexit.conf"

try:
    with open(cfile) as f:
        data = f.readlines()
        f.close()
except IOError:
    sys.stderr.write("Fail open config file " + cfile + ". You need to run setup.py script\n")
    sys.exit(1)

###################################################
#
# CONFIGURATION FILE STRUCTURE
#
# login=login
# password=password
# host=host
# daemon=yes|no (default=yes)
# interval=interval (default=600)
# proxyservs=proxyservs
# pidfile=pidfile (default=/var/run/ipUpdate.pid)
# logfile=logfile (default=/var/log/dnsexit.log)
# cachefile=cachefile (default=/tmp/dnsexit-ip.txt)
#
###################################################

keyval = []
for iter in data:
    key, val = iter.rstrip('\n').split('=',1)
    keyval.append(val)

login, password, host, daemon, interval  = keyval[0], keyval[1], keyval[2], keyval[3], keyval[4]
proxyservs, pidfile, logfile, cachefile, url = keyval[5], keyval[6], keyval[7], keyval[8], keyval[9]

def postNewIP(newip):
    posturl = url + "?login=" + login + "&password=" + password + "&host=" + host + "&myip=" + newip
    try:
        data = urllib.request.urlopen(posturl).read()
    except urllib.error.URLError:
        mark("ERROR", "-98", "Fail to post the IP of your machine")
        return
    httpstuff, response = data.decode('utf-8').split('\n',1)
    if re.match("\d+\=\D+", response):
        code, message =  response.split('=',1)
        mark("Success", code, message)
        f = open(cachefile, 'w')
        f.write(newip)
        f.close()
    else:
        mark("ERROR", "-99", "Return content format error")

def isIpChanged(newip):
    try:
        f = open(cachefile, 'r')
    except:
        return 0
    preip = f.read()
    f.close()
    if preip == newip:
        return 1
    else:
        return 0

def getProxyIP():
    servs = proxyservs.split(';')
    for server in servs:
        try:
            data = urllib.request.urlopen("http://" + server).read()
        except urllib.error.URLError:
            mark("ERROR", "-100", "Return message format error.... Fail to grep the IP address from " + server)
            continue
        ip = data.decode('utf-8')
        if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
            mark("INFO", "100", url + " says your IP address is: " + ip)
            return ip
        else:
            mark("ERROR", "-100", "Return message format error.... Fail to grep the IP address from " + server)
    mark("ERROR", "-99", "Fail to get the proxy IP of your machine")

def mark(type, code, message):
    now = datetime.now()
    dt_string = now.strftime("%c")
    f = open(logfile, 'a')
    f.write(dt_string + "\t" + type + "\t" + code + "\t" + message + "\n")
    f.close()

def clear():
    f = open(logfile, 'w')
    f.close()

###################################################
#
# MAIN
#
###################################################

if daemon != "yes":
    clear()
    ip = getProxyIP()
    ipFlag = isIpChanged(ip);
    if ipFlag == 1:
        mark("INFO", "100", "IP is not changed from last successful update")
        sys.exit(0)
    postNewIP(ip)
else:
    pid = str(os.getpid())
    if os.path.isfile(pidfile):
         print(pidfile + " already exists, exiting")
         sys.exit(1)
    f = open(pidfile, 'w')
    f.write(pid)
    f.close()
    while True:
        clear()
        mark("INFO", "100", "Started in daemon mode")
        ip = getProxyIP()
        ipFlag = isIpChanged(ip)
        if ipFlag == 1:
            mark("INFO", "100", "IP is not changed from last successful update")
        else:
            postNewIP(ip)
        time.sleep(int(interval))
