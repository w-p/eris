Eris
====

Eris is a chaos monkey tool for the excellent ldap3 library <https://github.com/cannatag/ldap3>.

Eris continously generates random objects and performs operations against your Active Directory
or Samba domain controller. This project was created to test certain systems being developed at
https://www.steelhive.com by producing error generating situations through the simulation of directory services activity found in real world deployments.

**WARNING: Do not run this against a production server unless you know what you're doing!**

The objectClass and operation lists below delineate the currently supported operations and objects
that Eris will use.  Eris only operates on objects with a matching `tag` in the `description`
attribute.  This means that of the operations performed, none are executed without validating the
presence of the `tag`. By default, `tag` is 'ERIS'. You may specify your own `tag` with the
`--tag` switch. It should be clear as to why a sufficiently unique tag is desired.

objectClass:
* user
* computer
* contact
* group (security, not distribution)

operations:
* create
* delete
* move

Known Issues
------------
**Issue**: On Samba domain controllers, running Eris for a longer period of time will eventually cause Samba to
hang and cease serving LDAP requests.

**Resolution**: Stop and restart the Samba service. `systemctl stop samba-ad-dc && systemctl start samba-ad-dc`

**Notes**: This is not an issue with Active Directory.  A bug has been submitted to the Samba team and I
continue explore this issue myself.

Requirements
------------
* python 3.4
* faker
* ldap3
* Active Directory (>=Server 2008 R2) or Samba (>=4)

Installation
------------
Pretty simple.

`git clone https://github.com/w-p/Eris.git`

`cd Eris`

`pip install .`

Running
-------
Eris performs `count` operations per cycle waiting `interval` seconds between cycles.
By default, `count=3` and `interval=3`.  You can throttle these options up and down
to increase or decrease the volatility of Eris.

`eris -u administrator@mydomain.com -p 'SUp3r$ecre7!!' -d mydomain.com`

To stop Eris, press `ctrl+c`. This tells Eris that on the next loop, delete everything
that it's created so far. If it hangs because a socket is hung (see known issues) or
some other oddity occurs, press `crtl+c` a second time to forcefully abort.

Options
-------
    usage: eris [-h] [-e VENV] -u USERNAME -p PASSWORD -d DOMAIN [-s]
                [-i INTERVAL] [-c COUNT] [--tag TAG] [--debug]

    A chaos monkey for ldap3

    optional arguments:
      -h, --help            show this help message and exit
      -e VENV, --environment VENV
                            absolute path of the python virtual environment
      -u USERNAME, --username USERNAME
                            username@domain.tld
      -p PASSWORD, --password PASSWORD
                            username's password
      -d DOMAIN, --domain DOMAIN
                            domain.tld
      -s, --ssl             use ssl (636)
      -i INTERVAL, --interval INTERVAL
                            max number of seconds between changes
      -c COUNT, --count COUNT
                            max number of changes per interval
      --tag TAG             A sufficiently unique string used to track objects
                            created by Eris
      --debug               enable ldap module debugging
