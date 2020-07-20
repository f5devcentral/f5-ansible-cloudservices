#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Wojciech Wypior <w.wypior@f5.com>
httpapi : f5
short_description: HttpApi Plugin for F5 Cloud Services
description:
  - This HttpApi plugin provides methods to connect to F5 Cloud Services over a HTTP(S)-based api.
version_added: "2.10"
"""

import re

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.connection import ConnectionError


try:
    import json
except ImportError:
    import simplejson as json

BASE_HEADERS = {'Content-Type': 'application/json'}
LOGIN_URL = "/v1/svc-auth/login"
LOGOUT_URL = "/v1/svc-auth/logout"
RELOG_URL = "/v1/svc-auth/relogin"


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApi, self).__init__(connection)
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

    def update_auth(self, response, response_text):
        """We never update token per request, we will utilize token timeouts for that instead at some point,
        for now we just return None."""
        return None

    def _refresh_token(self, username):
        """Refresh token method to be used in future implementation."""
        payload = {
            'username': username,
            'refresh_token': self.refresh_token
        }

        response = self.send_request(RELOG_URL, method='POST', data=payload, headers=BASE_HEADERS)
        try:
            self.access_token = response['contents']['access_token']
            self.connection._auth = {'Authorization': 'Bearer %s' % self.access_token}
        except KeyError:
            raise ConnectionError('Server returned invalid response during connection authentication.')

    def logout(self):
        if not self.connection._auth:
            return
        if not self.access_token:
            raise AnsibleConnectionFailure('Access token not found, could not perform logout operation.')

        payload = {
            'access_token': self.access_token
        }
        self.send_request(LOGOUT_URL, method='POST', data=payload, headers=BASE_HEADERS)

    def handle_httperror(self, exc):
        err_5xx = r'^5\d{2}$'
        # We raise AnsibleConnectionFailure without passing to the module, as 50x type errors indicate a problem
        # with the service, anything else will be handled by the caller

        handled_error = re.search(err_5xx, str(exc.code))
        if handled_error:
            raise AnsibleConnectionFailure('Could not connect to {0}: {1}'.format(self.connection._url, exc.reason))
        return False

    def send_request(self, url, method=None, **kwargs):
        body = kwargs.pop('data', None)
        data = json.dumps(body) if body else None

        try:
            self._display_request(method=method, data=data)
            response, response_data = self.connection.send(url, data, method=method, **kwargs)

            response_value = self._get_response_value(response_data)
            return dict(code=response.getcode(), contents=self._response_to_json(response_value))

        except HTTPError as e:
            return dict(code=e.code, contents=json.loads(e.read()))

    def _display_request(self, method, data):
        self.connection._log_messages(
            'F5 Cloud Services API Call: {0} {1} with data {2}'.format(method, self.connection._url, data)
        )

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            raise ConnectionError('Invalid JSON response: %s' % response_text)

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