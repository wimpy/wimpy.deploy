from troposphere import Join, Output, GetAtt
from troposphere import Parameter, Ref, Template, Not, Equals, If
from troposphere.autoscaling import AutoScalingGroup, Tag, ScalingPolicy
from troposphere.cloudwatch import Alarm, MetricDimension
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate, CreationPolicy, \
    AutoScalingCreationPolicy, ResourceSignal
import troposphere.elasticloadbalancing as elb
from troposphere.route53 import RecordSetType
import sys
import ast

__author__ = 'Jose Armesto'


def generate_cloudformation_template():
    enable_elb = sys.argv[1]
    input_scaling_policies = ast.literal_eval(sys.argv[2])
    input_alarms = ast.literal_eval(sys.argv[3])

    enable_elb = enable_elb == 'True'
    elb_listeners = ast.literal_eval(sys.argv[4])

    template = Template()

    template.add_description("""\
    Configures Auto Scaling Group for the app""")

    project_name = template.add_parameter(Parameter(
        "Name",
        Type="String",
        Description="Instances will be tagged with this name",
    ))

    scalecapacity = template.add_parameter(Parameter(
        "ScaleCapacity",
        Default="1",
        Type="String",
        Description="Number of api servers to run",
    ))

    minsize = template.add_parameter(Parameter(
        "MinScale",
        Type="String",
        Description="Minimum number of servers to keep in the ASG",
    ))

    maxsize = template.add_parameter(Parameter(
        "MaxScale",
        Type="String",
        Description="Maximum number of servers to keep in the ASG",
    ))

    signalcount = template.add_parameter(Parameter(
        "SignalCount",
        Default="1",
        Type="String",
        Description="No. of signals CF must receive before it sets the status as CREATE_COMPLETE",
    ))

    signaltimeout = template.add_parameter(Parameter(
        "SignalTimeout",
        Default="PT5M",
        Type="String",
        Description="Time that CF waits for the number of signals that was specified in Count ",
    ))

    minsuccessfulinstancespercent = template.add_parameter(Parameter(
        "MinSuccessfulInstancesPercent",
        Default="100",
        Type="String",
        Description="% instances in a rolling update that must signal success for CF to succeed",
    ))

    environment = template.add_parameter(Parameter(
        "Environment",
        Type="String",
        Description="The environment being deployed into",
    ))

    subnet = template.add_parameter(Parameter(
        "Subnets",
        Type="CommaDelimitedList",
    ))

    launchconfigurationname = template.add_parameter(Parameter(
        "LaunchConfigurationName",
        Type="String",
    ))

    health_check_grace_period = template.add_parameter(Parameter(
        "HealthCheckGracePeriod",
        Type="String",
        Default="300",
    ))

    if enable_elb:
        elb_subnets = template.add_parameter(Parameter(
            "LoadBalancerSubnets",
            Type="CommaDelimitedList",
        ))

        elb_bucket_name = template.add_parameter(Parameter(
            "LoadBalancerBucketName",
            Type="String",
            Description="S3 Bucket for the ELB access logs"
        ))

        template.add_condition("ElbLoggingCondition", Not(Equals(Ref(elb_bucket_name), "")))

        elb_schema = template.add_parameter(Parameter(
            "LoadBalancerSchema",
            Type="String",
        ))

        health_check_interval = template.add_parameter(Parameter(
            "LoadBalancerHealthCheckInterval",
            Type="String",
        ))

        health_check_timeout = template.add_parameter(Parameter(
            "LoadBalancerHealthCheckTimeout",
            Type="String",
        ))

        healthy_threshold = template.add_parameter(Parameter(
            "LoadBalancerHealthyThreshold",
            Type="String",
        ))

        unhealthy_threshold = template.add_parameter(Parameter(
            "LoadBalancerUnHealthyThreshold",
            Type="String",
        ))

        enable_connection_draining = template.add_parameter(Parameter(
            "LoadBalancerEnableConnectionDraining",
            Type="String",
            Default="True",
        ))

        connection_draining_timeout = template.add_parameter(Parameter(
            "LoadBalancerConnectionDrainingTimeout",
            Type="String",
            Default="30",
        ))

        loadbalancersecuritygroup = template.add_parameter(Parameter(
            "LoadBalancerSecurityGroup",
            Type="CommaDelimitedList",
            Description="Security group for api app load balancer.",
        ))

        hostedzone = template.add_parameter(Parameter(
            "HostedZoneName",
            Description="The DNS name of an existing Amazon Route 53 hosted zone",
            Type="String",
        ))

        dns_record = template.add_parameter(Parameter(
            "DNSRecord",
            Type="String",
        ))

        dns_ttl = template.add_parameter(Parameter(
            "DNSTTL",
            Default="300",
            Type="String",
        ))

        new_weight = template.add_parameter(Parameter(
            "NewDnsWeight",
            Type="String",
            Default="100",
        ))

        health_check_protocol = template.add_parameter(Parameter(
            "LoadBalancerHealthCheckProtocol",
            Type="String",
        ))

        template.add_condition("ElbTCPProtocolCondition", Equals(Ref(health_check_protocol), "TCP"))

        health_check_port = template.add_parameter(Parameter(
            "LoadBalancerHealthCheckPort",
            Type="String",
        ))

        health_check_path = template.add_parameter(Parameter(
            "LoadBalancerHealthCheckPath",
            Type="String",
        ))

        load_balancer_listeners = []
        for index, listener in enumerate(elb_listeners):
            template.add_condition("SSLCertificateCondition" + str(index), Equals(listener['protocol'], "https"))
            load_balancer_listeners.append(elb.Listener(
                LoadBalancerPort=listener['load_balancer_port'],
                InstancePort=listener['instance_port'],
                Protocol=listener['protocol'],
                InstanceProtocol=Ref(health_check_protocol),
                SSLCertificateId=If("SSLCertificateCondition" + str(index),
                                    listener.get('ssl_certificate_id', ''),
                                    Ref("AWS::NoValue")),
            ))

        loadbalancer = template.add_resource(elb.LoadBalancer(
            "LoadBalancer",
            AccessLoggingPolicy=If("ElbLoggingCondition",
                                   elb.AccessLoggingPolicy(
                                       EmitInterval=60,
                                       Enabled=True,
                                       S3BucketName=Ref(elb_bucket_name),
                                       S3BucketPrefix="ELBLogs"),
                                   Ref("AWS::NoValue")),
            ConnectionDrainingPolicy=elb.ConnectionDrainingPolicy(
                Enabled=Ref(enable_connection_draining),
                Timeout=Ref(connection_draining_timeout),
            ),
            Subnets=Ref(elb_subnets),
            HealthCheck=elb.HealthCheck(
                Target=Join("", [Ref(health_check_protocol), ":", Ref(health_check_port), If("ElbTCPProtocolCondition",
                                                                                             Ref("AWS::NoValue"),
                                                                                             Ref(health_check_path))
                                 ]),
                HealthyThreshold=Ref(healthy_threshold),
                UnhealthyThreshold=Ref(unhealthy_threshold),
                Interval=Ref(health_check_interval),
                Timeout=Ref(health_check_timeout),
            ),
            Listeners=load_balancer_listeners,
            CrossZone=True,
            SecurityGroups=Ref(loadbalancersecuritygroup),
            Scheme=Ref(elb_schema)
        ))

        route53record = template.add_resource(RecordSetType(
            "DNS",
            HostedZoneName=Join("", [Ref(hostedzone), "."]),
            Name=Join("", [Ref(dns_record), ".", Ref(hostedzone), "."]),
            ResourceRecords=[GetAtt(loadbalancer, "DNSName")],
            SetIdentifier=Ref(project_name),
            TTL=Ref(dns_ttl),
            Type="CNAME",
            Weight=Ref(new_weight),
        ))

    autoscalinggroup = template.add_resource(AutoScalingGroup(
        "AutoscalingGroup",
        Tags=[
            Tag("Name", Ref(project_name), True),
            Tag("Environment", Ref(environment), True)
        ],
        LaunchConfigurationName=Ref(launchconfigurationname),
        MinSize=Ref(minsize),
        MaxSize=Ref(maxsize),
        DesiredCapacity=Ref(scalecapacity),
        VPCZoneIdentifier=Ref(subnet),
        HealthCheckGracePeriod=Ref(health_check_grace_period),
        CreationPolicy=CreationPolicy(
            ResourceSignal=ResourceSignal(
                Count=Ref(signalcount),
                Timeout=Ref(signaltimeout)
            ),
            AutoScalingCreationPolicy=AutoScalingCreationPolicy(
                MinSuccessfulInstancesPercent=Ref(minsuccessfulinstancespercent)
            )
        ),
        UpdatePolicy=UpdatePolicy(
            AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                MaxBatchSize='1',
                MinInstancesInService='1',
                MinSuccessfulInstancesPercent=Ref(minsuccessfulinstancespercent),
                PauseTime=Ref(signaltimeout),
                WaitOnResourceSignals=True
            )
        )
    ))

    autoscalinggroup.HealthCheckType = 'EC2'
    if enable_elb:
        autoscalinggroup.LoadBalancerNames = [Ref(loadbalancer)]
        autoscalinggroup.HealthCheckType = 'ELB'

    created_scaling_policies = dict()
    for scaling_policy in input_scaling_policies:
        policy_properties = {
            'AdjustmentType': scaling_policy['adjustment_type'],
            'AutoScalingGroupName': Ref(autoscalinggroup),
            'Cooldown': scaling_policy['cooldown'],
            'PolicyType': scaling_policy['policy_type'],
            'ScalingAdjustment': scaling_policy['scaling_adjustment'],
        }
        if scaling_policy['policy_type'] != "SimpleScaling" \
                and 'estimated_instance_warmup' in scaling_policy:
            policy_properties['EstimatedInstanceWarmup'] = \
                scaling_policy['estimated_instance_warmup']

        if scaling_policy['policy_type'] != "SimpleScaling" \
                and 'metric_aggregation_type' in scaling_policy:
            policy_properties['MetricAggregationType'] = scaling_policy['metric_aggregation_type']

        if scaling_policy['adjustment_type'] == "PercentChangeInCapacity" \
                and 'min_adjustment_magnitude' in scaling_policy:
            policy_properties['MinAdjustmentMagnitude'] = scaling_policy['min_adjustment_magnitude']

        if 'step_adjustments' in scaling_policy:
            policy_properties['StepAdjustments'] = scaling_policy['step_adjustments']

        created_scaling_policies[scaling_policy['name']] = template.add_resource(ScalingPolicy(
            scaling_policy['name'],
            **policy_properties
        ))

    for alarm in input_alarms:
        template.add_resource(
            Alarm(
                alarm['name'],
                ActionsEnabled=True,
                AlarmActions=[Ref(created_scaling_policies[alarm['scaling_policy_name']])],
                AlarmDescription=alarm['description'],
                ComparisonOperator=alarm['comparison'],
                Dimensions=[
                    MetricDimension(
                        Name="AutoScalingGroupName",
                        Value=Ref(autoscalinggroup)
                    ),
                ],
                EvaluationPeriods=alarm['evaluation_periods'],
                InsufficientDataActions=[],
                MetricName=alarm['metric'],
                Namespace=alarm['namespace'],
                OKActions=[],
                Period=alarm['period'],
                Statistic=alarm['statistics'],
                Threshold=str(alarm['threshold']),
                Unit=alarm['unit'],
            )
        )

    template.add_output(Output("StackName", Value=Ref(project_name), Description="Stack Name"))
    if enable_elb:
        template.add_output(Output("DomainName", Value=Ref(route53record),
                                   Description="DNS to access the service"))
        template.add_output(Output("LoadBalancer", Value=GetAtt(loadbalancer, "DNSName"),
                                   Description="ELB dns"))
    template.add_output(Output("AutoScalingGroup", Value=Ref(autoscalinggroup),
                               Description="Auto Scaling Group"))
    template.add_output(Output("LaunchConfiguration", Value=Ref(launchconfigurationname),
                               Description="LaunchConfiguration for this deploy"))

    return template


if __name__ == "__main__":
    print(generate_cloudformation_template().to_json())
