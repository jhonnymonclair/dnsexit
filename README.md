# ipUpdate.py
Python client for DNSEXIT Dynamic Dns Service
###
This is a Python3 client for <b>DNSEXIT</b> dynamic dns service. 

It is a fork of jhonnymonclair's version.

However it is using the DNS Exit API which is more secure than 
the RemoteUpdate.sv as it is not sending your username or password down the wire.

It is also more resilient as it will not kill the daemon if you have temporarily lost
internet connectivity while your IP address is being checked.

The setup.py script generates <b>dnsexit.conf</b> configuration file in /etc
and enables a system service if requested. 

Install the program
-------

- copy the repository and set scripts as executables:
```
git clone https://github.com/Gerard-CK/dnsexit-updater.git
cd dnsexit-updater
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

log file (default:/var/log/dnsexit.log) saves info and errors
about last update attempt.
