---
layout: default
title: Wimpy Deployments
---

# Welcome to Wimpy!
Wimpy is a opinionated deploy pipeline that implements best-practices for deploying applications on [AWS (Amazon Web Services)](https://aws.amazon.com/).
It's build as a set of [Ansible](https://www.ansible.com/) roles that you can run in a playbook. And since it's ran by Ansible, it's really easy to extend Wimpy to do exactly what you want.

Every time you run Wimpy you need to specify
  - Version (typically a Git SHA1 commit) that you want to deploy
  - Environment where you want to deploy

And you end up with
- Instances of an AutoScaling Group run the published container.
- An Elastic Load Balancer to balance the traffic between the AutoScaling Group instances.
- Domain name pointing to the Load Balancer.

## Pipeline
The pipeline has three main steps
- [Packaging your application](building.md)
- [Creating resources on your AWS account](deploy.md)
- [Running your application inside EC2 instances](running.md)
