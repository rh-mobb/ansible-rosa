rosa_egress_vpc
=========

This role creates or destroys a VPC with public and private subnets and a transit gateway to allow for egress traffic from a ROSA cluster to the internet.  Useful for private-link ROSA clusters that utilize a private VPC and Transit Gateway.

Role Variables
--------------

```yaml
state: present|absent
rosa_egress_vpc:
  extra_tags: {}
  name: "rosa-egress-vpc"
  region: "us-east-2"
  cidr: ""
  transit_gateway:
    name:
    id:
    arn:
    route_table:
  public_subnets:
    - cidr: "10.0.128.0/17"
        az: "us-east-2a"
        resource_tags: { "name":"{{ cluster_name }}-egress-public" }
  private_subnets:
    - cidr: "10.0.0.0/17"
        az: "us-east-2a"
        resource_tags: { "name":"{{ cluster_name }}-egress-private" }
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


