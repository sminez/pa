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
  pa <command> [<args>...]
  pa [options]
  pa init

Options:
  -s, --sync        Run the sync scripts for all sub-commands
  -h, --help        Display this message and exit
  -v, --version     Display the current version of this program

Commands:
{}
Use 'pa <command> --help' for specific information regarding a sub command
'''
import os
from traceback import print_exc
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec

from docopt import docopt

from .db import db_init
from .utils import get_config, init_config_dir, print_red, MOD_DIR


__version__ = '0.3.3'


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
        init_config_dir()
        db_init(MOD_DIR)
        exit()
    elif args['--sync']:
        # Sync everything
        # NOTE: sync must take only the config as an argument
        config = get_config()
        for mod in cmd_map.values():
            if 'sync' in dir(mod):
                mod.sync(config)
        exit()
    elif args['<command>'] is not None:
        if args['<command>'].startswith('_comp'):
            # private helper functions for zsh completions
            _completion_helper(args['<command>'], args['<args>'])
            exit()
    else:
        # <command> is None and no flags set
        print(__doc__.format(cmd_str))
        exit()

    # We were passed a command so try to run it
    command = args['<command>']
    argv = [command] + args['<args>']

    try:
        module = cmd_map[command]
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
            cmd_map[entry] = module

    # User-defined
    for entry in os.listdir(MOD_DIR):
        path = os.path.join(MOD_DIR, entry)
        if os.path.isfile(path) and valid_module(entry):
            spec = spec_from_file_location("module", path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            cmd = entry[:-3]
            sub_commands.append((cmd, module.SUMMARY))
            cmd_map[cmd] = module

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


def _completion_helper(cmd, args):
    '''
    Output helper text for the _pa zsh completion file to use.
    '''
    sub_commands, cmd_map = get_sub_commands()

    if cmd == '_comp_sub_commands':
        # output zsh format completion descriptions
        comps = []
        for cmd, summary in sub_commands:
            comps.append('{}:{}'.format(cmd, summary))
        print('\n'.join(comps))

    elif cmd == '_comp_note_root':
        # Display the user's note root directory
        config = get_config()
        print(config['note']['note_root'])
