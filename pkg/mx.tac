# -*- encoding: utf-8 -*-
# mx.tac
# Copyright (C) 2013 LEAP
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

import sys
import ConfigParser

from functools import partial

from leap.mx import couchdbhelper
from leap.mx.mail_receiver import MailReceiver
from leap.mx.alias_resolver import AliasResolverFactory
from leap.mx.check_recipient_access import CheckRecipientAccessFactory

try:
    from twisted.application import service, internet
    from twisted.internet import inotify
    from twisted.internet.endpoints import TCP4ServerEndpoint
    from twisted.python import filepath, log
    from twisted.python import usage
except ImportError, ie:
    print "This software requires Twisted>=12.0.2, please see the README for"
    print "help on using virtualenv and pip to obtain requirements."

config_file = "/etc/leap/mx.conf"

config = ConfigParser.ConfigParser()
config.read(config_file)

user = config.get("couchdb", "user")
password = config.get("couchdb", "password")

server = config.get("couchdb", "server")
port = config.get("couchdb", "port")

alias_port = config.getint("alias map", "port")
check_recipient_port = config.getint("check recipient", "port")

cdb = couchdbhelper.ConnectedCouchDB(server,
                                     port=port,
                                     dbName="users",
                                     username=user,
                                     password=password)


application = service.Application("LEAP MX")

# Alias map
alias_map = internet.TCPServer(alias_port, AliasResolverFactory(couchdb=cdb))
alias_map.setServiceParent(application)

# Check recipient access
check_recipient = internet.TCPServer(check_recipient_port,
                                     CheckRecipientAccessFactory(couchdb=cdb))
check_recipient.setServiceParent(application)

# Mail receiver
mail_couch_url_prefix = "http://%s:%s@%s:%s" % (user,
                                                password,
                                                server,
                                                port)
directories = []
for section in config.sections():
    if section in ("couchdb", "alias map", "check recipient"):
        continue
    to_watch = config.get(section, "path")
    recursive = config.getboolean(section, "recursive")
    directories.append([to_watch, recursive])

mr = MailReceiver(mail_couch_url_prefix, cdb, directories)
mr.setServiceParent(application)
