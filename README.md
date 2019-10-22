# Data Driven Acquisition

This system is a POC of a document management tool that will initiate acquisition document packages, and allow the acquisition work force to manage them as data. Handling some of the manual work of keeping the document up to date from an intuitive user interface.

- [Data Driven Acquisition](#data-driven-acquisition)
  - [Documentation](#documentation)
  - [Quickstart](#quickstart)
  - [Features](#features)
  - [Running Tests](#running-tests)
  - [Credits](#credits)


## Documentation

TODO : The full documentation is at https://data-driven-acquisition.readthedocs.io. 

## Quickstart

1. Database Setup
   1. install [PostgreSQL](https://www.postgresql.org/docs/9.3/tutorial-install.html).
   2. Create [database](https://www.postgresql.org/docs/9.0/sql-createdatabase.html)
2. Project set up
   1. Create project folder

   ```shell
   mkdir data-driven-acquisition
   ```

   2. Create virtual environment (using [virtual env wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/install.html) in this example).

   ```shell
   mkvirtualenv data-driven-acquisition --python=python3
   ```

   3. Install the requirements

   ```shell
   pip install -r requirements.txt
   ```

   4. Optional: Install the development and testing requirements if needed.

   ```shell
   pip install -r requirements_dev.txt
   pip install -r requirements_test.txt
   ```

   5. Create a .env file looking like so
  
   ```shell
   DEBUG=on
   SECRET_KEY=your-secret-key # Make it random
   DATABASE_URL=psql://DB_USER:DB_PASS@127.0.0.1:8458/DB_NAME
   ALLOWED_HOSTS=127.0.0.1,0.0.0.0
   ```

## Features

* TODO

## Running Tests

Does the code actually work?

```shell
    (myenv) $ pip install tox (or -r requirements_test.txt)
    (myenv) $ tox
```
Credits
-------

Tools used in rendering this package:

* [Cookiecutter](https://github.com/audreyr/cookiecutter)
* [cookiecutter-djangopackage](https://github.com/pydanny/cookiecutter-djangopackage)
* [Django]