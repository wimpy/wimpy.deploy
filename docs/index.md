---
layout: default
title: Wimpy Deployments
---

# Welcome to Wimpy!

Wimpy is a opinionated deploy pipeline that implements best-practices for deploying applications on AWS (Amazon Web Services).
It's build as a set of Ansible roles that you can run in a playbook. And since it's ran by Ansible, it's really easy to extend Wimpy to do exactly what you want.

Every time you run Wimpy you need to specify
  - Version (typically a Git SHA1 commit) that you want to deploy
  - Environment where you want to deploy

And this will happen  
- Package the desired version of your application using Docker images.
- Publish the Docker image to a Docker Registry.
- Instances of an AutoScaling Group run the published container.
- Make an Elastic Load Balancer to balance the traffic between the AutoScaling Group instances.
- Configure your Route53 domain name to target the Load Balancer.

## Running your application
Your application is run using Docker, althought we use Docker-Compose to start your container.
This way it's easy for you to add companion containers to your application like log collectors, metric collectors and so on.

The docker-compose process is handled by systemd so you don't have to worry about the process dying: systemd will recreate the process if something happens.

