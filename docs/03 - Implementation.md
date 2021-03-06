# Implementation Details

You can read from top to bottom. This will help understanding immensely.


## Preface

All the code must go within the `src/` directory and only the `main.py` must be
ran directly. This ensures consistency across the project, by restricting what
other files can do when ran directly.


## The Database

Hence we prefer hosting CrunchBang on Heroku, we opted to use MySQL with
SQLAlchemy python package.

Please check out [the tables](10%20-%20Tables.md) for information about the data we store.

The SQLAlchemy uses PostgreSQL on production whilst using sqlite on development
environments. This can be set in the `.env` file by setting `ENV=dev` or
`ENV=prod`.


## Commands

The CrunchBang, hence the name, uses `#!` as it's prefix for commands.
Commands must be grouped using interfaces, which must be stored in different
files.

However, one interface can use others' code by importing it.


## For the "Admin interface"

Commands that require `Admin` role must go under this category. Other commands
must be available to all members.


> Next, read [SQL Interface](04%20-%20SQL%20Interface.md)