#-*- coding:utf-8 -*-


class Users:
    """슬랙 그룹 내 유저들의 정보를 저장하는 클래스.
    
    users: {'id': {'grade': Integer, 'gold': Integer, 'is_ignored': Boolean, 'is_admin': Boolean}}
    """

    def __init__(self, commands_file):
        self.users = {}
        self.users_file = commands_file
        self.load()

    def load(self):
        with open(self.users_file, 'r', encoding='utf-8') as f:
            id = None
            for line in f:
                line = line.strip()
                if 'id' in line:
                    self.users[line[len('id : '):]] = {}
                elif 'grade' in line:
                    self.users.get(id, {})['grade'] = int(line[len('grade : '):])
                elif 'gold' in line:
                    self.users.get(id, {})['gold'] = int(line[len('gold : '):])
                elif 'is_ignored' in line:
                    self.users.get(id, {})['is_ignored'] = bool(line[len('is_ignored : '):])
                elif 'is_admin' in line:
                    self.users.get(id, {})['is_admin'] = bool(line[len('is_admin : '):])

    def save(self):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            for id, info  in self.users.items():
                f.write('id : %s\n' % id)
                f.write('grade : %d\n' % info.get('grade', 0))
                f.write('gold : %d\n' % info.get('gold', 0))
                f.write('is_ignored : %d\n' % int(info.get('is_ignored', 1)))
                f.write('is_admin : %d\n' % int(info.get('is_admin', 0)))
