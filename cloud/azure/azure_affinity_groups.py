#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: azure_affinity_groups
short_description: create or delete an affinity group in azure
description:
  - Creates or deletes azure affinity groups. This module has a dependency on python-azure >= 0.7.1
version_added: ""
options:
  state:
    description:
      - use 'absent' to delete affinity group, default 'present' creates affinity group.
    required: false
    default: 'present'
  subscription_id:
    description:
      - azure subscription id. Overrides the AZURE_SUBSCRIPTION_ID environement variable.
    required: false
    default: null
  management_cert_path:
    description:
      - path to an azure management certificate associated with the subscription id. Overrides the AZURE_CERT_PATH environement variable.
    required: false
    default: null
  name:
    description:
      - name of the affinity group.
    required: true
    default: null
  label:
    description:
      - label for the affinity group. If not specified, value for 'name' is used. Can be up to 100 characters.
    required: false
    default: name value
  location:
    description:
      - azure location for the affinity group, e.g. 'East US'
    required: true
    default: null
  description:
    description:
      - description of affinity group. Can be up to 1024 characters.
    required: false
    default: null

requirements: [ "azure" ]
author: Richard Lander
'''

EXAMPLES = '''
# Note: None of these examples set subscription_id or management_cert_path
# It is assumed that their matching environment variables are set.

# Create new affinity group exampl
- local_action:
    module: azure_affinity_groups
    name: my-affinity-group
    location: 'East US'
'''

import sys
import os

AZURE_LOCATIONS = ['South Central US',
                   'Central US',
                   'East US 2',
                   'East US',
                   'West US',
                   'North Central US',
                   'North Europe',
                   'West Europe',
                   'East Asia',
                   'Southeast Asia',
                   'Japan West',
                   'Japan East',
                   'Brazil South']

try:
    from azure.servicemanagement import ServiceManagementService
except ImportError:
    print "failed=True msg='azure required for this module'"
    sys.exit(1)


def create_affinity_group(module, service_manager):
    """Create new affinity group if it doesn't exist."""

    name        = module.params.get('name')
    label       = module.params.get('label') or name
    location    = module.params.get('location')
    description = module.params.get('description')

    # check to see if affinity group already exists
    all_groups = service_manager.list_affinity_groups()
    for group in all_groups:
        if group.name == name:
            # affinity group with this name already exists - no need to create
            return False  # no changes made
    
    service_manager.create_affinity_group(name, label, location, description)

    return True


def delete_affinity_group(module, service_manager):
    """Delete the specified affinity group if it exists."""

    name = module.params.get('name')

    # check to see if affinity group already exists
    all_groups = service_manager.list_affinity_groups()
    for group in all_groups:
        if group.name == name:
            # affinity group with this name exists - delete it
            service_manager.delete_affinity_group(name)
            return True  # change made

    return False  # no changes made


def get_azure_creds(module):
    # Check modul args for credentials, then check environment vars
    subscription_id = module.params.get('subscription_id')
    if not subscription_id:
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID', None)
    if not subscription_id:
        module.fail_json(msg="No subscription_id provided. Please set 'AZURE_SUBSCRIPTION_ID' or use the 'subscription_id' parameter")

    management_cert_path = module.params.get('management_cert_path')
    if not management_cert_path:
        management_cert_path = os.environ.get('AZURE_CERT_PATH', None)
    if not management_cert_path:
        module.fail_json(msg="No management_cert_path provided. Please set 'AZURE_CERT_PATH' or use the 'management_cert_path' parameter")

    return subscription_id, management_cert_path


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present'),
            subscription_id=dict(no_log=True),
            management_cert_path=dict(),
            name=dict(),
            label=dict(),
            location=dict(choices=AZURE_LOCATIONS),
            description=dict()
        )
    )

    subscription_id, management_cert_path = get_azure_creds(module)

    service_manager = ServiceManagementService(subscription_id, management_cert_path)

    if not module.params.get('name'):
        module.fail_json(msg='name parameter is required for new affinity group')

    if module.params.get('state') == 'absent':
        changed = delete_affinity_group(module, service_manager)
        
    elif module.params.get('state') == 'present':
        if not module.params.get('location'):
            module.fail_json(msg='location parameter is required for new affinity group')

        changed = create_affinity_group(module, service_manager)

    module.exit_json(changed=changed)


# import module snippets
from ansible.module_utils.basic import *

main()

