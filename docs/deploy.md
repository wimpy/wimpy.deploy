---
layout: default
title: Deploying to AWS
---

# Deploying to AWS
Wimpy lets you deploy your applications on your own AWS account, following cloud best practices.
On every deploy, Wimpy creates a Launch Configuration and a CloudFormation Stack.

## Launch Configuration
A launch configuration is a template that an Auto Scaling group uses when launching EC2 instances.
The most important parameters are
- `security_groups`: A list that contains the EC2 security groups to assign to the Amazon EC2 instances in the Auto Scaling group.
- `instance_type`: Specifies the instance type of the EC2 instance. Defaults to `t2.small`.
- `key_name`: Name of the EC2 key pair to be used. If you don't pass this value, no key will be used.

Although you can also configure
- `image_id`: ID of the Amazon Machine Image (AMI) to use to start EC2 instances. It will use the latest stable version of CoreOS.
- `instance_profile_name`: Name of the instance profile associated with the IAM role for the instance. None is assigned by default.
- `ramdisk_id`: The ID of the RAM disk to select. None by default.
- `spot_price`: If a spot price is set, then the autoscaling group will launch when the current spot price is less than the amount specified.
- `instance_monitoring`: Whether detailed instance monitoring is enabled for the Auto Scaling group.
- `ebs_optimized`: Whether the launch configuration is optimized for EBS I/O. False by default.
- `volumes`: Volumes attached to EC2 instances in the Auto Scaling Group. None by default.
- `assign_public_ip`: Whether instances in the Auto Scaling group receive public IP addresses.


## A CloudFormation for all your resources
You application is deployed using a CloudFormation stack that contains:
- The AutoScaling Group with EC2 instances.
- An Elastic Load Balancer to distribute the load between your applications.
- A DNS name in Route53 that targets the Load Balancer.

### Creating the Auto Scaling Group
Wimpy creates an AutoScaling Group for every application. You don't have to worry about most of the configuration because Wimpy already provides sane defaults.
But here is an annotated list of the variables that you can configure, with the defaults used by Wimpy.
These variables map almost 1 to 1 [to native AWS AutoScaling variables](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-as-group.html).

```yaml
# Specifies the desired capacity for the Auto Scaling group
wimpy_aws_autoscaling_desired_capacity: "1"
# The length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health
wimpy_aws_autoscaling_healthcheck_grace_period: "300"
# The maximum size of the Auto Scaling group
wimpy_aws_autoscaling_max_size: "2"
# The minimum size of the Auto Scaling group
wimpy_aws_autoscaling_min_size: "1"
# How many previous launchconfigurations you want to keep
wimpy_aws_autoscaling_keep_launch_configurations: "1"
# Whether or not to delete the previous CloudFormation containing an older version of your application
wimpy_aws_autoscaling_destroy_previous: True
```

### Automatically scaling up or down your application
The main point of having an Auto Scaling Group is that it can automatically scale up and down depending on the current load of your instances.
This is done using
- CloudWatch alarms that alert the ASG when something is happening.
- Execute an action when the alarms are triggered. These actions are called Scaling Policies.

Wimpy automatically creates CloudWatch alarms that will trigger Scaling Policies to scale up and down one instance of your application:
- When the CPU utilization is higher than `wimpy_aws_autoscaling_high_cpu_threshold`% for two periods of 5 minutes.
- When the CPU utilization is lower than `wimpy_aws_autoscaling_low_cpu_threshold`% for two periods of 5 minutes.

You can configure your own thresholds

```yaml
# Reaching this threshold will make your group to scale up (if wimpy_aws_autoscaling_max_size not reached yet)
wimpy_aws_autoscaling_high_cpu_threshold: "85"
# Reaching this threshold will make your group to scale down (if wimpy_aws_autoscaling_min_size not reached yet)
wimpy_aws_autoscaling_low_cpu_threshold: "20"
```

But you can also define your custom alarms and scaling policies (this would Wimpy ignore `wimpy_aws_autoscaling_low_cpu_threshold` and `wimpy_aws_autoscaling_high_cpu_threshold`)

```yaml
wimpy_aws_autoscaling_policies:
  - name: "{{ wimpy_application_name }}-cpu-high"
    scaling_adjustment: 1
    cooldown: 300
    adjustment_type: "ChangeInCapacity"

  - name: "{{ wimpy_application_name }}-cpu-low"
    scaling_adjustment: -1
    cooldown: 300
    adjustment_type: "ChangeInCapacity"
wimpy_aws_autoscaling_alarms:
  - name: "{{ wimpy_application_name }}-cpu-high"
    metric: "CPUUtilization"
    statistics: Average
    comparison: ">="
    threshold: "{{ wimpy_aws_autoscaling_high_cpu_threshold }}"
    period: 300
    evaluation_periods: 2
    unit: "Percent"
    description: "CPU utilization is >= {{ wimpy_aws_autoscaling_high_cpu_threshold }}% for two periods of 5 minutes."
    dimensions:
      AutoScalingGroupName: "{{ wimpy_application_name }}"
    scaling_policy_name: "{{ wimpy_application_name }}-cpu-high"

  - name: "{{ wimpy_application_name }}-cpu-low"
    metric: "CPUUtilization"
    statistics: Average
    comparison: "<"
    threshold: "{{ wimpy_aws_autoscaling_low_cpu_threshold }}"
    period: 300
    evaluation_periods: 2
    unit: "Percent"
    description: "CPU utilization is < {{ wimpy_aws_autoscaling_low_cpu_threshold }}% for two periods of 5 minutes"
    dimensions:
      AutoScalingGroupName: "{{ wimpy_application_name }}"
    scaling_policy_name: "{{ wimpy_application_name }}-cpu-low"

  - name: "{{ wimpy_application_name }}-healthy-nodes-low"
    metric: "HealthyHostCount"
    statistics: Average
    comparison: "<"
    threshold: "1"
    period: 300
    evaluation_periods: 1
    unit: "Count"
    description: "No healthy instances behind the ELB for 5 minutes"
    dimensions:
      ElasticLoadBalancerName: "GroupELB"
    scaling_policy_name: "{{ wimpy_application_name }}-healthy-nodes-low"
```

### Deployment Strategies
How this CloudFormation behaves depends on your Deployment Strategy.

#### Rolling Update
By default, [wimpy.deploy](https://github.com/wimpy/wimpy.deploy) will use a Rolling Update strategy.
This means that a CloudFormation is created that will create an Auto Scaling Group with EC2 instances.

Every deploy will trigger a Rolling Update on the Auto Scaling Group, that will replace instances containing the old version of your application, with instances containing the version being deployed.
#### Blue / Green deployment
In this strategy, instead of having a single CloudFormation replacing instances of the Auto Scaling Group, we create a different CloudFormation for every version deployed.


### Signals: Deciding if the deployment has been successful
Wimpy instructs AWS CloudFormation to complete the stack creation only after your application is running and not after all the stack resources are created.
By default, AWS CloudFormation sets the status of the stack as `CREATE_COMPLETE` after it successfully creates all the resources (like EC2 instances).
This happens even though one of your services inside the EC2 instance failed to start.
To prevent the status from changing to `CREATE_COMPLETE` until all the services have successfully started, Wimpy sets the stack's status to `CREATE_IN_PROGRESS` until AWS CloudFormation receives the required number of success signals or the timeout period is exceeded.
If CloudFormation receives a failure signal or doesn't receive the specified number of signals before the timeout period expires, the resource creation fails and AWS CloudFormation rolls the stack back. 

If you have defined [Docker health checks in your Dockerfile](https://docs.docker.com/engine/reference/builder/#healthcheck), Wimpy will send a success signal to CloudFormation if your containers' health checks are `healthy`.
Otherwise, Wimpy will send a success signal to CloudFormation if your containers' status are `running`.

You can configure how to use these signals

```yaml
# The number of success signals AWS CloudFormation must receive before it sets the resource status as CREATE_COMPLETE
wimpy_aws_autoscaling_signal_count: "1"
# The length of time that AWS CloudFormation waits for the number of signals that was specified in the Count property
wimpy_aws_autoscaling_signal_timeout: "PT3M"
# Specifies the percentage of instances in an Auto Scaling replacement update that must signal success for the update to succeed
wimpy_aws_autoscaling_signal_min_successful: "100"
```

You can learn how your application is started in the EC2 instances in the [Running your application](running.md) section.
