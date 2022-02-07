import os

from importlib import machinery, util

def load_module(filename):
    bn = os.path.basename(filename).split('.')[0]

    #loader = importlib.machinery.SourceFileLoader(bn.replace('-', '_'), '/tmp/a-b.txt')
    #>>> mod = loader.load_module()


    loader = machinery.SourceFileLoader(bn, filename)
    spec = util.spec_from_loader( bn, loader )
    module = util.module_from_spec( spec )
    loader.exec_module(module)
    return module

class ScriptLoader:

    bad_filenames = [
            '__pycache__'
            ]

    def __init__(self):
        dname = os.environ.get('DECEL_SCRIPT_DIR')
        self.vars = {}
        if dname:
            paths = dname.split(os.pathsep)
            for path in paths:
                for filename in os.listdir(path):
                    if filename not in ScriptLoader.bad_filenames:
                        full_path = os.path.join(path, filename)
                        module = load_module(full_path)
                        self.load_module(module)

    def load_module(self, module):
        for val in dir(module):
            if not (val.startswith('__') and val.endswith('__')):
                self.vars[val] = getattr(module, val)

    def get_vars(self):
        return self.vars

global _decel_script_loader
_decel_script_loader = None

def get_loader():
    global _decel_script_loader
    if not _decel_script_loader:
        _decel_script_loader = ScriptLoader()
    return _decel_script_loader
