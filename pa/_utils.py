'''
Utility functions and constants for pa
'''
import os
from datetime import datetime
from configparser import ConfigParser


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
        'note_root': '/home/innes/notes',
    },
    'todoist': {
        'enabled': False,
        'api_token': '',
    },
    'toggl': {
        'enabled': False,
        'api_token': '',
    },
    'gmail': {
        'enabled': False,
    },
    'gcal': {
        'enabled': False,
    }
}


def get_config(path='~/.aard.cfg'):
    '''
    Read user config from the config dotfile and return as a dictionary.
    The config file is found at `~/.aard.cfg` and is a standard .ini file.

    The ConfigParser object returned by this function supports:
        get(section, key) -> String
        getboolean(section, key) -> Bool
        getfloat(section, key) -> Float
        getint(section, key) -> Int
    '''
    config_path = os.path.expanduser(path)
    config = ConfigParser(default_section='general')

    config.read_dict(DEFAULT_CONFIG)  # Set defaults
    config.read(config_path)          # Override with user config

    return config


def write_default_config_file(path='~/.aard.cfg'):
    '''
    Write out the default config to `path` in ini format.
    '''
    config_path = os.path.expanduser(path)
    config = ConfigParser(default_section='general')

    config.read_dict(DEFAULT_CONFIG)  # Set defaults

    with open(config_path, 'w') as f:
        config.write(f)


def today():
    '''
    Return today's date as a mm/dd/yyyy formatted string.
    Most APIs are American...
    '''
    td = datetime.now()
    return '{}/{}/{}'.format(td.month, td.day, td.year)
