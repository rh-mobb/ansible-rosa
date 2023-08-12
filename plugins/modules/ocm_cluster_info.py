#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from sys import stdout
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ocm_cluster_info

short_description: Fetches information about an OCM Cluster

version_added: "1.0.0"

description: Fetches information about an OCM (ROSA or OSD) Cluster

options:
    name:
        description: Name of the cluster. This will be used when generating a sub-domain for your cluster on openshiftapps.com.
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: get info about ocm cluster
  ocm_cluster_info:
    name: my-rosa-cluster
'''

RETURN = r'''
stdout: str
stderr: str
password: str
# These are examples of possible return values, and in general should use other names for return values.
'''

from ansible.module_utils.basic import *
from ansible.module_utils.ocm import OcmModule
from ansible.module_utils.ocm import OcmClusterModule
import ocm_client
from ocm_client.rest import ApiException
import time
import json


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        cluster={},
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

    name = module.params['name']
    cluster_id = ""

    # with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
    with ocm_client.ApiClient(OcmClusterModule.authenticate_ocm()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)

        if not cluster_id:
            cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, name)
            if err:
                module.fail_json(err)
            if not cluster_id:
                module.exit_json(**result)
                module.fail_json("Unable to determin cluster_id from cluster_name: {}".format(name))

        cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
        result['cluster'] = cluster_info
        if err:
            module.fail_json(err)
        module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
