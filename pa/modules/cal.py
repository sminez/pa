'''
pa cal - Check upcoming events in your calendars

The default query (no arguments) is to look at all calendars for
the next 7 days.
Dates should be provided in 'yyy-mm-dd' format.

Usage:
  pa cal list
  pa cal show [--from=<date>] [--to=<date>] [--cal=<name>]
  pa cal (-h | --help)
'''
from datetime import datetime, date, timedelta

import requests
from pytz import utc
from icalendar import Calendar

from ..utils import get_config, print_red, print_yellow, print_green


SUMMARY = 'View upcoming events in your calendars'

DEFAULT_QUERY_LENGTH = timedelta(days=7)
DEFAULT_ENCODING = 'utf-8'


def run(args):
    '''
    Entry point for the cli application.
    '''
    def str_to_date(s):
        try:
            return date(*(int(n) for n in s.split('-')))
        except Exception as e:
            raise ValueError('Invalid date given: {}\n{}'.format(s, e))

    config = get_config()

    if args['list']:
        show_calendars(config)
        exit()

    start = args['--from']
    if start is not None:
        start = str_to_date(start)

    end = args['--to']
    if end is not None:
        end = str_to_date(end)

    cal = args['--cal']

    if cal:
        # Only run for this calendar
        url = config['cal']['calendars'].get(cal)
        if url is None:
            print_red('{} is not a configured calendar'.format(cal))
            show_calendars(config)
            exit()

        show_events(cal, url, start, end)
    else:
        # Run for all calendars
        for cal, data in config['cal']['calendars'].items():
            url = data['url']
            show_events(cal, url, start, end)


def show_calendars(config):
    '''
    Show each of the currently configured calendars
    '''
    print_green('Configured calendars are:')
    for c in config['cal']['calendars']:
        print('  {}'.format(c))


def show_events(cal, url, start=None, end=None):
    '''
    Show all of the events in the given time range
    '''
    print_yellow('[{}]'.format(cal))
    for e in events(url, start=start, end=end):
        print(e)
    print()


def events(url=None, start=None, end=None, encoding=DEFAULT_ENCODING):
    '''
    Get all events form the given iCal URL occurring in the given time range.
    '''
    if url.startswith('webcal://'):
        url = url.replace('webcal://', 'http://', 1)

    resp = requests.get(url)

    if not resp.ok:
        raise ConnectionError(
            'Unable to fetch data from {}'.format(url)
        )

    content = resp.content.decode(encoding)
    content = content.replace('\r', '')

    # Fix Apple tzdata bug.
    content = content.replace('TZOFFSETFROM:+5328', 'TZOFFSETFROM:+0053')

    return parse_events(content, start=start, end=end)


def parse_events(content, start=None, end=None):
    '''
    Fetch all events in the given time range.
    '''
    if start is None:
        start = utc.localize(datetime.utcnow())

    if end is None:
        end = start + DEFAULT_QUERY_LENGTH

    start, end = map(normalize, [start, end])
    calendar = Calendar.from_ical(content)
    found = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            evt = Event(component)

            if evt.start <= end and evt.end >= start:
                # Event is in range so keep it
                found.append(evt)

    # Sort into ascending order
    return sorted(found)


def normalize(dt):
    '''
    Convert date or datetime to datetime with timezone.
    '''
    if not isinstance(dt, datetime):
        # convert the date to a datetime
        dt = datetime.combine(dt, datetime.min.time())

    if not dt.tzinfo:
        dt = utc.localize(dt)

    return dt


class Event:
    '''A single calendar event'''

    def __init__(self, component):
        '''
        Create a new event occurrence from an iCal component.
        '''
        self.all_day = False

        event_start = component.get('dtstart')
        if event_start is None:
            raise ValueError('Event must have a start date')

        if type(event_start.dt) is date:
            self.all_day = True

        event_start = normalize(event_start.dt)

        event_end = component.get('dtend')
        if event_end is not None:
            event_end = normalize(event_end.dt)
        else:
            # This is a single day all day event
            event_end = event_start + timedelta(days=1)
            self.all_day = True

        if component.get('rrule'):
            rule = component.get('rrule')
            freq = str(rule.get('FREQ')[0])
            recurring = True
        else:
            recurring = False
            freq = None

        self.start = event_start
        self.end = event_end
        self.summary = str(component.get('summary'))
        self.description = str(component.get('description'))
        self.recurring = recurring
        self.freq = freq

    def __lt__(self, other):
        '''
        Sort by start time
        '''
        if type(other) is not Event:
            raise TypeError('Can only compare events with each other.')
        else:
            return self.start < other.start

    def __str__(self):
        now = utc.localize(datetime.utcnow())
        time_left = self.start - now

        # Get a string repr of the time remaining on the event
        if self.start < now < self.end:
            msg = 'ongoing'
        elif self.start > now:
            # In the future
            if self.all_day:
                msg = '{} days left'.format(time_left.days)
            elif time_left.days > 0:
                msg = '{} days left'.format(time_left.days)
            else:
                hours = time_left.seconds // (60 * 60)
                s = 's' if hours == 1 else ''
                msg = '{} hour{} left'.format(hours, s)
        else:
            msg = 'ended'

        # Mark recurring events
        recur = ''
        if self.recurring:
            recur = ': recurring [{}]'.format(self.freq)

        start = self.start.strftime('%Y-%m-%d (%H:%M)')

        return '{}: {} ({}{})'.format(start, self.summary, msg, recur)
