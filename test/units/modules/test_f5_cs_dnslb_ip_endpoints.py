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
    from library.modules.f5_cs_eap_ip_enforcement import ModuleParameters
    from library.modules.f5_cs_eap_ip_enforcement import ModuleManager
    from library.modules.f5_cs_eap_ip_enforcement import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_dnslb_ip_endpoints import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_dnslb_ip_endpoints import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_dnslb_ip_endpoints import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}

default_endpoint = dict(
                    name='cloud_endpoint_default',
                    virtual_server_type='cloud',
                    display_name='cloud-endpoint-default',
                    port=80,
                    address='192.168.0.1',
                    monitor='none'
                )

cloud_endpoint_1 = dict(
                    virtual_server_type='cloud',
                    name='cloud_endpoint_1',
                    display_name='cloud-endpoint-1',
                    port=80,
                    address='192.168.1.1',
                    monitor='none'
                )

ltm_endpoint_1 = dict(
                    virtual_server_type='bigip-ltm',
                    name='bigip_ltm_endpoint_1',
                    display_name='bigip-ltm-endpoint-1',
                    port=80,
                    translation_address='192.168.1.1',
                    vip_id='vip-id',
                )


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            subscription_id='s-xxxxxxxxxx',
            state='present',
            ip_endpoints=[
                cloud_endpoint_1,
                ltm_endpoint_1,
            ]
        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.state == 'present'

        updated_endpoint_1 = p.ip_endpoints[0]
        assert cloud_endpoint_1['virtual_server_type'] == updated_endpoint_1['virtual_server_type']
        assert cloud_endpoint_1['display_name'] == updated_endpoint_1['display_name']
        assert cloud_endpoint_1['port'] == updated_endpoint_1['port']
        assert cloud_endpoint_1['address'] == updated_endpoint_1['address']
        assert cloud_endpoint_1['monitor'] == updated_endpoint_1['monitor']
        updated_endpoint_2 = p.ip_endpoints[1]
        assert ltm_endpoint_1['virtual_server_type'] == updated_endpoint_2['virtual_server_type']
        assert ltm_endpoint_1['display_name'] == updated_endpoint_2['display_name']
        assert ltm_endpoint_1['port'] == updated_endpoint_2['port']
        assert ltm_endpoint_1['translation_address'] == updated_endpoint_2['translation_address']
        assert ltm_endpoint_1['vip_id'] == updated_endpoint_2['vip_id']


class TestIPEndpointsUpdate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_endpoints_list(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        ip_endpoints = list(payload['configuration']['gslb_service']['virtual_servers'].items())
        updated_endpoint_1 = ip_endpoints[0][1]
        assert cloud_endpoint_1['virtual_server_type'] == updated_endpoint_1['virtual_server_type']
        assert cloud_endpoint_1['display_name'] == updated_endpoint_1['display_name']
        assert cloud_endpoint_1['port'] == updated_endpoint_1['port']
        assert cloud_endpoint_1['address'] == updated_endpoint_1['address']
        assert cloud_endpoint_1['monitor'] == updated_endpoint_1['monitor']
        updated_endpoint_2 = ip_endpoints[1][1]
        assert ltm_endpoint_1['virtual_server_type'] == updated_endpoint_2['virtual_server_type']
        assert ltm_endpoint_1['display_name'] == updated_endpoint_2['display_name']
        assert ltm_endpoint_1['port'] == updated_endpoint_2['port']
        assert ltm_endpoint_1['translation_address'] == updated_endpoint_2['translation_address']
        assert ltm_endpoint_1['vip_id'] == updated_endpoint_2['vip_id']

        return load_fixture('f5_cs_dnslb_ip_endpoints_post_subscription_update.json')

    def test_ip_enforcement_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            state='present',
            ip_endpoints=[
                cloud_endpoint_1,
                ltm_endpoint_1,
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dnslb_ip_endpoints_get_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_endpoints_list)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        updated_endpoint_1 = results['ip_endpoints'][0]
        assert cloud_endpoint_1['virtual_server_type'] == updated_endpoint_1['virtual_server_type']
        assert cloud_endpoint_1['display_name'] == updated_endpoint_1['display_name']
        assert cloud_endpoint_1['port'] == updated_endpoint_1['port']
        assert cloud_endpoint_1['address'] == updated_endpoint_1['address']
        assert cloud_endpoint_1['monitor'] == updated_endpoint_1['monitor']
        updated_endpoint_2 = results['ip_endpoints'][1]
        assert ltm_endpoint_1['virtual_server_type'] == updated_endpoint_2['virtual_server_type']
        assert ltm_endpoint_1['display_name'] == updated_endpoint_2['display_name']
        assert ltm_endpoint_1['port'] == updated_endpoint_2['port']
        assert ltm_endpoint_1['translation_address'] == updated_endpoint_2['translation_address']
        assert ltm_endpoint_1['vip_id'] == updated_endpoint_2['vip_id']


class TestIPEndpointsAppend(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_enforcement_list(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        ip_endpoints = list(payload['configuration']['gslb_service']['virtual_servers'].items())
        updated_endpoint_1 = ip_endpoints[0][1]
        assert default_endpoint['virtual_server_type'] == updated_endpoint_1['virtual_server_type']
        assert default_endpoint['display_name'] == updated_endpoint_1['display_name']
        assert default_endpoint['port'] == updated_endpoint_1['port']
        assert default_endpoint['address'] == updated_endpoint_1['address']
        assert default_endpoint['monitor'] == updated_endpoint_1['monitor']
        updated_endpoint_2 = ip_endpoints[1][1]
        assert cloud_endpoint_1['virtual_server_type'] == updated_endpoint_2['virtual_server_type']
        assert cloud_endpoint_1['display_name'] == updated_endpoint_2['display_name']
        assert cloud_endpoint_1['port'] == updated_endpoint_2['port']
        assert cloud_endpoint_1['address'] == updated_endpoint_2['address']
        assert cloud_endpoint_1['monitor'] == updated_endpoint_2['monitor']
        updated_endpoint_3 = ip_endpoints[2][1]
        assert ltm_endpoint_1['virtual_server_type'] == updated_endpoint_3['virtual_server_type']
        assert ltm_endpoint_1['display_name'] == updated_endpoint_3['display_name']
        assert ltm_endpoint_1['port'] == updated_endpoint_3['port']
        assert ltm_endpoint_1['translation_address'] == updated_endpoint_3['translation_address']
        assert ltm_endpoint_1['vip_id'] == updated_endpoint_3['vip_id']
        return load_fixture('f5_cs_dnslb_ip_endpoints_post_subscription_append.json')

    def test_ip_enforcement_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            append=True,
            ip_endpoints=[
                cloud_endpoint_1,
                ltm_endpoint_1,
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dnslb_ip_endpoints_get_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_enforcement_list)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        updated_endpoint_0 = results['ip_endpoints'][0]
        assert default_endpoint['virtual_server_type'] == updated_endpoint_0['virtual_server_type']
        assert default_endpoint['display_name'] == updated_endpoint_0['display_name']
        assert default_endpoint['port'] == updated_endpoint_0['port']
        assert default_endpoint['address'] == updated_endpoint_0['address']
        assert default_endpoint['monitor'] == updated_endpoint_0['monitor']
        updated_endpoint_1 = results['ip_endpoints'][1]
        assert cloud_endpoint_1['virtual_server_type'] == updated_endpoint_1['virtual_server_type']
        assert cloud_endpoint_1['display_name'] == updated_endpoint_1['display_name']
        assert cloud_endpoint_1['port'] == updated_endpoint_1['port']
        assert cloud_endpoint_1['address'] == updated_endpoint_1['address']
        assert cloud_endpoint_1['monitor'] == updated_endpoint_1['monitor']
        updated_endpoint_2 = results['ip_endpoints'][2]
        assert ltm_endpoint_1['virtual_server_type'] == updated_endpoint_2['virtual_server_type']
        assert ltm_endpoint_1['display_name'] == updated_endpoint_2['display_name']
        assert ltm_endpoint_1['port'] == updated_endpoint_2['port']
        assert ltm_endpoint_1['translation_address'] == updated_endpoint_2['translation_address']
        assert ltm_endpoint_1['vip_id'] == updated_endpoint_2['vip_id']


class TestIPEnforcementRulesExclude(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_enforcement_list(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        items = list(payload['configuration']['gslb_service']['virtual_servers'])
        assert len(items) == 0

        return load_fixture('f5_cs_dnslb_ip_endpoints_post_subscription_absent.json')

    def test_ip_enforcement_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            state='absent',
            ip_endpoints=[
                default_endpoint,
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dnslb_ip_endpoints_get_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_enforcement_list)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        assert len(results['ip_endpoints']) == 0
