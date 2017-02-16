#-*- coding:utf-8 -*-

import requests
import time
import json
import os

# get your token from here -> https://api.slack.com/docs/oauth-test-tokens
token = ''
# download files uploaded before n days
before_n_days = 1
# file_type = all / spaces / snippets / images / videos / audios / gdocs / zips / pdfs
file_type = 'all'
# local backup directory path
local_backup_path = ''
# backup files between min-max size. (KB)
# if max_size == 0: backup files without max limit.
backup_min_size = 0
backup_max_size = 0

def get_my_id_nick():
    params = {
        'token': token
    }
    uri = 'https://slack.com/api/auth.test'
    response = requests.get(uri, params=params)
    text = json.loads(response.text)
    return (text['user_id'], text['user'])

def list_files(before_n_days=30, user_id='', file_type='all'):
    """
    :param before_n_days: n일 이전에 올라온 파일만 받아옴. default=30
    :param user_id: 특정 유저가 업로드한 파일만 받아옴. 빈 문자열일 경우 모든 유저의 파일을 받아옴. default=''
    :param file_type: 특정 타입의 파일만 받아옴. default='all'
                      * 'all': All files
                      * 'spaces: Posts
                      * 'snippets': Snippets
                      * 'images': Image files
                      * 'videos': Video files
                      * 'audios': Audio files
                      * 'gdocs': Google docs
                      * 'zips': Zip files
                      * 'pdfs': PDF files
    """
    types = file_type
    if file_type == 'videos' or file_type == 'audios':
        types = 'all'
    
    params = {
        'token': token,
        'ts_to': int(time.time()) - before_n_days * 24 * 60 * 60,
        'ts_from': 0,
        'count': 1000,
        'types': types,
    }
    if user_id != '':
        params['user'] = user_id
        
    uri = 'https://slack.com/api/files.list'
    response = requests.get(uri, params=params)
    pages_num = json.loads(response.text)['paging']['pages']
    
    result_files = []
    for i in range(1, pages_num+1):
        params['page'] = i
        response = requests.get(uri, params=params)
        files = json.loads(response.text)['files']
        
        for file in files:
            # Video & Audio files 수동 
            if file_type == 'videos' or file_type == 'audios':
                if file['mimetype'].split('/')[0] != file_type[:-1]:
                    continue

            result_files.append(file)
    
    return result_files

def backup_files(files, local_backup_path=''):
    count = 0
    num_files = len(files)
    headers = {'Authorization': 'Bearer ' + token}

    if local_backup_path[-1] != '/':
        local_backup_path += '/'
    try:
        os.stat(local_backup_path)
    except:
        print('No such directory')

    for file in files:
        count = count + 1

        try:
            # size check
            if (file['size'] / 1024) < backup_min_size or (backup_max_size != 0 and (file['size'] / 1024) > backup_max_size):
                print (count, "of", num_files, "-", file['title'], 'pass by size')
                continue

            url = file['url_private_download']
            path = local_backup_path + file['id'] + '_' + url.split('/')[-1]

            r = requests.get(url, headers=headers)
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: f.write(chunk)

            print (count, "of", num_files, "-", file['title'], 'ok')

        except:
            print (count, "of", num_files, "-", file['title'], 'pass by error')

userId, nickname = get_my_id_nick()

files = list_files(before_n_days=before_n_days, user_id=userId, file_type=file_type)
print('import', len(files), 'files')

backup_files(files, local_backup_path=local_backup_path)