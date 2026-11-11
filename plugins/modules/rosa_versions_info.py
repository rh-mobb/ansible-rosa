#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: rosa_versions_info

short_description: List OpenShift versions available for ROSA

version_added: "1.0.0"

description: |
    Legacy module contract for ``rosa list versions``; uses OCM via ocm_version_info.
    Returns ``versions`` with ``version``, ``default_display`` (yes/no),
    and ``available_upgrades_display`` for table-style output.

options:
    version:
        description: Filter versions where raw_id starts with this prefix.
        required: false
        type: str
    channel_group:
        description: Channel group (rosa ``--channel-group``, default stable).
        required: false
        type: str
        default: stable
    hosted_cp:
        description: Hosted control plane enabled versions only (rosa ``--hosted-cp``).
        required: false
        type: bool
        default: false

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: List versions like rosa list versions
  rosa_versions_info:

- name: List HCP install versions
  rosa_versions_info:
    hosted_cp: true
'''

RETURN = r'''
commands:
    description: Synthetic command audit list
    type: list
versions:
    description: Version list from OCM (rosa list versions shape)
    type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import rosa_versions_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(type='str', required=False),
            channel_group=dict(type='str', required=False, default='stable'),
            hosted_cp=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**rosa_versions_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
