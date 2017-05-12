---
layout: default
title: Environment for Wimpy
---

# Environment for Wimpy
The [wimpy.deploy](https://github.com/wimpy/wimpy.deploy) role that deploys your application to AWS needs some parameters to work, like the VPC where you want to deploy, or the security groups used by the application.
You can create your own VPC, security groups, subnets, etc., and pass them to [wimpy.deploy](https://github.com/wimpy/wimpy.deploy).

But if you don't want to spend time on that, you can just use [wimpy.environment](https://github.com/wimpy/wimpy.environment).

It's another role that will create everything that's needed by [wimpy.deploy](https://github.com/wimpy/wimpy.deploy) to be able to deploy applications.
It'll create different CloudFormations for different resources.

## Base
It first creates a Base CloudFormation that creates the basic stuff that will be shared among all your applications in all your environments.
This CloudFormation includes things like:
- KMS Master key for your applications to encrypt and decrypt values
- S3 bucket for applications data like images
- S3 bucket for the CloudTrail audit log, ELB access log and S3 access log

## Environment
It will also create different environments so you can deploy first in your staging environment, and the to the production environment.
It creates a different CloudFormation for every different environment, and these resources are shared among all the applications running on a giving environment.
The CloudFormation for each environment contains:
- Virtual Private Cloud (VPC) for your applications
- Route tables for this VPC
- Internet gateway
- Public subnets for your Load Balancers
- Private subnets for your applications
- Private subnets for your databases

This creates a three layer network architecture where you separate public (open access from internet) and private resources (access only from your network).

## Application
Then for every application that you deploy, this role will create resources that are only for this specific application:
- A repository in Elastic Container Registry to store Docker images.
- Security Group for your application that allows traffic to the application port from Load Balancers and from instances with the same security group.
- Security Group for your Load Balancers that allows public traffic.
- Security Group for your databases that allows traffic from your applications.
- IAM Role for the application so it can access to S3, KMS and CloudWatch.

## Deployment
Finally, when you deploy your application, a new CloudFormation is created for that deployment.
How this CloudFormation behaves depends on your [Deployment Strategy](deploy.md#Deployment_Strategies).

