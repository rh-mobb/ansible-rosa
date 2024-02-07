#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from sys import stdout
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ocm_version_info

short_description: Fetches information about an OCM Cluster

version_added: "1.0.0"

description: Fetches information about an OCM (ROSA or OSD) Cluster

options:
    version:
        description: Version you want to check for.  examples 4, 4.14, 4.14.17
        required: false
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: get info about available versions
  ocm_version_info:
'''

RETURN = r'''
versions:
  - 4.14.17
  - 4.14.16
# These are examples of possible return values, and in general should use other names for return values.
'''

from ansible.module_utils.basic import *
from ..module_utils.ocm import OcmModule
from ..module_utils.ocm import OcmClusterModule
import ocm_client
from ocm_client.rest import ApiException
import time
import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        version=dict(type='str', required=False),
        channel_group=dict(type='str', required=False, default="stable"),
        hosted_cp=dict(type='bool', required=False, default=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        versions=[],
    )



    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    version = module.params['version']
    hosted_cp = module.params['hosted_cp']
    channel_group = module.params['channel_group']

    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        order_by = "default desc, id desc"
        search = f"enabled = true AND channel_group = '{channel_group}'"
        if hosted_cp:
            search += f" AND hosted_control_plane_enabled = true"
        else:
            search += f" AND rosa_enabled = true"
        if version:
            search += f" AND raw_id like '{version}%'"
        response = api_instance.api_clusters_mgmt_v1_versions_get(page=1,size=100,order=order_by, search=search)
        versions = response.to_dict()['items']
        # result['versions'] = response.to_dict()['items']
        for raw_version in response.to_dict()['items']:
            raw_version['version'] = raw_version['raw_id']
            result['versions'].append(raw_version)
        # if err:
        #     module.fail_json(err)
        module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
