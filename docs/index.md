---
layout: default
title: Wimpy Deployments
---

# Welcome to Wimpy!
Wimpy is a opinionated deploy pipeline that implements best-practices for deploying applications on [AWS (Amazon Web Services)](https://aws.amazon.com/).
It's build as a set of [Ansible](https://www.ansible.com/) roles that you can run in a playbook. And since it's ran by Ansible, it's really easy to extend to do exactly what you want.

Just tell Wimpy which version of your application (typically a Git SHA1 commit) you want to deploy and to which environment you want to deploy.
Then Wimpy will create in your own AWS account 
- Instances of an AutoScaling Group running a container with the desired version of your application.
- A load balancer (Elastic Load Balancer) to balance the traffic between the AutoScaling Group instances.
- Domain name (Route53) pointing to the Load Balancer.

## Installation
Wimpy is a set of Ansible roles but you don't really need to know how Ansible works.

### Using Wimpy from Docker
Instead of installing Ansible and the roles, you can just use [our Docker image that contains everything you need for running Wimpy](https://github.com/wimpy/docker).

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy/deploy.yml --extra-vars "wimpy_release_version=v1.2.3 wimpy_deployment_environment=production"
```

### Using Wimpy locally
You will need [to install Ansible](https://docs.ansible.com/ansible/intro_installation.html) and the Wimpy roles that you wan to use.
Follow this guide [to install Ansible](https://docs.ansible.com/ansible/intro_installation.html).

The following commands will install the roles from the Github repository. You can specify which version of each role you want to install. In this example we are installing the master version

```bash
$ ansible-galaxy install git+https://github.com/wimpy/wimpy.build.git,master
$ ansible-galaxy install git+https://github.com/wimpy/wimpy.deploy.git,master
$ ansible-galaxy install git+https://github.com/wimpy/wimpy.ecr.git,master
```

## Usage
Ansible executes commands using what they call "playbooks", which is like a list of tasks to do.
A playbook contains tasks or roles.
A role is a set of tasks that we group together.

Now that we know basic Ansible jargon, a playbook to deploy our application could be
```yaml
- hosts: localhost
  connection: local
  vars:
    wimpy_project_name: "spring-petclinic"
    wimpy_app_port: "8080"
    wimpy_aws_region: "eu-west-1"
    wimpy_aws_vpc_id: "vpc-ed1cc588"
    wimpy_vpc_subnets: ["subnet-asd234sa", "subnet-bcfg234sa"]
    wimpy_aws_elb_security_groups: ["sg-asd234sa"]
    wimpy_aws_lc_security_groups: ["sg-asd234sa", "sg-ifufd34sa"]
  roles:
    - role: wimpy.ecr
    - role: wimpy.build
    - role: wimpy.deploy

```

And run it using Ansible

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy/deploy.yml --extra-vars "wimpy_release_version=v1.2.3 wimpy_deployment_environment=production"
```

The cool thing about Wimpy being built using Ansible roles is that you can choose exactly which ones you want to execute.
For example, if you just want to build a Docker Image and push it to Amazon Elastic Container Registry (ECR), without deploying anything, just remove the `wimpy.deploy` role

```yaml
- hosts: localhost
  connection: local
  vars:
    wimpy_project_name: "my-awesome-application"
    wimpy_aws_region: "eu-west-1"
  roles:
    - role: wimpy.ecr
    - role: wimpy.build

```

And run it

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy/deploy.yml --extra-vars "wimpy_release_version=v1.2.3"
```

This helps you build your Continuous Integration / Continuous Deployment pipeline exactly the way you want it.

### Parameters
As you saw in the last section, Wimpy roles need some info about your application to work properly, like the project's name or the AWS region.
[Ansible offers several ways of passing parameters to playbooks](https://docs.ansible.com/ansible/playbooks_variables.html) like `vars`, `vars_files` or even `extra-vars`, that you can mix together, and Wimpy will work fine with any of those.

A pattern that has been working wonders for us is the following.
- Use the vars section of your playbook for parameters that won't change between deployments or environments like the project name or the service port.
- Pass as Ansible's `extra-vars` parameters that change for every deployment, like the version being deployed and the environment where the deployment is being made.
- When having several environments, use `vars_files` to dynamically load variables that depend on the environment where we are deploying.

For example, let's have a different `yaml` file for every environment. This would be our `development.yml`

```yaml
wimpy_aws_region: "eu-west-1"
wimpy_aws_vpc_id: "vpc-some_vpc_id"
wimpy_vpc_subnets: ["subnet-aa11aa11aa", "subnet-bb22bb22bb"]
wimpy_aws_elb_security_groups: ["sg-aaaaa11111"]
wimpy_aws_lc_security_groups: ["sg-aaaaa11111", "sg-bbbbb22222"]
```

And this our `production.yml`

```yaml
wimpy_aws_region: "eu-west-1"
wimpy_aws_vpc_id: "vpc-another_vpc_id"
wimpy_vpc_subnets: ["subnet-cc33cc33cc", "subnet-dd44dd44dd"]
wimpy_aws_elb_security_groups: ["sg-ccccc333333"]
wimpy_aws_lc_security_groups: ["sg-ccccc333333", "sg-ddddd44444"]
```

Then make our playbook to load the right file depending on the chosen environment.

```yaml
- hosts: localhost
  connection: local
  # Load here variables that change for every environment
  vars_files:
    - "{{ playbook_dir }}/{{ wimpy_deployment_environment }}.yml"
  vars:
    # Put here parameters that remain the same across deployments/environments
    wimpy_project_name: "my-awesome-application"
    wimpy_app_port: 8080
  roles:
    - role: wimpy.ecr
    - role: wimpy.build
    - role: wimpy.deploy

```

And run it passing the parameters that change on every deployment: the version being deployed and the environment where to deploy to

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy/deploy.yml --extra-vars "wimpy_release_version=v1.2.3 wimpy_deployment_environment=production"
```

## Pipeline
The pipeline has three main steps
- [Packaging your application](building)
- [Creating resources on your AWS account](deploy)
- [Running your application inside EC2 instances](running)
