from troposphere import Output
from troposphere import Parameter, Ref, Template
from troposphere.autoscaling import AutoScalingGroup, Tag
from troposphere.policies import UpdatePolicy, AutoScalingRollingUpdate

__author__ = 'Jose Armesto'


def generate_cloudformation_template():
    template = Template()

    template.add_description("""\
    Configures Auto Scaling Group for the app""")

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

    launchconfigurationname = template.add_parameter(Parameter(
        "LaunchConfigurationName",
        Type="String",
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
        VPCZoneIdentifier=Ref(subnet),
        HealthCheckType='EC2',
        HealthCheckGracePeriod=30,
        UpdatePolicy=UpdatePolicy(
            AutoScalingRollingUpdate=AutoScalingRollingUpdate(
                PauseTime='PT1M',
                MinInstancesInService="1",
                MaxBatchSize='1'
            )
        )
    ))

    template.add_output(Output("AutoScalingGroup", Value=Ref(autoscalinggroup), Description="Created Auto Scaling Group"))
    template.add_output(Output("LaunchConfiguration", Value=Ref(launchconfigurationname), Description="LaunchConfiguration for this deploy"))

    return template


if __name__ == "__main__":
    print(generate_cloudformation_template().to_json())