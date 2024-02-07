rosa_transit_gateway
=========

This role creates or destroys a transit gateway for a ROSA cluster.  This is useful for private-link ROSA clusters that utilize a private VPC and Transit Gateway for egress traffic to the internet.

Role Variables
--------------

```yaml
state: present|absent
rosa_transit_gateway:
  name: rosa-tgw
  region: us-east-2
  cidr: 10.0.0.0/16
  tags: {}

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


