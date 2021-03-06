import os
import string
import random
import urllib
import mimetypes
import base64
import urlparse
import getpass
import httplib2
from anyjson import deserialize

DEFAULT_ENDPOINT = 'http://redux.divvyshot.com/api/v2/json/'
#DEFAULT_ENDPOINT = 'http://localhost:8080/api/v2/json/'

class BasicAuth(object):

    def __init__(self, username, password, host, port):
        """Builds class. Creates authentication and connection objects."""
        auth = "Basic %s" % base64.encodestring("%s:%s" % (username, password)).strip()
        self.authentication = {"Authorization": auth}
        self.base = 'http://'+host
        if port:
            self.base += ':'+str(port)

        self.client = httplib2.Http()
        self.client.add_credentials(username, password)

    def get(self, path):
        """Generates and executes authenticated GET request."""
        resp, content = self.client.request(self.base+path, "GET", headers=self.authentication)
        return content

    def _send(self, method, path, data):
        """Generates and executes authenticated POST request."""
        headers = {'Content-Type':'application/x-www-form-urlencoded'}
        headers.update(self.authentication)
        resp, content = self.client.request(self.base+path, method,
                                            body=urllib.urlencode(data),
                                            headers=headers)
        return content

    def put(self, path, data):
        return self._send("PUT", path, data)

    def post(self, path, data):
        """Generates and executes authenticated POST request."""
        return self._send("POST", path, data)

    def post_file(self, path, data, files):
        """Post a file."""
        boundary = ''.join(random.choice(string.letters) for i in xrange(30))
        lines = []
        for name, value in data.iteritems():
            lines.extend(('--'+boundary,
                          'Content-Disposition: form-data; name="%s"' % name,
                          '', value))
        for name, f in files.iteritems():
            lines.extend(('--'+boundary,
                          'Content-Disposition: form-data; name="%s"; filename="%s"' % (name,
                                                                                        os.path.basename(f.name)),
                          'Content-Type: %s'%(mimetypes.guess_type(f.name)[0] or 'application/octet-stream'),
                          '', f.read()))
        lines.extend(('--%s--' % boundary, ''))
        body = '\r\n'.join(lines)
        headers = {'Content-Type':'multipart/form-data; boundary=' + boundary,
                   'Content-Length':str(len(body))}
        headers.update(self.authentication)
        resp, content = self.client.request(self.base+path, "POST",
                                            body=body, headers=headers)
        return content


class DivvyshotClient(object):

    def __init__(self, endpoint=DEFAULT_ENDPOINT, username=None, password=None):
        self.endpoint = endpoint

        username = username or raw_input("Divvyshot username: ")
        password = password or getpass.getpass("Divvyshot password: ")
        parsed = urlparse.urlparse(endpoint)
        self.client = BasicAuth(username, password, parsed.hostname, parsed.port)

    def create_event(self, name='', description=''):
        return deserialize(self.client.post('/api/v2/json/event/',
                                            {'name':name, 'description':description}))

    def create_photo(self, event, filename):
        event_path = '/api/v2/json/event/%s/photo/' % event
        return deserialize(self.client.post_file(event_path, {}, {'image':open(filename, 'rb')}))

    def update_photo(self, photo, name=''):
        photo_path = '/api/v2/json/photo/%s/' % photo
        return deserialize(self.client.put(photo_path, {'name':name}))
