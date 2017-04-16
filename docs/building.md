---
layout: default
title: Building your application
---

# Building your application

We package your application using Docker. All you need is to have a valid Dockerfile in the root of your Git repository.
This is done by the [wimpy.build](https://github.com/wimpy/wimpy.build) role, and allows you to
- Build a container for your application.
- Publish the container to a Docker Registry (DockerHub, private registry or even AWS ECR).
