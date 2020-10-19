# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

import unittest
from unittest.mock import Mock

from test.units.modules.utils import set_module_args

try:
    from library.modules.f5_cs_organization import ModuleParameters
    from library.modules.f5_cs_organization import ModuleManager
    from library.modules.f5_cs_organization import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_organization import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_organization import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_organization import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='account',
            account_id='a-xxxxxxxxxx',
            parent_account_id='',
            address=dict(
                street_1='line 1',
                street_2='line 2',
                city='city',
                state='state',
                country='country',
                postal_code=98000,
            ),
            phone='+1 (123) 4567899',
            state='absent',
        )

        p = ModuleParameters(params=args)

        assert p.name == 'account'
        assert p.account_id == 'a-xxxxxxxxxx'
        assert p.parent_account_id == ''
        assert p.address['street_1'] == 'line 1'
        assert p.address['street_2'] == 'line 2'
        assert p.address['city'] == 'city'
        assert p.address['state'] == 'state'
        assert p.address['country'] == 'country'
        assert p.address['postal_code'] == 98000
        assert p.phone == '+1 (123) 4567899'
        assert p.state == 'absent'


class TestOrganizationOperate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        get_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')
        get_memberships_fake = load_fixture('f5_cs_get_memberships.json')
        get_account_fake = load_fixture('f5_cs_organization_get_account.json')
        connection = Mock()
        self.api_client = CloudservicesApi(connection)
        self.api_client.login = Mock()

        self.api_client.get_current_user = Mock(return_value=get_user_fake)
        self.api_client.get_memberships = Mock(return_value=get_memberships_fake)
        self.api_client.get_account = Mock(return_value=get_account_fake)
        self.api_client.create_account = Mock(side_effect=self.create_account)
        self.api_client.delete_account = Mock(return_value=dict())

    def create_account(self, payload, *args, **kwargs):
        assert payload['name'] == 'account'
        assert payload['parent_account_id'] == ''
        assert payload['address']['street_1'] == 'line 1'
        assert payload['address']['street_2'] == 'line 2'
        assert payload['address']['city'] == 'city'
        assert payload['address']['state'] == 'state'
        assert payload['address']['country'] == 'country'
        assert payload['address']['postal_code'] == 98000
        assert payload['phone'] == '+1 (123) 4567899'
        return load_fixture('f5_cs_organization_create.json')

    def test_organization_create(self, *args):
        set_module_args(dict(
            name='account',
            address=dict(
                street_1='line 1',
                street_2='line 2',
                city='city',
                state='state',
                country='country',
                postal_code=98000,
            ),
            phone='+1 (123) 4567899',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'account'
        assert results['parent_account_id'] == ''
        assert results['address']['street_1'] == 'line 1'
        assert results['address']['street_2'] == 'line 2'
        assert results['address']['city'] == 'city'
        assert results['address']['state'] == 'state'
        assert results['address']['country'] == 'country'
        assert results['address']['postal_code'] == 98000
        assert results['phone'] == '+1 (123) 4567899'

    def test_organization_fetch(self, *args):
        set_module_args(dict(
            state='fetch',
            account_id='a-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['name'] == 'firstaccount'
        assert results['parent_account_id'] == ''
        assert results['address']['street_1'] == ''
        assert results['address']['street_2'] == ''
        assert results['phone'] == ''

    def test_subscription_fetch_all(self, *args):
        set_module_args(dict(
            state='fetch',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        accounts = results['accounts']
        assert len(accounts) == 1

    def test_fetch_all_organizations(self, *args):
        set_module_args(dict(
            state='absent',
            account_id='a-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['account_id'] == 'a-xxxxxxxxxx'
