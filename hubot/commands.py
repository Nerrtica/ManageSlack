#-*- coding:utf-8 -*-


class Commands:
    """Factbot의 모든 명령어를 저장하는 클래스.

    commands: [{'main_command', 'sub_info': ['sub_command', 'contents', 'description']}]
    """

    def __init__(self, commands_file):
        self.commands = []
        self.commands_file = commands_file
        self.load()

    def get_command(self, full_command):
        full_command = [command for command in full_command.split(' ') if command]
        main_command = full_command[0]
        main_command_idx = self.get_main_command_index(main_command)
        if main_command_idx == -1:
            main_command_candidates = self.get_main_command_candidates(main_command)
            return {'is_command': False, 'main_command_candidates': main_command_candidates}
        # main command만 입력됨
        if len(full_command) == 1:
            sub_command_idx = self.get_sub_command_index(main_command_idx, 'None')
            if len(sub_command_idx) != 0:
                for idx in sub_command_idx:
                    if self.commands[main_command_idx]['sub_info'][idx]['contents'] == 'None':
                        return {'is_command': True, 'main_command': main_command}
                return {'is_command': False, 'main_command': main_command}
            else:
                return {'is_command': False, 'main_command': main_command}
        # main command와 sub command, 혹은 main command와 contents만 입력됨
        elif len(full_command) == 2:
            extra_command = full_command[1]
            extra_command_idx = self.get_sub_command_index(main_command_idx, extra_command)
            if len(extra_command_idx) == 0:
                for sub_command_idx in self.get_sub_command_index(main_command_idx, 'None'):
                    if self.commands[main_command_idx]['sub_info'][sub_command_idx]['contents'] != 'None':
                        return {'is_command': True, 'main_command': main_command, 'contents': extra_command}
                return {'is_command': False, 'main_command': main_command}
            else:
                for idx in extra_command_idx:
                    if self.commands[main_command_idx]['sub_info'][idx]['contents'] == 'None':
                        return {'is_command': True, 'main_command': main_command, 'sub_command': extra_command}
                return {'is_command': False, 'main_command': main_command}
        # main command, sub command, contents가 모두 입력되거나 main command와 contents가 입력됨
        elif len(full_command) == 3:
            sub_command = full_command[1]
            sub_command_idx = self.get_sub_command_index(main_command_idx, sub_command)
            contents = full_command[2]
            if len(sub_command_idx) == 0:
                for idx in self.get_sub_command_index(main_command_idx, 'None'):
                    if self.commands[main_command_idx]['sub_info'][idx]['contents'] != 'None':
                        return {'is_command': True, 'main_command': main_command,
                                'contents': ' '.join(full_command[1:])}
                return {'is_command': False, 'main_command': main_command}
            else:
                for idx in sub_command_idx:
                    if self.commands[main_command_idx]['sub_info'][idx]['contents'] != 'None':
                        return {'is_command': True, 'main_command': main_command,
                                'sub_command': sub_command, 'contents': contents}
                return {'is_command': False, 'main_command': main_command}
        # main command와 띄어쓰기를 포함한 contents가 입력됨
        else:
            sub_command = full_command[1]
            sub_command_idx = self.get_sub_command_index(main_command_idx, sub_command)
            if len(sub_command_idx) == 0:
                contents = ' '.join(full_command[1:])
                sub_command_idx = self.get_sub_command_index(main_command_idx, 'None')
                if len(sub_command_idx) != 0:
                    for idx in sub_command_idx:
                        if self.commands[main_command_idx]['sub_info'][idx]['contents'] != 'None':
                            return {'is_command': True, 'main_command': main_command, 'contents': contents}
                    return {'is_command': False, 'main_command': main_command}
                else:
                    return {'is_command': False, 'main_command': main_command}
            else:
                contents = ' '.join(full_command[2:])
                for idx in sub_command_idx:
                    if self.commands[main_command_idx]['sub_info'][idx]['contents'] != 'None':
                        return {'is_command': True, 'main_command': main_command,
                                'sub_command': sub_command, 'contents': contents}
                return {'is_command': False, 'main_command': main_command}

    def get_main_command_index(self, main_command):
        for i, command in enumerate(self.commands):
            if command['main_command'] == main_command:
                return i
        return -1

    def get_sub_command_index(self, main_idx, sub_command):
        common_idx = []
        for i, info in enumerate(self.commands[main_idx]['sub_info']):
            if info['sub_command'] == sub_command:
                common_idx.append(i)
        return common_idx

    def get_main_command_candidates(self, main_command):
        candidates = self.get_correction_candidates(main_command)
        return list(candidates)

    def get_correction_candidates(self, misspelled_command):

        def known(words):
            return set(w for w in words if w in [c['main_command'] for c in self.commands])

        def edits1(word):
            letters = 'abcdefghijklmnopqrstuvwxyz'
            splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
            deletes = [L + R[1:] for L, R in splits if R]
            transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
            replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
            inserts = [L + c + R for L, R in splits for c in letters]
            return set(deletes + transposes + replaces + inserts)

        def edits2(word):
            return (e2 for e1 in edits1(word) for e2 in edits1(e1))

        return known(edits1(misspelled_command)) or known(edits2(misspelled_command)) or set()

    def load(self):
        with open(self.commands_file, 'r', encoding='utf-8') as f:
            command_dict = {'sub_info': []}
            sub_command = ''
            description = ''
            for line in f.readlines():
                line = line.strip()
                if 'main_command' in line:
                    if 'main_command' in command_dict.keys():
                        self.commands.append(command_dict)
                        command_dict = {'sub_info': []}
                    main_command = line[len('main_command : '):]
                    command_dict['main_command'] = main_command
                elif 'sub_command' in line:
                    sub_command = line[len('sub_command : '):]
                elif 'description' in line:
                    description = line[len('description : '):]
                elif 'contents' in line:
                    contents = line[len('contents : '):]
                    command_dict['sub_info'].append({'sub_command': sub_command, 'description': description,
                                                     'contents': contents})
            self.commands.append(command_dict)

    def save(self):
        with open(self.commands_file, 'w', encoding='utf-8') as f:
            for command in self.commands:
                f.write('main command : %s\n' % command['main_command'])
                f.write('sub command : %s\n' % command['sub_info']['sub_command'])
                f.write('description : %s\n' % command['sub_info']['description'])
                f.write('contents : %s\n\n' % str(command['sub_info']['contents']))
