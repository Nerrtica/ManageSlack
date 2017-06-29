#-*- coding:utf-8 -*-

import time
import json
import random
import datetime
import asyncio
import websockets
from slacker import Error
from slacker import Slacker
from collections import defaultdict

from commands import Commands


class FactBot:
    """

    """

    def __init__(self, token, admin_name, default_path, bot_channel_name, notice_channel_name):
        self.token = token
        self.slacker = Slacker(self.token)
        self.default_path = default_path
        self.bot_channel_name = bot_channel_name
        self.bot_channel_id = [c_id['id'] for c_id in self.slacker.channels.list().body['channels']
                               if c_id['name'] == bot_channel_name[1:]][0]
        self.notice_channel_name = notice_channel_name
        self.notice_channel_id = [c_id['id'] for c_id in self.slacker.channels.list().body['channels']
                                  if c_id['name'] == notice_channel_name[1:]][0]
        self.ignore_channel_list = []
        self.load_ignore_channel_list()
        self.ignore_user_list = []
        self.load_ignore_user_list()
        self.id = self.slacker.auth.test().body['user_id']
        self.admin_id = self.get_user_id(admin_name)

        self.keywords = defaultdict(lambda: set())
        try:
            with open(self.default_path+'data/keyword_list.txt', 'r', encoding='utf-8') as f:
                keyword = 'NONE'
                for line in f.readlines():
                    line = line.strip()
                    if line[:10] == 'keyword : ':
                        keyword = line[10:]
                    elif line != '':
                        self.keywords[keyword].add(line)
        except FileNotFoundError:
            pass

        self.kingname_alias = dict()
        try:
            with open(self.default_path+'data/kingname_alias.txt', 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line.strip().split(maxsplit=1)
                    self.kingname_alias[line[0]] = line[1]
        except FileNotFoundError:
            pass

        self.slacking_dict = defaultdict(lambda: defaultdict(lambda: 0))
        self.statistics_dict = defaultdict(lambda: defaultdict(lambda: 0))

        self.commands = Commands(self.default_path+'commands.data')
        self.admin_commands = Commands(self.default_path+'admin_commands.data')
        self.hello_message = 'Factbot Start running!'
        self.error_message = 'Error Error <@nerrtica>'
        self.stop_message = 'Too many Error... <@nerrtica>'
        self.kill_message = 'Bye Bye!'
        self.die_messages = [':innocent: :gun:', '으앙듀금', '꿲', '영웅은 죽지않아요']

        self.ALIVE = 0
        self.RESTART = 1
        self.DIE = 2
        self.status = self.ALIVE

        self.version = '1.4.5'

    def run(self):
        async def execute_bot():
            response = self.slacker.rtm.start()
            sock_endpoint = response.body['url']
            ws = await websockets.connect(sock_endpoint)
            now = time.localtime()
            day = '%4d' % now.tm_year + '%02d' % now.tm_mon + '%02d' % now.tm_mday
            today = now.tm_mday
            error_count = 0
            self.status = self.ALIVE

            if len(list(self.slacking_dict.keys())) == 0:
                self.slacking_dict = self.get_slacking_counts(day)
            if len(list(self.statistics_dict.keys())) == 0:
                self.statistics_dict = self.get_statistics_counts(day)
            self.slacker.chat.post_message(self.notice_channel_id, self.hello_message, as_user=True)
            message_json = {}

            while True:
                if self.status != self.ALIVE:
                    return

                try:
                    if error_count >= 5:
                        self.slacker.chat.post_message(self.notice_channel_id, self.stop_message, as_user=True)
                        self.save_slacking_counts(day)
                        self.save_statistics_counts(day)
                        if now.tm_mday != today:
                            self.print_slacking()
                            self.slacking_dict = defaultdict(lambda: defaultdict(lambda: 0))
                            self.statistics_dict = defaultdict(lambda: defaultdict(lambda: 0))
                        return

                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    except asyncio.TimeoutError:
                        continue

                    message_json = json.loads(message)

                    # Print Slacking
                    now = time.localtime()
                    if now.tm_mday != today:
                        self.print_slacking()
                        self.save_slacking_counts(day)
                        self.save_statistics_counts(day)

                        today = now.tm_mday
                        day = '%04d' % now.tm_year + '%02d' % now.tm_mon + '%02d' % now.tm_mday
                        self.slacking_dict = defaultdict(lambda: defaultdict(lambda: 0))
                        self.statistics_dict = defaultdict(lambda: defaultdict(lambda: 0))
                        error_count = 0

                    full_command = self.get_full_command(message_json)
                    if full_command:
                        # Admin Command Message
                        admin_command_info = self.admin_commands.get_command(full_command)
                        if admin_command_info.get('is_command', False) and message_json.get('user') == self.admin_id:
                            done = self.react_admin_command(message_json, admin_command_info, day)
                            if done:
                                continue
                        # Command Message
                        command_info = self.commands.get_command(full_command)
                        if command_info.get('is_command', False):
                            self.react_command(message_json, command_info, day)
                            continue
                        else:
                            if len(command_info.get('main_command_candidates', [])) != 0:
                                answer = '혹시 이 명령어를 쓰려고 하셨나요? `%s`' % \
                                         ', '.join(command_info['main_command_candidates'])
                                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id),
                                                               answer, as_user=True)
                                continue
                            elif command_info.get('main_command', None):
                                answer = '명령어의 사용법이 틀린 것 같아요. :cry:'
                                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id),
                                                               answer, as_user=True)
                                self.print_help(message_json, {'contents': command_info['main_command']})
                                continue

                    if self.is_keyword(message_json):
                        keyword = message_json.get('text')[1:].replace(' ', '')
                        replies = self.keywords.get(keyword)
                        if len(replies) == 0:
                            pass
                        else:
                            answer = list(replies)[random.randrange(len(replies))]
                            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id),
                                                           answer, as_user=True)

                    # Slacking Count
                    self.slacking_count(message_json)
                    self.statistics_count(message_json)

                except:
                    self.slacker.chat.post_message(self.notice_channel_id, self.error_message, as_user=True)
                    for im in self.slacker.im.list().body['ims']:
                        if im['user'] == self.admin_id:
                            self.slacker.chat.post_message(im['id'], str(message_json), as_user=True)
                    error_count += 1
                    if now.tm_mday != today:
                        error_count = 5
                    continue

        for i in range(5):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.get_event_loop().run_until_complete(execute_bot())

            if self.status == self.DIE:
                self.slacker.chat.post_message(self.notice_channel_id, self.kill_message, as_user=True)
                return

            time.sleep(15)

    def get_full_command(self, message_json):
        """If a user calls factbot, get bot command string.

        :param message_json: Slack message json
        :return: full command string
        """
        if message_json.get('type', '') != 'message':
            return None
        if 'subtype' in message_json.keys():
            return None
        if 'bot_id' in message_json.keys():
            return None
        if message_json.get('text', '') == '':
            return None

        if message_json.get('text', '')[:8] == 'factbot ':
            full_command = message_json.get('text', '')[8:]
        elif message_json.get('text', '')[:len(self.id)+4] == '<@%s> ' % self.id:
            full_command = message_json.get('text', '')[len(self.id)+4:]
        else:
            return None
        return full_command.strip()

    def is_keyword(self, message_json):
        if message_json.get('type') != 'message':
            return False
        if 'subtype' in message_json.keys():
            return False
        if 'bot_id' in message_json.keys():
            return False
        if message_json.get('text', '') == '':
            return False
        if message_json.get('text', '')[0] == '!' \
                and message_json.get('text', '')[1:].replace(' ', '') in self.keywords.keys():
            return True

    def slacking_count(self, message_json):
        """Count user's message for Today's Slacking.

        :param message_json: Slack message json
        """
        if message_json.get('type') != 'message':
            return
        if 'subtype' in message_json.keys():
            return
        if 'bot_id' in message_json.keys():
            return
        if message_json.get('user') in self.ignore_user_list:
            return

        self.slacking_dict[message_json.get('channel', '')][message_json.get('user', '')] += 1

    def statistics_count(self, message_json):
        if message_json.get('type') != 'message':
            return
        if 'subtype' in message_json.keys():
            return
        if 'bot_id' in message_json.keys():
            return
        if message_json.get('user') in self.ignore_user_list:
            return

        hour = time.localtime(float(message_json.get('ts', time.time()))).tm_hour
        self.statistics_dict[message_json.get('channel', '')][hour] += 1

    def react_command(self, message_json, command_info, day):
        if message_json.get('channel') in self.get_im_id_list():
            pass
        elif message_json.get('channel') in self.get_group_id_list():
            pass
        elif not self.get_channel_info(message_json.get('channel')).get('is_member', False):
            return

        main_command = command_info.get('main_command')

        if main_command == 'help':
            self.print_help(message_json, command_info)

        elif main_command == 'ping':
            answer = '<@%s> pong' % message_json.get('user', 'UNDEFINED')
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        elif main_command == 'count':
            self.swap_count_auth(message_json, command_info)

        elif main_command == 'mute':
            self.swap_ignore_channel(message_json, command_info)

        elif main_command == 'stats':
            self.print_stats(message_json, command_info, day)

        elif main_command == 'keyword':
            sub_command = command_info.get('sub_command')
            if sub_command == 'add' or sub_command == 'delete':
                self.manage_keyword(message_json, command_info)
            elif sub_command == 'show':
                keyword = command_info.get('contents')
                replies = self.keywords.get(keyword.replace(' ', ''), [])
                if len(replies) == 0:
                    answer = '%s 키워드에 대한 리액션이 존재하지 않아요.' % keyword
                else:
                    answer = ''
                    for i, reply in enumerate(replies):
                        answer += '%d : %s\n' % (i+1, reply)
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        elif main_command == 'kingname':
            sub_command = command_info.get('sub_command')
            if sub_command == 'set' or sub_command == 'init':
                self.set_kingname(message_json, command_info)
            elif sub_command == 'show':
                im_id_list = self.get_im_id_list()
                group_id_list = self.get_group_id_list()
                if self.kingname_alias.get(message_json.get('channel'), '') != '':
                    answer = '<#%s> 채널의 슬랙왕 호칭은 %s에요.' % \
                             (message_json.get('channel'), self.kingname_alias[message_json.get('channel')])
                elif message_json.get('channel') in im_id_list:
                    answer = '<@%s>! 언제나 당신이 슬랙왕인데 다른게 필요한가요? :pika_smile:' % message_json.get('user')
                elif message_json.get('channel') in group_id_list:
                    answer = 'private channel에서는 슬랙왕이 출력되지 않아요 :sob:'
                else:
                    answer = '아직 <#%s> 채널의 슬랙왕 호칭이 없어요.' % (message_json.get('channel'))
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        elif main_command == 'die':
            answer = self.die_messages[random.randrange(len(self.die_messages))]
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        elif main_command == 'version':
            answer = 'Factbot version %s' % self.version
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        elif main_command == 'echo':
            answer = command_info.get('contents')
            try:
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            except Error:
                answer = '절 테스트하시려는 건가요? 그런 얕은 수에는 넘어가지 않아요.'
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

    def react_admin_command(self, message_json, command_info, day):
        main_command = command_info.get('main_command')

        if main_command == 'admin':
            if command_info.get('sub_command') == 'help':
                self.print_admin_help(message_json, command_info)
                return True

        elif main_command == 'kill':
            self.status = self.DIE
            return True

        elif main_command == 'restart':
            self.status = self.RESTART
            return True

        elif main_command == 'save':
            if command_info.get('contents', '') != '':
                day = command_info.get('contents')
            self.save_slacking_counts(day)
            self.save_statistics_counts(day)
            answer = '%s 카운트 저장 완료' % day
            self.slacker.chat.post_message(message_json.get('channel', self.notice_channel_id), answer, as_user=True)
            return True

        elif main_command == 'load':
            if command_info.get('contents', '') != '':
                day = command_info.get('contents')
            self.slacking_dict = self.get_slacking_counts(day)
            self.statistics_dict = self.get_statistics_counts(day)
            answer = '%s 카운트 로드 완료' % day
            self.slacker.chat.post_message(message_json.get('channel', self.notice_channel_id), answer, as_user=True)
            return True

        elif main_command == 'crawl':
            if command_info.get('contents', '') != '':
                day = command_info.get('contents')
            self.slacking_dict = defaultdict(lambda: defaultdict(lambda: 0))
            self.statistics_dict = defaultdict(lambda: defaultdict(lambda: 0))
            self.get_past_count_history(day)
            answer = '%s 카운트 크롤링 완료' % day
            self.slacker.chat.post_message(message_json.get('channel', self.notice_channel_id), answer, as_user=True)
            return True

        elif main_command == 'print':
            if command_info.get('sub_command') == 'slacking':
                self.print_slacking()
                return True

        elif main_command == 'echo':
            contents = command_info.get('contents')
            channel_id = contents.split(' ')[0][2:contents.find('|')]
            if channel_id in self.get_channel_id_list():
                self.slacker.chat.post_message(channel_id, ' '.join(contents.split(' ')[1:]), as_user=True)
                return True
        return False

    def print_help(self, message_json, command_info):
        if command_info.get('contents', '') == '':
            answer = '※ factbot을 사용하기 위해서는 각 채널에 초대를 하시기 바랍니다.\n\n'
            answer += 'factbot은 각 채널 별로 매일 가장 슬랙 사용량이 높은 유저를 슬랙왕으로 추대합니다 :innocent: \n'
            answer += '사용량 통계는 *사용자별, 날짜별 메시지 count* 로만 추정하며, 지난 정보 저장을 위해 로컬에 파일로 저장됩니다.'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

            answer = ''
            for command in self.commands.commands:
                main_command = command['main_command']
                for sub_info in command['sub_info']:
                    full_command = main_command
                    sub_command = sub_info['sub_command']
                    if sub_command != 'None':
                        full_command += ' ' + sub_command
                    contents = sub_info['contents']
                    if contents != 'None':
                        full_command += ' ' + contents
                    answer += 'factbot %s - %s\n' % (full_command, sub_info['description'])
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

            answer = '기능 추가 및 버그 수정은 GitHub Repository에 Pull Request로 보내주시기 바랍니다.\n'
            answer += 'Repository : https://github.com/Nerrtica/ManageSlack'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        else:
            main_command = command_info.get('contents')
            command_idx = self.commands.get_main_command_index(main_command)
            if command_idx != -1:
                answer = ''
                for sub_info in self.commands.commands[command_idx]['sub_info']:
                    full_command = main_command
                    sub_command = sub_info['sub_command']
                    if sub_command != 'None':
                        full_command += ' ' + sub_command
                    contents = sub_info['contents']
                    if contents != 'None':
                        full_command += ' ' + contents
                    answer += 'factbot %s - %s\n' % (full_command, sub_info['description'])
            else:
                answer = 'no such command : factbot %s' % main_command
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

    def print_admin_help(self, message_json, command_info):
        if command_info.get('contents', '') == '':
            answer = ''
            for command in self.admin_commands.commands:
                main_command = command['main_command']
                for sub_info in command['sub_info']:
                    full_command = main_command
                    sub_command = sub_info['sub_command']
                    if sub_command != 'None':
                        full_command += ' ' + sub_command
                    contents = sub_info['contents']
                    if contents != 'None':
                        full_command += ' ' + contents
                    answer += 'factbot %s - %s\n' % (full_command, sub_info['description'])
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

        else:
            main_command = command_info.get('contents')
            command_idx = self.admin_commands.get_main_command_index(main_command)
            if command_idx != -1:
                answer = ''
                for sub_info in self.admin_commands.commands[command_idx]['sub_info']:
                    full_command = main_command
                    sub_command = sub_info['sub_command']
                    if sub_command != 'None':
                        full_command += ' ' + sub_command
                    contents = sub_info['contents']
                    if contents != 'None':
                        full_command += ' ' + contents
                    answer += 'factbot %s - %s\n' % (full_command, sub_info['description'])
            else:
                answer = 'no such command : factbot %s' % main_command
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

    def swap_count_auth(self, message_json, command_info):
        sub_command = command_info.get('sub_command')
        if sub_command == 'start':
            try:
                self.ignore_user_list.remove(message_json.get('user'))
                self.save_ignore_user_list()
                answer = '다시 <@%s> 님의 메시지 개수를 저장하기 시작했어요.' % message_json.get('user', 'UNDEFINED')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            except ValueError:
                answer = '이미 <@%s> 님의 메시지 개수를 저장하고 있어요.' % message_json.get('user', 'UNDEFINED')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return True
        elif sub_command == 'stop':
            if self.ignore_user_list.count(message_json.get('user')) == 0:
                self.ignore_user_list.append(message_json.get('user'))
                self.save_ignore_user_list()
                answer = '더 이상 <@%s> 님의 메시지 개수를 저장하지 않아요.' % message_json.get('user', 'UNDEFINED')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            else:
                answer = '이미 <@%s> 님의 메시지 개수를 저장하지 않고 있어요.' % message_json.get('user', 'UNDEFINED')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return True
        else:
            return False

    def swap_ignore_channel(self, message_json, command_info):
        im_id_list = self.get_im_id_list()
        group_id_list = self.get_group_id_list()
        if message_json.get('channel') in im_id_list:
            answer = '저와의 DM에서 슬랙왕은 언제나 <@%s> 님이기 때문에 굳이 말하지 않아요 :pika_wink:' % message_json.get('user')
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        if message_json.get('channel') in group_id_list:
            answer = 'private channel에서는 오늘의 슬랙왕이 출력되지 않아요 :sob:'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        if message_json.get('channel') == self.bot_channel_id or message_json.get('channel') == self.notice_channel_id:
            answer = '관리 채널에서는 사용할 수 없는 명령어입니다.'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return

        sub_command = command_info.get('sub_command')
        if sub_command == 'off':
            try:
                self.ignore_channel_list.remove(message_json.get('channel'))
                self.save_ignore_channel_list()
                answer = '다시 <#%s> 채널에서 오늘의 슬랙왕을 출력할게요.' % message_json.get('channel')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            except ValueError:
                answer = '이미 <#@s> 채널에서 오늘의 슬랙왕을 출력하고 있어요.' % message_json.get('channel')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        elif sub_command == 'on':
            if self.ignore_channel_list.count(message_json.get('channel')) == 0:
                self.ignore_channel_list.append(message_json.get('channel'))
                self.save_ignore_channel_list()
                answer = '더 이상 <#%s> 채널에서 오늘의 슬랙왕을 출력하지 않아요.' % message_json.get('channel')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            else:
                answer = '이미 <#%s> 채널에서 오늘의 슬랙왕을 출력하지 않고 있어요.' % message_json.get('channel')
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        else:
            return

    def print_stats(self, message_json, command_info, day):
        if self.ignore_user_list.count(message_json.get('user')) != 0:
            answer = '메시지 개수를 저장하지 않는 유저는 사용할 수 없는 기능이에요.'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return True

        sub_command = command_info.get('contents', '').split(' ')
        if len(sub_command) == 1:
            if sub_command[0][:2] == '<#' and sub_command[0][-1] == '>':
                channel_id = sub_command[0][2:-1].split('|')[0]
                date = ''
            else:
                channel_id = None
                date = sub_command[0]
        elif len(sub_command) == 2:
            if sub_command[0][:2] == '<#' and sub_command[0][-1] == '>':
                channel_id = sub_command[0][2:-1].split('|')[0]
                date = sub_command[1]
            elif sub_command[1][:2] == '<#' and sub_command[1][-1] == '>':
                channel_id = sub_command[1][2:-1].split('|')[0]
                date = sub_command[0]
            else:
                answer = '제대로 된 포맷으로 적어주세요. (사용법을 모르신다면 `factbot help stats`!)'
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
                return True
        else:
            answer = '제대로 된 포맷으로 적어주세요. (사용법을 모르신다면 `factbot help stats`!)'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return True

        if date == '' or date == '%s' % day:
            date = day
            channel_count_dict = self.slacking_dict

        # easter egg
        elif date == '석양이진다빵빵빵':
            date = '석양이진다빵빵빵'
            channel_count_dict = defaultdict(lambda: defaultdict(lambda: 0))

        elif len(date) == 8:
            try:
                _ = datetime.datetime(int(date[:4]), int(date[4:6]), int(date[6:8]))

                if int(date[:4]) < 2017:
                    answer = '그 때는 제가 태어나기 전이라구요 :sob:'
                    self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id),
                                                   answer, as_user=True)
                    return True

                elif int(date) > int(day):
                    answer = '뭐에요, 저보고 미래라도 보라는 건가요?'
                    self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id),
                                                   answer, as_user=True)
                    return True

                channel_count_dict = self.get_slacking_counts(date)

            except ValueError:
                answer = '제대로 된 포맷으로 적어주세요. (사용법을 모르신다면 `factbot help stats`!)'
                self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
                return True

        else:
            answer = '제대로 된 포맷으로 적어주세요. (사용법을 모르신다면 `factbot help stats`!)'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return True

        answer = '<@%s> 님의 %s년 %s월 %s일 통계에요.\n\n' % \
                 (message_json.get('user', 'UNDEFINED'), date[:4], date[4:6], date[6:8])

        user_count_dict = defaultdict(lambda: 0)
        im_id_list = self.get_im_id_list()
        group_id_list = self.get_group_id_list()
        for channel in sorted(list(channel_count_dict.keys())):
            if channel_id and channel != channel_id:
                continue
            if channel in im_id_list:
                continue
            if channel in group_id_list:
                continue
            if channel == self.notice_channel_id:
                continue
            my_ch_count = channel_count_dict[channel][message_json.get('user')]
            channel_count_sum = sum(channel_count_dict[channel].values())
            for user in channel_count_dict[channel].keys():
                user_count_dict[user] += channel_count_dict[channel][user]
            if my_ch_count != 0:
                ch_count = sorted(channel_count_dict[channel].items(), key=lambda x: x[1], reverse=True)

                ranks = []
                before_count = ch_count[0][1]
                rank = 1
                ranks.append(rank)
                for i, count in enumerate(ch_count[1:]):
                    if count[1] != before_count:
                        before_count = count[1]
                        rank = i + 2
                    ranks.append(rank)

                answer += '<#%s> %d회 (%d위, 점유율 %d%%)\n' % \
                          (channel, my_ch_count, ranks[[i[0] for i in ch_count].index(message_json['user'])],
                           my_ch_count / channel_count_sum * 100)

        if user_count_dict[message_json.get('user')] == 0:
            answer += '해당 날짜의 메시지 카운트 정보가 없어요.'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return True

        if not channel_id:
            all_count = sorted(user_count_dict.items(), key=lambda x: x[1], reverse=True)

            ranks = []
            before_count = all_count[0][1]
            rank = 1
            ranks.append(rank)
            for i, count in enumerate(all_count[1:]):
                if count[1] != before_count:
                    before_count = count[1]
                    rank = i + 2
                ranks.append(rank)

            answer += '\n전체 %d회 (%d위, 점유율 %d%%)\n' % \
                      (user_count_dict[message_json.get('user')],
                       ranks[[i[0] for i in all_count].index(message_json.get('user'))],
                       user_count_dict[message_json.get('user')] / sum([i[1] for i in all_count]) * 100)

        self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
        return True

    def manage_keyword(self, message_json, command_info):
        contents = command_info.get('contents').split(' / ')
        if len(contents) > 2:
            contents[1] = ' / '.join(contents[1:])
            del contents[2:]
        if len(contents) != 2:
            answer = '제대로 된 포맷으로 입력해주세요. <keyword> / <sentence>'
        else:
            keyword = contents[0]
            reply = contents[1]

            sub_command = command_info.get('sub_command')
            if sub_command == 'add':
                self.keywords[keyword.replace(' ', '')].add(reply)
                answer = '%s 키워드에 %s 리액션을 추가했어요.' % (keyword, reply)
            elif sub_command == 'delete':
                if keyword.replace(' ', '') not in self.keywords.keys():
                    answer = '%s 키워드에 대한 리액션이 존재하지 않아요.' % keyword
                else:
                    try:
                        self.keywords[keyword.replace(' ', '')].remove(reply)
                        answer = '%s 키워드에 대한 %s 리액션을 삭제했어요.' % (keyword, reply)
                    except KeyError:
                        answer = '%s 키워드에 대한 %s 리액션이 존재하지 않아요.' % (keyword, reply)
            else:
                return

        with open(self.default_path+'data/keyword_list.txt', 'w', encoding='utf-8') as f:
            for keyword, replies in self.keywords.items():
                if len(replies) == 0:
                    continue
                f.write('keyword : %s\n' % keyword)
                for reply in replies:
                    f.write('%s\n' % reply)
        self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

    def set_kingname(self, message_json, command_info):
        im_id_list = self.get_im_id_list()
        group_id_list = self.get_group_id_list()
        if message_json.get('channel') in im_id_list:
            answer = '저와의 DM에서 슬랙왕은 언제나 <@%s>, 당신이랍니다 :pika_wink:' % message_json.get('user')
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        if message_json.get('channel') in group_id_list:
            answer = 'private channel에서는 오늘의 슬랙왕이 출력되지 않아요 :sob:'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        if message_json.get('channel') == self.bot_channel_id or message_json.get('channel') == self.notice_channel_id:
            answer = '관리 채널에서는 사용할 수 없는 명령어입니다.'
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return
        if message_json.get('channel') in self.ignore_channel_list:
            answer = '<#%s> 채널에서는 오늘의 슬랙왕이 출력되지 않아요 :sob:' % message_json.get('channel')
            self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)
            return

        if command_info.get('contents', '') != '':
            self.kingname_alias[message_json.get('channel')] = command_info.get('contents')
            answer = '<#%s> 채널에서 `[오늘의 %s]` 로 슬랙왕 호칭을 변경했어요.' % \
                     (message_json.get('channel'), command_info.get('contents'))
        else:
            if self.kingname_alias.get(message_json.get('channel'), '') != '':
                del self.kingname_alias[message_json.get('channel')]
                answer = '<#%s> 채널의 슬랙왕 호칭을 초기화했어요.' % (message_json.get('channel'))
            else:
                answer = '아직 <#%s> 채널의 슬랙왕 호칭이 없어요.' % (message_json.get('channel'))
        with open(self.default_path+'data/kingname_alias.txt', 'w', encoding='utf-8') as f:
            for c, alias in self.kingname_alias.items():
                f.write('%s %s\n' % (c, alias))
        self.slacker.chat.post_message(message_json.get('channel', self.bot_channel_id), answer, as_user=True)

    def print_slacking(self):
        im_id_list = self.get_im_id_list()
        group_id_list = self.get_group_id_list()
        for channel in self.slacking_dict.keys():
            if channel == self.bot_channel_id or channel == self.notice_channel_id:
                continue
            if channel in self.ignore_channel_list:
                continue
            if channel in im_id_list:
                continue
            if channel in group_id_list:
                continue
            if not self.get_channel_info(channel).get('is_member', False):
                continue
            if self.kingname_alias.get(channel, '') == '':
                bot_say = '[오늘의 <#%s>왕]\n' % channel
            else:
                bot_say = '[오늘의 %s]\n' % self.kingname_alias.get(channel)

            ch_count = sorted(self.slacking_dict[channel].items(), key=lambda x: x[1], reverse=True)
            chat_count_sum = sum([i[1] for i in ch_count])
            kings = [user[0] for user in ch_count if user[1] == ch_count[0][1]]
            if chat_count_sum < 5 or len(ch_count) < 2:
                continue
            elif chat_count_sum < 10:
                bot_say += '충분한 채팅이 오가지 않았어요. 많은 참여 부탁드립니다! :3'
            else:
                kings_name = []
                for king in kings:
                    kings_name.append(self.get_user_info(king).get('name', 'UNDEFINED'))
                king_name = ' & '.join(['%s.%s' % (name[0], name[1:]) for name in kings_name])
                bot_say += ':crown: %s! (%d회 / 총 %d회, 지분율 %.2f%%)' % \
                           (king_name, ch_count[0][1], chat_count_sum, float(ch_count[0][1])/chat_count_sum*100)

            self.slacker.chat.post_message(channel, bot_say, as_user=True)

    def save_slacking_counts(self, day):
        with open(self.default_path+'data/slacking_counts/'+day+'.log', 'w') as f:
            for channel in self.slacking_dict.keys():
                f.write('#%s\n' % channel)
                for user in self.slacking_dict[channel].keys():
                    f.write('%s : %d\n' % (user, self.slacking_dict[channel][user]))
                f.write('\n')

    def get_slacking_counts(self, day):
        try:
            with open(self.default_path+'data/slacking_counts/'+day+'.log', 'r') as f:
                channel_count_dict = defaultdict(lambda: defaultdict(lambda: 0))
                channel = ''
                for line in f.readlines():
                    line = line.strip()
                    if '#' in line:
                        channel = line[1:]
                    elif ':' in line:
                        channel_count_dict[channel][line.split(':')[0].strip()] = int(line.split(':')[1].strip())
            return channel_count_dict

        except FileNotFoundError:
            return defaultdict(lambda: defaultdict(lambda: 0))

    def save_statistics_counts(self, day):
        with open(self.default_path+'data/statistics_counts/'+day+'.log', 'w') as f:
            for channel in self.statistics_dict.keys():
                f.write('#%s\n' % channel)
                for hour in self.statistics_dict[channel].keys():
                    f.write('%d : %d\n' % (hour, self.statistics_dict[channel][hour]))
                f.write('\n')

    def get_statistics_counts(self, day):
        try:
            with open(self.default_path+'data/statistics_counts/'+day+'.log', 'r') as f:
                channel_count_dict = defaultdict(lambda: defaultdict(lambda: 0))
                channel = ''
                for line in f.readlines():
                    line = line.strip()
                    if '#' in line:
                        channel = line[1:]
                    elif ':' in line:
                        channel_count_dict[channel][int(line.split(':')[0].strip())] = int(line.split(':')[1].strip())
            return channel_count_dict

        except FileNotFoundError:
            return defaultdict(lambda: defaultdict(lambda: 0))

    def get_past_count_history(self, day):
        def _slacking_count(message_json, chan):
            if message_json.get('type') != 'message':
                return
            if 'subtype' in message_json.keys():
                return
            if 'bot_id' in message_json.keys():
                return
            if message_json.get('user') in self.ignore_user_list:
                return

            self.slacking_dict[chan][message_json.get('user', '')] += 1

        def _statistics_count(message_json, chan):
            if message_json.get('type') != 'message':
                return
            if 'subtype' in message_json.keys():
                return
            if 'bot_id' in message_json.keys():
                return
            if message_json.get('user') in self.ignore_user_list:
                return

            hour = time.localtime(float(message_json.get('ts', time.time()))).tm_hour
            self.statistics_dict[chan][hour] += 1

        start_unix_sec = '%.6f' % time.mktime(time.strptime(day[:4]+'/'+day[4:6]+'/'+day[6:], '%Y/%m/%d'))
        end_unix_sec = '%.6f' % time.mktime(time.strptime(day[:4]+'/'+day[4:6]+'/'+day[6:]+' 23:59:59',
                                                          '%Y/%m/%d %H:%M:%S'))
        channels = self.get_channel_id_list()

        for channel in channels:
            if not self.get_channel_info(channel).get('is_member', False):
                continue

            while True:
                channel_history = self.slacker.channels.history(channel=channel, count=1000, oldest=start_unix_sec,
                                                                latest=end_unix_sec).body
                for msg in channel_history['messages']:
                    _slacking_count(msg, channel)
                    _statistics_count(msg, channel)
                if not channel_history.get('has_more', False):
                    break
                end_unix_sec = '%.6f' % (float(channel_history['messages'][-1].get('ts', 1)) - 0.00001)

    def save_ignore_channel_list(self):
        with open(self.default_path+'data/ignore_channel_list.txt', 'w') as f:
            for channel in self.ignore_channel_list:
                f.write('%s\n' % channel)

    def load_ignore_channel_list(self):
        with open(self.default_path+'data/ignore_channel_list.txt', 'r') as f:
            self.ignore_channel_list = [line.strip() for line in f.readlines()]

    def save_ignore_user_list(self):
        with open(self.default_path+'data/ignore_user_list.txt', 'w') as f:
            for user in self.ignore_user_list:
                f.write('%s\n' % user)

    def load_ignore_user_list(self):
        with open(self.default_path+'data/ignore_user_list.txt', 'r') as f:
            self.ignore_user_list = [line.strip() for line in f.readlines()]

    def get_user_id_list(self):
        return [user['id'] for user in self.slacker.users.list().body['members']]

    def get_channel_id_list(self):
        return [channel['id'] for channel in self.slacker.channels.list().body['channels']]

    def get_group_id_list(self):
        return [group['id'] for group in self.slacker.groups.list().body['groups']]

    def get_im_id_list(self):
        return [im['id'] for im in self.slacker.im.list().body['ims']]

    def get_user_id(self, user_name):
        users = self.slacker.users.list().body['members']
        for user in users:
            if user['name'] == user_name:
                return user['id']
        return None

    def get_user_info(self, user_id):
        """

        :param user_id: user id
        :return: {'color': 'hex color',
                  'deleted': True/False,
                  'id': 'user id',
                  'is_admin': True/False,
                  'is_bot': True/False,
                  'is_owner': True/False,
                  'is_primary_owner': True/False,
                  'is_restricted': True/False,
                  'is_ultra_restricted': True/False,
                  'name': 'user nickname',
                  'profile': {'avatar_hash', 'email', 'first_name', 'last_name', 'real_name',
                              'real_name_normalized', 'image_<size>', 'title'},
                  'real_name': 'user realname',
                  ...
                  }
        """
        return self.slacker.users.info(user=user_id).body['user']

    def get_channel_info(self, channel_id):
        """

        :param channel_id: channel id
        :return: {'created': Unix time,
                  'creator': 'user id',
                  'id': 'channel id',
                  'is_archived': True/False,
                  'is_channel': True/False,
                  'is_general': True/False,
                  'is_member': True/False,
                  'members': [user id],
                  'name': 'channel name',
                  'previous_names': [previous name],
                  'purpose': {'creator': 'user id', 'last_set': Unix time, 'value': 'text'},
                  'topic': {'creator': 'user id', 'last_set': Unix time, 'value': 'text'}}
        """
        return self.slacker.channels.info(channel=channel_id).body['channel']

    def get_group_info(self, group_id):
        return self.slacker.groups.info(channel=group_id).body['group']
