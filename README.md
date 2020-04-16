# ipUpdate.py
Python client for DNSEXIT Dynamic Dns Service
###
This is a Python3 client for <b>DNSEXIT</b> dynamic dns service. It is an (almost) faithful replica of the Perl original
package for Linux available at http://www.dnsexit.com.

The setup.py script generates <b>dnsexit.conf</b> configuration file (100% compatible with the Perl version) in /etc
and enables a system service if requested. Program runs successfully on Raspberry, tested under Buster Lite. 

Install the program
-------

- copy the repository and set scripts as executables:
```
git clone https://github.com/jhonnymonclair/dnsexit.git
cd dnsexit
chmod 755 ipUpdate.py
chmod 755 setup.py
```


Configure the program
-------

- run the setup program and follow instructions:
``` 
sudo ./setup.py
```
if configured to run as daemon, a system service will be created and enabled.
To start it:
```
sudo service dnsexit start
```
To check it:
```
sudo service dnsexit status
```


Log
-------

log file (default:/var/log/dnsexit) saves info and errors
about last update attempt.
