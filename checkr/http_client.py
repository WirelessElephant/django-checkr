import os
import sys
import textwrap

# This library requires Requests. Most Django/Python
# libraries also require Requests, so this dependency
# shouldn't be a problem.

import requests


class HttpClient(object):

    def __init__(self, verify_ssl_certs=True):
        self._verify_ssl_certs = verify_ssl_certs

    def request(self, method, url, headers, post_data=None):
        raise NotImplementedError(
            'HttpClient subclasses must implement "request"')


class RequestsClient(HTTPClient):
    name = 'requests'

    def request(self, method, url, headers, post_data=None):
        kwargs = {}

        if self._verify_ssl_certs:
            kwargs['verify'] = requests.certs.where()
        else:
            kwargs['verify'] = False

        try:
            try:
                result = requests.request(method,
                                          url,
                                          headers=headers,
                                          data=post_data,
                                          timeout=80,
                                          **kwargs)
            except TypeError as e:
                raise TypeError(
                    'Warning: It looks like your installed version of the '
                    '"requests" library is not compatible with this library '
                    'usage thereof. (HINT: The most likely cause is that '
                    'your "requests" library is out of date. You can fix '
                    'that by running "pip install -U requests".) The '
                    'underlying error was: %s' % (e,))

            # This causes the content to actually be read, which could cause
            # e.g. a socket timeout. TODO: The other fetch methods probably
            # are susceptible to the same and should be updated.
            content = result.content
            status_code = result.status_code
        except Exception as e:
            # Would catch just requests.exceptions.RequestException, but can
            # also raise ValueError, RuntimeError, etc.
            self._handle_request_error(e)
        return content, status_code, result.headers

     def _handle_request_error(self, e):
        if isinstance(e, requests.exceptions.RequestException):
            msg = ("Unexpected error communicating with Checkr.  "
                   "If this problem persists, let the gents know at "
                   "hello@checkr.com")
            err = "%s: %s" % (type(e).__name__, str(e))
        else:
            msg = ("Unexpected error communicating with Checkr. "
                   "It looks like there's probably a configuration "
                   "issue locally.")
            err = "A %s was raised" % (type(e).__name__,)
            if str(e):
                err += " with error message %s" % (str(e),)
            else:
                err += " with no error message"
        msg = textwrap.fill(msg) + "\n\n(Network error: %s)" % (err,)
        raise error.APIConnectionError(msg)

def get_default_http_client(*args, **kwargs):
    if requests:
        client = RequestsClient

    # Open to other http request libraries, but we'll use requests for now.
    return client(*args, **kwargs)
