import os
from key_command import decode_command

class ConfigFile:

    def __init__(self, filename, env_var):
        f = os.environ.get(env_var, filename)
        self.data = {}
        self.read(f)

    def read(self, filename):
        fname = os.path.expanduser(filename)
        if not os.path.exists(fname):
            return
        with open(fname) as f:
            lines = [line.strip() for line in f.readlines() if len(line.strip()) > 0]
            for line in lines:
                if line.startswith('#'):
                    continue
                items = line.split(' ')
                self._read_line(items)

    def _read_line(self, line):
        value = True
        if len(line) > 1:
            value = line[1:]
        token = line[0]
        self._register_token(token, value)

    def _register_token(self, token, value):
        self.data[token] = value

    def get_val(self, key, action=False, default=None, argtype=None):
        if key not in self.data:
            return default
        else:
            val = self.data[key]
            if len(val) == 1:
                val = val[0]
            if action:
                val = action(val)
            return val

class DecelConfig(ConfigFile):

    def __init__(self):
        self.commands = {}
        super().__init__('~/.decel_config.dcfg', 'DECEL_CONFIG_FILE')

    def _register_token(self, token, value):
        if token == 'cmd':
            self.add_command(value)
        if token == 'ecmd':
            self.add_command(value, final_enter=True)
        else:
            super()._register_token(token, value)

        self.data[token] = value

    def add_command(self, values, final_enter=False):
        name = values[0]
        commands = values[1:]
        key_sequence = decode_command(values, final_enter)
        self.commands[name] = key_sequence

    def get_commands(self):
        return self.commands

    def default_column_width(self):
        return self.get_val('col_width', action=int, default=7)

    def row_jump_size(self):
        return self.get_val('row_jump', action=int, default=5)

    def col_jump_size(self):
        return self.get_val('col_jump', action=int, default=3)

