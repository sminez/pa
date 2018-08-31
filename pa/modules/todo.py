'''\
pa todo - Command line TODO management with Todoist sync

Create, manage and sync TODOs from the command line. Running any of the
commands for the first time that day will migrate outstanding TODOs from the
previous file to today's.

The default action is to add the remaining command line arguments as a new todo
in todays TODO file.

Usage:
  pa todo <todo>...
  pa todo [options]
  pa todo (-h | --help)

Options:
  -l, --list    List today's outstanding TODOs
  -o, --open    Open the current TODO file in your editor
  -s, --sync    Sync the local TODO file with Todoist
'''
import os
import re
import sys
import json
import uuid
import subprocess
from datetime import datetime, date

import peewee
from requests import get, post, HTTPError

from ..db import PaModel
from ..utils import today, get_config, print_red, print_yellow, \
    print_green, TEMPLATE


SUMMARY = 'Create, manage and sync todo\'s with todoist'
URL = 'https://beta.todoist.com/API/v8/{}'


# TODO: add tables for labels and projects
class Todo(PaModel):
    '''
    A TODO with associated metadata.

    This is intended to map nearly 1-1 with the JSON response from the
    todoist API.
    '''
    id = peewee.IntegerField(unique=True)
    project_id = peewee.IntegerField(null=True)
    completed = peewee.BooleanField(default=False)
    content = peewee.TextField()
    label_ids_str = peewee.CharField(null=True)
    due_date = peewee.DateField(null=True)
    due_time = peewee.DateTimeField(null=True)
    url = peewee.CharField(null=True)
    priority = peewee.IntegerField()

    @property
    def label_ids(self):
        '''
        A nasty hack but this lets us store all of the label ids in
        a single field rather than creating an entire label_id table
        to allow for todos to have more than one field.
        '''
        return self.label_ids_str.split(',')

    @staticmethod
    def format_json_for_insert(data):
        '''
        Format the JSON response from todoist for the creation of Todo
        instances.
        The resulting dictionary can be used either as:
        >>> t = Todo(*data)  # Single todo
        >>> t.save()

        Or:
        >>> Todo.insert_many([...]).execute() # array of todos

        NOTE: data should be a dictionary not a raw string
        '''
        data['label_ids_str'] = ','.join(str(i) for i in data['label_ids'])

        due = data.get('due')
        if due:
            d = due.get('date')
            dt = due.get('datetime')
            if dt:
                due['due_date'] = date(*map(int, d.split('-')))
            if dt:
                due['due_time'] = datetime.strptime(
                    dt + due['timezone'].replace(':', ''),
                    '%Y-%m-%dT%H:%M:%SZUTC%z'
                )
            del(data['due'])

        del(data['order'])
        del(data['indent'])
        del(data['label_ids'])
        del(data['comment_count'])

        return data

    @classmethod
    def fetch_all_open(cls):
        '''
        Pull all currently open tasks and load them into the database.
        '''
        config = get_config()
        tasks = query(config, get, 'tasks')
        tasks = [cls.format_json_for_insert(t) for t in tasks]
        cls.insert_many(tasks).execute()


def run(args):
    '''
    Entry point for the cli application.
    '''
    config = get_config()

    # Ensure that the path exists and the file is there with the header
    todo_file = ensure_default_todo_file(config)

    if args['--list']:
        list_todo(config)

    elif args['--open']:
        quick_open(todo_file, config)

    elif args['--sync']:
        if not config['todoist']['enabled']:
            print_red('Todoist functionality is not enabled')
            exit()

        sync(config)

    else:
        todo = args['<todo>']
        if not todo:
            print(__doc__)
            exit()

        quick_todo(todo_file, args['<todo>'])


def query(config, req_func, endpoint, params={}, data=None, headers=None):
    '''
    Query the Todoist REST API using an api token
    '''
    if not config.get('todoist', 'api_token'):
        raise ValueError('No Todoist API token given in config')

    params['token'] = config['todoist']['api_token']
    resp = req_func(
        URL.format(endpoint),
        params=params,
        data=data,
        headers=headers
    )

    if 200 <= resp.status_code < 400:
        try:
            return resp.json()
        except json.JSONDecodeError:
            # TODO: confirm that this is the correct error
            return resp.text

    raise HTTPError(resp.reason)


def ensure_default_todo_file(config):
    '''
    Conditionally migrate over any notes from yesterday and open a new file
    '''
    root = config['note']['note_root']
    today = datetime.today()
    y, m, d = today.year, today.month, today.day
    date = '{}/{}/{}'.format(y, m, d)

    today_dir = root + '/daily-notes/{}/{}'.format(y, m)
    todo_file = today_dir + '/{}.md'.format(d)

    if not os.path.exists(today_dir):
        os.makedirs(today_dir)

    if not os.path.exists(todo_file):
        # Get the name of all of the files containing incomplete TODOs
        try:
            os.chdir(root + '/daily-notes')
        except FileNotFoundError:
            os.mkdir(root + '/daily-notes')
            os.chdir(root + '/daily-notes')

        if config['general']['ag_enabled']:
            res = subprocess.run(
                r'ag -l --nocolor "\[[ o+]\]"',
                shell=True,
                stdout=subprocess.PIPE
            )
            res = res.stdout.decode().split('\n')
        else:
            res = _get_open_todos(config)

        os.chdir(os.path.expanduser('~/'))

        old_todo_files = list(filter(lambda l: len(l) > 0, res))

        open_todos = []

        for fname in old_todo_files:
            old_notes = '{}/daily-notes/{}'.format(root, fname)

            with open(old_notes, 'r') as f:
                lines = f.readlines()

            for n, line in enumerate(lines):
                # Find open TODOs
                if line.startswith('- [ ]'):
                    open_todos.append((n, line))
                    lines[n] = line[:3] + '-' + line[4:]

            if open_todos:
                print_yellow('Moving existing TODOs to today:')
                for line, todo in open_todos:
                    print(todo[6:])

                with open(old_notes, 'w') as f:
                    f.writelines(lines)

        with open(todo_file, 'w') as f:
            f.write(TEMPLATE.format(date, '') + '\n')
            for line, todo in open_todos:
                f.write(todo)

    return todo_file


def quick_todo(todo_file, note_content):
    '''
    Add a new TODO to today's todo file
    '''
    # Add the quick note
    with open(todo_file, 'a') as f:
        f.write('- [ ] {}\n'.format(' '.join(note_content)))


def list_todo(config):
    '''
    List the current todos
    '''
    os.chdir(config['note']['note_root'] + '/daily-notes')
    subprocess.run(
        r'ag "\[[ o+]\]" ',
        shell=True,
    )


def quick_open(todo_file, config):
    '''
    Open today's TODO file in the user specified editor
    '''
    subprocess.run([config['general']['editor'], todo_file])


def today_and_overdue(config):
    '''Get tasks that need to be done today'''
    json_tasks = query(
        config, get, 'tasks', {'filter': '(overdue|{})'.format(today())})
    tasks = [(t['id'], t['content']) for t in json_tasks]
    return tasks


def close_task(config, task_id):
    '''Close a task by ID'''
    query(config, post, 'tasks/{}/close'.format(task_id))


def new_task(config, content, priority=1):
    '''Create a new task'''
    data = json.dumps({
        'content': content,
        'due_string': today(),
        'due_lang': 'en',
        'priority': 1
    })
    headers = {
        "Content-Type": "application/json",
        "X-Request-Id": str(uuid.uuid4()),
    }

    resp = query(config, post, 'tasks', data=data, headers=headers)
    return resp['id']


def sync(config):
    '''
    Align the local todos with todoist.
    '''
    todo_file = ensure_default_todo_file(config)
    tasks = today_and_overdue(config)
    IDs = {t[0] for t in tasks}
    new_tasks = []
    completed_tasks = []
    closed = []
    local_open = []

    with open(todo_file, 'r') as f:
        lines = f.readlines()

    for n, line in enumerate(lines):
        # Find open tasks
        if line.startswith('- [ ]'):
            task = line[5:-1]
            # Don't re-add tasks with an existing ID
            if not re.match(r'- \[ \] \(\d*\)', line):
                new_tasks.append((n, task))
            else:
                # check for open local tasks that are now closed
                parts = line[6:-1].partition(') ')
                try:
                    ID, task = int(parts[0][1:]), parts[2]
                    local_open.append((n, ID, task))
                except ValueError:
                    # This wasn't a task ID so skip it
                    pass
        # Find completed tasks
        elif line.startswith('- [x] ('):
            parts = line[6:-1].partition(') ')
            try:
                ID, task = int(parts[0][1:]), parts[2]
                completed_tasks.append((ID, task))
            except ValueError:
                # This wasn't a task ID so skip it
                pass

    # Close completed tasks in Todoist
    for ID, task in completed_tasks:
        if ID in IDs:
            try:
                close_task(config, ID)
                print_yellow('Closed "{}"'.format(task))
                closed.append(ID)
            except HTTPError:
                print_red('Unable to close task: {}'.format(ID),
                          file=sys.stderr)

    for n, ID, task in local_open:
        if ID not in IDs:
            # The task is now closed in Todoist so close locally as well
            lines[n] = line[:3] + 'x' + line[4:]

    # Add new tasks to Todoist
    for n, task in new_tasks:
        try:
            ID = new_task(config, task)
            lines[n] = '- [ ] ({}) '.format(ID) + lines[n][6:]
            print_green('Added "{}" to Todoist'.format(task))
        except HTTPError:
            print(
                'Unable to add task to Todoist: {}'.format(task),
                file=sys.stderr)

    # Add new tasks from Todoist
    for ID, task in tasks:
        if ID not in closed:
            for line in lines:
                if str(ID) in line:
                    break
            else:
                lines.append('- [ ] ({}) {}\n'.format(ID, task))
                print_green('Adding "{}" from Todoist'.format(task))

    # Update the quicknote file
    with open(todo_file, 'w') as f:
        f.writelines(lines)


def _get_open_todos(config):
    '''
    Find all open todos
    '''
    pattern = re.compile('\[[ o+]\]')
    base = config['note']['note_root'] + '/daily-notes'

    note_files = []

    for path, _, fnames in os.walk(base):
        for fname in fnames:
            path = os.path.join(base, fname)

            with open(path, 'r') as f:
                for line in f:
                    if pattern.search(line):
                        note_files.append(fname)
                        break

    return note_files
