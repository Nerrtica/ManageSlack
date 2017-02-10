#-*- coding:utf-8 -*-

import requests
import time
import json
from collections import defaultdict
import asyncio
import websockets
from slacker import Slacker

# hubot token
token = ''
slack = Slacker(token)

def get_channel_list():
    params = {
        'token': token
    }
    uri = 'https://slack.com/api/channels.list'
    response = requests.get(uri, params=params)
    return json.loads(response.text)['channels']

def get_user_list():
    params = {
        'token': token
    }
    uri = 'https://slack.com/api/users.list'
    response = requests.get(uri, params=params)
    return json.loads(response.text)['members']

def count_to_dict(message_json, channel_count_dict):
    try:
        ck1 = message_json['type'] == 'message'
        ck2 = 'subtype' not in message_json.keys()
        ck3 = 'bot_id' not in message_json.keys()
    except KeyError:
        return
    
    if ck1 and ck2 and ck3:
        if user_name[message_json['user']] == '':
            return
        channel_count_dict[channel_name[message_json['channel']]][user_name[message_json['user']]] += 1

# channel list that will not compile statistics
delete_channel_list = ['channel_name']
# user list that will not compile statistics
delete_user_list = ['user_name']

# channel name to id
channel_id = defaultdict(lambda: '')
# channel id to name
channel_name = defaultdict(lambda: '')

channel_list = get_channel_list()
for channel in channel_list:
	channel_id[channel['name']] = channel['id']
	channel_name[channel['id']] = channel['name']

# channel name to id
user_id = defaultdict(lambda: '')
# channel id to name
user_name = defaultdict(lambda: '')

user_list = get_user_list()
for user in user_list:
    if user['name'] in delete_user_list:
        continue
    user_id[user['name']] = user['id']
    user_name[user['id']] = user['name']

daily_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))

# bot execution part
async def execute_bot(daily_dict):
    response = slack.rtm.start()
    sock_endpoint = response.body['url']
    ws = await websockets.connect(sock_endpoint)
    now = time.localtime()
    day = '%04d' % now.tm_year + '%02d' % now.tm_mon + '%02d' % now.tm_mday
    yesterday = now.tm_mday

    while True:
        message = await ws.recv()
        message_json = json.loads(message)
        
        now = time.localtime()
        
        if now.tm_mday != yesterday:
            channel_count_dict = daily_dict[day]
            
            for channel in channel_count_dict.keys():
                if channel in delete_channel_list:
                    continue
                
                bot_say = '[오늘의 슬랙왕 BETA]\n\n'
                
                ch_count = sorted(channel_count_dict[channel].items(), key=lambda x:x[1], reverse=True)
                chat_count_sum = sum([i[1] for i in ch_count])
                if chat_count_sum < 5:
                    bot_say += '오늘은 <#%s|%s> 채널의 채팅이 거의 없었네요. 많은 참여 부탁드립니다! :3\n' % (channel_id[channel], channel)
                else:
                    bot_say += '오늘 <#%s|%s> 채널에서는 총 %d회의 채팅이 오갔어요!\n' % (channel_id[channel], channel, chat_count_sum)
                    bot_say += '오늘의 <#%s|%s> 채널 슬랙왕은 %s입니다! %d회의 채팅을 하셨어요!\n' % (channel_id[channel], channel, ch_count[0][0][0]+'.'+ch_count[0][0][1:], ch_count[0][1])
                bot_say += '\n(본인의 닉네임이 나오지 않기를 원하시는 분, 기타 피드백은 <@bot_master>에게 DM 주세요.)'
                bot_say += '\n(특정 채널에서 오늘의 슬랙왕을 사용하시려면 <@bot_name>을 초대해주시고, 사용하지 않으시려면 내보내주세요.)'
                
                slack.chat.post_message(channel_id[channel], bot_say, as_user=True)
                
            yesterday = now.tm_mday
            day = '%04d' % now.tm_year + '%02d' % now.tm_mon + '%02d' % now.tm_mday
            
        count_to_dict(message_json, daily_dict[day])
        
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
asyncio.get_event_loop().run_until_complete(execute_bot(daily_dict))
asyncio.get_event_loop().run_forever()