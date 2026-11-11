#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: rosa_cluster_info

short_description: Fetch ROSA cluster information

version_added: "1.0.0"

description: |
    Returns ROSA cluster details. Implements the historical module contract;
    cluster data is retrieved via OCM (same backend as ocm_cluster_info).
    Requires OCM credentials (for example after ``rosa login``).

options:
    name:
        description: Name of the cluster. This will be used when generating a sub-domain for your cluster on openshiftapps.com.
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: get info about rosa cluster
  rosa_cluster_info:
    name: my-rosa-cluster
'''

RETURN = r'''
commands:
    description: Command audit list (synthetic OCM invocation)
    type: list
cluster:
    description: Cluster description (OCM API shape)
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_cluster_lib import rosa_cluster_info_run


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    result = rosa_cluster_info_run(module)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
