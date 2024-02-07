rosa_operator_roles
=========

Create or destroy the necessary operator roles and policies for a ROSA cluster.

Role Variables
--------------

```yaml
state: present|absent
rosa_operator_roles:
  hosted_cp: false
  oidc_endpoint_url: ''
  cluster_id: ''
  cluster_name: rosa-cluster
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


