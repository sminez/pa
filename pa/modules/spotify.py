'''\
pa spotify - Control the Linux Spotify desktop app from the commandline

For this to work you need to have the Spotify application open already
as all this script does is send dbus commands to the running process.

Adding a new playlist:
  - Playlist names are stored in config and map to Spotify URIs
  - In Spotify, click on the triple dot icon, share, Copy Spotify URI
  - Add this to your config.toml under the name that you want to use:
    [spotify]
    my_awesome_playlist='<URI from Spotify>'

Usage:
  pa spotify start <playlist>
  pa spotify play
  pa spotify pause
  pa spotify next
  pa spotify prev
  pa spotify current
  pa spotify list
  pa spotify (-h | --help)
'''
import dbus
from subprocess import Popen, PIPE
from ..utils import get_config, print_red, print_yellow, print_green


SUMMARY = 'control the Linux Spotify desktop app'


def run(args):
    '''
    Entry point for the cli application.
    '''
    config = get_config()

    if args['play']:
        player_action('Play')

    elif args['pause']:
        player_action('Pause')

    elif args['next']:
        player_action('Next')

    elif args['prev']:
        player_action('Previous')

    elif args['<playlist>']:
        key = args['<playlist>']
        uri = config['spotify'].get(key)

        if uri is None:
            keys = '\n  '.join(config['spotify'].keys())
            print_red(f'"ERROR: {key}" is not a known playlist')
            print_yellow(f'Available playlists are:\n  {keys}')
            exit(42)

        play_uri(uri)

    elif args['current']:
        current_song()

    elif args['list']:
        keys = '\n  '.join(config['spotify'].keys())
        print_yellow(f'Available playlists are:\n  {keys}')


def _cmd(action, arg=''):
    '''Send a command via dbus.'''
    base_cmd = 'qdbus org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2'
    # ' org.mpris.MediaPlayer2.Player.OpenUri'
    # ' spotify:track:1WNPappMd13lY5o9POZ4gU3'
    cmd = ' '.join([base_cmd, action, arg])
    Popen(cmd, shell=True, stdout=PIPE)


def player_action(action):
    '''Run a media player action on the current playback'''
    _cmd(f'org.mpris.MediaPlayer2.Player."{action}"')


def play_uri(uri):
    '''Start playing a spotify uri'''
    _cmd(f'org.mpris.MediaPlayer2.Player.OpenUri {uri}')


def get_metadata():
    try:
        session_bus = dbus.SessionBus()
        bus = session_bus.get_object(
            "org.mpris.MediaPlayer2.spotify",
            "/org/mpris/MediaPlayer2")
    except Exception:
        print_red('Unable to connect to Spotify. Is it running?')
        exit(42)

    properties = dbus.Interface(bus, "org.freedesktop.DBus.Properties")
    metadata = properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    return metadata


def show_metadata():
    metadata = get_metadata()
    for k, v in metadata.items():
        print_yellow(f'{k}: {v}')


def current_song():
    '''Show the currently playing song'''
    metadata = get_metadata()
    artist = metadata['xesam:artist'][0]
    title = metadata['xesam:title']
    print_green(f'{artist}: {title}')
