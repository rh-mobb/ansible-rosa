rosa_account_roles
=========

This role is designed to create the necessary roles and policies for a ROSA account.  It can be used once per account (ROSA clusters can share account roles), or once per cluster depending on your needs.


Role Variables
--------------

The following variables are required for this role:

```yaml
state: present|absent
rosa_account_roles:
  hosted_cp: False
  version: "4.14"
  prefix: ManagedOpenShift

  # set force to true to delete the default account role
  # (prefix is ManagedOpenShift or ManagedOpenShift-HCP)
  force: False

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


