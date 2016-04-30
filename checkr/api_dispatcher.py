import urlparse
import urllib
import checkr
from checkr import error, http_client
from checkr.multipart_data_generator import MultipartDataGenerator

def _build_api_url(url, query):
    scheme, netloc, path, base_query, fragment = urlparse.urlsplit(url)

    if base_query:
        query = '%s&%s' % (base_query, query)

    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))

class APIDispatcher(object):

    def __init__(self, key=None, client=None):
        self.api_key = key or checkr.api_key

        from checkr import verify_ssl_certs as verify

        self._client = client or checkr.default_http_client or \
            http_client.get_default_http_client(verify_ssl_certs=verify)

    def request(self, method, url, params=None, headers=None):
        rbody, rcode, rheaders, my_api_key = self.request_raw(
            method.lower(), url, params, headers)
        resp = self.interpret_response(rbody, rcode, rheaders)
        return resp, my_api_key

    def handle_api_error(self, rbody, rcode, resp, rheaders):
        raise error.APIError(err.get('message'), rbody, rcode, resp, rheaders)

    def interpret_response(self, rbody, rcode, rheaders):
        try:
            if hasattr(rbody, 'decode'):
                rbody = rbody.decode('utf-8')
            resp = util.json.loads(rbody)
        except Exception:
            raise error.APIError(
                "Invalid response body from API: %s "
                "(HTTP response code was %d)" % (rbody, rcode),
                rbody, rcode, rheaders)
        if not (200 <= rcode < 300):
            self.handle_api_error(rbody, rcode, resp, rheaders)
        return resp

    def request_raw(self, method, url, params=None, supplied_headers=None):
        """
        Mechanism for issuing an API call
        """
        from checkr import api_version

        if self.api_key:
            my_api_key = self.api_key
        else:
            from checkr import api_key
            my_api_key = api_key

        if my_api_key is None:
            raise error.AuthenticationError(
                'No API key provided. (HINT: set your API key using '
                '"checkr.api_key = <API-KEY>").')

        abs_url = '%s%s' % (self.api_base, url)

        encoded_params = urllib.urlencode(list(_api_encode(params or {})))

        if method == 'get' or method == 'delete':
            if params:
                abs_url = _build_api_url(abs_url, encoded_params)
            post_data = None
        elif method == 'post':
            if supplied_headers is not None and \
                    supplied_headers.get("Content-Type") == \
                    "multipart/form-data":
                generator = MultipartDataGenerator()
                generator.add_params(params or {})
                post_data = generator.get_post_data()
                supplied_headers["Content-Type"] = \
                    "multipart/form-data; boundary=%s" % (generator.boundary,)
            else:
                post_data = encoded_params
        else:
            raise error.APIConnectionError(
                'Unrecognized HTTP method %r.  This may indicate a bug in the '
                'Stripe bindings.  Please contact support@stripe.com for '
                'assistance.' % (method,))

        ua = {
            'bindings_version': version.VERSION,
            'lang': 'python',
            'publisher': 'Walkio',
            'httplib': self._client.name,
        }
        for attr, func in [['lang_version', platform.python_version],
                           ['platform', platform.platform],
                           ['uname', lambda: ' '.join(platform.uname())]]:
            try:
                val = func()
            except Exception as e:
                val = "!! %s" % (e,)
            ua[attr] = val

        headers = {
            'User-Agent': 'Checkr/v1 PythonBindings/%s' % (version.VERSION,),
            'Authorization': 'Bearer %s' % (my_api_key,)
        }

        if self.stripe_account:
            headers['Stripe-Account'] = self.stripe_account

        if method == 'post':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        if api_version is not None:
            headers['Stripe-Version'] = api_version

        if supplied_headers is not None:
            for key, value in supplied_headers.items():
                headers[key] = value

        rbody, rcode, rheaders = self._client.request(
            method, abs_url, headers, post_data)

        util.logger.info('%s %s %d', method.upper(), abs_url, rcode)
        util.logger.debug(
            'API request to %s returned (response code, response body) of '
            '(%d, %r)',
            abs_url, rcode, rbody)
        return rbody, rcode, rheaders, my_api_key
