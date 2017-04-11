import sys

from troposphere import Output
from troposphere import Parameter, Ref, Template
from troposphere.autoscaling import AutoScalingGroup, Tag, ScalingPolicy
from troposphere.cloudwatch import Alarm, MetricDimension
from troposphere.policies import (
    UpdatePolicy,
    AutoScalingRollingUpdate,
    CreationPolicy,
    AutoScalingCreationPolicy,
    ResourceSignal
)

__author__ = 'Jose Armesto'


def generate_cloudformation_template():
    template = Template()

    template.add_description("""\
    Configures Auto Scaling Group for the app""")

    project_name = template.add_parameter(Parameter(
        "Name",
        Type="String",
        Description="Instances will be tagged with this name",
    ))

    health_check_grace_period = template.add_parameter(Parameter(
        "HealthCheckGracePeriod",
        Type="String",
        Default="300",
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
        Description="Specifies the % of instances in an ASG replacement update that must signal "
                    "success for the update to succeed",
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
        HealthCheckType='EC2',
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

    input_scaling_policies = eval(sys.argv[1])
    input_alarms = eval(sys.argv[2])

    created_scaling_policies = dict()
    for scaling_policy in input_scaling_policies:
        policy_properties = {
            'AdjustmentType': scaling_policy['adjustment_type'],
            'AutoScalingGroupName': Ref(autoscalinggroup),
            'Cooldown': scaling_policy['cooldown'],
            'PolicyType': scaling_policy['policy_type'],
            'ScalingAdjustment': scaling_policy['scaling_adjustment'],
            'StepAdjustments': scaling_policy['step_adjustments']
        }
        if scaling_policy['policy_type'] != "SimpleScaling":
            policy_properties['EstimatedInstanceWarmup'] = scaling_policy['estimated_instance_warmup']
            policy_properties['MetricAggregationType'] = scaling_policy['metric_aggregation_type']

        if scaling_policy['adjustment_type'] == "PercentChangeInCapacity":
            policy_properties['MinAdjustmentMagnitude'] = scaling_policy['min_adjustment_magnitude']

        created_scaling_policies[scaling_policy['name']] = template.add_resource(ScalingPolicy(
            scaling_policy['name'],
            **policy_properties
        ))

    for alarm in input_alarms:
        template.add_resource(
            Alarm(
                alarm['name'],
                AlarmDescription=alarm['description'],
                Namespace="AWS/EC2",
                MetricName=alarm['metric'],
                Dimensions=[
                    MetricDimension(
                        Name="AutoScalingGroupName",
                        Value=Ref(autoscalinggroup)
                    ),
                ],
                Statistic=alarm['statistics'],
                Period=alarm['period'],
                EvaluationPeriods=alarm['evaluation_periods'],
                Threshold=str(alarm['threshold']),
                ComparisonOperator=alarm['comparison'],
                AlarmActions=[Ref(created_scaling_policies[alarm['scaling_policy_name']])]
            )
        )

    template.add_output(Output("StackName", Value=Ref(project_name), Description="Stack Name"))
    template.add_output(Output("AutoScalingGroup", Value=Ref(autoscalinggroup),
                        Description="Auto Scaling Group"))
    template.add_output(Output("LaunchConfiguration", Value=Ref(launchconfigurationname),
                               Description="LaunchConfiguration for this deploy"))

    return template


if __name__ == "__main__":
    print(generate_cloudformation_template().to_json())
