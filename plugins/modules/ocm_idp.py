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
module: ocm_idp

short_description: This module manages IDP for OCM / ROSA clusters

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This module manages IDP for OCM / ROSA clusters

options:
    name:
        description: The name of the IDP
        required: true
        type: str
    type:
        description: type of the IDP (currently only accepts 'htpasswd')
        required: true
        type: str
    cluster_name:
        description: name of the OCM cluster (one of this or cluster_id needed)
        required: false
        type: str
    cluster_id:
        description: ID of the OCM cluster (one of this or clustr_name is needed)
        required: false
        type: str
    username:
        description: username to set for htpasswd
        required: false
        type: str
    password:
        description: password to set for htpasswd
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
# create a htpasswd idp
- name: create htpasswd idp
    rh_mobb.ansible_rosa.ocm_idp:
      name: admin
      password: 'admin1234567890!'
      username: admin
      type: htpasswd
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
name:
    description: name of the IDP
    type: str
    returned: always
    sample: 'admin'
password:
    description: htpasswd password (is always empty string for security)
    type: str
    returned: when idp type is htpasswd
    sample: ''
username:
    description: htpasswd username
    type: str
    returned:  when idp type is htpasswd
    sample: 'admin'
type:
    description: type of IDP
    type: str
    returned: always
    sample: 'HTPasswdIdentityProvider'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ocm import OcmModule
from ansible.module_utils.ocm import OcmIdpModule
from ansible.module_utils.ocm import OcmClusterModule
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
        cluster_name=dict(type='str', required=False),
        cluster_id=dict(type='str', required=False),
        name=dict(type='str', required=True),
        type=dict(type='str', required=True),
        username=dict(type='str', required=False),
        password=dict(type='str', required=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        # response='',
        name='',
        type='',
        username='',
        password='',
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

    # check complex dependencies
    if module.params['type'] == 'htpasswd':
        if not module.params['username']:
            module.fail_json(msg='must provide "username" for "htpasswd"', **result)
        if not module.params['password']:
            module.fail_json(msg='must provide "password" for "htpasswd"', **result)

    if not (module.params['cluster_name']) and (not module.params['cluster_id']):
        module.fail_json(msg='must provide "cluster_name" or "cluster_id"', **result)
    if (module.params['cluster_name']) and (module.params['cluster_id']):
        module.fail_json(msg='cannot provide both "cluster_name" or "cluster_id"', **result)

    # with the easy checks out of the way, log into ocm so we can API
    cluster_id = module.params['cluster_id']

    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)

        # First, fetch the cluster_id if we don't already have it
        if not cluster_id:
            cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, module.params['cluster_name'])
            if err:
                module.fail_json(err)
            if not cluster_id:
                module.fail_json("Unable to determin cluster_id from cluster_name: {}".format(module.params['cluster_name']))
        # Fetch identity providers
        existing_idps, err = OcmIdpModule.get_cluster_idps(api_instance, cluster_id)
        if err:
            module.fail_json(err)

        # process request, if its a htpasswd
        if module.params['type'] == 'htpasswd':
            # find existing idp
            if existing_idps:
                existing_htpasswd = OcmIdpModule.get_existing_htpasswd_idps(existing_idps)
                if existing_htpasswd:
                    if existing_htpasswd.name == module.params['name']:
                        result['name'] = existing_htpasswd.name
                        result['type'] = existing_htpasswd.type
                        result['username'] = existing_htpasswd.htpasswd.username
                        result['password'] = ''
                        module.exit_json(**result)
                    else:
                        module.fail_json("an htpasswd IDP called {} already exists. OCM only supports a single IDP.".format(existing_htpasswd.name))
            # construct the htpasswd object
            identity_provider = OcmIdpModule.htpasswd_idp_builder(
                                    username=module.params['username'],
                                    password=module.params['password'],
                                    name=module.params['name']
                                )

            # create htpasswd
            new_htpasswd_idp, err = OcmIdpModule.create_htpasswd_idp(api_instance, cluster_id, identity_provider)
            if err:
                module.fail_json(err)

            result['name'] = new_htpasswd_idp.name
            result['type'] = new_htpasswd_idp.type
            result['username'] = new_htpasswd_idp.htpasswd.username
            result['password'] = ''
            result['changed'] = True

            # grant cluster-admin access
            cluster_role, err = OcmIdpModule.create_cluster_role(api_instance, cluster_id, 'cluster-admins', module.params['username'])
            if err:
                module.fail_json(err)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
