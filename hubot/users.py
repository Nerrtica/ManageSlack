#-*- coding:utf-8 -*-
from collections import defaultdict
import dill


class Users:
    """슬랙 그룹 내 유저들의 정보를 저장하는 클래스.
    
    users: {'id': {'grade': Integer, 'gold': Integer, 'is_ignored': Boolean, 'is_admin': Boolean}}
    """

    def __init__(self, commands_file):
        self.users = None
        self.users_file = commands_file
        self.load()

    def load(self):
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = dill.load(f)
        except FileNotFoundError:
            self.users = defaultdict(lambda: {'grade': 0, 'gold': 0, 'is_ignored': False, 'is_admin': False})

    def save(self):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            dill.dump(self.users, f)
