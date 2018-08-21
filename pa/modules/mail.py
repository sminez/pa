'''\
pa mail - Quick querying of your email

The default query will look in both the body of the email and the headers
(including subject line). A summary of the message will be shown by default
unless the `--full` flag is passed.
For more specific querying, use one of the options listed below. Note that
queries may optionally use boolean AND/OR clauses if needed.

Usage:
  pa mail <query> [--full] [--max=<n>] [--account=<name>]
  pa mail [options] [--full] [--max=<n>] [--account=<name>]
  pa mail accounts
  pa mail (-h | --help)

Options:
  -f, --from <query>    Query the 'from' field (does not need to be a
                        full email address)
  -b, --before <date>   Messages before a given date in yyy-mm-dd format.
  -a, --after <date>    Messages after a given date in yyy-mm-dd format.
  -o, --on <date>       Messages on a given date in yyy-mm-dd format.
  -n, --new             All recent messages that have not been seen yet.
'''
import email
import getpass
import imaplib

from ..utils import get_config, print_red, print_yellow, print_green


SUMMARY = 'Query your email inboxes via IMAP'
MSG_SUMMARY_LEN = 400


def run(args):
    '''
    Entry point for the cli application.
    '''
    config = get_config()
    accounts = config['mail']['accounts']
    full = args['--full']
    count = args['--max']
    count = int(count) if count else count

    if args['accounts']:
        print_green('Configured accounts are:')
        for account in accounts:
            print(account)
        exit()

    try:
        method, query = get_imap_key(args)
    except ValueError:
        print(__doc__)
        exit()

    account = args['--account']

    if account:
        # Only run for the selected account
        details = accounts[account]
        process_account(account, details, method, query, full, count)
        exit()

    # Otherwise run for all configured accounts
    for account, details in accounts.items():
        process_account(account, details, method, query, full, count)


def process_account(account, details, method, query, full, count):
    '''
    Run the selected query for a given account
    '''
    m = MailBox(
        username=details['username'],
        password=getpass.getpass(),
        server=details['server']
    )

    try:
        results = m._query(method, (query,), full=full)
        print_green('[{}]'.format(account))
        for i, json_msg in enumerate(results):
            if i == count:
                break

            for section, content in json_msg.items():
                end = ':\n' if section == 'body' else ': '
                print_yellow(section, end=end)
                print(content)

            # Separator
            print('\n', '-' * 80, '\n')

    except Exception as e:
        print_red('Error querying mailbox: {}'.format(e))


class MailBox:
    '''
    A custom wrapper for querying an email inbox vis IMAP

    This should realy be done using oath not direct login:
        https://github.com/google/gmail-oauth2-tools/wiki/OAuth2DotPyRunThrough
    '''

    def __init__(self, username, password, server='imap.gmail.com'):
        self.username = username
        self.client = imaplib.IMAP4_SSL(server)
        self.client.login(username, password)
        # Select the default folder
        self.client.select()

    def _query(self, key, args=(), folder=None, full=False):
        '''
        Run an rfc3501 SEARCH query and iterate over the messages returned

        See section 6.4.4 of the rfc for details on query syntax:
            http://www.faqs.org/rfcs/rfc3501.html

        Examples:
        >>> results = m._query('BODY', ('quicycle',))
            # Anywhere not just the body
            results = m._query('TEXT', ('quicycle',))
            results = m._query('FROM', ('katie@katiemanderson.com',))
            results = m._query('NEW')
        '''
        if folder is not None:
            self.client.select(folder)

        _, data = self.client.search(None, key, *args)

        for num in data[0].split():
            typ, data = self.client.fetch(num, '(RFC822)')
            msg = email.message_from_string(data[0][1].decode('utf-8'))
            yield json_message(msg, full)


def get_imap_key(args):
    '''
    Turn an argument flag into an IMAP key
    '''
    if args['--from']:
        return 'FROM', args['--from']
    elif args['--before']:
        return 'BEFORE', args['--before']
    elif args['--after']:
        return 'SINCE', args['--after']
    elif args['--on']:
        return 'ON', args['--on']
    elif args['--new']:
        return 'NEW', ''

    if args['<query>'] is None:
        # Catch in run and show help
        raise ValueError()

    return 'TEXT', args['<query>']


def get_body(msg, full=False):
    '''
    Extract the body from a message, optionally returning the full message
    but by default returning a summary of length MSG_SUMMARY_LEN.
    '''
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition'))

            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in disp:
                body = part.get_payload(decode=True)
                break
    else:
        # not multipart - i.e. plain text, no attachments (hopefully!)
        body = msg.get_payload(decode=True)

    try:
        body = body.decode()
    except UnicodeDecodeError:
        pass

    if full:
        return body
    else:
        return body[:MSG_SUMMARY_LEN]


def json_message(msg, full=False):
    '''
    Convert a message to a JSON payload (python dict) of the fields that
    we care about.
    '''
    cc = msg.get('Cc')
    if cc is not None:
        cc = [c.strip() for c in cc.split(',')]

    bcc = msg.get('Bcc')
    if bcc is not None:
        bcc = [b.strip() for b in bcc.split(',')]

    return {
        'id': msg.get('Message-ID'),
        'to': msg.get('To'),
        'cc': cc,
        'bcc': bcc,
        'from': msg.get('From'),
        'date': msg.get('Date'),
        'subject': msg.get('Subject'),
        'body': get_body(msg, full)
    }
