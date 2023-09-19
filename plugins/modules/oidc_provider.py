#!/usr/bin/python

# Copyright: (c) 2018, Paul Czarkowski <pczarkow@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: oidc_provider

short_description: Creates an IAM entity to describe an identity provider (IdP) that supports OpenID Connect (OIDC)

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: |
  Creates an IAM entity to describe an identity provider (IdP) that supports OpenID Connect (OIDC) .
  The OIDC provider that you create with this operation can be used as a principal in a role's trust policy. Such a policy establishes a trust relationship between Amazon Web Services and the OIDC provider.

options:
    url:
        description: Creates an IAM entity to describe an identity provider (IdP) that supports OpenID Connect (OIDC). The OIDC provider that you create with this operation can be used as a principal in a role's trust policy. Such a policy establishes a trust relationship between Amazon Web Services and the OIDC provider.
        required: true
        type: str
    thumbprints:
        description: |
            A list of server certificate thumbprints for the OpenID Connect (OIDC) identity provider's server certificates. Typically this list includes only one entry. However, IAM lets you have up to five thumbprints for an OIDC provider. This lets you maintain multiple thumbprints if the identity provider is rotating certificates.
            The server certificate thumbprint is the hex-encoded SHA-1 hash value of the X.509 certificate used by the domain where the OpenID Connect provider makes its keys available. It is always a 40-character string.
            You must provide at least one thumbprint when creating an IAM OIDC provider. For example, assume that the OIDC provider is server.example.com and the provider stores its keys at https://keys.server.example.com/openid-connect. In that case, the thumbprint string would be the hex-encoded SHA-1 hash value of the certificate used by https://keys.server.example.com.
        required: true
        type: list
    client_ids:
        description: |
            Provides a list of client IDs, also known as audiences. When a mobile or web app registers with an OpenID Connect provider, they establish a value that identifies the application. This is the value that's sent as the client_id parameter on OAuth requests.
            You can register multiple client IDs with the same provider. For example, you might have multiple applications that use the same OIDC provider. You cannot register more than 100 client IDs with a single IAM OIDC provider.
            There is no defined format for a client ID. The CreateOpenIDConnectProviderRequest operation accepts client IDs up to 255 characters long.
        required: false
        type: list
    tags:
        description: AWS tags
        required: false
        type: list
    state:
        description: present or absent
        required: true
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
  - amazon.aws.common.modules

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.oidc_provider:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.oidc_provider:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.oidc_provider:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

# from ansible_collections.amazon.aws.plugins.module_utils.acm import ACMServiceManager
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule
from time import sleep
from re import sub

def snake_case(s):
  return '_'.join(
    sub('([A-Z][a-z]+)', r' \1',
    sub('([A-Z]+)', r' \1',
    s.replace('-', ' '))).split()).lower()

def process_response(response):
    if not response:
        return response
    oidc_provider = dict()
    if 'Tags' in response.keys():
        oidc_provider['tags'] = boto3_tag_list_to_ansible_dict(response['Tags'])
    for key in response.keys():
        if key == 'Tags': next
        oidc_provider[snake_case(key)] = response[key]
    return oidc_provider

def get_oidc_arn(connection, arn_filter):
    try:
        response = connection.list_open_id_connect_providers()
    except (BotoCoreError, ClientError) as e:
        return None, e
    for oidc in response['OpenIDConnectProviderList']:
        if arn_filter in oidc['Arn']:
            return oidc['Arn'], None

def get_oidc_info(connection, oidc_arn):
    try:
        response = connection.get_open_id_connect_provider(
            OpenIDConnectProviderArn=oidc_arn
        )
    except (BotoCoreError, ClientError) as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            return None, None
        else:
            return None, e
    return process_response(response), None

def run_module():
    module_args = dict(
        url=dict(type='str', required=True),
        client_ids=dict(type='list', required=False, default=[]),
        thumbprints=dict(type='list', required=False),
        tags=dict(type=dict, required=False),
        state=dict(type='str', default='present', choices=['present','absent']),
    )

    result = dict(
        changed=False,
        oidc_provider=dict(
            url=str(),
            client_ids=list(),
            thumbprint_ids=list(),
            tags=dict(),
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    try:
        sts_connecton = module.client("sts", retry_decorator=AWSRetry.jittered_backoff())
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed get account id for current user")
    account_id = sts_connecton.get_caller_identity()["Account"]

    arn_prefix = "arn:aws:iam::{}:oidc-provider".format(account_id)
    connection = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())
    arn_suffix = module.params['url'].replace('https://','')
    existing_oidc_arn = "/".join([arn_prefix, arn_suffix])

    result['oidc_provider'], err = get_oidc_info(connection, existing_oidc_arn)
    if err:
        module.fail_json_aws(err, msg="Failed to fetch existing oidc provider {}".format(existing_oidc_arn))

    # if it is to be deleted
    if module.params['state'] == "absent":
        if not result['oidc_provider']:
            module.exit_json(**result)
        try:
            _ = connection.delete_open_id_connect_provider(
                OpenIDConnectProviderArn=existing_oidc_arn
            )
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to delete oidc provider")
        result['changed'] = True
        sleep(1)
        result['oidc_provider'], err = get_oidc_info(connection, existing_oidc_arn)
        if err:
            module.fail_json_aws(err, msg="Failed to fetch existing oidc provider {}".format(existing_oidc_arn))
        module.exit_json(**result)

    # if it exists, we can simply output the details
    # todo support modifying existing
    if result['oidc_provider']:
        module.exit_json(**result)


    if not module.params['thumbprints']:
        module.fail_json_aws(msg="Must provide at least one thumbprint")

    # create it
    try:
        response = connection.create_open_id_connect_provider(
            Url=module.params['url'],
            ClientIDList=module.params['client_ids'],
            ThumbprintList=module.params['thumbprints'],
            Tags=ansible_dict_to_boto3_tag_list(module.params['tags']),
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unknown error")

    sleep(1)

    result['oidc_provider'], err = get_oidc_info(connection, existing_oidc_arn)
    if err:
        module.fail_json_aws(err, msg="Failed to fetch existing oidc provider {}".format(existing_oidc_arn))
    result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
