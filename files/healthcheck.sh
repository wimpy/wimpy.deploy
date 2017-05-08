#!/usr/bin/env bash

STACK_NAME=$1
USING_ELB=$2
RESOURCE_NAME=${3:-AutoscalingGroup}
AWS_REGION=${4:-eu-west-1}
SLEEP=${5:-5}

function cfn-signal() {
  /usr/bin/docker run --rm mbabineau/cfn-bootstrap cfn-signal \
    -e $? \
    --stack ${STACK_NAME} \
    --resource ${RESOURCE_NAME} \
    --region ${AWS_REGION}
}
trap cfn-signal EXIT

if [ ${USING_ELB} == 'True' ]; then
    until [ "$state" == "\"InService\"" ]; do state=$(/usr/bin/docker run --rm xueshanf/awscli aws elb describe-instance-health --region ${AWS_REGION} --load-balancer-name ${STACK_NAME} --instances $(curl -s http://169.254.169.254/latest/meta-data/instance-id) --query InstanceStates[0].State); sleep ${SLEEP}; done
else
    sleep ${SLEEP} # It takes compose a few seconds to create the container
    CONTAINER_NAME=$(/opt/bin/docker-compose -f /home/core/docker-compose.yml ps | head -n 3 | tail -n 1 | cut -f 1 -d" ")
    # If no Docker health check has been defined, use regular container status
    if [[ $(docker inspect ${CONTAINER_NAME} | jq '.[].State.Health|length') == 0 ]]; then
      until [ "$state" == '"running"' ]; do state=$(docker inspect ${CONTAINER_NAME} | jq '.[].State.Status'); sleep ${SLEEP}; done
    else # Otherwise, use the health check
      until [ "$state" == '"healthy"' ]; do state=$(docker inspect ${CONTAINER_NAME} | jq '.[].State.Health.Status'); sleep ${SLEEP}; done
    fi
fi
