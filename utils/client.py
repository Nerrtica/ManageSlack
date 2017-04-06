from flask import Flask, request
import urllib.parse
import requests
import requests.auth
from delete_file import DeleteFile


class Client:
    def __init__(self, CLIENT_ID, CLIENT_SECRET, PORT):
        self.CLIENT_ID = CLIENT_ID
        self.CLIENT_SECRET = CLIENT_SECRET
        self.PORT = PORT

    def delete_file(self, token):
        _delete_file = DeleteFile(token)
        num_files, deleted_count = _delete_file.run()
        return 'total %d files - %d files deleted.' % (num_files, deleted_count)

    def get_token(self, code):
        client_auth = requests.auth.HTTPBasicAuth(self.CLIENT_ID, self.CLIENT_SECRET)
        post_data = {'code': code}
        response = requests.post("https://slack.com/api/oauth.access?",
                                 auth=client_auth,
                                 data=post_data)
        token_json = response.json()
        return token_json['access_token']

    def make_delete_file_authorization_url(self):
        params = {"client_id": self.CLIENT_ID,
                  "scope": 'files:read, files:write:user'}
        url = 'https://slack.com/oauth/authorize?' + urllib.parse.urlencode(params)
        return url

    def run(self):
        app = Flask(__name__)

        @app.route('/delete_file')
        def homepage():
            text = '<a href="%s"><img src="https://api.slack.com/img/sign_in_with_slack.png" /></a>'
            return text % self.make_delete_file_authorization_url()

        @app.route('/oauth')
        def oauth():
            error = request.args.get('error', '')
            if error:
                return 'Error: ' + error
            code = request.args.get('code')
            token = self.get_token(code)
            msg = self.delete_file(token)
            return msg

        app.run(debug=False, port=self.PORT)
