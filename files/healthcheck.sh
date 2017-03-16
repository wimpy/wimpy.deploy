#!/usr/bin/env bash

STACK_NAME=$1
RESOURCE_NAME=${2:-AutoscalingGroup}
AWS_REGION=${3:-eu-west-1}
MAX_RETRIES=${4:-10}
RETRIES=2
SLEEP=10

function cfn-signal() {
  /usr/bin/docker run --rm mbabineau/cfn-bootstrap cfn-signal \
    -e $? \
    --stack ${STACK_NAME} \
    --resource ${RESOURCE_NAME} \
    --region ${AWS_REGION}
}
trap cfn-signal EXIT

sleep 5 # It takes compose a few seconds to create the container

CONTAINER_NAME=$(/opt/bin/docker-compose -f /home/core/docker-compose.yml ps | head -n 3 | tail -n 1 | cut -f 1 -d" ")

# If no healthcheck has been defined, use regular container status
if [[ $(docker inspect ${CONTAINER_NAME} | jq '.[].State.Health|length') == 0 ]]; then
  while [ "$RETRIES" -le "$MAX_RETRIES" ]; do
    echo '.'
    if [[ $(docker inspect ${CONTAINER_NAME} | jq '.[].State.Status') == '"running"' ]]; then
      exit 0
    fi
    RETRIES=$((RETRIES+1))
    sleep ${SLEEP}
  done
else # Otherwise, check the health check status
  while [ "$RETRIES" -le "$MAX_RETRIES" ]; do
    printf '.'
    if [[ $(docker inspect ${CONTAINER_NAME} | jq '.[].State.Health.Status') == '"healthy"' ]]; then
      exit 0
    fi
    RETRIES=$((RETRIES+1))
    sleep ${SLEEP}
  done
fi

echo 'Failing: container has not been become healthy'
exit 1
