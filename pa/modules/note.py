'''\
pa note - Command line note management and search

Usage:
  pa note <title>
  pa note [options]
  pa note (-h | --help)

Options:
  -g <pattern>, --grep <pattern>    Grep your notes
  -l, --list                        List the contents of your notes directory
  -s, --sync                        Sync the local notes to the remote git repo
'''
import os
import re
import subprocess
from datetime import datetime

from .._utils import today, get_config, TEMPLATE, GREEN, NC


SUMMARY = 'Create and manage markdown note files'


def run(args):
    '''
    Entry point for the cli application
    '''
    config = get_config()

    if args['--list']:
        list_notes(config)
    elif args['--grep']:
        grep_notes(config, args['--grep'])
    elif args['--sync']:
        sync(config)
    else:
        title = args['<title>']
        if title is None:
            print(__doc__)
            exit()

        # Start a new note
        create_note(config, title)


def list_notes(config):
    '''
    Show the contents of the notes directory
    '''
    os.chdir(config.get('note', 'note_root'))
    print('{} Current notes: {}'.format(GREEN, NC))
    subprocess.run(['ls', 'notes'])


def grep_notes(config, pattern):
    '''
    Grep through the notes and daily_notes for a given pattern.
    If `ag` is enabled then prefer that over searching in python
    '''
    use_ag = config.getboolean('general', 'ag_enabled')
    note_root = config.get('note', 'note_root')

    for subdir in ['/daily-notes', '/notes']:
        if use_ag:
            os.chdir(note_root + subdir)
            subprocess.run(['ag', pattern])
        else:
            _grep(note_root + subdir, pattern)


def sync(config):
    '''
    Push the local note content to the remote git repo
    '''
    os.chdir(config.get('note', 'note_root'))
    print('{}Pushing notes to remote repo...{}'.format(GREEN, NC))
    subprocess.run('git add -A', shell=True)
    subprocess.run(
        'git commit -m"Updating notes: {}"'.format(today()),
        shell=True)
    subprocess.run('git push', shell=True)


def create_note(config, title):
    '''
    Start a new note file, opening it in the editor
    '''
    today = datetime.today()
    y, m, d = today.year, today.month, today.day
    date = '{}/{}/{}'.format(y, m, d)

    root = config.get('note', 'note_root')

    # Make sure we have a notes directory
    note_dir = os.path.join(root, 'notes')
    if not os.path.isdir(note_dir):
        os.mkdir(note_dir)

    note_file = '{}/notes/{}.md'.format(root, title)

    editor = config.get('general', 'editor')

    if not os.path.exists(note_file):
        with open(note_file, 'w') as f:
            f.write(TEMPLATE.format(date, '') + '\n')

    subprocess.run([editor, note_file])


def _grep(base_directory, pattern):
    '''
    `grep` for a pattern in all files in a directory
    '''
    pattern = re.compile(pattern)

    for base_path, _, fnames in os.walk(base_directory):
        for fname in fnames:
            has_matches = False
            path = os.path.join(base_path, fname)

            with open(path, 'r') as f:
                for lno, line in enumerate(f):
                    if pattern.search(line):
                        if not has_matches:
                            # Print header
                            print('\n[{}]'.format(path))
                            has_matches = True

                        print('{}: {}'.format(lno+1, line.strip()))
