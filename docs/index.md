---
layout: default
title: Wimpy Deployments
---

# Automatically Deploy following AWS Best Practices
Wimpy is a opinionated deploy pipeline that implements best-practices for deploying applications on [AWS (Amazon Web Services)](https://aws.amazon.com/).
It's build as a set of [Ansible](https://www.ansible.com/) roles that you can run in a playbook. And since it's ran by Ansible, it's really easy to extend to do exactly what you want.

Following Continuous Deployment practices, you can execute the playbook on every change merged to your application master branch so on every change Wimpy will
- Make sure all the infrastructure is in place and with the right configuration, only spending time when something is not created yet.
- Publish a new Docker image of your application to a Docker registry.
- Deploy the new version of your application to the selected environment using one of the available deployment strategies.

## Installation
Wimpy is a set of Ansible roles but you don't really need to know how Ansible works.

### Using Wimpy from Docker
Instead of installing Ansible and the roles, you can just use [our Docker image that contains everything you need for running Wimpy](https://github.com/wimpy/docker).

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy.yml --extra-vars "wimpy_release_version=`git rev-parse HEAD` wimpy_deployment_environment=production"
```

### Using Wimpy locally
You will need [to install Ansible](https://docs.ansible.com/ansible/intro_installation.html) and the Wimpy roles that you wan to use.

The following commands will install the roles from the Github repository. You can specify which version of each role you want to install. In this example we are installing the master version

```bash
$ ansible-galaxy install git+https://github.com/wimpy/wimpy.build.git,master
$ ansible-galaxy install git+https://github.com/wimpy/wimpy.deploy.git,master
$ ansible-galaxy install git+https://github.com/wimpy/wimpy.ecr.git,master
```

## Usage
Ansible executes commands using what they call "playbooks", which is like a list of tasks to execute.
A playbook contains tasks or roles. A role is a set of tasks that we group together.

Now that we know basic Ansible jargon, a playbook to deploy our application could be
```yaml
- hosts: localhost
  connection: local
  vars:
    wimpy_application_name: "my-awesome-project"
    wimpy_application_port: "8080"
  roles:
    - role: wimpy.environment
    - role: wimpy.build
    - role: wimpy.deploy
```

And use Ansible (or our Docker image) to run it

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy.yml --extra-vars "wimpy_release_version=v1.2.3 wimpy_deployment_environment=production"
```

The cool thing about Wimpy being built using Ansible roles is that you can choose exactly which ones you want to execute.
For example, if you just want to build a Docker Image and push it to Amazon Elastic Container Registry (ECR), without deploying anything, just remove the `wimpy.deploy` role

```yaml
- hosts: localhost
  connection: local
  vars:
    wimpy_application_name: "my-awesome-application"
  roles:
    - role: wimpy.environment
    - role: wimpy.build
```

And run it

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy.yml --extra-vars "wimpy_release_version=`git rev-parse HEAD`"
```

This helps you build your Continuous Integration / Continuous Deployment pipeline exactly the way you want it.

### Parameters
As you saw in the last section, Wimpy roles need some info about your application to work properly, like the project's name or the AWS region.
[Ansible offers several ways of passing parameters to playbooks](https://docs.ansible.com/ansible/playbooks_variables.html) like `vars`, `vars_files` or even `extra-vars`, that you can mix together, and Wimpy will work fine with any of those.

When passing parameters to our playbook, a pattern that has been working wonders for us is the following:
- Use the vars section of your playbook for parameters that won't change between deployments or environments like the project name or the HTTP port exposed by the application.
- Use `vars_files` to dynamically load variables that depend on the environment where you are deploying.
- Use [the `extra-vars` Ansible's argument](https://docs.ansible.com/ansible/playbooks_variables.html#passing-variables-on-the-command-line) to pass the parameters that change for every deployment, like the version being deployed and the environment where the deployment is being made.

For example, let's have a different `yaml` file for every environment. This would be our `staging.yml`

```yaml
wimpy_aws_hosted_zone_name: "staging.example.com"
```

And this our `production.yml`

```yaml
wimpy_aws_hosted_zone_name: "example.com"
wimpy_aws_elb_scheme: "internal"
```

Then make our playbook to load the right file depending on the chosen environment.
{% raw %}
```yaml
- hosts: localhost
  connection: local
  # Load here variables that change for every environment
  vars_files:
    - "{{ playbook_dir }}/{{ wimpy_deployment_environment }}.yml"
  vars:
    # Put here parameters that remain the same across deployments/environments
    wimpy_application_name: "my-awesome-application"
    wimpy_application_port: 8080
  roles:
    - role: wimpy.environment
    - role: wimpy.build
    - role: wimpy.deploy

```
{% endraw %}

And run the playbook passing the parameters that change on every deployment: the version of your application that you want to deploy (typically a Git SHA1 commit) and to which environment you want to deploy it.

```bash
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/app" \
    -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY \
    fiunchinho/wimpy /app/deploy.yml --extra-vars "wimpy_release_version=git rev-parse HEAD wimpy_deployment_environment=production"
```

## Learn More
- [Preparing the AWS Account environment](environment.md)
- [Packaging your application](building.md)
- [Creating Auto Scaling Groups on your AWS account](deploy.md)
- [Running your application with Docker inside EC2 instances](running.md)
