#!/usr/bin/env python3

import os
import cgi
import cgitb
import datetime
from configparser import SafeConfigParser

from dnsupdate import doUpdate, isValidV4Addr, isValidV6Addr

cgitb.enable()

configuration_file = "ddns.ini"


def read_data(domain):
    valid_options = ["password", "dns-server", "nsupdate-key", "origin"]

    cp = SafeConfigParser()
    cp.read(configuration_file)
    if cp.has_section(domain):
        data = dict()
        for option, value in cp.items(domain):
            if option in valid_options:
                data[option] = value
            else:
                print("Error: Found a invalid option for domain",
                      domain, ":", option)
                exit()
        return data

    return None


def print_header():
    print("Content-Type: text/html")     # HTML is following
    print()                              # blank line, end of headers


ip_arguments = ["ip4addr", "ip6addr"]


def read_arguments():
    required_arguments = ["domain", "password"]

    ip_check = {"ip4addr": isValidV4Addr, "ip6addr": isValidV6Addr}

    valid_arguments = required_arguments + ip_arguments
    args = dict()
    # Read the arguments
    form = cgi.FieldStorage()
    for arg in valid_arguments:
        if arg in form:
            args[arg] = form[arg].value

    # Verify that they are complete
    error = False
    for reqarg in required_arguments:
        if reqarg not in args:
            print("Error:", reqarg, "was not passed<br>")
            error = True

    foundAny = False
    for iparg in ip_arguments:
        if iparg in args:
            if not ip_check[iparg](args[iparg]):
                print("Error:", args[iparg], "is not a valid", iparg)
                error = True
            else:
                foundAny = True

    if not error and not foundAny:
        # Get IP from REMOTE_ADDR anc check whether it is v4 or v6
        ip = os.environ["REMOTE_ADDR"]
        for iparg in ip_arguments:
            if ip_check[iparg](ip):
                args[iparg] = ip

    if error is True:
        print("Error: There were errors while parsing the arguments.<br>")
        exit()

    return args


def generate_nsupdate_key_string(ddata):
    origin = ddata["origin"]
    if not origin.endswith("."):
        origin = origin + "."

    return {origin: ddata["nsupdate-key"]}


def generate_action_string(domain, ddata, ip, ipaddr_type, action="update"):
    ip_type = {"ip4addr": "A", "ip6addr": "AAAA"}

    TTL = 60
    TYPE = ip_type[ipaddr_type]
    return [action, domain, str(TTL), TYPE, ip]


def main():
    print_header()

    # Parse the passed arguments
    arguments = read_arguments()

    domain = arguments["domain"]

    # Read the 'configuration_file'
    data = read_data(domain)

    # Is the request valid and the domain configured?
    if not (data is not None and arguments["password"] == data["password"]):
        print("Error: Invalid domain/password combination")
        exit()

    nsu_str = generate_nsupdate_key_string(data)

    def date_update_str(): return ["update", domain, "60", "TXT",
                                   "last update: %s Europe/Berlin" % datetime.datetime.now()]

    # add date record
    doUpdate(data["dns-server"], nsu_str,
             data["origin"], False, date_update_str())

    # Update each requested ipaddr_type, or delete if not passed
    for ipaddr_type in ip_arguments:
        if ipaddr_type in arguments:
            a = "update"
        else:
            a = "delete"

        action = generate_action_string(
            domain, data, arguments[ipaddr_type], ipaddr_type, action=a)
        doUpdate(data["dns-server"], nsu_str,
                 data["origin"], False, action)


if __name__ == "__main__":
    main()
