---
layout: default
title: Building your application
---

# Building your application
We package your application using Docker. All your application needs to be compatible with Wimpy, is to have a valid Dockerfile in the root of its Git repository.

## Why Docker?
One of the problems when trying to create a deployment tool for applications is that depending on the programming language of the application, the deployment tool would have certain installed tools and execute specific actions for every different platform. This makes the deployment tool more complex for every new technology you want to deploy.
Wimpy tries to keep it simple and be agnostic of the language of the applications being deployed. That's why we chose Docker images to package the applications.

People tend to think of Docker as a runtime platform, where applications ran, but it's also a packaging format that we can use to distribute our applications.
Using a Docker Registry to store your applications, you get versioning, caching and many features out of the box.
It also makes it easier for developers, for example when they want to do integration testing between different applications: they just have to download a Docker image locally and run it. 

## Building
This is done by the [wimpy.build](https://github.com/wimpy/wimpy.build) role, and allows you to
- Build a Docker image for your application.
- Publish the container to a Docker Registry (DockerHub, private registry or even AWS ECR).
