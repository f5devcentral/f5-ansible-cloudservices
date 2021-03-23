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
    from library.modules.f5_cs_primary_dns_records import ModuleParameters
    from library.modules.f5_cs_primary_dns_records import ModuleManager
    from library.modules.f5_cs_primary_dns_records import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_primary_dns_records import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_primary_dns_records import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_primary_dns_records import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}

default_record = [
      {
        "ttl": 86400,
        "type": "NS",
        "values": [
          "ns1.f5cloudservices.com",
          "ns2.f5cloudservices.com"
        ]
      }
    ]

demo_record = [
        {
            "ttl": 3600,
            "type": "A",
            "values": [
                "127.0.0.1"
            ]
        }
    ]

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
            records={
                "": default_record
            }
        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.state == 'present'

        updated_record = p.records[''][0]
        assert default_record[0]['ttl'] == updated_record['ttl']
        assert default_record[0]['type'] == updated_record['type']
        assert default_record[0]['values'] == updated_record['values']


class TestRecordsUpdate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_records(self, payload, subscription_id):
        assert subscription_id == 's-xxxxxxxxxx'
        remote_default_record = payload['configuration']['dns_service']['records'][''][0]
        assert default_record[0]['ttl'] == remote_default_record['ttl']
        assert default_record[0]['type'] == remote_default_record['type']
        assert default_record[0]['values'] == remote_default_record['values']
        remote_demo_record = payload['configuration']['dns_service']['records']['demo-record'][0]
        assert demo_record[0]['ttl'] == remote_demo_record['ttl']
        assert demo_record[0]['type'] == remote_demo_record['type']
        assert demo_record[0]['values'] == remote_demo_record['values']
        return load_fixture('f5_cs_dns_subscription_update.json')

    def test_records_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            state='present',
            append=False,
            records={
                "": default_record,
                "demo-record": demo_record
            }
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dns_subscription_get.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_records)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        remote_default_record = results['records'][''][0]
        assert default_record[0]['ttl'] == remote_default_record['ttl']
        assert default_record[0]['type'] == remote_default_record['type']
        assert default_record[0]['values'] == remote_default_record['values']
        remote_demo_record = results['records']['demo-record'][0]
        assert demo_record[0]['ttl'] == remote_demo_record['ttl']
        assert demo_record[0]['type'] == remote_demo_record['type']
        assert demo_record[0]['values'] == remote_demo_record['values']



class TestRecordsAppend(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_records(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'
        remote_default_record = payload['configuration']['dns_service']['records'][''][0]
        assert default_record[0]['ttl'] == remote_default_record['ttl']
        assert default_record[0]['type'] == remote_default_record['type']
        assert default_record[0]['values'] == remote_default_record['values']
        remote_demo_record = payload['configuration']['dns_service']['records']['demo-record'][0]
        assert demo_record[0]['ttl'] == remote_demo_record['ttl']
        assert demo_record[0]['type'] == remote_demo_record['type']
        assert demo_record[0]['values'] == remote_demo_record['values']
        return load_fixture('f5_cs_dns_subscription_update.json')

    def test_records_append(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            append=True,
            records={
                "": default_record,
                "demo-record": demo_record
            }
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dns_subscription_get.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_records)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        remote_default_record = results['records'][''][0]
        assert default_record[0]['ttl'] == remote_default_record['ttl']
        assert default_record[0]['type'] == remote_default_record['type']
        assert default_record[0]['values'] == remote_default_record['values']
        remote_demo_record = results['records']['demo-record'][0]
        assert demo_record[0]['ttl'] == remote_demo_record['ttl']
        assert demo_record[0]['type'] == remote_demo_record['type']
        assert demo_record[0]['values'] == remote_demo_record['values']


class TestRecordsExclude(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_records(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        remote_default_record = payload['configuration']['dns_service']['records'][''][0]
        assert default_record[0]['ttl'] == remote_default_record['ttl']
        assert default_record[0]['type'] == remote_default_record['type']
        assert default_record[0]['values'] == remote_default_record['values']

        assert len(payload['configuration']['dns_service']['records'].keys()) == 1

        return load_fixture('f5_cs_dns_subscription_absent.json')

    def test_records_exclude(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            state='absent',
            records={
                "demo-record": {}
            }
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_dns_subscription_get_multi_records.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_records)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert len(results['records'].keys()) == 1
        remote_default_record = results['records'][''][0]
        assert default_record[0]['ttl'] == remote_default_record['ttl']
        assert default_record[0]['type'] == remote_default_record['type']
        assert default_record[0]['values'] == remote_default_record['values']
