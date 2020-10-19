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
    from library.modules.f5_cs_eap_certificate import ModuleParameters
    from library.modules.f5_cs_eap_certificate import ModuleManager
    from library.modules.f5_cs_eap_certificate import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_certificate import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_certificate import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_certificate import ArgumentSpec
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
        subscription = dict(
            subscription_id='s-xxxxxxxxxx',
            enabled=True,
            https_port=443,
            https_redirect=True,
            update_comment='update SSL certificate'
        )

        args = dict(
            certificate='cert',
            private_key='key',
            passphrase='pass_phrase',
            certificate_chain='certificate_chain',
            assigned_subscriptions=[
                subscription
            ]
        )

        p = ModuleParameters(params=args)

        assert p.assigned_subscriptions[0]['subscription_id'] == 's-xxxxxxxxxx'
        assert p.assigned_subscriptions[0]['enabled'] is True
        assert p.assigned_subscriptions[0]['https_port'] == 443
        assert p.assigned_subscriptions[0]['https_redirect'] is True
        assert p.assigned_subscriptions[0]['update_comment'] == 'update SSL certificate'
        assert p.certificate == 'cert'
        assert p.private_key == 'key'
        assert p.passphrase == 'pass_phrase'
        assert p.certificate_chain == 'certificate_chain'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

        get_subscription_fake = load_fixture('f5_cs_eap_certificate_get_subscription.json')
        get_subscriptions_by_type_fake = load_fixture('f5_cs_eap_certificate_get_subscriptions.json')
        update_subscription_fake = load_fixture('f5_cs_eap_certificate_update_subscription.json')
        post_certificate_fake = load_fixture('f5_cs_eap_certificate_post_certificate.json')
        get_certificates_fake = load_fixture('f5_cs_eap_certificate_get_certificates.json')
        get_current_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')

        connection = Mock()
        self.api_client = CloudservicesApi(connection)
        self.api_client.login = Mock()
        self.api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        self.api_client.get_subscriptions_by_type = Mock(return_value=get_subscriptions_by_type_fake)
        self.api_client.update_subscription = Mock(return_value=update_subscription_fake)
        self.api_client.post_certificate = Mock(return_value=post_certificate_fake)
        self.api_client.get_certificates = Mock(return_value=get_certificates_fake)
        self.api_client.get_current_user = Mock(return_value=get_current_user_fake)
        self.api_client.retire_certificate = Mock(return_value=True)

    def test_certificate_upload(self, *args):
        subscription = dict(
            subscription_id='s-xxxxxxxxxx',
            enabled=True,
            update_comment='update SSL certificate'
        )

        set_module_args(dict(
            state='present',
            certificate='cert',
            private_key='key',
            passphrase='pass_phrase',
            certificate_chain='certificate_chain',
            assigned_subscriptions=[
                subscription
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['certificate_id'] == 'cert-xxxxxxxxxx'
        assert results['expiration_date'] == '2030-02-14T19:46:40Z'
        assert results['common_name'] == 'fqdn.test.com'
        subscription = results['assigned_subscriptions'][0]
        assert subscription['subscription_id'] == 's-xxxxxxxxxx'

    def test_certificate_remove(self, *args):
        set_module_args(dict(
            state='absent',
            certificate_id='cert-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True

    def test_certificate_fetch_by_subscription_id(self, *args):
        set_module_args(dict(
            state='fetch',
            subscription_id='s-xxxxxxxxxx',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['certificate_id'] == 'cert-xxxxxxxxxx'
        assert results['expiration_date'] == '2030-02-14T19:46:40Z'
        assert results['common_name'] == 'fqdn.test.com'
        subscription = results['assigned_subscriptions'][0]
        assert subscription['subscription_id'] == 's-xxxxxxxxxx'

    def test_certificate_fetch_all(self, *args):
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
        certificate = results['certificates'][0]
        assert certificate['id'] == 'cert-xxxxxxxxxx'