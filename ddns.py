#!/usr/bin/env python3

import cgi
import cgitb
import datetime
import os
import socket
from configparser import ConfigParser

import dns
import dns.exception
import dns.ipv4
import dns.ipv6
import dns.query
import dns.tsigkeyring
from dns.tsig import HMAC_MD5
from dns.update import UpdateMessage

cgitb.enable()

configuration_file = "ddns.ini"

# Is a valid IPV4 address?
def isValidV4Addr(Address):
    try:
        dns.ipv4.inet_aton(Address)
    except socket.error:
        print('Error:', Address, 'is not a valid IPv4 address')
        exit()
    return True


# Is a valid IPv6 address?
def isValidV6Addr(Address):
    try:
        dns.ipv6.inet_aton(Address)
    except SyntaxError:
        print('Error:', Address, 'is not a valid IPv6 address')
        exit()
    return True


def read_data(domain):
    valid_options = ["password", "dns-server", "nsupdate-key", "origin"]

    cp = ConfigParser()
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
            try:
                ip_check[iparg](args[iparg])
                foundAny = True
            except dns.exception.SyntaxError as e:
                print("Error:", args[iparg], "is not a valid", iparg)
                error = True

    if not error and not foundAny:
        # Get IP from REMOTE_ADDR anc check whether it is v4 or v6
        ip = os.environ["REMOTE_ADDR"]
        for iparg in ip_arguments:
            try:
                if ip_check[iparg](ip):
                    args[iparg] = ip

            except dns.exception.SyntaxError as e:
                pass

    if error is True:
        print("Error: There were errors while parsing the arguments.<br>")
        exit()

    return args


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

    def clean_domain():
        if not arguments["domain"].endswith(data["origin"]):
            raise ValueError("the domain", arguments["domain"], "does not end with the origin parameter", data["origin"])
        
        return arguments["domain"].replace("." + data["origin"], "")

    name = clean_domain()


    # add "." to origin if required
    if not data["origin"].endswith("."):
        data["origin"] = data["origin"] + "."

    # convert dns server name to ip
    data["dns-server-ip"] = socket.gethostbyname(data["dns-server"])
    keyring = dns.tsigkeyring.from_text({data["origin"]: data["nsupdate-key"]})
    um = UpdateMessage(data["origin"], keyring=keyring, keyalgorithm=HMAC_MD5)

    um.replace(name, 60, "TXT",  "last update: %s Europe/Berlin" %
               datetime.datetime.now())
    dns.query.tcp(um, data["dns-server-ip"])

    # Update each requested ipaddr_type, or delete if not passed
    ip_type = {"ip4addr": "A", "ip6addr": "AAAA"}
    for ipaddr_type in ip_arguments:

        um = UpdateMessage(
            data["origin"], keyring=keyring, keyalgorithm=HMAC_MD5)

        if ipaddr_type in arguments:
            um.replace(
                name, 60, ip_type[ipaddr_type], arguments[ipaddr_type])
        else:
            um.delete(name, ip_type[ipaddr_type])

        dns.query.tcp(um, data["dns-server-ip"], )


if __name__ == "__main__":
    main()
