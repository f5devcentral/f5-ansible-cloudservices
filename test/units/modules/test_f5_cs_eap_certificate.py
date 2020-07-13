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
    from library.module_utils.cloudservices import HttpRestApi
    from library.module_utils.cloudservices import HttpConnection
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_certificate import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_certificate import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_certificate import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import HttpRestApi
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import HttpConnection


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
            f5_cloudservices=dict(
                user='user',
                password='password',
            ),
            certificate='cert',
            private_key='key',
            passphrase='pass_phrase',
            certificate_chain='certificate_chain',
            https_port=443,
            https_redirect=True,
            update_comment='update SSL certificate'

        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.f5_cloudservices['user'] == 'user'
        assert p.f5_cloudservices['password'] == 'password'
        assert p.certificate == 'cert'
        assert p.private_key == 'key'
        assert p.passphrase == 'pass_phrase'
        assert p.certificate_chain == 'certificate_chain'
        assert p.https_port == 443
        assert p.https_redirect is True
        assert p.update_comment == 'update SSL certificate'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_certificate_upload(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            f5_cloudservices=dict(
                user='user',
                password='password',
            ),
            certificate='cert',
            private_key='key',
            passphrase='pass_phrase',
            certificate_chain='certificate_chain',
            https_port=443,
            https_redirect=True,
            update_comment='update SSL certificate'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_eap_certificate_get_subscription.json')
        update_subscription_fake = load_fixture('f5_cs_eap_certificate_update_subscription.json')
        post_certificate_fake = load_fixture('f5_cs_eap_certificate_post_certificate.json')

        api_client = HttpRestApi(HttpConnection())
        api_client.login = Mock()
        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(return_value=update_subscription_fake)
        api_client.post_certificate = Mock(return_value=post_certificate_fake)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['configuration']['waf_service']['application']['http']['https_redirect'] is True
        assert results['configuration']['waf_service']['application']['https']['enabled'] is True
        assert results['configuration']['waf_service']['application']['https']['port'] == 443
        assert results['configuration']['waf_service']['application']['https']['tls']['certificate_id'] == 'cert-xxxxxx_xxx'