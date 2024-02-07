Role Name
=========

A brief description of the role goes here.

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

```yaml
state: present|absent
rosa_vpc:
  extra_tags: {}
  name: "rosa-vpc"
  region: "us-east-2"
  cidr: ""
  # set to true if you want this VPC to act as an egress for a TGW
  transit_gateway: {}
    # name:
    # id:
    # arn:
    # route_table:

  add_ocp_subnet_tags: true
  endpoints:
    # set these to empty lists to skip
    gateway_endpoints: [s3]
    interface_endpoints: [sts,ec2,elasticloadbalancing]
  rosa_vpc.public_subnets:
  - cidr: "10.0.128.0/17"
      az: "us-east-2a"
      resource_tags: { "name":"{{ cluster_name }}-public" }
  rosa_vpc.private_subnets:
  - cidr: "10.0.0.0/17"
      az: "us-east-2a"
      resource_tags: { "name":"{{ cluster_name }}-private" }
```

License
-------

Copyright 2024 Red Hat

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


