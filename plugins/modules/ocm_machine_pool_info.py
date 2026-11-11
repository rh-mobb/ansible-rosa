#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_machine_pool_info

short_description: Describe a machine pool on a ROSA cluster

version_added: "1.0.0"

description: |
    Returns a machine pool or HCP node pool from OCM (mirrors ``rosa describe machinepool``).
    Classic clusters use machine pools; hosted control plane clusters use node pools with the same ID.
    Use ocm_machine_pools_info to list all pools on a cluster.

options:
    cluster:
        description: Cluster name or ID.
        required: true
        type: str
    machine_pool:
        description: Machine pool ID (for example ``workers``).
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: Describe the workers machine pool
  ocm_machine_pool_info:
    cluster: my-rosa-cluster
    machine_pool: workers
'''

RETURN = r'''
machine_pool:
    description: Machine or node pool object from OCM
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import ocm_machine_pool_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=True),
            machine_pool=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**ocm_machine_pool_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
