#!/usr/bin/python

# Copyright: (c) 2018, Paul Czarkowski <pczarkow@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: transit_gateway_route

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
  my_namespace.my_collection.transit_gateway_route:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.transit_gateway_route:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.transit_gateway_route:
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

def process_response(response_in):
    if not response_in:
        return response_in
    response_out = dict()
    for key in response_in.keys():
        response_out[snake_case(key)] = response_in[key]
    return response_out

def get_tgw_rt(connection,tgw_rt_id, tgw_att_id):
    filters = [dict(
        Name = 'attachment.transit-gateway-attachment-id',
        Values = [tgw_att_id]
    )]
    try:
        response = connection.search_transit_gateway_routes(
            TransitGatewayRouteTableId=tgw_rt_id, Filters=filters, MaxResults=5)
    except (BotoCoreError, ClientError) as e:
        return None, e
    tgw = response['Routes']
    return tgw, None

def run_module():
    module_args = dict(
        destination_cidr_block=dict(type='str', required=True),
        region=dict(type='str', required=True),
        transit_gateway_route_table_id=dict(type='str', required=True),
        transit_gateway_attachment_id=dict(type='str', required=True),
        blackhole=dict(type='bool', default=False, required=False),
        # Todo: support dry run
        state=dict(type='str', default='present', choices=['present','absent']),
    )

    result = dict(
        changed=False,
        routes=[dict()],
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    connection = module.client("ec2",
                    retry_decorator=AWSRetry.jittered_backoff(),
                    region=module.params['region'])

    # check to see if it exists
    result['routes'], err = get_tgw_rt(
        connection,
        module.params['transit_gateway_route_table_id'],
        module.params['transit_gateway_attachment_id'])
    if err:
        module.fail_json_aws(err, msg="Failed to check for existing transit gateway route")

    # if it is to be deleted
    if module.params['state'] == "absent":
        if not result['routes']:
            module.exit_json(**result)
        try:
            _ = connection.delete_transit_gateway_route(
                DestinationCidrBlock=module.params['destination_cidr_block'],
                TransitGatewayRouteTableId=module.params['transit_gateway_route_table_id'],
                # todo DryRun=module.params['string'],
            )
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to delete transit gateway route")
        result['changed'] = True
        module.exit_json(**result)

    if result['routes']:
        module.exit_json(**result)

    # create it
    try:
        response = connection.create_transit_gateway_route(
            DestinationCidrBlock=module.params['destination_cidr_block'],
            TransitGatewayRouteTableId=module.params['transit_gateway_route_table_id'],
            TransitGatewayAttachmentId=module.params['transit_gateway_attachment_id'],
            Blackhole=module.params['blackhole'],
            # todo DryRun=module.params['string'],
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unknown error")

    result['routes'] = [process_response(response)]
    result['changed'] = True
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
