# Wimpy
Ansible playbook to deploy Docker containers to AWS EC2 instances.

## Requirements
The system executing this role needs
- [troposphere](https://github.com/cloudtools/troposphere)

## Usage
To use this role, your project repository should contain a playbook like the following

```yaml
- hosts: localhost
  connection: local
  vars:
     wimpy_application_name: my_awesome_project
     wimpy_application_port: 8000
     wimpy_aws_hosted_zone_name: "global-dev.spain.schibsted.io"
  roles:
    - role: wimpy.deploy
```

When your CI server receives a push to the repository, it'll execute the playbook inside

```bash
$ ansible-playbook deploy.yml --extra-vars "wimpy_release_version=2.3 wimpy_deployment_environment=staging"
```
