#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_upgrade_info

short_description: Describe scheduled upgrades for a ROSA cluster

version_added: "1.0.0"

description: |
    Returns scheduled upgrade policies from OCM (mirrors ``rosa describe upgrade``).
    Hosted control plane clusters use control plane or node pool upgrade policies;
    classic clusters use cluster upgrade policies.

options:
    cluster:
        description: Cluster name or ID.
        required: true
        type: str
    machine_pool:
        description: When set, list scheduled upgrades for this machine/node pool (rosa ``--machinepool``).
        required: false
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: Describe scheduled cluster upgrades
  ocm_upgrade_info:
    cluster: my-rosa-cluster

- name: Describe scheduled upgrades for workers pool
  ocm_upgrade_info:
    cluster: my-rosa-cluster
    machine_pool: workers
'''

RETURN = r'''
upgrade:
    description: Scheduled upgrade policies and metadata
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import ocm_upgrade_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=True),
            machine_pool=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**ocm_upgrade_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
