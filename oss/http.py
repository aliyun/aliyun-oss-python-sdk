import requests


class Session(object):
    def __init__(self):
        self.session = requests.Session()

    def do_request(self, req):
        return Response(self.session.request(req.method, req.url,
                                             data=req.data,
                                             params=req.params,
                                             headers=req.headers,
                                             stream=False))


class Request(object):
    def __init__(self, method, url,
                 data=None,
                 params=None,
                 headers=None):
        self.method = method
        self.url = url
        self.data = data
        self.params = params or {}

        if headers is None:
            self.headers = {}
        else:
            self.headers = dict((k.lower(), v) for k, v in headers.items())


class Response(object):
    def __init__(self, response):
        self.response = response
        self.status = response.status_code
        self.headers = response.headers

    def read(self, amt=None):
        if amt is None:
            content = ''
            for chunk in self.response.iter_content(512 * 1024):
                content += chunk
            return content
        else:
            return self.response.iter_content(amt).next()
