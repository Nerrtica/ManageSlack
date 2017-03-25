#-*- coding:utf-8 -*-

class Commands:
	"""Factbot의 모든 명령어를 저장하는 클래스.

	commands: [{'main_command', 'sub_info': ['sub_command', 'contents', 'description']}]
	"""

	def __init__(commands_file):
		self.commands = []
		self.commands_file = commands_file

	def get_command(full_command):
		full_command = full_command.split(' ')
		main_command = full_command[0]
		main_command_idx = self.get_main_command_index(main_command)
		if main_command_idx == -1:
			return {'is_command': False}
		if len(full_command) == 1:
			if 'None' in [command['sub_command'] for command in self.commands[command_idx]['sub_info']]:
				return {'is_command': True, 'main_command': main_command}
			else:
				return {'is_command': False}
		elif len(full_command) == 2:
			sub_command = full_command[1]
			sub_command_idx = self.get_sub_command_index(main_command_idx, sub_command)
			if sub_command_idx == -1 or self.commands[main_command_idx]['sub_info'][sub_command_idx]['contents']:
				return {'is_command': False}
			else:
				return {'is_command': True, 'main_command': main_command, 'sub_command': sub_command}
		elif len(full_command) == 3:
			sub_command = full_command[1]
			sub_command_idx = self.get_sub_command_index(main_command_idx, sub_command)
			contents = full_command[2]
			if sub_command_idx == -1 or not self.commands[main_command_idx]['sub_info'][sub_command_idx]['contents']:
				return {'is_command': False}
			else:
				return {'is_command': True, 'main_command': main_command, 'sub_command': sub_command, 'contents': contents}

	def get_main_command_index(main_command):
		for i, command in enumerate(self.commands):
			if command['main_command'] == main_command:
				return i
		return -1

	def get_sub_command_index(main_idx, sub_command):
		common_idx = -1
		for i, info in enumerate(self.commands[main_idx]['sub_info']):
			if info['sub_command'] == sub_command:
				return i
			if '<' in info['sub_command']:
				common_idx = i
		return common_idx

	def load():
		with open(self.commands_file, 'r', encoding='utf-8') as f:
			command_dict = {'sub_info': []}
			for line in f.readlines():
				line = line.strip()
				if 'main_command' in line:
					main_command = line[len('main command : '):]
					command_dict['main_command'] = main_command
				elif 'sub_command' in line:
					sub_command = line[len('sub command : '):]
				elif 'description' in line:
					description = line[len('description : '):]
				elif 'contents' in line:
					contents = line[len('contents : '):]
					if contents == 'True':
						contents = True
					else:
						contents = False
				elif line == '':
					command_dict['sub_info'].append({'sub_command': sub_command, 'description': description, 'contents': contents})
					self.commands.append(command_dict)
					command_dict = {'sub_info': []}

	def save():
		with open(self.commands_file, 'w', encoding='utf-8') as f:
			for command in self.commands:
				f.write('main command : %s\n' % command['main_command'])
				f.write('sub command : %s\n' % command['sub_info']['sub_command'])
				f.write('description : %s\n' % command['sub_info']['description'])
				f.write('contents : %s\n\n' % str(command['sub_info']['contents']))
