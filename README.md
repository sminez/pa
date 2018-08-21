pa - An ADHD Personal Assistant
===============================

`pa` is intended to be a great old pot of glue that holds together my daily work
flow in terms of managing web services via their APIs (if available), local
content (using git/the file system/SQLite) and reminding me of the things that I
have most likely forgotten.

Individual modules/sub-commands follow a UNIX philosophy of being responsible
for a single thing and doing it well. `pa` itself is a horrible hydra that holds
everything together!


### Config
`pa` is configured via the `pa.toml` file (located at `~/.config/pa/pa.toml`. An
example configuration is shown below:
```toml
[general]
ag_enabled=true
editor='vim'

[note]
note_root='~/notes'

[todoist]
enabled=true
api_token='supersecretapitoken1'

[toggl]
enabled=true
api_token='supersecretapitoken2'

[mail]
enabled=true
oath2=false

[mail.accounts]
  [mail.accounts.personal]
  server='imap.gmail.com'
  username='myusername'

  [mail.accounts.work]
  server='imap.gmail.com'
  username='myusername@work.com'

[cal]
enabled=false
```

Sub-commands _should_ provide details on their own config options (but at
present do not...).


### Sub-Commands
All sub-commands should be a single file in the `modules` directory with their
docstring being a `docopt` valid specification and a top level `SUMMARY` string.

"User" created modules (and things I don't want in the main repo) can be placed
in `~/.config/pa/user_modules` and `pa` will pick them up as if they were built
in. This is recommended as well for modules that are under development as it
means you don't need to constantly re-install `pa`.


### peewee
`pa` uses [peewee](https://github.com/coleifer/peewee) as an ORM for a local
SQLite database. Docs for ongoing development work can be found
[here](http://docs.peewee-orm.com/en/latest/peewee/).

### keyring
`pa` uses [keyring](https://github.com/jaraco/keyring) for local storage of
secure details in the OS keyring.


### File Storage
Local file storage (text files) is currently in the `~/notes` directory due to
maintaining compatibility with my original `notes` script. This may change in
the future.


### mail - less secure apps with google
At present, `pa` uses IMAP with standard username/password sign-in in order to
query your email inbox. In order to get this to work with gmail you need to
first enable IMAP through the gmail settings then follow the instructions
[here](https://support.google.com/accounts/answer/6010255?hl=en) to allow access
without Oath2.
Please make sure you are happy with the implications of this and that you have
read the code in `pa/modules/mail.py` and that you are happy with using this
kind of access to your account.
If you are not, then wait for Oath2 support to be implemented and disable the
mail module / do not add any account details into your config file.


### APIs
The following APIs are being used as part of `pa`:
- [toggl](https://github.com/toggl/toggl_api_docs)
- [todist](https://developer.todoist.com/sync/v7/)
- [google](https://console.developers.google.com/apis/credentials?authuser=0&project=pa---adhd-assist-1534778218277)
  [lib](https://developers.google.com/api-client-library/python/)


### TODO
- [ ] Implement todo database functionality
  - This is most likely going to be a move away from the daily todo files
  entirely and instead only storing todos in the db.
  - Editing of ongoing todos can then be done by writing out a temp file,
  opening in vim, reading back the file and updating the db.
- [ ] Re-think daily notes
  - Some sort of daily todo's / ongoing notes is useful (it helped a lot at
  Cocoon) but the current system isn't great.
  - Auto-parsing todos out of the daily file and adding to the db for bonus
  points!
- [ ] Work out how to query google calendar details
  - Ideally without having to register an app with google...
- [ ] Decide on a format / storage for HOWTO files.
  - Store in the DB?
  - Keep as plain-text notes?
  - Ideally they should be machine readable in order to allow for automated
  actions being run.
- [ ] Re-read the toggl API and implement the toggl module
