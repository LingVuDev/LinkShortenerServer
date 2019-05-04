#!/usr/bin/env python3

import http.server
import string
import random
import os

import requests
from urllib.parse import unquote, parse_qs

memory = {}
serverport = 8000

form = '''<!DOCTYPE html>
<title>Bookmark Server</title>
<form method="POST">
    <label>URL:
        <input name="url">
    </label>
    <br>
    <label>Name:
        <input name="name">
    </label>
    <br>
    <button type="submit">Save it!</button>
</form>
<p>URIs I know about:
<pre>
{}
</pre>
'''


def CheckURI(uri, timeout=5):
    '''Check whether this URI is reachable, i.e. does it return a 200 OK?

    This function returns True if a GET request to uri returns a 200 OK, and
    False if that GET request returns any other response, or doesn't return
    (i.e. times out).
    '''
    res = requests.get(uri)
    return res.status_code == 200


class Shortener(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # A GET request will either be for / (the root path) or for /some-name.
        # Strip off the / and we have either empty string or a name.
        short = unquote(self.path[1:])
        if short:
            if short in memory:
                # Send a 301 redirect to the long URL.
                self.send_response(301)
                self.send_header('Location', memory[short]['url'])
                self.end_headers()

            else:
                # We don't know that name! Send a 404 error.
                self.send_response(404)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("I don't know '{}'.".format(short).encode())
        else:
            # Root path. Send the form.
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # List the known associations in the form.
            known = "\n".join("{} : {}".format(memory[key]['name'], self.address_string() + ":" +
                                               str(serverport) + "/" + key)
                              for key in sorted(memory.keys()))
            self.wfile.write(form.format(known).encode())

    def do_POST(self):
        # Decode the form data.
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)

        # Check that the user submitted the form fields.
        if "url" not in params or "name" not in params:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Your request was incomplete".encode())

        url = params["url"][0]
        name = params["name"][0]

        if CheckURI(url):
            randomString = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            memory[randomString] = {'url': url, 'name': name}
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

        else:
            # Didn't successfully fetch the long URI.
            self.send_response(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("I don't know '{}'.".format(url).encode())


if __name__ == '__main__':
    serverport = int(os.environ.get('PORT', 8000))
    server_address = ('', serverport)
    httpd = http.server.HTTPServer(server_address, Shortener)
    httpd.serve_forever()
