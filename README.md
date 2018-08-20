pa - An ADHD Personal Assistant
===============================

`pa` is intended to be a great old pot of glue that holds together my daily work
flow in terms of managing web services via their APIs (if available), local
content (using git) and reminding me of the things that I have most likely
forgotten.


### Modular
`pa` has a modular design that should allow me to add new sub-commands and
functionality as and when I need it. Ideally, all `pa` generated content will
live in the same directory (alongside the code?) and all API actions should work
on a sync basis. (Determining which is correct: local vs remote TBD).


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


### File Storage
Local file storage (text files) is currently in the `~/notes` directory due to
maintaining compatibility with my original `notes` script. This may change in
the future.
