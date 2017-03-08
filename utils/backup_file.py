import requests
import time
import json
import os


class BackupFile:

    def __init__(self, token, before_n_days=1, file_type='all', local_backup_path='', min_size=0, max_size=0):
        self.token = token
        self.before_n_days = before_n_days
        self.file_type = file_type

        if local_backup_path[-1] != '/':
            local_backup_path += '/'
        try:
            os.stat(local_backup_path)
        except FileNotFoundError:
            print('No such directory : '+local_backup_path)
            raise FileNotFoundError
        self.local_backup_path = local_backup_path
        self.min_size = min_size
        self.max_size = max_size

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
                # Video & Audio files 수동
                if self.file_type == 'videos' or self.file_type == 'audios':
                    if file.get('mimetype', 'foo/foo').split('/')[0] != self.file_type[:-1]:
                        continue

                result_files.append(file)

        return result_files

    def backup_files(self, files):
        count = 0
        num_files = len(files)
        headers = {'Authorization': 'Bearer '+self.token}

        for file in files:
            try:
                # size check
                if (file['size'] / 1024) < self.min_size or \
                        (self.max_size != 0 and (file['size'] / 1024) > self.max_size):
                    continue

                url = file.get('url_private_download', '/')
                path = self.local_backup_path + file['id'] + '_' + url.split('/')[-1]

                r = requests.get(url, headers=headers)
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                count += 1
            except:
                continue

        return num_files, count

    def run(self):
        files = self.list_files()
        num_files, backup_count = self.backup_files(files)

        return num_files, backup_count
