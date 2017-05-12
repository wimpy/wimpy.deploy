---
layout: default
title: Running your application
---

# Running your application
Wimpy provision EC2 instances using [CoreOS](https://coreos.com/). CoreOS is a lightweight Linux operating system designed to ran every application using containers.
Your application [is packaged and run using Docker](building.md), and we use [Docker-Compose](https://docs.docker.com/compose/) to start the container.

## Provisioning your application
Wimpy uses [Cloud-init](https://cloudinit.readthedocs.io/en/latest/) to execute actions on EC2 instance startup.
This performs, among others, the following actions
- Install Docker Compose and the CloudWatch agent to ship your application's logs.
- Start your containers using Docker Compose.
- Start the CloudWatch agent.

The docker-compose process is handled by [systemd](https://www.freedesktop.org/wiki/Software/systemd/) so you don't have to worry about the process dying: systemd will recreate the process if something happens.

## Docker Compose
You application is started using Docker Compose.
This is the Docker Compose file used to start your application

{% raw %}
```yaml
version: '2'
services:
  {{ wimpy_application_name }}:
    image: {{ wimpy_docker_image_name }}:{{ wimpy_release_version }}
    ports:
      - "{{ wimpy_application_port }}:{{ wimpy_application_port }}"

```
{% endraw %}

But you can provide your own Docker Compose file for every environment where you want to deploy.
If there is a file called `docker-compose-production.yml` in the root of your Git repository, Wimpy will use that one when deploying to the `production` environment.
You just need a file called `docker-compose-{wimpy_deployment_environment}.yml`, and Wimpy will use it.

Wimpy uses Docker Compose instead of just executing `docker run` because this way it's very easy for you to add companion containers to your application like log collectors, metric collectors and so on.
For example, imagine that your application wants to send metrics to DataDog when running in the `production` environment.
You just need to create the file `docker-compose-production.yml` in your repository, with something like

```yaml
version: '2'
services:
  my-project:
    image: my-project:v1.2.3
    ports:
      - "8000:8000"
  datadog:
    image: datadog/docker-dd-agent:11.0.5123-alpine
    environment:
      API_KEY=YOUR_API_KEY_GOES_HERE
      SD_BACKEND=docker
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "/proc/:/host/proc/:ro"
      - "/sys/fs/cgroup/:/host/sys/fs/cgroup:ro"
```

## Environment variables
Wimpy makes a couple of environment variables available to the Docker Compose process, that are passed to the applications. These variables are
`ENVIRONMENT` Value for the `wimpy_deployment_environment` variable with the current environment 
`DOCKER_REGISTRY` The `wimpy_docker_registry` variable containing the Docker Registry where your application image is stored
`KMS_MASTER_KEY` The `wimpy_aws_kms_key` variable that contains the KMS key that your application can use to encrypt and decrypt values
`S3_BUCKET` The `wimpy_aws_s3_application_bucket` variable with the S3 bucket to store files

If you are defining your own Docker Compose files, you can then use these variables in your Docker Compose file

```yaml
version: '2'
services:
  my-project:
    image: ${DOCKER_REGISTRY}/my-project:fs9d67f
    environment:
      ENVIRONMENT
      KMS_MASTER_KEY
      S3_BUCKET
    ports:
      - "8000:8000"

### Passing environment variables to my application
Sometimes you need to pass environment variables to your containers.
The variable `wimpy_application_environment_vars` contains a list of environment variables that will be available for Docker Compose.

You can later on refer to these variables inside your Docker Compose file.
Using the same example as above, if we don't want to hardcode the DataDog API KEY in our Docker Compose file, we could put it in the `wimpy_application_environment_vars` variable inside the environment vars file (that can be encrypted).

```yaml
wimpy_application_environment_vars:
  - API_KEY: "YOUR_API_KEY_GOES_HERE"
  - ANOTHER_SECRET: "s3cr3t"
```

Then tell Docker Compose to pass it to the DataDog container

```yaml
version: '2'
services:
  my-project:
    image: my-project:v1.2.3
    environment:
      ANOTHER_SECRET
    ports:
      - "8000:8000"
  datadog:
    image: datadog/docker-dd-agent:11.0.5123-alpine
    environment:
      API_KEY
      SD_BACKEND=docker
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "/proc/:/host/proc/:ro"
      - "/sys/fs/cgroup/:/host/sys/fs/cgroup:ro"
```
This will make your application be able to access the `ANOTHER_SECRET` environment variable, and the DataDog agent to access the `API_KEY` environment variable.

## Executing actions before and after your container is started
The variable `wimpy_application_pre_commands` contains a list of commands that will be executed before your container.
For example, if you need to log in to a Docker Registry before runing the container, this is the recommended way.

```yaml
wimpy_application_pre_commands:
  - "/usr/bin/sh -c '/usr/bin/$(/usr/bin/docker run --rm xueshanf/awscli aws ecr get-login --region eu-west-1 --registry-ids=1234567890)'"
```

Similarly, if you need to execute commands after your container has started, add commands to the `wimpy_application_post_commands` list.

## Customizing your instance
You can add more systemd units to your EC2 instance with the `wimpy_application_additional_units` variable, that expects text describing systemd units.
