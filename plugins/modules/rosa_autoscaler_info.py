#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: rosa_autoscaler_info

short_description: Describe cluster autoscaler configuration

version_added: "1.0.0"

description: |
    Legacy module contract for ``rosa describe autoscaler``; uses OCM via ocm_autoscaler_info.

options:
    cluster:
        description: Cluster name or ID (rosa ``-c`` / ``--cluster``).
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: Describe autoscaler for a cluster
  rosa_autoscaler_info:
    cluster: my-rosa-cluster
'''

RETURN = r'''
commands:
    description: Synthetic command audit list
    type: list
autoscaler:
    description: Cluster autoscaler configuration
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import rosa_autoscaler_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**rosa_autoscaler_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
