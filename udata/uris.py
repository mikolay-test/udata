# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from netaddr import IPAddress, AddrFormatError
from tlds import tld_set as TLDS

URL_REGEX = re.compile(
    r'^'
    # scheme
    r'^(?P<scheme>[a-z0-9\.\-]*)://'
    # user:pass authentication
    r'(?P<credentials>\S+(?::\S*)?@)?'
    r'(?:'
    # localhost
    r'(?P<localhost>localhost(?:\.localdomain)?)'
    r'|'
    # IPv4 addresses
    r'(?P<ipv4>(?:\d{,3}\.){3}(?:\d{,3}))'
    r'|'
    # IPv6 address
    r'(?:\[(?P<ipv6>[0-9a-f:]+)\])'
    r'|'
    # host name
    r'(?:(?:[a-z\u00a1-\uffff0-9_]-?)*[a-z\u00a1-\uffff0-9]+)'
    # domain name
    r'(?:\.(?:[a-z\u00a1-\uffff0-9_]-?)*[a-z\u00a1-\uffff0-9]+)*'
    # TLD identifier
    r'(?:\.(?P<tld>[a-z0-9\u00a1-\uffff]{2,}))'
    r')'
    # port number
    r'(?::\d{2,5})?'
    # resource path
    r'(?:/\S*)?'
    # query string
    r'(?:\?\S*)?'
    r'$',
    re.UNICODE | re.IGNORECASE
)

SCHEMES = ('http', 'https', 'ftp', 'ftps')


class ValidationError(ValueError):
    '''Raised when URL is invalid'''
    pass


def error(url, reason=None):
    __tracebackhide__ = True
    msg = 'Invalid URL "{0}"'.format(url)
    if reason:
        msg = ': '.join((msg, reason))
    raise ValidationError(msg)


def validate(url, schemes=SCHEMES, tlds=TLDS, private=False, local=False):
    '''
    Validate and normalize an URL

    :param str url: The URL to validate and normalize
    :return str: The normalized URL
    :raises ValidationError: when URL does not validate
    '''
    url = url.strip()
    match = URL_REGEX.match(url)
    if not match:
        error(url)

    scheme = match.group('scheme').lower()
    if scheme not in schemes:
        error(url, 'Invalid scheme {0}'.format(scheme))

    tld = match.group('tld')
    if tld and tld not in tlds and tld.encode('idna') not in tlds:
        error(url, 'Invalid TLD {0}'.format(tld))

    ip = match.group('ipv6') or match.group('ipv4')
    if ip:
        try:
            ip = IPAddress(ip)
        except AddrFormatError:
            error(url)
        if ip.is_multicast():
            error(url, '{0} is a multicast IP'.format(ip))
        elif not ip.is_loopback() and ip.is_hostmask() or ip.is_netmask():
            error(url, '{0} is a mask IP'.format(ip))

    if not local:
        if ip and ip.is_loopback() or match.group('localhost'):
            error(url, 'is a local URL')

    if not private and ip and ip.is_private():
        error(url, 'is a private URL')

    return url
