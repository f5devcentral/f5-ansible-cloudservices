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
    from library.modules.f5_cs_dnslb_subscription_app import ModuleParameters
    from library.modules.f5_cs_dnslb_subscription_app import ModuleManager
    from library.modules.f5_cs_dnslb_subscription_app import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_dnslb_subscription_app import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_dnslb_subscription_app import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_dnslb_subscription_app import ArgumentSpec
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
            catalog_id='c-xxxxxxxxxx',
            service_instance_name='s_i_n',
            state='absent',
            patch=True,
            activate=True,
            configuration=dict(
                gslb_service=dict(
                    zone='fqdn.demo.com'
                )
            )
        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.account_id == 'a-xxxxxxxxxx'
        assert p.catalog_id == 'c-xxxxxxxxxx'
        assert p.service_instance_name == 's_i_n'
        assert p.state == 'absent'
        assert p.patch is True
        assert p.activate is True
        assert p.configuration['gslb_service']['zone'] == 'fqdn.demo.com'


class TestSubscriptionAppCreate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def create_subscription(self, payload, *args, **kwargs):
        assert payload['account_id'] == 'a-xxxxxxxxxx'
        assert payload['catalog_id'] == 'c-xxxxxxxxxx'
        assert payload['service_instance_name'] == 'fqdn.demo.com'
        assert payload['configuration']['gslb_service']['zone'] == 'fqdn.demo.com'
        assert payload['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['address'] == '12.34.56.78'
        return load_fixture('f5_cs_dnslb_subscription_app_create.json')

    def test_subscription_app_create(self, *args):
        set_module_args(dict(
            service_instance_name="fqdn.demo.com",
            configuration=dict(
                gslb_service=dict(
                    zone="fqdn.demo.com",
                    virtual_servers=dict(
                        ipEndpoint_1=dict(
                            address="12.34.56.78",
                            display_name="endpoint_1",
                            monitor="none",
                            port=80,
                            virtual_server_type="cloud"
                        )
                    )
                )
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_catalogs_fake = load_fixture('f5_cs_subscription_app_get_catalogs.json')
        get_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')
        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_catalogs = Mock(return_value=get_catalogs_fake)
        api_client.get_current_user = Mock(return_value=get_user_fake)
        api_client.create_subscription = Mock(side_effect=self.create_subscription)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['catalog_id'] == 'c-xxxxxxxxxx'
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['service_instance_name'] == 'fqdn.demo.com'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['address'] == '12.34.56.78'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['display_name'] == 'endpoint_1'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['monitor'] == 'none'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['port'] == 80
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['virtual_server_type'] == 'cloud'


class TestSubscriptionFetch(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_subscription_fetch(self, *args):
        set_module_args(dict(
            state='fetch',
            subscription_id='s-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dnslb_subscription_app_fetch.json')
        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['catalog_id'] == 'c-xxxxxxxxxx'
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['service_instance_name'] == 'fqdn.demo.com'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['address'] == '12.34.56.78'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['display_name'] == 'endpoint_1'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['monitor'] == 'none'
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['port'] == 80
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['virtual_server_type'] == 'cloud'


class TestSubscriptionOperate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def retire_subscription(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'
        assert payload['subscription_id'] == 's-xxxxxxxxxx'
        return load_fixture('f5_cs_dnslb_subscription_app_retire.json')

    def test_subscription_retire(self, *args):
        set_module_args(dict(
            state='absent',
            subscription_id='s-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()
        api_client.retire_subscription = Mock(side_effect=self.retire_subscription)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['status'] == 'RETIRED'
        assert results['subscription_id'] == 's-xxxxxxxxxx'

    def test_subscription_activate(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            state='active',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_status = load_fixture('f5_cs_dnslb_subscription_app_active.json')
        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()
        api_client.activate_subscription = Mock()
        api_client.get_subscription_status = Mock(return_value=get_subscription_status)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['status'] == 'ACTIVE'

    def test_subscription_suspend(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            state='suspended',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_status = load_fixture('f5_cs_dnslb_subscription_app_suspend.json')
        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()
        api_client.activate_subscription = Mock()
        api_client.get_subscription_status = Mock(return_value=get_subscription_status)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['status'] == 'DISABLED'


class TestSubscriptionBatchUpdate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_subscription(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'
        assert payload['configuration']['gslb_service']['custom_parameter'] is True
        return load_fixture('f5_cs_dnslb_subscription_app_update_batch.json')

    def test_subscription_batch_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            configuration=dict(
                gslb_service=dict(
                    custom_parameter=True
                )
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dnslb_subscription_app_update_default.json')
        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()
        api_client.update_subscription = Mock(side_effect=self.update_subscription)
        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['configuration']['gslb_service']['custom_parameter'] is True


class TestSubscriptionPatchUpdate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_subscription(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'
        assert payload['configuration']['gslb_service']['custom_parameter'] is True
        assert payload['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['address'] == '12.34.56.78'
        return load_fixture('f5_cs_dnslb_subscription_app_update_patch.json')

    def test_subscription_patch_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            patch=True,
            configuration=dict(
                gslb_service=dict(
                    custom_parameter=True
                )
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dnslb_subscription_app_update_default.json')
        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()
        api_client.update_subscription = Mock(side_effect=self.update_subscription)
        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['configuration']['gslb_service']['custom_parameter'] is True
        assert results['configuration']['gslb_service']['virtual_servers']['ipEndpoint_1']['address'] == '12.34.56.78'

