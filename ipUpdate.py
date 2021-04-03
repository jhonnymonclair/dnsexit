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
# autostart=yes|no
# interval=interval (default=600)
# proxyservs=proxyservs
# pidfile=pidfile (default=/run/ipUpdate.pid)
# logfile=logfile (default=/var/log/dnsexit.log)
# cachefile=cachefile (default=/tmp/dnsexit-ip.txt)
# url==https://update.dnsexit.com/RemoteUpdate.sv
#
###################################################

keyval = []
for iter in data:
    key, val = iter.rstrip('\n').split('=',1)
    keyval.append(val)

login, password, host, daemon, autostart, interval  = keyval[0], keyval[1], keyval[2], keyval[3], keyval[4], keyval[5]
proxyservs, pidfile, logfile, cachefile, url = keyval[6], keyval[7], keyval[8], keyval[9], keyval[10]

def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError as err:
        sys.stderr.write('fork #1 failed: {0}\n'.format(err))
        sys.exit(1)

    # decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError as err:
        sys.stderr.write('fork #2 failed: {0}\n'.format(err))
        sys.exit(1)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

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
            mark("ERROR", "-100", "Return message format error.... Fail to grep the IP address from http://" + server)
            continue
        ip = data.decode('utf-8')
        if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
            mark("INFO", "100", "http://" + server + " says your IP address is: " + ip)
            return ip
        else:
            mark("ERROR", "-100", "Return message format error.... Fail to grep the IP address from http://" + server)
    mark("ERROR", "-99", "Fail to get the proxy IP of your machine")

def mark(type, code, message):
    now = datetime.now()
    dt_string = now.strftime("%c")
    try:
        with open(logfile, 'a') as f:
            f.write(dt_string + "\t" + type + "\t" + code + "\t" + message + "\n")
            f.close
    except:
        sys.exit(1)

def clear():
    try:
        with open(logfile, 'w') as f:
            f.close
    except:
        sys.exit(1)

###################################################
#
# MAIN
#
###################################################

if daemon != "yes":
    clear()
    ip = getProxyIP()
    if ip == None:
        sys.exit(1)
    ipFlag = isIpChanged(ip);
    if ipFlag == 1:
        mark("INFO", "100", "IP is not changed from last successful update")
        sys.exit(0)
    postNewIP(ip)
else:
    if os.path.isfile(pidfile):
        sys.stderr.write("Pidfile " + pidfile + " exists, another instance already running?\n")
        sys.exit(1)
    else:
        # write pidfile
        pid = str(os.getpid())
        with open(pidfile,'w+') as f:
            f.write(pid)
            f.close
    if sys.stdin.isatty() == 1:
        # if launched by a real terminal:
        #    then fork and redirect input/output
        # else
        #    systemd will take care of everything
        daemonize()
    while True:
        clear()
        mark("INFO", "100", "Started in daemon mode")
        ip = getProxyIP()
        if ip == None:
            sys.exit(1)
        ipFlag = isIpChanged(ip)
        if ipFlag == 1:
            mark("INFO", "100", "IP is not changed from last successful update")
        else:
            postNewIP(ip)
        time.sleep(int(interval))
