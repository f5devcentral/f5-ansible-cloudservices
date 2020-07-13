#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
---
author: Alex Shemyakin
short_description: HttpApi Plugin for F5 Cloud Services
description:
  - This HttpApi plugin provides methods to connect to F5 Cloud Services over a HTTP(S)-based api.
version_added: "1.0"
"""

import re

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.urls import Request
from ansible.module_utils.basic import env_fallback
from collections import defaultdict
from ansible.module_utils.six import iteritems

try:
    import json
except ImportError:
    import simplejson as json


f5_cs_spec = {
    'user': dict(
        required=True,
        no_log=True,
        fallback=(env_fallback, ['F5_USER'])
    ),
   'password': dict(
        required=True,
        no_log=True,
        aliases=['pass', 'pwd'],
        fallback=(env_fallback, ['F5_PASSWORD']),
    ),
}

f5_cs_argument_spec = {
    'f5_cloudservices': dict(type='dict', options=f5_cs_spec),
}

f5_cs_eap_default_policy = {
    "compliance_enforcement": {
      "data_guard": {
        "cc": True,
        "enabled": True,
        "ssn": True
      },
      "enabled": True,
      "sensitive_parameters": {
        "enabled": True,
        "parameters": [
          "cc_id",
          "creditcard",
          "passwd",
          "password"
        ]
      }
    },
    "encoding": "utf-8",
    "high_risk_attack_mitigation": {
      "allowed_methods": {
        "enabled": True,
        "methods": [
          {
            "name": "GET"
          },
          {
            "name": "POST"
          },
          {
            "name": "HEAD"
          }
        ]
      },
      "api_compliance_enforcement": {
        "enabled": True
      },
      "disallowed_file_types": {
        "enabled": True,
        "file_types": [
          "back",
          "bat",
          "bck",
          "bin",
          "cfg",
          "cmd",
          "com",
          "config",
          "dat",
          "dll",
          "eml",
          "exe",
          "exe1",
          "exe_renamed",
          "hta",
          "htr",
          "htw",
          "ida",
          "idc",
          "idq",
          "ini",
          "old",
          "sav",
          "save"
        ]
      },
      "enabled": True,
      "enforcement_mode": "monitoring",
      "geolocation_enforcement": {
        "disallowed_country_codes": [
          "CU",
          "IR",
          "KP",
          "LY",
          "SD",
          "SY"
        ],
        "enabled": True
      },
      "http_compliance_enforcement": {
        "enabled": True
      },
      "ip_enforcement": {
        "enabled": True,
        "ips": [

        ]
      },
      "signature_enforcement": {
        "enabled": True
      }
    },
    "malicious_ip_enforcement": {
      "enabled": True,
      "enforcement_mode": "monitoring",
      "ip_categories": [
        {
          "block": True,
          "log": True,
          "name": "mobile_threats"
        },
        {
          "block": True,
          "log": True,
          "name": "cloud_services"
        },
        {
          "block": True,
          "log": True,
          "name": "anonymous_proxies"
        },
        {
          "block": True,
          "log": True,
          "name": "phishing_proxies"
        },
        {
          "block": True,
          "log": True,
          "name": "infected_sources"
        },
        {
          "block": True,
          "log": True,
          "name": "denial_of_service"
        },
        {
          "block": True,
          "log": True,
          "name": "scanners"
        },
        {
          "block": True,
          "log": True,
          "name": "bot_nets"
        },
        {
          "block": True,
          "log": True,
          "name": "web_attacks"
        },
        {
          "block": True,
          "log": True,
          "name": "windows_exploits"
        },
        {
          "block": True,
          "log": True,
          "name": "spam_sources"
        }
      ]
    },
    "threat_campaigns": {
      "campaigns": [

      ],
      "enabled": True,
      "enforcement_mode": "monitoring"
    }
}

BASE_HEADERS = {'Content-Type': 'application/json'}
LOGIN_URL = "/v1/svc-auth/login"
LOGOUT_URL = "/v1/svc-auth/logout"
RELOG_URL = "/v1/svc-auth/relogin"
SUBSCRIPTION_BY_ID_URL = "/v1/svc-subscription/subscriptions/{0}"
SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions"
SUBSCRIPTION_STATUS_URL = "/v1/svc-subscription/subscriptions/{0}/status"
ACTIVATE_SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions/{0}/activate"
RETIRE_SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions/{0}/retire"
GET_CURRENT_USER = "/v1/svc-account/user"
GET_CATALOGS = "/v1/svc-catalog/catalogs"
CERTIFICATES_URL = "/v1/svc-certificates/certificates"


class HttpRestApi():
    def __init__(self, connection):
        self.connection = connection
        self.access_token = None
        self.refresh_token = None
        self.token_timeout = None

    def login(self, username, password):
        if username and password:
            payload = {
                'username': username,
                'password': password
                }
            response = self.send_request(LOGIN_URL, method='POST', data=payload, headers=BASE_HEADERS)
        else:
            raise AnsibleConnectionFailure('Username and password are required for login.')

        try:
            self.refresh_token = response['contents']['refresh_token']
            self.access_token = response['contents']['access_token']
            self.token_timeout = int(response['contents']['expires_at'])
            self.connection._auth = {'Authorization': 'Bearer {0}'.format(self.access_token)}
        except KeyError:
            raise ConnectionError('Server returned invalid response during connection authentication.')

    def get_subscription_by_id(self, subscription_id):
        if subscription_id:
            response = self.send_request(SUBSCRIPTION_BY_ID_URL.format(subscription_id), method='GET', headers=BASE_HEADERS)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Subscription Id is required.')

    def create_subscription(self, payload):
        if payload:
            response = self.send_request(SUBSCRIPTION_URL, method='POST', headers=BASE_HEADERS, data=payload)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Payload is empty.')

    def update_subscription(self, payload, subscription_id):
        if payload:
            response = self.send_request(SUBSCRIPTION_BY_ID_URL.format(subscription_id), method='PUT', headers=BASE_HEADERS, data=payload)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Payload is empty.')

    def retire_subscription(self, payload, subscription_id):
        response = self.send_request(RETIRE_SUBSCRIPTION_URL.format(subscription_id), method='POST', headers=BASE_HEADERS, data=payload)
        return response['contents']

    def activate_subscription(self, subscription_id):
        response = self.send_request(ACTIVATE_SUBSCRIPTION_URL.format(subscription_id), method='POST', headers=BASE_HEADERS)
        return response['contents']

    def get_subscription_status(self, subscription_id):
        response = self.send_request(SUBSCRIPTION_STATUS_URL.format(subscription_id), method='GET', headers=BASE_HEADERS)
        return response['contents']

    def get_current_user(self):
        response = self.send_request(GET_CURRENT_USER, method='GET', headers=BASE_HEADERS)
        return response['contents']

    def get_catalogs(self):
        response = self.send_request(GET_CATALOGS, method='GET', headers=BASE_HEADERS)
        return response['contents']

    def post_certificate(self, payload):
        response = self.send_request(CERTIFICATES_URL, method='POST', headers=BASE_HEADERS, data=payload)
        return response['contents']

    def _refresh_token(self, username):
        payload = {
            'username': username,
            'refresh_token': self.refresh_token
        }

        response = self.send_request(RELOG_URL, method='POST', data=payload, headers=BASE_HEADERS)
        try:
            self.access_token = response['contents']['access_token']
            # self.connection._auth = {'Authorization': 'Bearer %s' % self.access_token}
        except KeyError:
            raise ConnectionError('Server returned invalid response during connection authentication.')

    def handle_httperror(self, exc):
        err_5xx = r'^5\d{2}$'
        # We raise AnsibleConnectionFailure without passing to the module, as 50x type errors indicate a problem
        # with the service, anything else will be handled by the caller

        handled_error = re.search(err_5xx, str(exc.code))
        if handled_error:
            raise AnsibleConnectionFailure('Could not connect to {0}: {1}'.format(exc.reason))
        return False

    def send_request(self, url, method=None, **kwargs):
        body = kwargs.pop('data', None)
        data = json.dumps(body) if body else None
        self._display_request(method=method, data=data)

        try:
            response = self.connection.send(url, data, method=method, **kwargs)
            if response.getcode() in [200]:
                return dict(code=response.getcode(), contents=json.loads(response.read() or 'null'))
            else:
                raise ConnectionError('Request failed with status code {0}: {1}'.format(response.getcode(), response.read()))
        except HTTPError as exc:
            raise ConnectionError('Request failed with status code {0}: {1}'.format(exc.code, exc.reason))

    def _display_request(self, method, data):
         self.connection._log_messages(
            'F5 Cloud Services API Call: {0} with data {1}'.format(method, data)
         )

    def delete(self, url, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='DELETE', headers=headers, **kwargs)
        return self.send_request(url, method='DELETE', headers=BASE_HEADERS,  **kwargs)

    def get(self, url, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='GET', headers=headers, **kwargs)
        return self.send_request(url, method='GET', headers=BASE_HEADERS, **kwargs)

    def patch(self, url, data=None, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='PATCH', data=data, headers=headers, **kwargs)
        return self.send_request(url, method='PATCH', data=data, headers=BASE_HEADERS, **kwargs)

    def post(self, url, data=None, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='POST', data=data, headers=headers, **kwargs)
        return self.send_request(url, method='POST', data=data, headers=BASE_HEADERS, **kwargs)

    def put(self, url, data=None, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='PUT', data=data, headers=headers, **kwargs)
        return self.send_request(url, method='PUT', data=data, headers=BASE_HEADERS, **kwargs)


class HttpConnection(object):
    def __init__(self):
        self._auth = None
        self.api_uri = 'api.cloudservices.f5.com'

    def _log_messages(self, message):
        return True

    def send(self, url, data, method="GET", **kwargs):
        headers=None
        use_proxy=True
        force=False
        timeout=120
        validate_certs=kwargs.pop('validate_certs', True)
        url_username=None
        url_password=None
        http_agent=None
        force_basic_auth=False
        follow_redirects='urllib2'
        client_cert=None
        client_key=None
        cookies=None
        headers = kwargs.pop('headers', None)

        self.request = Request(
            headers=headers,
            use_proxy=use_proxy,
            force=force,
            timeout=timeout,
            validate_certs=validate_certs,
            url_username=url_username,
            url_password=url_password,
            http_agent=http_agent,
            force_basic_auth=force_basic_auth,
            follow_redirects=follow_redirects,
            client_cert=client_cert,
            client_key=client_key,
            cookies=cookies
        )

        if data:
            kwargs['data'] = data

        if self._auth:
            self.request.headers['Authorization'] = self._auth['Authorization']

        self.request.headers['Content-Type'] = 'application/json'
        response = self.request.open(method, 'https://{0}{1}'.format(self.api_uri, url), **kwargs)
        return response

class F5ModuleError(Exception):
    pass

class AnsibleF5Parameters(object):
    def __init__(self, *args, **kwargs):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        self.client = kwargs.pop('client', None)
        self._module = kwargs.pop('module', None)
        self._params = {}

        params = kwargs.pop('params', None)
        if params:
            self.update(params=params)
            self._params.update(params)

    def update(self, params=None):
        if params:
            self._params.update(params)

            for k, v in iteritems(params):
                # Adding this here because ``username`` is a connection parameter
                # and in cases where it is also an API parameter, we run the risk
                # of overriding the specified parameter with the connection parameter.
                #
                # Since this is a problem, and since "username" is never a valid
                # parameter outside its usage in connection params (where we do not
                # use the ApiParameter or ModuleParameters classes) it is safe to
                # skip over it if it is provided.
                if k == 'password':
                    continue
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result

    def __getattr__(self, item):
        # Ensures that properties that weren't defined, and therefore stashed
        # in the `_values` dict, will be retrievable.
        return self._values[item]

    @property
    def partition(self):
        if self._values['partition'] is None:
            return 'Common'
        return self._values['partition'].strip('/')

    @partition.setter
    def partition(self, value):
        self._values['partition'] = value

    def _filter_params(self, params):
        return dict((k, v) for k, v in iteritems(params) if v is not None)
