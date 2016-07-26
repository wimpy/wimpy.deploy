#!/usr/bin/python
# encoding: utf-8

# (c) 2015, Jose Armesto <jose@armesto.net>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = """
---
module: ec2_lc_find
short_description: Find AWS Autoscaling Launch Configurations
description:
  - Returns list of matching Launch Configurations for a given name, along with other useful information
  - Results can be sorted and sliced
  - It depends on boto
  - Based on the work by Tom Bamford (https://github.com/tombamford)

version_added: "2.2"
author: "Jose Armesto (@fiunchinho)"
options:
  region:
    description:
      - The AWS region to use.
    required: true
    aliases: ['aws_region', 'ec2_region']
  name_regex:
    description:
      - A Launch Configuration to match
      - It'll be compiled as regex
    required: false
  sort:
    description:
      - Whether or not to sort the results
    required: false
    default: false
  sort_order:
    description:
      - Order in which to sort results.
      - Only used when the 'sort' parameter is specified.
    choices: ['ascending', 'descending']
    default: 'ascending'
    required: false
  sort_start:
    description:
      - Which result to start with (when sorting).
      - Corresponds to Python slice notation.
    default: null
    required: false
  sort_end:
    description:
      - Which result to end with (when sorting).
      - Corresponds to Python slice notation.
    default: null
    required: false
requirements:
  - "python >= 2.6"
  - boto
"""

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Search for the Launch Configurations that start with "app"
- ec2_lc_find:
    name_regex: app.*
    sort: true
    sort_order: descending
    sort_start: 1
    sort_end: 2
'''

RETURN = '''
image_id:
    description: AMI id
    returned: when AMI found
    type: string
    sample: "ami-0d75df7e"
user_data:
    description: User data used to start instance
    returned: when AMI found
    type: string
    user_data: "ZXhwb3J0IENMT1VE"
name:
    description: Name of the AMI
    returned: when AMI found
    type: string
    sample: "myapp-v123"
arn:
    description: Name of the AMI
    returned: when AMI found
    type: string
    sample: "arn:aws:autoscaling:eu-west-1:12345:launchConfiguration:d82f050e-e315:launchConfigurationName/yourproject"
instance_type:
    description: Type of ec2 instance
    returned: when AMI found
    type: string
    sample: "t2.small"
...
'''


def find_launch_configs(client, module):
    name_regex = module.params.get('name_regex')
    sort = module.params.get('sort')
    sort_order = module.params.get('sort_order')
    sort_start = module.params.get('sort_start')
    sort_end = module.params.get('sort_end')

    launch_configs = client.describe_launch_configurations()

    if launch_configs['ResponseMetadata'] and launch_configs['ResponseMetadata']['HTTPStatusCode'] == 200:
        results = []
        for lc in launch_configs['LaunchConfigurations']:
            data = {
                'name': lc['LaunchConfigurationName'],
                'arn': lc['LaunchConfigurationARN'],
                'user_data': lc['UserData'],
                'instance_type': lc['InstanceType'],
                'image_id': lc['ImageId'],
            }
            results.append(data)
        if name_regex:
            regex = re.compile(name_regex)
            results = [result for result in results if regex.match(result['name'])]
        if sort:
            results.sort(key=lambda e: e['name'], reverse=(sort_order == 'descending'))
        try:
            if sort and sort_start and sort_end:
                results = results[int(sort_start):int(sort_end)]
            elif sort and sort_start:
                results = results[int(sort_start):]
            elif sort and sort_end:
                results = results[:int(sort_end)]
        except TypeError:
            module.fail_json(msg="Please supply numeric values for sort_start and/or sort_end")
        module.exit_json(changed=False, results=results)
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True, aliases=['aws_region', 'ec2_region']),
        name_regex=dict(required=False),
        sort=dict(required=False, default=None, type='bool'),
        sort_order=dict(required=False, default='ascending', choices=['ascending', 'descending']),
        sort_start=dict(required=False),
        sort_end=dict(required=False),
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, True)

    client = boto3_conn(module=module, conn_type='client', resource='autoscaling', region=region, **aws_connect_params)
    find_launch_configs(client, module)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
