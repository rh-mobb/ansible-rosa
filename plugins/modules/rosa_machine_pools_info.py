#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: rosa_machine_pools_info

short_description: List machine pools on a ROSA cluster

version_added: "4.1.0"

description: |
    Legacy module contract for ``rosa list machinepool``; uses OCM via ocm_machine_pools_info.
    Use rosa_machine_pool_info to describe a single pool.

options:
    cluster:
        description: Cluster name or ID (rosa ``-c`` / ``--cluster``).
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: List machine pools like rosa list machinepool
  rosa_machine_pools_info:
    cluster: my-rosa-cluster
'''

RETURN = r'''
commands:
    description: Synthetic command audit list
    type: list
machine_pools:
    description: Machine or node pool list from OCM
    type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import rosa_machine_pools_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**rosa_machine_pools_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
