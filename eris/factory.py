
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

from faker import Factory as FakerFactory


faker = FakerFactory.create()


class Factory(object):
    root_dn = None
    computer_ous = [
        ('Servers',         ['Development', 'Testing', 'Production']),
        ('Workstations',    ['Development', 'Testing', 'Production'])
    ]
    user_ous = [
        ('Staff',           ['Executive', 'Finance', 'Engineering', 'Support']),
        ('External',        ['Vendors', 'Customers'])
    ]
    salutations = [
        'Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Gen.', 'Col.', 'Maj.', 'Capt.'
    ]
    access_levels = [
        'USERS', 'MGMT', 'ADMINS', 'SVC'
    ]
    service_names = [
        'SQL', 'NET', 'WEB', 'APP', 'SEC'
    ]
    os_names = [
        'WIN', 'LIN', 'OSX', 'BSD', 'HPX'
    ]
    special_chars = [x for x in '!@#$%^&*()_+']

    def __init__(self, domain, root_dn, tag):
        self.domain = domain
        self.root_dn = root_dn
        self.tag = tag

    def get_ou(self, type='user'):
        if type == 'user':
            base, subs = faker.random_element(self.user_ous)
        else:
            base, subs = faker.random_element(self.computer_ous)
        sub = faker.random_element(subs)
        parts = [sub] + [base] + [self.root_dn]
        return 'ou={},ou={},{}'.format(*parts)

    def get_computer_name(self):
        return '{}-{}-{}'.format(
            faker.random_element(self.service_names),
            faker.random_element(self.os_names),
            faker.numerify('###')
        )

    def get_group_name(self):
        return '{}-{}'.format(
            faker.random_element(self.service_names),
            faker.random_element(self.access_levels)
        )

    def get_password(self, length=15):
        if length < 8:
            length = 8
        return (
            faker.random_letter().upper() +
            faker.random_letter().upper() +
            faker.random_letter().lower() +
            faker.random_letter().lower() +
            str(faker.random_digit()) +
            str(faker.random_digit()) +
            faker.random_element(self.special_chars) +
            faker.random_element(self.special_chars) +
            faker.lexify('?' * (length - 8))
        )

    def get_user(self):
        givenName = faker.first_name()
        sn = faker.last_name()
        name = '{} {}'.format(givenName, sn)
        sAMAccountName = '{}.{}'.format(givenName[:18], sn)[:20].lower()
        userPrincipalName = '{}@{}'.format(sAMAccountName, self.domain)
        obj = {
            'givenName': givenName,
            'sn': sn,
            'name': name,
            'displayName': '{} {}'.format(faker.random_element(self.salutations), name),
            'mail': '{}.{}@{}'.format(givenName, sn, self.domain),
            'description': '{}-{}'.format(self.tag, faker.job()),
            'streetAddress': faker.street_address(),
            'st': faker.state_abbr(),
            'l': faker.city(),
            'postalCode': faker.postcode(),
            'telephoneNumber': faker.phone_number(),
            'c': faker.country_code(),
            'sAMAccountName': sAMAccountName,
            'userPrincipalName': userPrincipalName,
            'company': faker.company()
        }
        for k, v in obj.items():
            obj[k] = [v]
        return (self.get_ou(), obj)

    def get_contact(self):
        givenName = faker.first_name()
        sn = faker.last_name()
        name = '{} {}'.format(givenName, sn)
        obj = {
            'givenName': givenName,
            'sn': sn,
            'name': name,
            'displayName': '{} {}'.format(faker.random_element(self.salutations), name),
            'mail': '{}.{}@{}'.format(givenName, sn, self.domain),
            'description': '{}-{}'.format(self.tag, faker.job()),
        }
        for k, v in obj.items():
            obj[k] = [v]
        return (self.get_ou(), obj)

    def get_computer(self):
        obj = {
            'name': self.get_computer_name(),
            'description': '{}-{}'.format(self.tag, faker.sentence())
        }
        for k, v in obj.items():
            obj[k] = [v]
        return (self.get_ou(), obj)

    def get_group(self):
        obj = {
            'name': self.get_group_name(),
            'description': '{}-{}'.format(self.tag, faker.sentence())
        }
        for k, v in obj.items():
            obj[k] = [v]
        return (self.get_ou(), obj)
