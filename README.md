# Wimpy Deploy [![Build Status](https://travis-ci.org/wimpy/wimpy.deploy.svg?branch=master)](https://travis-ci.org/wimpy/wimpy.deploy)
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
     wimpy_aws_hosted_zone_name: "armesto.net"
  roles:
    - role: wimpy.deploy
```

When your CI server receives a push to the repository, it'll execute the playbook inside

```bash
$ ansible-playbook deploy.yml --extra-vars "wimpy_release_version=`git rev-parse HEAD` wimpy_deployment_environment=staging"
```

## Configuration
Here is a list of all the variables that you set when using to this role, and their default value

```yaml
# REQUIRED VARIABLES
# Name of the application, used to name CloudFormation stacks, DNS record sets and so on
wimpy_application_name: ""
# Port that your application's container will expose
wimpy_application_port: ""
# Full name of the docker image. It contains the Docker Registry in the name
wimpy_docker_image_name: ""
# Docker container version to deploy 
wimpy_release_version: ""
# Environment where it's deploying
wimpy_deployment_environment: ""
# AWS Virtual Private Cloud where it deploys
wimpy_aws_vpc_id: ""
# Route53 hosted zone. A subdomain will be created in this hosted zone
wimpy_aws_hosted_zone_name: ""
# Subnets where the Auto Scaling Group instances will be deployed
wimpy_aws_autoscaling_vpc_subnets: ""
# Subnets where the ELB will be deployed
wimpy_aws_elb_vpc_subnets: ""
# Security groups to be assigned to the Elastic Load Balancer
wimpy_aws_elb_security_groups: ""
# Security groups to be assigned to the Auto Scaling Group instances
wimpy_aws_lc_security_groups: ""

# OPTIONAL VARIABLES
# Whether to use RollingUpdate or BlueGreen
wimpy_application_deploy_strategy: "RollingUpdate"
# If passed, the role will send a request to Github's API to create a Deployment
wimpy_application_github_repository: ""
# If a systemd service does not signal start-up completion within the configured time, the service will be considered failed and will be shut down again
wimpy_application_bootstrap_timeout: 500s
# Environment variables that will be available for the Docker-Compose process
wimpy_application_environment_vars: {}
# Commands that will be executed before docker-compose up
wimpy_application_pre_commands: []
# Commands that will be executed after docker-compose up
wimpy_application_post_commands: []
# Systemd units to be executed, apart from the application
wimpy_application_additional_units: []
# docker-compose version to be used to start the application
wimpy_docker_compose_version: "1.11.1"
# Path where this role will try to find a valid docker-compose file to start the application
wimpy_docker_compose_file: "{{ lookup('env','PWD') }}/docker-compose-{{ wimpy_deployment_environment }}.yml"
# Template to be used when no docker-compose file is provided by the application
wimpy_docker_compose_template: "templates/docker-compose.yml.j2"

# Docker registry login configuration - Set only if using private images and login is required. You can use the same values used in wimpy.build
# Docker registry url/host. The trailing slash is not required but it works with it anyway
wimpy_docker_registry: ""
# Docker registry username
wimpy_docker_registry_username: ""
# Docker registry email (only if needed)
wimpy_docker_registry_email: ""
# Docker registry password
wimpy_docker_registry_password: ""
  
# Launch Configuration
# AWS Region where to deploy
wimpy_aws_region: "eu-west-1"
# AMI ID for the EC2 instances
wimpy_aws_ami_id: "{{ wimpy_aws_coreos_amis[wimpy_aws_region] }}"
# Instance type for the EC2 instances
wimpy_aws_instance_type: "t2.small"
# Whether or not instances have a public IP
wimpy_aws_assign_public_ip: "{{ (wimpy_aws_elb_scheme == 'internet-facing') }}"
# KeyPair to use in the Auto Scaling Group instances
wimpy_aws_keypair: ""
# Instance profile to be assigned to the Auto Scaling Group instances
wimpy_aws_instance_role: ""
wimpy_aws_ramdisk_id: ""
wimpy_aws_spot_price: ""
wimpy_aws_instance_monitoring: ""
wimpy_aws_ebs_optimized: ""
wimpy_aws_volumes: ""

# Available CoreOS AMI's
wimpy_aws_coreos_amis:
  eu-central-1: "ami-c6f424a9"
  ap-northeast-1: "ami-ad0f2bca"
  us-gov-west-1: "ami-070f8a66"
  ap-northeast-2: "ami-2163b04f"
  ca-central-1: "ami-d004b9b4"
  ap-south-1: "ami-286d1e47"
  sa-east-1: "ami-c51675a9"
  ap-southeast-2: "ami-32d2dd51"
  ap-southeast-1: "ami-deeb54bd"
  us-east-1: "ami-6bb93c7d"
  us-east-2: "ami-40f7d325"
  us-west-2: "ami-fcc4539c"
  us-west-1: "ami-ef015b8f"
  eu-west-1: "ami-f6a49b90"
  eu-west-2: "ami-16150172"

# CloudWatch logs
# Whether or not to enable the CloudWatch agent that ships logs to CloudWatch
wimpy_aws_cloudwatch_enabled: True
# Minimum log level for log entries that will be send to CloudWatch
wimpy_aws_cloudwatch_log_level: 7

# Route53
# Subdomain that will be created in the hosted zone
wimpy_aws_dns_name: "{{ wimpy_application_name }}"
# DNS Time To Live
wimpy_aws_dns_ttl: "60"
# Weight used to distribute traffic among record sets of the same subdomain
wimpy_aws_dns_weight: "10"

# KMS
# ARN for a KMS key that will be passed to the application
wimpy_aws_kms_key: ""

# S3
# Name of the bucket to store data that will be passed to the application
wimpy_aws_s3_application_bucket: ""
# Name of the bucket to store logs
wimpy_aws_s3_bucket: ""

# Elastic Load Balancer
# Whether or not to assign an ELB in front of the ASG instances
wimpy_aws_elb_enable: True
# Private or public ip's for instances behind. Possible values: 'internal' or 'internet-facing'
wimpy_aws_elb_scheme: "internet-facing"
# Wait a specified timeout allowing connections to drain before terminating an instance
wimpy_aws_elb_draining_timeout: "10"
# Enable draining of connections from ELB
wimpy_aws_elb_enable_draining: "True"
# Distribute load across all configured Availability Zones
wimpy_aws_elb_cross_az: "no"
# Enable ELB stickiness
wimpy_aws_elb_stickiness:
  enabled: no
  type: "loadbalancer"
# Healthcheck request protocol
wimpy_aws_elb_healthcheck_ping_protocol: "http"
# Healthcheck request path
wimpy_aws_elb_healthcheck_ping_path: "/health"
# Healthcheck response timeout
wimpy_aws_elb_healthcheck_response_timeout: 4
# Healthcheck request interval
wimpy_aws_elb_healthcheck_interval: 5
# Healthcheck failed responses needed to mark instances as 'OutOfService'
wimpy_aws_elb_healthcheck_unhealthy_threshold: 2
# Healthcheck successful responses needed to mark instances as 'InService'
wimpy_aws_elb_healthcheck_healthy_threshold: 2
# ELB listeners
wimpy_aws_elb_listeners:
  - protocol: "http"
    load_balancer_port: "80"
    instance_port: "{{ wimpy_application_port }}"
    # ARN of the SSL certificate to be attached
    ssl_certificate_id: ""

# Auto Scaling Group
# Number of launch configurations to keep. They can be used for fast rollback.
wimpy_aws_autoscaling_keep_launch_configurations: "1"
# Minimum number of instances for the Auto Scaling Group
wimpy_aws_autoscaling_min_size: "1"
# Maximum number of instances for the Auto Scaling Group
wimpy_aws_autoscaling_max_size: "2"
# Desired number of instances for the Auto Scaling Group
wimpy_aws_autoscaling_desired_capacity: "1"
# Auto Scaling waits until the health check grace period ends before checking the health status of the instance
wimpy_aws_autoscaling_healthcheck_grace_period: "300"
# Number of success signals AWS CloudFormation must receive before it sets the resource status as CREATE_COMPLETE
wimpy_aws_autoscaling_signal_count: "1"
# How much time will AWS CloudFormation wait for signals
wimpy_aws_autoscaling_signal_timeout: "PT3M"
# Percentage of instances in a RollingUpdate that must signal success for the update to succeed
wimpy_aws_autoscaling_signal_min_successful: "100"
# Whether or not the role should automatically destroy the old ASG when the new has been deployed
wimpy_aws_autoscaling_destroy_previous: True
# Increase number of instances in the ASG when the Average CPU for the ASG is higher than this value for 10 mins
wimpy_aws_autoscaling_high_cpu_threshold: "85"
# Decrease number of instances in the ASG when the Average CPU for the ASG is lower than this value for 10 mins
wimpy_aws_autoscaling_low_cpu_threshold: "20"
# Auto Scaling Policies for the Auto Scaling Group
wimpy_aws_autoscaling_policies:
  - name: "ScalingPolicyCpuHigh"
    adjustment_type: "ChangeInCapacity"
    cooldown: 300
    metric_aggregation_type: "Average"
    policy_type: "SimpleScaling"
    scaling_adjustment: 1
  - name: "ScalingPolicyCpuLow"
    adjustment_type: "ChangeInCapacity"
    cooldown: 300
    metric_aggregation_type: "Average"
    policy_type: "SimpleScaling"
    scaling_adjustment: -1
# CloudWatch alarms to be used for Auto Scaling Policies
wimpy_aws_autoscaling_alarms:
  - name: "AlarmCpuHigh"
    namespace: "AWS/EC2"
    metric: "CPUUtilization"
    statistics: "Average"
    comparison: "GreaterThanOrEqualToThreshold"
    threshold: "{{ wimpy_aws_autoscaling_high_cpu_threshold }}"
    period: 300
    evaluation_periods: 2
    unit: "Percent"
    description: "CPU utilization is >= {{ wimpy_aws_autoscaling_high_cpu_threshold }}% for two periods of 5 minutes."
    dimensions:
      AutoScalingGroupName: "{{ wimpy_asg_name }}"
    scaling_policy_name: "ScalingPolicyCpuHigh"

  - name: "AlarmCpuLow"
    namespace: "AWS/EC2"
    metric: "CPUUtilization"
    statistics: "Average"
    comparison: "LessThanThreshold"
    threshold: "{{ wimpy_aws_autoscaling_low_cpu_threshold }}"
    period: 300
    evaluation_periods: 2
    unit: "Percent"
    description: "CPU utilization is < {{ wimpy_aws_autoscaling_low_cpu_threshold }}% for two periods of 5 minutes"
    dimensions:
      AutoScalingGroupName: "{{ wimpy_asg_name }}"
    scaling_policy_name: "ScalingPolicyCpuLow"

# Authenticate to AWS using a boto profile
boto_profile: ""

# Only passed if you want to rollback to this LaunchConfiguration
wimpy_rollback_to_launchconfiguration: ""


```

