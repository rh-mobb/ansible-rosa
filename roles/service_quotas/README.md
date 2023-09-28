Role Name
=========

This role will perform a check on AWS account(region) to verify the required Amazon Web Service (AWS) service quotas that are required to run an Red Hat OpenShift Service on AWS cluster.

Role Variables
--------------
The `aws_region` variable it is the required one.

Documentations
------------

More details regarding the AWS service quotas can be find [here](https://docs.openshift.com/rosa/rosa_install_access_delete_clusters/rosa_getting_started_iam/rosa-required-aws-service-quotas.html#rosa-required-aws-service-quotas).

Example Playbook
----------------
(TO BE UPDATED)
Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
