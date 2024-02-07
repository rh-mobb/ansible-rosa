rosa_dns_resolver
=========

this role will create or destroy a Route53 DNS resolver for a ROSA cluster in multiple VPCs in order to make your private-link ROSA cluster accessible from multiple VPCs.

Role Variables
--------------

```yaml
state: present|absent
rosa_dns_resolver:
  zone: example.com.
  tags: {}
  vpcs:
    - id: vpc-12345678
      region: us-east-2
    - id: vpc-87654321
      region: us-east-2

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


