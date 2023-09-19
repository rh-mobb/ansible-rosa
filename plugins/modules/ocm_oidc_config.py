#!/usr/bin/python

# Copyright 2023 Paul Czarkowski <pczarkow@redhat.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_oidc_config

short_description: This manages OIDC Configs for OCM / ROSA clusters

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description:
  - This module manages OIDC Configs for OCM / ROSA clusters.

options:
    state:
        description: when `present` will choose an unused oidc config, or create a new one.
        required: true
        type: str
    id:
        description: ID of oidc config (for deletion)
        required: false
        type: str

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - rh_mobb.ansible_rosa.my_doc_fragment_name

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
# create a oidc config
- name: create  oidc config
    rh_mobb.ansible_rosa.ocm_oidc_config:
      state: present
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
oidc_config:
    name:
        id: ID of oidc config
        type: str
        returned: always
        sample: '254431u95bhurrsq9sqt591vflfmgbt0'
    managed:
        description: is it a managed oidc config
        type: bool
        returned: always
        sample: True
    issuer_url:
        description: url of oidc issuer
        type: str
        returned:  always
        sample: 'https://dvbwgdztaeq9o.cloudfront.net/254431u95bhurrsq9sqt591vflfmgbt0'
    installer_role_arn:
        description: ARN of the AWS role to assume when installing the cluster as to reveal the secret, supplied in request. It is only to be used in Unmanaged Oidc Config.
        type: str
        returned:  always
        sample:
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ocm import OcmModule
import ocm_client
from ocm_client.rest import ApiException
import os
from pathlib import Path
import json
import requests

# def check_for_existing_htpasswd(api_instance,):


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        id=dict(type='str', required=False),
        installer_role_arn=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['present','absent']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        oidc_config=dict(),
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

    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)

        # check complex dependencies
        if module.params['state'] == 'present':
            oidc_config = ocm_client.OidcConfig(
                managed = True,
                installer_role_arn = module.params['installer_role_arn'] or None
            )
            try:
                api_response = api_instance.api_clusters_mgmt_v1_oidc_configs_post(oidc_config=oidc_config)
            except ApiException as e:
                err = "Exception when calling DefaultApi->api_clusters_mgmt_v1_oidc_configs_post: {}".format(e)
                module.fail_json(err)
            result['oidc_config'] = api_response.to_dict()
            result['changed'] = True
            module.exit_json(**result)

        if module.params['state'] == 'absent':
            api_instance = ocm_client.DefaultApi(api_client)
            oidc_config_id = module.params['id']
            try:
                api_instance.api_clusters_mgmt_v1_oidc_configs_oidc_config_id_delete(oidc_config_id)
            except ApiException as e:
                err = "Exception when calling DefaultApi->api_clusters_mgmt_v1_oidc_configs_oidc_config_id_delete: {}".format(e)
                module.fail_json(err)
            result['changed'] = True
            module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
