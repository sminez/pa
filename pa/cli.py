'''\
                 pa - The ADHD Assistant

      .: An Executive Function Replacement Tool :.
      ============================================
          .--.                        .-.
      .---|--|   .-.     .---.  .---. |~|    .--.
   .--|===|  |---|_|--.__|   |--|:::| |~|-==-|==|---.
 .-|%%|   |  |===| |~~|%%|   |--|   |_|~|    |  |___|-.
 |=|  |   |  |===| |==|  |   |  |:::|=| |    |  |---|=|
 | |  |   |  |   |_|__|  |   |__|   | | |    |  |___| |
 |=|~~|===|--|===|~|~~|%%|~~~|--|:::|=|~|----|==|---|=|
 '-^--^---'--^---^-^--^--^---'--^---^-^-^-==-^--^---^-'

Usage:
  pa init
  pa <command> [<args>...]
  pa (-h | --help)
  pa --version

Options:
  -h, --help    Display this message and exit
  --version     Display the current version of this program

Commands:
{}
Use 'pa <command> --help' for specific information regarding a sub command
'''
import os
from traceback import print_exc
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec

import peewee
from docopt import docopt


# Ensure that we have the config directory before importing from _utils as
# that will try to look for the DB.
CONFIG_ROOT = os.path.expanduser('~/.config/pa')
MOD_DIR = os.path.expanduser('~/.config/pa/user_modules')

if not os.path.isdir(CONFIG_ROOT):
    os.makedirs(CONFIG_ROOT)
    os.makedirs(MOD_DIR)


from ._utils import PaModel, print_green, print_yellow, print_red  # noqa


__version__ = '0.2.1'


def main(argv=None):
    sub_commands, cmd_map = get_sub_commands()
    cmd_str = format_sub_command_section(sub_commands)

    args = docopt(
        __doc__.format(cmd_str),
        argv=argv,
        version=__version__,
        options_first=True,
    )

    if args['init']:
        init()
        exit()

    command = args['<command>']
    argv = [command] + args['<args>']

    try:
        if cmd_map[command] == 'built-in':
            module = import_module('.modules.' + command, package='pa')
        elif cmd_map[command] == 'user-defined':
            path = os.path.join(MOD_DIR, command + '.py')
            spec = spec_from_file_location("module", path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            # We populate the cmd_map so these should be the only two values
            raise RuntimeError('Should never reach here!')

        args = docopt(module.__doc__, argv=argv)
        module.run(args)
    except ImportError:
        print_red("Module '{}' failed to load".format(command))
        print_red("Error was:")
        print_exc()
        exit()
    except KeyError:
        exit("{} is not a pa command. See 'pa --help'".format(command))


def get_sub_commands():
    '''
    Walk both the modules directory and the user module directory to find
    commands that we can run.

    pa makes no distinction between built-in and user defined modules.
    '''
    def valid_module(fname):
        '''_ marks a file as not being a pa module'''
        return fname.endswith('.py') and not fname.startswith('_')

    sub_commands = []
    cmd_map = {}

    # Built-in
    built_in_modules = import_module('.modules', package='pa')
    for entry in dir(built_in_modules):
        if not entry.startswith('_'):
            module = getattr(built_in_modules, entry)
            sub_commands.append((entry, module.SUMMARY))
            cmd_map[entry] = 'built-in'

    # User-defined
    for entry in os.listdir(MOD_DIR):
        path = os.path.join(MOD_DIR, entry)
        if os.path.isfile(path) and valid_module(entry):
            spec = spec_from_file_location("module", path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            cmd = entry[:-3]
            sub_commands.append((cmd, module.SUMMARY))
            cmd_map[cmd] = 'user-defined'

    # Sort by sub-command name
    sub_commands = sorted(sub_commands, key=lambda t: t[0])

    return sub_commands, cmd_map


def format_sub_command_section(sub_commands):
    '''
    Generate the docstring/cli help for each subcommand.
    '''
    max_cmd_len = 0
    cmd_str = ''

    for cmd, summary in sub_commands:
        cmd_len = len(cmd)
        if cmd_len > max_cmd_len:
            max_cmd_len = cmd_len

    base_padding = max_cmd_len + 4

    for cmd, summary in sub_commands:
        padding = ' ' * (base_padding + max_cmd_len - len(cmd))
        cmd_str += '  {}{}{}\n'.format(cmd, padding, summary)

    return cmd_str


def init():
    db_init()


def db_init():
    '''
    Initialise the DB
    '''
    def init_tables(module):
        for entry in dir(module):
            mod = getattr(module, entry)

            if isinstance(mod, type) and issubclass(mod, PaModel):
                if entry == 'PaModel':
                    # Don't create the base class
                    continue
                try:
                    mod.create_table()
                    print_green('Created table: {}'.format(entry))
                except peewee.OperationalError:
                    print_yellow('Table already exists: {}'.format(entry))

    # Built-in
    built_in_modules = import_module('.modules', package='pa')
    for entry in dir(built_in_modules):
        module = getattr(built_in_modules, entry)
        init_tables(module)

    # User-defined
    for entry in os.listdir(MOD_DIR):
        path = os.path.join(MOD_DIR, entry)
        if os.path.isfile(path) and path.endswith('.py'):
            spec = spec_from_file_location("module", path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            init_tables(module)
