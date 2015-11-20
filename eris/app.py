
#
# Eris, A chaos monkey for ldap3.
# Copyright (C) 2015  William Palmer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import sys
import json
import ldap3
import random
import signal
from time import sleep
from datetime import datetime
from eris.factory import Factory
from ldap3.utils import dn as dn_utils
from ldap3.utils.log import set_library_log_detail_level, EXTENDED


logger = logging.getLogger('eris')

TREE_DELETE = ('1.2.840.113556.1.4.805', False, None)
SHOW_DELETED = ('1.2.840.113556.1.4.417', False, None)
SHOW_RECYCLED = ('1.2.840.113556.1.4.2064', False, None)

def get_relative_dn(dn):
    return dn_utils.get_next_ava(dn)[0]


def get_parent_dn(dn):
    rdn = get_relative_dn(dn)
    return dn.replace(rdn + ',', '')


def get_path_dns(dn):
    dns = []
    while not dn.lower().startswith('dc'):
        dns.append(dn)
        dn = get_parent_dn(dn)
    dns.sort(key=len)
    return dns


class ErisStats(object):
    deleted = 0
    created = 0
    moved = 0
    errors = 0
    start = datetime.utcnow()

    @property
    def run_time(self):
        return datetime.utcnow() - self.start

    @property
    def total(self):
        return self.deleted + self.created + self.moved

    def __repr__(self):
        return (
            '\n' +
            'Started:  {}\n' +
            'Run Time: {}\n' +
            '------------\n' +
            'Deleted:  {}\n' +
            'Created:  {}\n' +
            'Moved:    {}\n' +
            'Total:    {}\n' +
            'Errors:   {}\n'
        ).format(
            self.start,
            self.run_time,
            self.deleted,
            self.created,
            self.moved,
            self.total,
            self.errors
        )


class Eris(object):
    __running__ = False
    classes = [
        'user',
        'group',
        'contact',
        'computer'
    ]
    actions = [
        'move',
        'create',
        'delete'
    ]

    def __init__(self, username, password, domain, ssl=False, interval=5, count=5, tag='ERIS', debug=False):
        self.stats = ErisStats()
        self.interval = interval
        self.count = count
        self.tag = tag
        self.server = ldap3.Server(
            domain,
            port=(636 if ssl else 389),
            use_ssl=ssl,
            allowed_referral_hosts=[('*', True)],
            get_info=ldap3.ALL,
            connect_timeout=5
        )
        self.client = ldap3.Connection(
            self.server,
            user=username,
            password=password,
            check_names=True,
            auto_bind=True,
            client_strategy=ldap3.SYNC,
            raise_exceptions=True,
            fast_decoder=True # set False to test pyasn1
        )
        self.factory = Factory(domain, self.root_dn, self.tag)
        logger.info('[ connected to {} on {} ]'.format(
            self.root_dn,
            self.hostname
            )
        )

    @property
    def hostname(self):
        try:
            return self.client.server.info.other.get('dnsHostName')
        except Exception as e:
            return self.server.host

    @property
    def vendor(self):
        vendor = self.client.server.info.vendor_name or []
        version = self.client.server.info.vendor_version or []
        return ' '.join(vendor + version)

    @property
    def root_dn(self):
        self.client.server.info.naming_contexts.sort(key=len)
        return self.client.server.info.naming_contexts[0]

    def find(self, object_class):
        result = self.client.extend.standard.paged_search(
            self.root_dn,
            '(&(objectclass={})(description={}*))'.format(object_class, self.tag),
            search_scope=ldap3.SUBTREE,
            attributes=['*'],
            paged_size=500,
            generator=False
        )
        if result:
            entries = json.loads(self.client.response_to_json())
            return list(
                map(
                    lambda x: x.get('attributes'),
                    entries.get('entries')
                )
            )
        return []

    def generate_objects(self, object_class, count=0):
        if object_class in self.classes:
            producer = getattr(self.factory, 'get_{}'.format(object_class))
            for i in range(count):
                yield producer()
        else:
            yield iter([])

    def create(self, object_class, count=0):
        objects = self.generate_objects(object_class, count)
        for ou, attributes in objects:
            for dn in get_path_dns(ou):
                try:
                    self.client.add(
                        dn,
                        'organizationalUnit',
                        {'description': ['{}'.format(self.tag)]}
                    )
                    logger.info(' + create: {}'.format(dn))
                    self.stats.created += 1
                except ldap3.LDAPEntryAlreadyExistsResult as e:
                    logger.info(' - create: already exists - {}'.format(dn))
                    self.stats.errors += 1
            cn = attributes.get('givenName', attributes.get('name'))[0]
            dn = 'cn={},{}'.format(cn, ou)
            try:
                self.client.add(dn, object_class, attributes)
                logger.info(' + create: {}'.format(dn))
                self.stats.created += 1
            except ldap3.LDAPEntryAlreadyExistsResult as e:
                logger.info(' - create: already exists: {}'.format(dn))
                self.stats.errors += 1
            except Exception as e:
                logger.info(' - create: error: {}'.format(dn))
                logger.exception(e)
                self.stats.errors += 1

    def delete(self, object_class, count=0):
        objects = self.find('*')
        objects = objects[:count] if count else objects
        for obj in objects:
            dn = obj.get('distinguishedName')
            try:
                self.client.delete(dn, controls=[TREE_DELETE])
                logger.info(' + delete: {}'.format(dn))
                self.stats.deleted += 1
            except ldap3.LDAPNoSuchObjectResult as e:
                logger.info(' - delete: no longer present: {}'.format(dn))
                self.stats.errors += 1
            except ldap3.LDAPInsufficientAccessRightsResult as e:
                logger.info(' - delete: insufficient rights: {}'.format(dn))
                self.stats.errors += 1
            except Exception as e:
                logger.info(' - delete: error: {}'.format(dn))
                logger.exception(e)
                self.stats.errors += 1

    def move(self, count):
        objects = self.find('*')[:count]
        for obj in objects:
            dn = obj.get('distinguishedName')
            targets = self.find('organizationalUnit')
            new_dn = random.choice(targets).get('distinguishedName')
            if dn != new_dn and dn not in new_dn:
                try:
                    self.client.modify_dn(
                        dn,
                        get_relative_dn(dn),
                        delete_old_dn=True,
                        new_superior=new_dn
                    )
                    logger.info(' + move: {} -> {}'.format(dn, new_dn))
                    self.stats.moved += 1
                except ldap3.LDAPEntryAlreadyExistsResult as e:
                    logger.info(' - move: duplicate cn: {}'.format(dn))
                    self.stats.errors += 1
                except ldap3.LDAPNoSuchObjectResult as e:
                    logger.info(' - move: no longer present: {}'.format(dn))
                    self.stats.errors += 1
                except Exception as e:
                    logger.info(' - move: error: {}'.format(dn))
                    logger.exception(e)
                    self.stats.errors += 1

    def run(self):
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        self.__running__ = True
        while self.__running__:
            interval = random.randint(0, self.interval)
            count = random.randint(0, self.count)
            action = random.choice(self.actions)
            object_class = random.choice(self.classes)
            try:
                if action == 'create':
                    self.create(object_class, count)
                elif action == 'delete':
                    self.delete(object_class, count)
                elif action == 'move':
                    self.move(count)
            except Exception as e:
                logger.exception(e)
                self.stats.errors += 1
            logger.info(self.stats)
            logger.info('[ next cycle in {} seconds... ]'.format(interval))
            sleep(interval)

        logger.info('[ cleaning up... ]')
        self.delete('*')
        logger.info('[ cleanup complete ]')
        logger.info(self.stats)

    def shutdown(self, signal, frame):
        if self.__running__ == False:
            logger.info('[ forcing shutdown without cleanup ]')
            sys.exit(1)
        self.__running__ = False
        logger.info('[ shutting down... ]')
