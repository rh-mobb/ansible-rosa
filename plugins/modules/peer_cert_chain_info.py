#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from sys import stdout
__metaclass__ = type


DOCUMENTATION = r'''
---
module: peer_cert_chain_info

short_description: Fetches certificate chain from peer

version_added: "1.0.0"

description:
  - Fetches certificate chain from peer of TLS connection.
  - Attempts to determine CA cert (last cert in chain) and thumbprint.

options:
    host:
        description: host to fetch cert chain from
        required: true
        type: str
    port:
        description: port of host to fetch cert chain from
        required: false
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: get peer cert chain from google
  peer_cert_chain_info:
    host: google.com
    port: 443
'''

RETURN = r'''
chain:
  - <X509 cert>
  - <X509 cert>
ca_cert: <X509 cert>
ca_thumbprint: 9E:99:A4:8A:99:60:B1:49:26:BB:7F:3B:02:E2:2D:A2:B0:AB:72:80

# These are examples of possible return values, and in general should use other names for return values.
'''

from ansible.module_utils.basic import *
import socket
from OpenSSL import SSL, crypto
import certifi
import urllib.parse
from hashlib import sha1

def run_module():
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=False, default=443),
    )

    result = dict(
        chain=list(),
        ca_thumbprint=str(),
        ca_cert=str()
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    hostname = urllib.parse.urlparse(module.params['host']).netloc
    if not hostname:
        hostname = module.params['host']
    port = module.params['port']
    dst = (hostname, port)
    try:
        ctx = SSL.Context(SSL.TLS_METHOD)
        s = socket.create_connection(dst)
        s = SSL.Connection(ctx, s)
        s.set_connect_state()
        s.set_tlsext_host_name(str.encode(dst[0]))

        s.sendall(str.encode('HEAD / HTTP/1.0\n\n'))

        cert_chain = s.get_peer_cert_chain()
        ca_cert = cert_chain[-1]
        result['ca_thumbprint'] = ca_cert.digest("sha1")
        result['ca_cert'] = crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode("utf-8")
        for cert in cert_chain:
            result['chain'].append(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        s.close()
    except SSL.Error as e:
        module.fail_json(e) #, msg="failed")
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
