from troposphere import Join, Output, GetAtt
from troposphere import Parameter, Ref, Template
from troposphere.autoscaling import AutoScalingGroup, Tag
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate
import troposphere.elasticloadbalancing as elb
from troposphere.route53 import RecordSetType

__author__ = 'Jose Armesto'


def generate_cloudformation_template():
    template = Template()

    template.add_description("""\
    Configures Auto Scaling Group for the app""")

    hostedzone = template.add_parameter(Parameter(
        "HostedZoneName",
        Description="The DNS name of an existing Amazon Route 53 hosted zone",
        Type="String",
    ))

    dnsRecord = template.add_parameter(Parameter(
        "DNSRecord",
        Type="String",
    ))

    loadbalancersecuritygroup = template.add_parameter(Parameter(
        "LoadBalancerSecurityGroup",
        Type="CommaDelimitedList",
        Description="Security group for api app load balancer.",
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

    environment = template.add_parameter(Parameter(
        "Environment",
        Type="String",
        Description="The environment being deployed into",
    ))

    subnet = template.add_parameter(Parameter(
        "Subnets",
        Type="CommaDelimitedList",
    ))

    loadbalancername = template.add_parameter(Parameter(
        "LoadBalancerName",
        Type="String",
    ))

    elbSchema = template.add_parameter(Parameter(
        "LoadBalancerSchema",
        Type="String",
    ))

    healthCheckTarget = template.add_parameter(Parameter(
        "LoadBalancerHealthCheckTarget",
        Type="String",
    ))

    healthCheckInterval = template.add_parameter(Parameter(
        "LoadBalancerHealthCheckInterval",
        Type="String",
    ))

    healthCheckTimeout = template.add_parameter(Parameter(
        "LoadBalancerHealthCheckTimeout",
        Type="String",
    ))

    healthyThreshold = template.add_parameter(Parameter(
        "LoadBalancerHealthyThreshold",
        Type="String",
    ))

    unhealthyThreshold = template.add_parameter(Parameter(
        "LoadBalancerUnHealthyThreshold",
        Type="String",
    ))

    launchconfigurationname = template.add_parameter(Parameter(
        "LaunchConfigurationName",
        Type="String",
    ))

    loadbalancer = template.add_resource(elb.LoadBalancer(
        "LoadBalancer",
        ConnectionDrainingPolicy=elb.ConnectionDrainingPolicy(
            Enabled=True,
            Timeout=30,
        ),
        Subnets=Ref(subnet),
        HealthCheck=elb.HealthCheck(
            Target=Ref(healthCheckTarget),
            HealthyThreshold=Ref(healthyThreshold),
            UnhealthyThreshold=Ref(unhealthyThreshold),
            Interval=Ref(healthCheckInterval),
            Timeout=Ref(healthCheckTimeout),
        ),
        Listeners=[
            elb.Listener(
                LoadBalancerPort="80",
                InstancePort="80",
                Protocol="HTTP",
                InstanceProtocol="HTTP",
            ),
        ],
        CrossZone=True,
        SecurityGroups=Ref(loadbalancersecuritygroup),
        LoadBalancerName=Ref(loadbalancername),
        Scheme=Ref(elbSchema),
    ))

    autoscalinggroup = template.add_resource(AutoScalingGroup(
        "AutoscalingGroup",
        Tags=[
            Tag("Environment", Ref(environment), True)
        ],
        LaunchConfigurationName=Ref(launchconfigurationname),
        MinSize=Ref(minsize),
        MaxSize=Ref(maxsize),
        DesiredCapacity=Ref(scalecapacity),
        LoadBalancerNames=[Ref(loadbalancer)],
        VPCZoneIdentifier=Ref(subnet),
        HealthCheckType='ELB',
        HealthCheckGracePeriod=30,
        UpdatePolicy=UpdatePolicy(
            AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                PauseTime='PT1M',
                MinInstancesInService="1",
                MaxBatchSize='1'
            )
        )
    ))

    route53record = template.add_resource(RecordSetType(
        "myDNSRecord",
        HostedZoneName=Join("", [Ref(hostedzone), "."]),
        Name=Join("", [Ref(dnsRecord), ".", Ref(hostedzone), "."]),
        Type="CNAME",
        TTL="300",
        ResourceRecords=[GetAtt(loadbalancer, "DNSName")],
    ))

    template.add_output(Output("DomainName", Value=Ref(route53record), Description="DNS to access the service"))
    template.add_output(Output("LoadBalancer", Value=GetAtt(loadbalancer, "DNSName"), Description="ELB dns"))
    template.add_output(Output("AutoScalingGroup", Value=Ref(autoscalinggroup), Description="Created Auto Scaling Group"))
    template.add_output(Output("LaunchConfiguration", Value=Ref(launchconfigurationname), Description="LaunchConfiguration for this deploy"))

    return template


if __name__ == "__main__":
    print(generate_cloudformation_template().to_json())