'''\
pa toggl - Command line toggl tracking and push to STATs

Manage toggl timers from the command line. (You will need to add your
toggl api token to your config file and enable toggl to use this module.)

Usage:
  pa toggl start <project> [<details>...]
  pa toggl stop
  pa toggl [options]
  pa toggl (-h | --help)

Options:
  -s, --status                          Show the current timer status.
  -b <period>, --breakdown <period>     Display a breakdown of the time spent
                                        on each tracked project for the given
                                        period. Periods are: [d]ay, [w]eek,
                                        [m]onth or [y]ear.
'''
#  -u, --update-stats                    Update the SEI-Y STATs system with
#                                        hours worked so far this week on SEI
#                                        projects.
from collections import defaultdict
from datetime import datetime, date, timedelta

import requests
from requests.auth import HTTPBasicAuth

from ..utils import get_config, print_red


SUMMARY = 'Manage toggl timers and view breakdowns'

# Toggl API urls
WORKSPACE_URL = 'https://www.toggl.com/api/v8/workspaces'
DATA_URL = 'https://toggl.com/reports/api/v2/details'


def run(args):
    '''
    Entry point for the cli application.
    '''
    config = get_config()

    if not config['toggl']['enabled']:
        print_red('Toggl functionality is not enabled. See config file.')
        exit()

    if args['start']:
        project = args['<project>']
        details = ' '.join(args['<details>'])
        start_timer(config, project, details)
    elif args['stop']:
        stop_active_timer(config)
    elif args['--status']:
        get_status(config)
    elif args['--breakdown']:
        period = args['--breakdown']
        get_breakdown(config, period)
    else:
        print(__doc__)
        exit()


def start_timer(config, project, details):
    '''
    Start a toggl timer
    '''
    pass


def stop_active_timer(config):
    '''
    Stop the current active toggl timer
    '''
    pass


def get_status(config):
    '''
    Show the status of the current toggl timer
    '''
    pass


def get_breakdown(config, period):
    '''
    Display a breakdown of the time spent on each project being tracked
    within the user's toggl account.
    '''
    pass


def _make_request(config, url, params={}):
    '''
    Make an API request
    '''
    api_token = config['toggl']['api_token']
    headers = {'content-type': 'application/json'}
    full_params = {'user_agent': 'aardvark'}
    full_params.update(params)

    resp = requests.get(
        url,
        params=full_params,
        headers=headers,
        auth=HTTPBasicAuth(api_token, 'api_token'),
    )

    if not resp.ok:
        raise requests.HTTPError()

    return resp.json()


def get_toggl_data(config, start, stop):
    resp = _make_request(config, WORKSPACE_URL)
    workspace_id = resp[0]['id']

    # Get the week's raw data from toggl
    params = {
        'since': start,
        'until': stop,
        'workspace_id': workspace_id,
    }

    toggl_data = _make_request(config, DATA_URL, params=params)

    # The response is a JSON array of time entries which we flatten into:
    # {project: {date: total hours (decimal), ...}, ...}
    data = defaultdict(lambda: defaultdict(float))

    # Collect all of the time spent each day (in case of multiple entries)
    for entry in toggl_data['data']:
        # NOTE: This is discarding the timezone info which will break
        #       for users far enough away from UTC.
        entry_date = datetime.strptime(
            entry['start'].split('T')[0],
            '%Y-%m-%d'
        ).date()

        # Toggl timer durations are in milliseconds for some reason...
        duration = entry['dur'] / 1000 / 60 / 60

        data[entry['project']][entry_date] = round(
            data[entry['project']][entry_date] + duration, 2)

    return data
