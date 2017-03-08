## backup_file.py

특정 유저, 특정 포맷, 특정 용량의 오래된 파일을 한꺼번에 백업해주는 코드

Python3 환경에서 다음의 코드로 실행합니다.

```
from backup_file import BackupFile

BackupFile(token, before_n_days, file_type, local_backup_path, min_size, max_size).run()
```

* `token` 변수에 발급받은 [토큰값](https://api.slack.com/docs/oauth-test-tokens)을 넣습니다.
* `before_n_days` 변수에 며칠이 지난 파일부터 다운로드할 것인지 값을 설정합니다.
 * default value : 1
* `file_type` 변수에 다운로드할 파일의 타입을 설정합니다. (all / spaces / snippets / images / videos / audios / gdocs / zips / pdfs)
 * default value : 'all'
* `local_backup_path` 백업할 로컬 폴더의 path를 설정합니다.
* `min_size`와 `max_size`에 다운로드할 파일 용량의 범위를 설정합니다. (단위: KB)
 * `max_size`에 0의 값을 설정할 경우, max size에 제한을 두지 않습니다.
 * default value : 0, 0

## delete_file.py

특정 유저, 특정 포맷의 오래된 파일을 한꺼번에 지워주는 코드

Python3 환경에서 다음의 코드로 실행합니다.

```
from delete_file import DeleteFile

DeleteFile(token, before_n_days, file_type, exclude_starred_items, min_size, max_size).run
```

* `token` 변수에 발급받은 [토큰값](https://api.slack.com/docs/oauth-test-tokens)을 넣습니다.
* `before_n_days` 변수에 며칠이 지난 파일부터 지울 것인지 값을 설정합니다.
 * default value : 1
* `file_type` 변수에 지울 파일의 타입을 설정합니다. (all / spaces / snippets / images / videos / audios / gdocs / zips / pdfs)
 * default value : 'images'
* `exclude_starred_items` 변수에 누군가에게 Star된 아이템은 제외할지의 여부를 설정합니다.
 * default value : True
* `min_size`와 `max_size`에 삭제할 파일 용량의 범위를 설정합니다. (단위: KB)
 * `max_size`에 0의 값을 설정할 경우, max size에 제한을 두지 않습니다.
 * default value : 0, 0

## list_heavy_users.py

슬랙 그룹 내에서 업로드한 전체 파일 용량이 큰 순서대로, 유저와 해당 유저의 파일 용량을 출력하는 코드

* `token` 변수에 발급받은 [토큰값](https://api.slack.com/docs/oauth-test-tokens)을 넣습니다.
* `blind_username` 변수에 출력시 유저 이름 중간에 '.' 을 포함할지 여부를 설정합니다. (복사&붙여넣기시 유저 전체 호출 방지용)

## list_topn_files.py

슬랙 그룹 내에서 업로드한 파일 중 용량이 큰 순서대로, 해당 파일을 올린 유저와 파일 이름, 용량을 출력하는 코드

* `token` 변수에 발급받은 [토큰값](https://api.slack.com/docs/oauth-test-tokens)을 넣습니다.
* `topn` 변수에 상위 몇 개의 파일을 출력할 것인지 값을 설정합니다.
* 특정 유저의 파일만 받아오고 싶다면, `nickname` 변수에 Slack 닉네임을 넣습니다.
* `blind_username` 변수에 출력시 유저 이름 중간에 '.' 을 포함할지 여부를 설정합니다. (복사&붙여넣기시 유저 전체 호출 방지용)
