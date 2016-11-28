# Wimpy
Ansible playbook to deploy Docker containers to AWS.
The goal of this project is to provide playbooks to deploy Docker applications to EC2 instances using immutable infrastructure.
You could create a parametrized job in your CI server that will be triggered every time a tag is created in your repository (or push to master, etc).
This job would execute these playbooks using as parameters your project's name, tagged version and so on.

**After the execution of the playbooks, you will have an Auto Scaling Group with EC2 instances running docker containers with your project's code.**

## Requirements
The system running this role needs
- troposphere

## Usage
To use this role, your project repository should contain a playbook like the following

```yml
- hosts: all
  vars:
     wimpy_project_name: my_awesome_project
     wimpy_aws_vpc_id: "vpc-ed1cc588"
     wimpy_aws_keypair: "midleware"
     wimpy_aws_hosted_zone_name: "{{ vars.group_names[0] }}.spain.schibsted.io."
     wimpy_aws_elb_security_groups: ["sg-asd234sa", "sg-ifufd34sa"]
     wimpy_vpc_subnets: ["subnet-asd234sa", "subnet-bcfg234sa"]
     wimpy_aws_lc_security_groups: ["sg-asd234sa", "sg-ifufd34sa"]
  roles:
    - role: wimpy
```

When your CI server receives a push to the repository, it'll execute the playbook inside

```bash
$ ansible-playbook -i preprod deploy.yml --extra-vars "wimpy_release_version=2.3 wimpy_deployment_environment=preprod"
```

The flow for every deploy is the following:
- Use `docker-compose` to build the project locally (e.g running gradle, npm, etc). Your repository must contain a `docker-compose-build.yml` file that generates an artifact.
- Create docker image using project's `Dockerfile` that copies the artifact generated on the previous step into the container image.
- Push image to Docker Registry.
- Create new Launch Configuration using CoreOS AMI. The cloud-init will start the app's container for the deployed version.
- Make sure there is an Auto Scaling Group with the created Launch Configuration.
- If there were running instances in the Auto Scaling group, replace these instances with new instances using the new AMI.

## Required parameters
The only required parameters that have no default values are:
```
- wimpy_project_name: "my_awesome_project" # Name of your project
- wimpy_release_version: "2.5" # Version being deployed
- wimpy_deployment_environment: "preprod" # Environment where to deploy
- wimpy_aws_vpc_id: "vpc-123456" # AWS VPC to use
- wimpy_aws_keypair: "authentication" # Key pair to put on EC2 instances
- wimpy_aws_hosted_zone_name: "example.com" # Hosted zone where to create the DNS record for your project
- wimpy_aws_elb_security_groups: ["sg-asd234sa"]
- wimpy_vpc_subnets: ["subnet-asd234sa", "subnet-bcfg234sa"]
- wimpy_aws_lc_security_groups: ["sg-asd234sa", "sg-ifufd34sa"]
```
Traditionally, `wimpy_release_version` will contain the new version pushed to the repository that is being built on Jenkins.

## Authentication
### AWS
This role expects to be runned on a server with a IAM Instance Role with permissions to create and modify AWS resources.

```bash
$ ansible-playbook -i preprod deploy.yml --extra-vars "wimpy_release_version=2.3 wimpy_deployment_environment=preprod"
```

You can also pass a `boto_profile` parameter to use a boto_profile to authenticate yourself.

```bash
$ ansible-playbook -i global_pre_hosts deploy.yml --extra-vars "boto_profile=profile_with_permissions wimpy_release_version=2.3 wimpy_deployment_environment=preprod"
```

### Docker Registry
Currently, Docker only way to authenticate a request to a Docker Registry is using the docker login command. These playbooks will place the config file that Docker generates whenever you login in the command line. A "deploy" user should be created to make it easier to deploy from a CI server.

## Environments
The `wimpy_deployment_environment` variable is used to determine which file from your repository to pass to `docker-compose`. Typically, you'd have a different `docker-compose` file for each environment.

## Optional Parameters
There are lots of parameters to configure the way this is going to deploy your application, but if you don't, sane defaults will be used for almost anything.

```yml
ansible_connection: local

wimpy_docker_image_name: "{{ wimpy_project_name }}" # Name of the docker image that will be created

wimpy_docker_image_version: "{{ (release_version == 'master') | ternary('latest',wimpy_release_version) }}" # Version of the docker image to push.

wimpy_aws_region: "eu-west-1"

# Auto Scaling Group parameters
wimpy_aws_autoscalinggroup_min_size: 1
wimpy_aws_autoscalinggroup_max_size: 2
wimpy_aws_autoscalinggroup_desired_capacity: 1

# There are two different strategies:
# - rolling_asg: old instances will be replaced by new instances with the new launch configuration
# - new_asg: old instances stay alive, new stack is created
wimpy_deploy_strategy: "rolling_asg"

wimpy_aws_dns_name: "{{ wimpy_project_name }}" # DNS record for the deployed instance

wimpy_dns_ttl: 300 # DNS record Time To Live

wimpy_needs_elb: false # Whether or not to assign an ELB in front of the ASG instances

wimpy_app_port: 8000 # Port where app will be listening for requests

# Needed for some weird check
wimpy_elb_result:
  elb:

# ELB Basic Configuration
wimpy_aws_elb_scheme: "internal" # Private or public ip's for instances behind. Possible values: 'internal' or 'internet-facing'
wimpy_aws_elb_draining_timeout: 10 # Wait a specified timeout allowing connections to drain before terminating an instance
wimpy_cross_az_load_balancing: "no" # Distribute load across all configured Availability Zones

# ELB Healthcheck
wimpy_aws_elb_health_check:
  ping_protocol: http
  ping_port: "{{ wimpy_app_port }}"
  ping_path: /healthcheck
  response_timeout: 5
  interval: 10
  unhealthy_threshold: 2
  healthy_threshold: 3

# ELB Listeners. By default ELB listens on port 80 and forward requests to {{app_port}} using HTTP
wimpy_aws_elb_listeners:
  - protocol: "http"
    load_balancer_port: "80"
    instance_port: "{{ wimpy_app_port }}"

# ELB Stickiness. Disabled by default.
wimpy_aws_elb_stickiness:
  - enabled: yes
    type: application
    cookie: SESSIONID


wimpy_aws_instance_type: t2.small # EC2 instance type

#wimpy_role_instance_profile: "ansible-deploy" # When commented out, role set to instances. Role needs to exists

wimpy_aws_ami_name: "CoreOS-alpha-*" # The latest version of this AMI name will be used

wimpy_dockerfile: "docker-compose-{{ wimpy_deployment_environment }}.yml" # docker-compose file to use to start the app

# User data executed when the instance is started. We basically do:
# - Install docker-compose
# - Create systemd units to start our service
#
# Systemd unit executes docker-compose up
wimpy_user_data: |-
  #cloud-config
  write_files:
    - path: /home/core/install_docker_compose
      owner: core:core
      permissions: 0744
      content: |
        #!/bin/sh
        mkdir -p /opt/bin
        curl -L https://github.com/docker/compose/releases/download/1.7.0/docker-compose-Linux-x86_64 > /opt/bin/docker-compose
        chmod +x /opt/bin/docker-compose
    - path: /home/core/docker-compose.yml
      owner: core:core
      permissions: 0644
      content: |
        {{ lookup('file', playbook_dir + '/' + wimpy_dockerfile) | indent(6, False) }}
  coreos:
    units:
      - name: "{{ wimpy_project_name }}.service"
        command: "start"
        content: |
          [Unit]
          Description={{ wimpy_project_name }} container
          After=install_docker_compose.service
          Requires=install_docker_compose.service
          [Service]
          User=core
          Restart=always
          ExecStart=-/usr/bin/docker-compose up
          ExecStop=-/usr/bin/docker-compose down
          [Install]
          WantedBy=multi-user.target
      - name: install_docker_compose.service
        command: start
        content: |
          [Unit]
          Description=Install docker-compose
          After=docker.service
          Requires=docker.service

          [Service]
          Type=oneshot
          ExecStart=/home/core/install_docker_compose

```