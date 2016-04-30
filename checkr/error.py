import sys


class CheckrError(Exception):

    def __init__(self, message=None, http_body=None, http_status=None,
                 json_body=None, headers=None):
        super(StripeError, self).__init__(message)

        if http_body and hasattr(http_body, 'decode'):
            try:
                http_body = http_body.decode('utf-8')
            except:
                http_body = ('<Could not decode body as utf-8.>')

        self._message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body
        self.headers = headers or {}
        self.request_id = self.headers.get('request-id', None)

    def __unicode__(self):
        if self.request_id is not None:
            msg = self._message or "<empty message>"
            return u"Request {0}: {1}".format(self.request_id, msg)
        else:
            return self._message

    def __str__(self):
        return unicode(self).encode('utf-8')


class APIError(CheckrError):
    pass

class APIConnectionError(CheckrError):
    pass

class AuthenticationError(CheckrError):
    pass
