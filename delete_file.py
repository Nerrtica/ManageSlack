import requests
import time
import json


class DeleteFile:

    def __init__(self, token, before_n_days=1, file_type='images', exclude_starred_items=True):
        self.token = token
        self.before_n_days = before_n_days
        self.file_type = file_type
        self.exclude_starred_items = exclude_starred_items

    def get_my_id_nick(self):
        params = {
            'token': self.token
        }
        uri = 'https://slack.com/api/auth.test'
        response = requests.get(uri, params=params)
        text = json.loads(response.text)
        return text['user_id'], text['user']

    def list_files(self):
        userid, nickname = self.get_my_id_nick()
        types = self.file_type
        if self.file_type == 'videos' or self.file_type == 'audios':
            types = 'all'

        params = {
            'token': self.token,
            'ts_to': int(time.time()) - self.before_n_days * 24 * 60 * 60,
            'ts_from': 0,
            'count': 1000,
            'types': types,
        }
        if userid != '':
            params['user'] = userid

        uri = 'https://slack.com/api/files.list'
        response = requests.get(uri, params=params)
        pages_num = json.loads(response.text)['paging']['pages']

        result_files = []
        for i in range(1, pages_num + 1):
            params['page'] = i
            response = requests.get(uri, params=params)
            files = json.loads(response.text)['files']

            for file in files:
                # Starred items 제외
                if self.exclude_starred_items:
                    if file.get('is_starred', False):
                        continue

                # Pinned items 제외
                if len(file.get('pinned_to', [])) > 0:
                    continue

                # Video & Audio files 수동
                if self.file_type == 'videos' or self.file_type == 'audios':
                    if file.get('mimetype', 'foo/foo').split('/')[0] != self.file_type[:-1]:
                        continue

                result_files.append(file)

        return result_files

    def delete_files(self, files):
        count = 0
        num_files = len(files)

        for file in files:
            params = {
                'token': self.token,
                'file': file['id']
            }

            uri = 'https://slack.com/api/files.delete'
            response = requests.get(uri, params=params)
            if json.loads(response.text).get('ok', False):
                count += 1

        return num_files, count

    def run(self):
        files = self.list_files()
        num_files, deleted_count = self.delete_files(files)

        return num_files, deleted_count
