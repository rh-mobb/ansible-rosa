#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: rosa_upgrade_info

short_description: Describe scheduled upgrades for a ROSA cluster

version_added: "1.0.0"

description: |
    Legacy module contract for ``rosa describe upgrade``; uses OCM via ocm_upgrade_info.

options:
    cluster:
        description: Cluster name or ID (rosa ``-c`` / ``--cluster``).
        required: true
        type: str
    machine_pool:
        description: Machine pool ID (rosa ``--machinepool``).
        required: false
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: Describe scheduled cluster upgrades
  rosa_upgrade_info:
    cluster: my-rosa-cluster

- name: Describe scheduled upgrades for workers pool
  rosa_upgrade_info:
    cluster: my-rosa-cluster
    machine_pool: workers
'''

RETURN = r'''
commands:
    description: Synthetic command audit list
    type: list
upgrade:
    description: Scheduled upgrade policies and metadata
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import rosa_upgrade_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=True),
            machine_pool=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**rosa_upgrade_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
