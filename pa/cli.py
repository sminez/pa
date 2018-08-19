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

from docopt import docopt


__version__ = '0.1.1'
MOD_DIR = os.path.expanduser('~/.config/pa/user_modules')


def main(argv=None):
    sub_commands, cmd_map = get_sub_commands()
    cmd_str = format_sub_command_section(sub_commands)

    args = docopt(
        __doc__.format(cmd_str),
        argv=argv,
        version=__version__,
        options_first=True,
    )

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
        print("Module '{}' failed to load".format(command))
        print("Error was:")
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
