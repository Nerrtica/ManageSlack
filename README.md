# ManageSlack
* [Nerrtica](https://github.com/Nerrtica)에 의해 만들어진 Repository입니다.
* ZeroPage Slack을 관리하기 위해 짠 Python 코드들을 모아두었습니다.

## delete_file.py
특정 유저, 특정 포맷의 오래된 파일을 한꺼번에 지워주는 코드

* `token` 변수에 발급받은 [토큰값](https://api.slack.com/docs/oauth-test-tokens)을 넣습니다.
* `before_n_days` 변수에 며칠이 지난 파일부터 지울 것인지 값을 설정합니다.
* `file_type` 변수에 지울 파일의 타입을 설정합니다. (all / spaces / snippets / images / videos / audios / gdocs / zips / pdfs)
* `exclude_starred_items` 변수에 누군가에게 Star된 아이템은 제외할지의 여부를 설정합니다.
* `local_backup_path` *변수에 삭제하기 전 백업을 원한다면, 백업할 폴더의 path를 설정합니다.* (구현 예정)

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