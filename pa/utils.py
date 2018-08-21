'''
Utility functions and constants for pa
'''
import os
from datetime import datetime

import toml
import peewee


# Location of the pa sqlite database
DB_PATH = os.path.expanduser('~/.config/pa/pa.db')
DB = peewee.SqliteDatabase(DB_PATH)

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


class PaModel(peewee.Model):
    '''
    Base Class for pa DB models. This should be inherited from for all
    database models.
    '''
    class Meta:
        database = DB


def get_config(path='~/.config/pa/pa.toml'):
    '''
    Read user config from the config dotfile and return as a dictionary. The
    config file is found at `~/.config/pa/pa.toml` and is a standard toml file.
    '''
    config_path = os.path.expanduser(path)
    config = DEFAULT_CONFIG
    from_file = toml.load(config_path)
    config.update(from_file)

    return config


def write_default_config_file(path='~/.config/pa/pa.cfg'):
    '''
    Write out the default config to `path` in ini format.
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
