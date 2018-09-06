'''
Utility functions and constants for pa
'''
import os
import concurrent.futures
from datetime import datetime

import toml


CONFIG_ROOT = os.path.expanduser('~/.config/pa')
MOD_DIR = os.path.expanduser('~/.config/pa/user_modules')
DEFAULT_CONFIG_FILE = os.path.expanduser('~/.config/pa/pa.toml')

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

# A simple Markdown template that allows for tagging and
# searching of notes and TODOs
TEMPLATE = '''\
### Date :: {}
### Tags :: {}
'''

DEFAULT_CONFIG = {
    'general': {
        'ag_enabled': False,
        'editor': 'vim',
    },
    'note': {
        'note_root': '~/notes',
    },
    'todoist': {
        'enabled': False,
        'api_token': '',
    },
    'toggl': {
        'enabled': False,
        'api_token': '',
    },
    'mail': {
        'enabled': False,
        'oath2': False,
        'accounts': {},
    },
    'cal': {
        'enabled': False,
    }
}


def get_config(path=DEFAULT_CONFIG_FILE):
    '''
    Read user config from the config dotfile and return as a dictionary. The
    config file is found at `~/.config/pa/pa.toml` and is a standard toml file.

    NOTE: This will create the config directory if it does not already exist.
    '''
    config = DEFAULT_CONFIG

    if not os.path.isdir(CONFIG_ROOT):
        # Do a full init of the config dir in this case. This means that we
        # don't attempt a partial init if the user has created the directory
        # themselves.
        init_config_dir(CONFIG_ROOT)

    config_path = os.path.expanduser(path)
    from_file = toml.load(config_path)
    config.update(from_file)

    return config


def init_config_dir(config_dir=CONFIG_ROOT):
    '''
    Create all of the default config directories and files.
    '''
    # Create the base directory
    os.makedirs(config_dir)
    # Create the user_modules directory
    user_dir = os.path.join(config_dir, 'user_modules')
    os.makedirs(user_dir)
    # Touch the __init__.py file to mark it as a python module
    open(os.path.join(user_dir, '__init__.py'), 'a').close()
    # Write out the default config file
    write_default_config_file()


def write_default_config_file(path=DEFAULT_CONFIG_FILE):
    '''
    Write out the default config to `path` in toml format.
    '''
    config_path = os.path.expanduser(path)
    toml.dump(DEFAULT_CONFIG, config_path)


def today():
    '''
    Return today's date as a mm/dd/yyyy formatted string.
    Most APIs are American...
    '''
    td = datetime.now()
    return '{}/{}/{}'.format(td.month, td.day, td.year)


def print_red(s, end='\n'):
    '''Helper to give coloured output.'''
    print('{}{}{}'.format(RED, s, NC), end=end)


def print_yellow(s, end='\n'):
    '''Helper to give coloured output.'''
    print('{}{}{}'.format(YELLOW, s, NC), end=end)


def print_green(s, end='\n'):
    '''Helper to give coloured output.'''
    print('{}{}{}'.format(GREEN, s, NC), end=end)


def run_many(func, args_list, max_threads=10, fail_quiet=False):
    '''
    Run a function multiple times with different inputs,
    each on its own thread. Intended for use with blocking IO
    '''
    results = []
    max_workers = min([max_threads, len(args_list)])

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = (
            ex.submit(func, *args)
            for args in args_list
        )

        for f in concurrent.futures.as_completed(futures):
            try:
                res = f.result()
                if res:
                    results.append(res)
            except Exception as e:
                if fail_quiet:
                    pass
                else:
                    raise e

    return results


def run_many_tagged(func, tag_args, max_threads=10, fail_quiet=False):
    '''
    Run a function multiple times with different inputs,
    each on its own thread. Intended for use with blocking IO
    '''
    def tagged(tag, func):
        '''Helper to maintain tags'''
        def _inner(*args):
            return tag, func(*args)
        return _inner

    results = {}
    max_workers = min([max_threads, len(tag_args)])

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = (
            ex.submit(tagged(tag, func), *args)
            for (tag, args) in tag_args
        )

        for f in concurrent.futures.as_completed(futures):
            try:
                tag, res = f.result()
                if res:
                    results[tag] = res
            except Exception as e:
                if fail_quiet:
                    pass
                else:
                    raise e

    return results
