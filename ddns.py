#!/usr/bin/python2.6

from dnsupdate import doUpdate
from dnsupdate import isValidV6Addr
from dnsupdate import isValidV4Addr

from ConfigParser import SafeConfigParser

import cgi
import cgitb
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
                print "Error: Found a invalid option for domain", domain, ":", option
                exit()
        return data

    return None


def print_header():
    print "Content-Type: text/html"     # HTML is following
    print                               # blank line, end of headers


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
            print "Error:", reqarg, "was not passed<br>"
            error = True

    foundAny = False
    for iparg in ip_arguments:
        if iparg in args:
            if not ip_check[iparg](args[iparg]):
                print "Error:", args[iparg], "is not a valid", iparg
                error = True
            else:
                foundAny = True

    if foundAny is False:
        print "Error: none of the following parameters was given", ip_arguments, "<br>"
        error = True

    if error is True:
        print "Error: There were errors while parsing the arguments.<br>"
        exit()

    return args


def generate_nsupdate_key_string(ddata):
    origin = ddata["origin"]
    if not origin.endswith("."):
        origin = origin + "."

    return {origin: ddata["nsupdate-key"]}


def generate_action_string(domain, ddata, ip, ipaddr_type):
    ip_type = {"ip4addr": "A", "ip6addr": "AAAA"}

    TTL = 60
    TYPE = ip_type[ipaddr_type]
    return ["update", domain, str(TTL), TYPE, ip]


def main():
    print_header()

    # Parse the passed arguments
    arguments = read_arguments()

    domain = arguments["domain"]

    # Read the 'configuration_file'
    data = read_data(domain)

    # Is the request valid and the domain configured?
    if not (data is not None and arguments["password"] == data["password"]):
        print "Error: Invalid domain/password combination"
        exit()

    nsu_str = generate_nsupdate_key_string(data[domain])

    # Update each requested ipaddr_type
    for ipaddr_type in ip_arguments:
        if ipaddr_type in arguments:
            action = generate_action_string(domain, data, arguments[ipaddr_type], ipaddr_type)
            doUpdate(data["dns-server"], nsu_str, data["origin"], False, action)

if __name__ == "__main__":
    main()
