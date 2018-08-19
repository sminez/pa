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

##### Spec
All modules should be a single file in the `modules` directory with their
docstring being a `docopt` valid specification and a top level `SUMMARY` tuple
of (module-name, description).
