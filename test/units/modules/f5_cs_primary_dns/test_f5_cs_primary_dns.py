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
    from library.modules.f5_cs_primary_dns import ModuleParameters
    from library.modules.f5_cs_primary_dns import ModuleManager
    from library.modules.f5_cs_primary_dns import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_primary_dns import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_primary_dns import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_primary_dns import ArgumentSpec
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
            subscription_id='s-xxxxxxxxxx',
            account_id='a-xxxxxxxxxx',
            service_instance_name='s_i_n',
            state='absent',
            patch=True,
            activate=True,
            configuration=dict(
                dns_service=dict(
                    zone='test_zone'
                )
            )
        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.account_id == 'a-xxxxxxxxxx'
        assert p.service_instance_name == 's_i_n'
        assert p.state == 'absent'
        assert p.patch is True
        assert p.activate is True
        assert p.configuration['dns_service']['zone'] == 'test_zone'


class TestSubscriptionAppCreate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        get_catalogs_fake = load_fixture('f5_cs_subscription_app_get_catalogs.json')
        get_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')
        get_subscription_fake = load_fixture('f5_cs_dns_subscription_get.json')
        activate_subscription_fake = load_fixture('f5_cs_dns_subscription_activate.json')
        get_subscriptions_fake = load_fixture('f5_cs_dns_subscription_get_subscriptions.json')
        connection = Mock()
        self.api_client = CloudservicesApi(connection)
        self.api_client.login = Mock()
        self.api_client.get_catalogs = Mock(return_value=get_catalogs_fake)
        self.api_client.get_current_user = Mock(return_value=get_user_fake)
        self.api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        self.api_client.get_subscriptions_by_type = Mock(return_value=get_subscriptions_fake)
        self.api_client.activate_subscription = Mock(return_value=activate_subscription_fake)
        self.api_client.get_subscription_status = Mock(return_value=activate_subscription_fake)

        self.api_client.create_subscription = Mock(side_effect=self.create_subscription)
        self.api_client.retire_subscription = Mock(side_effect=self.retire_subscription)

    def create_subscription(self, payload, *args, **kwargs):
        assert payload['account_id'] == 'a-xxxxxxxxxx'
        assert payload['service_instance_name'] == 'new-fqdn.demo.com'
        assert payload['configuration']['dns_service']['zone'] == 'new-fqdn.demo.com'
        assert payload['configuration']['id'] == 'createPrimary'
        return load_fixture('f5_cs_dns_subscription_create.json')

    def retire_subscription(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'
        assert payload['subscription_id'] == 's-xxxxxxxxxx'
        return load_fixture('f5_cs_dns_subscription_retire.json')

    def test_subscription_app_create(self, *args):
        set_module_args(dict(
            service_instance_name='new-fqdn.demo.com'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()
        assert results['changed'] is True

    def test_subscription_fetch(self, *args):
        set_module_args(dict(
            state='fetch',
            subscription_id='s-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['service_instance_name'] == 'fqdn.demo.com'
        assert len(results['configuration']['nameservers']) == 2
        assert results['configuration']['dns_service']['zone'] == 'fqdn.demo.com'
        assert results['configuration']['dns_service']['admin'] == 'dns-admin@f5cloudservices.com'
        assert results['configuration']['dns_service']['primary_nameserver'] == 'ns1.f5cloudservices.com'

    def test_subscription_retire(self, *args):
        set_module_args(dict(
            state='absent',
            subscription_id='s-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'


class TestSubscriptionBatchUpdate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        get_catalogs_fake = load_fixture('f5_cs_subscription_app_get_catalogs.json')
        get_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')
        get_subscription_fake = load_fixture('f5_cs_dns_subscription_get.json')
        activate_subscription_fake = load_fixture('f5_cs_dns_subscription_activate.json')
        get_subscriptions_fake = load_fixture('f5_cs_dns_subscription_get_subscriptions.json')
        connection = Mock()
        self.api_client = CloudservicesApi(connection)
        self.api_client.login = Mock()
        self.api_client.get_catalogs = Mock(return_value=get_catalogs_fake)
        self.api_client.get_current_user = Mock(return_value=get_user_fake)
        self.api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        self.api_client.get_subscriptions_by_type = Mock(return_value=get_subscriptions_fake)
        self.api_client.activate_subscription = Mock(return_value=activate_subscription_fake)
        self.api_client.get_subscription_status = Mock(return_value=activate_subscription_fake)
        self.api_client.update_subscription = Mock(side_effect=self.update_subscription)

    def update_subscription(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'
        assert payload['configuration']['dns_service']['custom_parameter'] is True
        return load_fixture('f5_cs_dns_subscription_update_batch.json')

    def test_subscription_batch_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            configuration=dict(
                dns_service=dict(
                    custom_parameter=True
                )
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['configuration']['dns_service']['custom_parameter'] is True

    def test_subscription_batch_update_no_change(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            service_instance_name='fqdn.demo.com',
            configuration=dict(
                dns_service=dict(
                    expire=360000,
                    negative_ttl=1800,
                    refresh=86400,
                    retry=7200,
                    remark='',
                    serial=2021031704,
                    ttl=86400,
                    zone='fqdn.demo.com',
                    records={
                        "": [
                          {
                            "ttl": 86400,
                            "type": "NS",
                            "values": [
                              "ns1.f5cloudservices.com",
                              "ns2.f5cloudservices.com"
                            ]
                          }
                        ],
                        "demo-record": [
                          {
                            "ttl": 3600,
                            "type": "A",
                            "values": [
                              "127.0.0.1"
                            ]
                          }
                        ]
                    }
                )
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['subscription_id'] == 's-xxxxxxxxxx'
