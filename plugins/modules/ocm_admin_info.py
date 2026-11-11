#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_admin_info

short_description: Describe the cluster-admin user for a ROSA cluster

version_added: "1.0.0"

description: |
    Reports whether a ``cluster-admin`` htpasswd identity provider exists and
    returns API URL and a suggested ``oc login`` command (mirrors ``rosa describe admin``).

options:
    cluster:
        description: Cluster name or ID.
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: Describe cluster-admin for a cluster
  ocm_admin_info:
    cluster: my-rosa-cluster
'''

RETURN = r'''
admin:
    description: Admin user summary from OCM
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import ocm_admin_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**ocm_admin_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
