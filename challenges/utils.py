""" Utils module for ssh connections """

import ipaddress
import re

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

from urllib.parse import urlparse

numeric = re.compile(r'[0-9]+$')
allowed = re.compile(r'(?!-)[a-z0-9-]{1,63}(?<!-)$', re.IGNORECASE)


def to_str(bstr, encoding='utf-8'):
    """ Decodes bytes to str """
    if isinstance(bstr, bytes):
        return bstr.decode(encoding)
    return bstr


def to_bytes(ustr, encoding='utf-8'):
    """ Encodes str to bytes """
    if isinstance(ustr, UnicodeType):
        return ustr.encode(encoding)
    return ustr


def to_int(string):
    """ convert string to int """
    try:
        return int(string)
    except (TypeError, ValueError):
        return string


def to_ip_address(ipstr):
    """ convert string to an ip address """
    ip_address = to_str(ipstr)
    if ip_address.startswith('fe80::'):
        ip_address = ip_address.split('%')[0]
    return ipaddress.ip_address(ip_address)


def is_valid_ip_address(ipstr):
    """ check if string is a valid ip address """
    try:
        to_ip_address(ipstr)
    except ValueError:
        return False
    return True


def is_valid_port(port):
    """ is a valid port number? """
    return 0 < port < 65536


def is_valid_encoding(encoding):
    """ is encoding string a valid encoding? """
    try:
        'test'.encode(encoding)
    except LookupError:
        return False
    except ValueError:
        return False
    return True


def is_ip_hostname(hostname):
    """ check if hostname is an ip address """
    iterator = iter(hostname)
    if next(iterator) == '[':
        return True
    for character in iterator:
        if character != '.' and not character.isdigit():
            return False
    return True


def is_valid_hostname(hostname):
    """ Is hostname string a valid hostname? """
    if hostname[-1] == '.':
        # strip exactly one dot from the right, if present
        hostname = hostname[:-1]
    if len(hostname) > 253:
        return False

    labels = hostname.split('.')

    # the TLD must be not all-numeric
    if numeric.match(labels[-1]):
        return False

    return all(allowed.match(label) for label in labels)


def is_same_primary_domain(domain1, domain2):
    i = -1
    dots = 0
    ldomain1 = len(domain1)
    ldomain2 = len(domain2)
    lmin = min(ldomain1, ldomain2)

    while i >= -lmin:
        char1 = domain1[i]
        char2 = domain2[i]

        if char1 == char2:
            if char1 == '.':
                dots += 1
                if dots == 2:
                    return True
        else:
            return False

        i -= 1

    if ldomain1 == ldomain2:
        return True

    if dots == 0:
        return False

    character = domain1[i] if ldomain1 > lmin else domain2[i]
    return character == '.'


def parse_origin_from_url(url):
    """ parse url """
    url = url.strip()
    if not url:
        return url

    if not (url.startswith('http://') or
            url.startswith('https://') or
            url.startswith('//')):
        url = '//' + url

    parsed = urlparse(url)
    port = parsed.port
    scheme = parsed.scheme

    if scheme == '':
        scheme = 'https' if port == 443 else 'http'

    if port == 443 and scheme == 'https':
        netloc = parsed.netloc.replace(':443', '')
    elif port == 80 and scheme == 'http':
        netloc = parsed.netloc.replace(':80', '')
    else:
        netloc = parsed.netloc

    return f'{scheme}://{netloc}'
