#!/usr/bin/env python3
###################################################
##
##  DnsExit.Com Dynamic IP update setup script
##  based on original 1.6 Perl version
##
###################################################

import os
import sys
import time
from datetime import datetime
import urllib.request
import re

servicefile = "/lib/systemd/system/dnsexit.service"
cfile = "/etc/dnsexit.conf"
proxyservs = "ip.dnsexit.com;ip2.dnsexit.com;ip3.dnsexit.com"
logfile = "/var/log/dnsexit.log"
cachefile = "/tmp/dnsexit-ip.txt"
pidfile = "/run/ipUpdate.pid"
siteurl = "https://update.dnsexit.com"
apiurl = "https://api.dnsexit.com/dns/ud/"
geturlfrom = siteurl + "/ipupdate/dyndata.txt"

URL_VALIDATE = siteurl + "/ipupdate/account_validate.jsp"
URL_DOMAINS = siteurl + "/ipupdate/domains.jsp"
URL_HOSTS = siteurl + "/ipupdate/hosts.jsp"

MSG_WELCOME = "Welcome to DNSExit.Com Dynamic IP update setup script.\n" \
                 "Please follow instructions to setup our script.\n"
MSG_ROOT = "Please run this script as root user."
MSG_USERNAME = "Enter the username to dnsexit.com: "
MSG_PASSWORD = "Enter password for your username: "
MSG_APIKEY = "Enter your DNSExit API Key (generate one from DNSExit > Settings > DNS API Key): "
MSG_CHECKING_USERPASS = "Validating your login credentials..."
MSG_CHECKING_DOMAINS = "Fetching your DNS domains. It may take a while...\n" \
                         "Note: You should setup DNS for the domain first at your web account to get the domain listed below.\n"
MSG_USERPASSOK = "Login Successfully...\n"
MSG_HOSTS = "Please type password for your username:\n"
MSG_SELECT_DOMAINS = "Please select the domains to update:"
MSG_FETCHING_HOSTS = "Feching hosts in your domains. This may take a while...\n"
MSG_SELECT_HOSTS = "Please select host(s) to be updated:"
MSG_YOU_HAVE_SELECTED = "You have selected the following hosts to be updated:"
MSG_SELECT_DAEMON = "Do you want to run it as a daemon?"
MSG_SELECT_INTERVAL = "How often (in minutes) should the program checks IP changes ?\n" \
                        "IP will be posted to dnsExit.com only when IP address has been\n" \
                        "changed from the last update (minimum 3 minutes):"
MSG_SELECT_DIR = "Please select the directory to install the script:"
ERR_COPY_PROGRAM = "Fail to copy program file in selected directory."
ERR_SET_EXE = "Fail to set program file as executable."
ERR_WRITE_SERVICE = "Fail to write service file " + servicefile + "."
ERR_ENABLE_SERVICE = "Fail to enable system service."
ERR_WRITE_CFG = "Fail to write config file " + cfile + ". Please check if have proper permissions."
MSG_GENERATING_CFG = "Generating config file: "
MSG_DONE = "Done creating config file. You can run the script now.\n" \
             "To do it you can run ipUpdate.py or use service file.\n\n" \
             "File " + cachefile + " will cache the ip address of\n" \
             "the last successful IP update to our system. For next\n" \
             "update, if the IP stays the same, the update request\n" \
             "won't be sent to our server. You can simply change the\n" \
             "IP at dnsexit-ip.txt file to force the update to DNSEXIT.\n"
MSG_PATHS = "Here are paths to some interesting files:\n"
MSG_END = "Don't forget to read README file!\n"
ERR_DOMAINS = "Can't get list of your domains from the server"
ERR_NO_DOMAINS = "You don't have any domains with DNS. You should login to your account " \
                  "at www.dnsexit.com and setup DNS for your domains first.\n"
ERR_NO_URL = "Can't fetch url info from dnsexit.com. Please try again later...\n"


def make_select(arrayRef, selTitle, multiselect):
    while True:
        print(selTitle)
        iter = 0
        for item in arrayRef:
            print("  " + str(iter) + "\t" + item)
            iter += 1
        if len(arrayRef) > 1 and multiselect == 1:
            print("[separate multi selects by space]")
        selection = input("Your selection: ")
        selection = selection.replace('\t', ' ')
        selection = re.sub(' +', ' ', selection)
        selection = selection.split(' ')
        list = []
        for iter in selection:
            try:
                list.append(arrayRef[int(iter)])
            except:
                pass
        if len(list) == 1 and multiselect == 0:
            break
        if len(list) > 0:
            if multiselect == 0:
                print("Please select one only !!")
            else:
                break
    return list


print(MSG_WELCOME)
#
# Check user id
#
if os.geteuid() != 0:
    print(MSG_ROOT)
    sys.exit(0)

#
# Delete old cache file
#
if os.path.isfile(cachefile):
    try:
        os.remove(cachefile)
    except:
        print("can't remove " + cachefile)
        sys.exit(1)

#
# Get url from dnsexit.com
#
# Obsolete: We're now using the API url instead
# try:
#     data = urllib.request.urlopen(geturlfrom).readline()
# except urllib.error.URLError:
#     print(ERR_NO_URL)
#     sys.exit(1)
# trash, url = data.decode('utf-8').split('=')

#
# Get username/password and validate it.
#
while True:
    # Get username
    username = input(MSG_USERNAME)
    # Get password
    password = input(MSG_PASSWORD)
    password = password.replace(' ', '%20')
    print(MSG_CHECKING_USERPASS)
    try:
        data = urllib.request.urlopen(URL_VALIDATE + "?login=" + username + "&password=" + password).read()
    except urllib.error.URLError:
        print("URL Error")
        sys.exit(1)
    response = data.decode('utf-8').replace('\n', '')
    code, message = response.split('=')
    if int(code) == 0:
        break
    else:
        print("\nError: " + message + "\n")
print(MSG_USERPASSOK)

#
# Get list of domains and ask user which of them should be explored
#
print(MSG_CHECKING_DOMAINS)
try:
    data = urllib.request.urlopen(URL_DOMAINS + "?login=" + username + "&password=" + password).read()
except urllib.error.URLError:
    print(ERR_DOMAINS + "\n\n")
    sys.exit(1)
response = data.decode('utf-8').replace('\n', '')
code, message = response.split('=')
if int(code) == 0:
    domains = message.split(' ')
elif int(code) == 1:
    print(ERR_NO_DOMAINS + "\n")
    sys.exit(1)
else:
    print("\nError: " + message + "\n")
    sys.exit(1)
selected = make_select(domains, MSG_SELECT_DOMAINS, 1)

#
# Get list of hosts from selected domains and ask user which should be added
# to the config file.
#
print(MSG_FETCHING_HOSTS)
hosts = []
for domain in selected:
    try:
        data = urllib.request.urlopen(URL_HOSTS + "?login=" + username + "&password=" + password + "&domain=" + domain).read()
    except urllib.error.URLError:
        print("URL Error")
        sys.exit(1)
    response = data.decode('utf-8').replace('\n', '')
    code, message = response.split('=')
    if int(code) == 0:
        list = message.split(' ')
        for iter in list:
            hosts.append(iter)
selected = make_select(hosts, MSG_SELECT_HOSTS, 1)

print("\n" + MSG_YOU_HAVE_SELECTED)
for iter in selected:
    print("\t" + iter)
hosts = ",".join(hosts)

#
# Ask if user wants daemon mode.
#
print(MSG_SELECT_DAEMON)
answer = None
while answer != "yes" and answer != "no":
    answer = input("Your choice [yes]: ")
    if answer == "":
        answer = "yes"
daemon = answer
autostart = answer

#
# If daemon=YES then ask for an interval
#
print("\n")
interval = 600
programdir = os.path.dirname(os.path.realpath(__file__))
program = programdir + "/ipUpdate.py"
if daemon == "yes":
    print(MSG_SELECT_INTERVAL)
    while True:
        interval = input("Your choice [10]: ")
        if interval == "":
            interval = 10
            break
        try:
            interval = int(interval)
            if interval > 3:
                break
            print("Error: minimum 3 minutes")
        except:
            pass
    #convert to seconds
    interval = interval * 60

    apikey = input(MSG_APIKEY)

    seldirs = (programdir, "/usr/local/bin", "/usr/sbin")
    dir = make_select(seldirs, MSG_SELECT_DIR, 0)
    if dir[0] != programdir:
        try:
            os.chmod(program, 0o755)
        except:
            print(ERR_SET_EXE)
            sys.exit(1)
        try:
            os.system("cp " + program + " " + dir[0])
        except:
            print(ERR_COPY_PROGRAM)
            sys.exit(1)
    #
    # Generate .service file
    #
    try:
        f = open(servicefile, 'w')
        f.write("[Unit]" + "\n")
        f.write(" Description=DNSEXIT Dynamic Dns Service" + "\n")
        f.write(" After=network-online.target" + "\n")
        f.write("\n")
        f.write("[Service]" + "\n")
        f.write(" Type=simple" + "\n")
        f.write(" PIDFile=" + pidfile + "\n")
        if dir[0] != programdir:
            f.write(" ExecStart=" + dir[0] + "/ipUpdate.py" + "\n")
        else:
            f.write(" ExecStart=" + program + "\n")
        f.write(" Restart=on-failure" + "\n")
        f.write(" RestartSec=30" + "\n")
        f.write("\n")
        f.write("[Install]" + "\n")
        f.write(" WantedBy=default.target" + "\n")
        f.close()
    except:
        print(ERR_WRITE_SERVICE)
        sys.exit(1)
    #
    # enable service
    #
    try:
        os.system("systemctl enable dnsexit")
    except:
        print(ERR_ENABLE_SERVICE)
        sys.exit(1)


#
# Set program as executable
#
try:
    os.chmod(program, 0o755)
except:
    print(ERR_SET_EXE)
    sys.exit(1)


#
# Generate config file
#
print("\n" + MSG_GENERATING_CFG + cfile)
try:
    f = open(cfile, 'w')
    f.write("apikey=" + apikey + "\n")
    f.write("host=" + hosts + "\n")
    f.write("daemon=" + daemon + "\n")
    f.write("autostart=" + autostart + "\n")
    f.write("interval=" + str(interval) + "\n")
    f.write("proxyservs=" + proxyservs + "\n")
    f.write("pidfile=" + pidfile + "\n")
    f.write("logfile=" + logfile + "\n")
    f.write("cachefile=" + cachefile + "\n")
    f.write("url=" + apiurl)
    f.close()
except:
    print(ERR_WRITE_CFG)
    sys.exit(1)

print("\n" + MSG_DONE)
print(MSG_PATHS)
print("  Config file:\t" + cfile)
print("  Pid file:\t" + pidfile)
print("  Log file:\t" + logfile)
print("  Cache file:\t" + cachefile)
print("\n" + MSG_END)
