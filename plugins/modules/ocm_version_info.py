#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_version_info

short_description: List ROSA/OpenShift install versions from OCM

version_added: "1.0.0"

description: |
    Lists enabled OpenShift versions for ROSA or hosted control plane installs
    (same data as ``rosa list versions``). Each entry includes ``version`` (raw_id),
    ``default``, and ``available_upgrades``.

options:
    version:
        description: Filter versions where raw_id starts with this prefix (examples 4, 4.14, 4.14.17).
        required: false
        type: str
    channel_group:
        description: Channel group (rosa ``--channel-group``, default stable).
        required: false
        type: str
        default: stable
    hosted_cp:
        description: When true, only hosted control plane enabled versions (rosa ``--hosted-cp``).
        required: false
        type: bool
        default: false

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: List stable ROSA classic versions
  ocm_version_info:

- name: List HCP-enabled versions for 4.22
  ocm_version_info:
    hosted_cp: true
    version: "4.22"
'''

RETURN = r'''
versions:
    description: List of version objects from OCM
    type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_info_lib import ocm_version_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(type='str', required=False),
            channel_group=dict(type='str', required=False, default='stable'),
            hosted_cp=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True,
    )
    module.exit_json(**ocm_version_info_run(module))


def main():
    run_module()


if __name__ == '__main__':
    main()
