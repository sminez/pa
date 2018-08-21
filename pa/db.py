'''
Database functionality for pa via peewee.
'''
import os
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec

import peewee

from .utils import print_yellow, print_green, MOD_DIR


# Location of the pa sqlite database
DB_PATH = os.path.expanduser('~/.config/pa/pa.db')
DB = peewee.SqliteDatabase(DB_PATH)


class PaModel(peewee.Model):
    '''
    Base Class for pa DB models. This should be inherited from for all
    database models in order to enable us to auto-init the db and provide
    common functionality.
    '''
    class Meta:
        database = DB


def db_init(mod_dir=MOD_DIR):
    '''
    Initialise the local SQLite database by walking each of the built-in and
    user modules, looking for PaModel classes and creating a table for each
    one that we find.
    '''
    # Built-in
    built_in_modules = import_module('.modules', package='pa')
    for entry in dir(built_in_modules):
        module = getattr(built_in_modules, entry)
        init_tables(module)

    # User-defined
    for entry in os.listdir(mod_dir):
        path = os.path.join(mod_dir, entry)
        if os.path.isfile(path) and path.endswith('.py'):
            spec = spec_from_file_location("module", path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            init_tables(module)


def init_tables(module):
    '''
    For a given module, find all occurances of PaModel and create the
    corresponding database tables in our local database.
    '''
    for entry in dir(module):
        mod = getattr(module, entry)

        if isinstance(mod, type) and issubclass(mod, PaModel):
            if entry == 'PaModel':
                # Don't create the base class
                continue
            try:
                mod.create_table()
                print_green('Created table: {}'.format(entry))
            except peewee.OperationalError:
                print_yellow('Table already exists: {}'.format(entry))
