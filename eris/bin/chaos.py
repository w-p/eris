#1 /usr/bin/env python3

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

import sys
import logging
import argparse
import subprocess


parser = argparse.ArgumentParser(
    description='A chaos monkey for ldap3'
)
parser.add_argument(
    '-e',
    '--environment',
    dest='venv',
    help='absolute path of the python virtual environment'
)
parser.add_argument(
    '-u',
    '--username',
    dest='username',
    help='username@domain.tld',
    required=True
)
parser.add_argument(
    '-p',
    '--password',
    dest='password',
    help='username\'s password',
    required=True
)
parser.add_argument(
    '-d',
    '--domain',
    dest='domain',
    help='domain.tld',
    required=True
)
parser.add_argument(
    '-s',
    '--ssl',
    dest='ssl',
    action='store_true',
    help='use ssl (636)'
)
parser.add_argument(
    '-i',
    '--interval',
    default=3,
    type=int,
    dest='interval',
    help='max number of seconds between changes'
)
parser.add_argument(
    '-c',
    '--count',
    default=3,
    type=int,
    dest='count',
    help='max number of changes per interval'
)
parser.add_argument(
    '--tag',
    dest='tag',
    default='ERIS',
    help='A sufficiently unique string used to track objects created by Eris'
)
parser.add_argument(
    '--debug',
    dest='debug',
    action='store_true',
    help='enable ldap module debugging'
)
args = parser.parse_args()

if args.venv:
    if args.venv[-1] != '/':
        args.venv += '/'

    activate_this = args.venv + 'bin/activate_this.py'
    with open(activate_this) as f:
        exec(
            f.read(),
            {'__file__': activate_this}
        )

from eris.app import Eris

def main():

    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger = logging.getLogger('eris')

    ps = subprocess.Popen(['ps', '-x'], stdout=subprocess.PIPE)
    output, _ = ps.communicate()
    pids = [
        int(p.split()[0]) for p
        in output.decode('utf-8').splitlines()
        if __name__ in p
    ]

    if len(pids) == 2:
        logger.info('Eris is already running with PID: {}'.format(pids[0]))
        logger.info('Kill the current instance before starting a new one.')
        sys.exit(1)

    logger.info(
        '\n' +
        'This program comes with ABSOLUTELY NO WARRANTY.' +
        'This is free software, and you are welcome to ' +
        'redistribute it under certain conditions.\n\n' +
        'Eris, Copyright (C) 2015  William Palmer\n\n' +
        'Eris is starting up...\n'
    )

    logger.info((
        'Authenticating with:\n' +
        '    username: {}\n'.format(args.username) +
        '    password: {}\n'.format(args.password) +
        '    domain:   {}\n'.format(args.domain) +
        '    ssl:      {}\n'.format(args.ssl) +
        '    interval: {}\n'.format(args.ssl) +
        '    count:    {}\n'.format(args.ssl)
    ))

    Eris(
        args.username,
        args.password,
        args.domain,
        ssl=args.ssl,
        interval=args.interval,
        count=args.count,
        tag=args.tag,
        debug=args.debug
    ).run()

if __name__ == '__main__':
    main()
