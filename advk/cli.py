'''\
              aardvark - The ADHD Assistant

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

This is primarily a personal project so ymmv with getting
it integrated into your own workflow.
aardvark is extensible and is built using docopt.

Usage:
  advk <command> [<args>...]
  advk (-h | --help)
  advk --version

Options:
  -h, --help    Display this message and exit
  --version     Display the current version of this program

Commands:
  howto         HOWTO Human: reminders, schedules and procedures for life
  note          Create and manage markdown note files
  toggl         Manage toggl timers and view breakdowns
  todo          Create, manage and sync todo's with todoist
  mail          Search your gmail account
  cal           View and edit your google calendar

Use 'advk <command> --help' for specific information regarding a sub command
'''
from docopt import docopt
from importlib import import_module
from importlib.util import find_spec
from traceback import print_exc


__version__ = '0.0.2'


def main(argv=None):
    args = docopt(
        __doc__,
        argv=argv,
        version=__version__,
        options_first=True,
    )

    command = args['<command>']
    argv = [command] + args['<args>']

    try:
        module = import_module('.' + command, package='advk')
        args = docopt(module.__doc__, argv=argv)
        module.run(args)
    except ImportError:
        if find_spec('.' + command, package='advk'):
            print("Module '%s' failed to load" % command)
            print("Error was:")
            print_exc()
            exit()
        else:
            exit(
                "%s is not a aardvark command. See 'aard --help'" % (command)
            )


# def main():
#     '''
#     Run the CLI aardvark tool.
#     '''
#     args = get_args()
#     tags = ', '.join(args.tags)

#     if args.quick:
#         # Ensure that the path exists and the file is there with the header
#         qnote_file = ensure_default_qnote()

#         note = args.note + ' ' + ' '.join(args.tags)

#         # Add the quick note
#         with open(qnote_file, 'a') as f:
#             f.write('- [ ] {}\n'.format(note))

#     elif args.quick_show:
#         qnote_file = ensure_default_qnote()
#         subprocess.run(['vim', qnote_file])

#     elif args.todo:
#         # Look for TODO items in daily notes and the notes folder
#         os.chdir(NOTE_ROOT + '/daily-notes')
#         subprocess.run(
#             r'ag "\[[ o+]\]" ',
#             shell=True,
#         )
#         # os.chdir(NOTE_ROOT + '/notes')
#         # subprocess.run(
#         #     r'ag "\[[ o+]\]" ',
#         #     shell=True,
#         # )

#     elif args.list:
#         os.chdir(NOTE_ROOT)
#         print('{} Current notes: {}'.format(GREEN, NC))
#         subprocess.run(['ls', 'notes'])

#     elif args.grep:
#         os.chdir(NOTE_ROOT + '/daily-notes')
#         subprocess.run(['ag', args.grep])
#         os.chdir(NOTE_ROOT + '/notes')
#         subprocess.run(['ag', args.grep])

#     elif args.open:
#         subprocess.run(['vim', NOTE_ROOT + '/notes'])

#     elif args.sync:
#         tasks = today_and_overdue()
#         IDs = {t[0] for t in tasks}
#         new_tasks = []
#         completed_tasks = []
#         closed = []
#         local_open = []

#         qnote_file = ensure_default_qnote()

#         with open(qnote_file, 'r') as f:
#             lines = f.readlines()

#         for n, line in enumerate(lines):
#             # Find open tasks
#             if line.startswith('- [ ]'):
#                 task = line[5:-1]
#                 # Don't re-add tasks with an existing ID
#                 if not re.match(r'- \[ \] \(\d*\)', line):
#                     new_tasks.append((n, task))
#                 else:
#                     # check for open local tasks that are now closed
#                     parts = line[6:-1].partition(') ')
#                     try:
#                         ID, task = int(parts[0][1:]), parts[2]
#                         local_open.append((n, ID, task))
#                     except ValueError:
#                         # This wasn't a task ID so skip it
#                         pass
#             # Find completed tasks
#             elif line.startswith('- [x] ('):
#                 parts = line[6:-1].partition(') ')
#                 try:
#                     ID, task = int(parts[0][1:]), parts[2]
#                     completed_tasks.append((ID, task))
#                 except ValueError:
#                     # This wasn't a task ID so skip it
#                     pass

#         # Close completed tasks in Todoist
#         for ID, task in completed_tasks:
#             if ID in IDs:
#                 try:
#                     close_task(ID)
#                     print('{}Closed "{}"{}'.format(YELLOW, task, NC))
#                     closed.append(ID)
#                 except:
#                     print('{}Unable to close task: {}{}'.format(RED, ID, NC),
#                           file=sys.stderr)

#         for n, ID, task in local_open:
#             if ID not in IDs:
#                 # The task is now closed in Todoist so close locally as well
#                 lines[n] = line[:3] + 'x' + line[4:]

#         # Add new tasks to Todoist
#         for n, task in new_tasks:
#             try:
#                 ID = new_task(task)
#                 lines[n] = '- [ ] ({}) '.format(ID) + lines[n][6:]
#                 print('{}Added "{}" to Todoist{}'.format(GREEN, task, NC))
#             except:
#                 print(
#                     '{}Unable to add task to Todoist: {}{}'.format(RED, task, NC),
#                     file=sys.stderr)

#         # Add new tasks from Todoist
#         for ID, task in tasks:
#             if ID not in closed:
#                 for line in lines:
#                     if str(ID) in line:
#                         break
#                 else:
#                     lines.append('- [ ] ({}) {}\n'.format(ID, task))
#                     print('{}Adding "{}" from Todoist{}'.format(GREEN, task, NC))

#         # Update the quicknote file
#         with open(qnote_file, 'w') as f:
#             f.writelines(lines)

#         # Push notes to bitbucket
#         os.chdir(NOTE_ROOT)
#         print('{}Pushing notes to bitbucket...{}'.format(GREEN, NC))
#         subprocess.run('git add notes/ daily-notes/', shell=True)
#         subprocess.run(
#             'git commit -m"Updating notes: {}"'.format(_today()),
#             shell=True)
#         subprocess.run('git push', shell=True)


#     else:
#         if args.note is None:
#             parser.print_help()
#             sys.exit(42)

#         # Open the note file for editing
#         if args.note.endswith(NOTE_FORMAT):
#             note_file = NOTE_ROOT + '/notes/{}'.format(args.note)
#         else:
#             note_file = NOTE_ROOT + '/notes/{}.{}'.format(args.note, NOTE_FORMAT)

#         if not os.path.exists(note_file):
#             with open(note_file, 'w') as f:
#                 f.write(TEMPLATE.format(date, tags) + '\n')

#         subprocess.run([EDITOR, note_file])


if __name__ == '__main__':
    import sys
    main(sys.argv)
