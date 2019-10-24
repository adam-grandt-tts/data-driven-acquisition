# Data Driven Acquisition

This system is a POC of a document management tool that will initiate acquisition document packages, and allow the acquisition work force to manage them as data. Handling some of the manual work of keeping the document up to date from an intuitive user interface.

- [Data Driven Acquisition](#data-driven-acquisition)
  - [Documentation](#documentation)
    - [Model Design](#model-design)
    - [Third party libraries](#third-party-libraries)
  - [Quickstart](#quickstart)
  - [Features](#features)
  - [Running Tests](#running-tests)


## Documentation

### Model Design

I opted to use relational database to allow rapid development using Django, and PostgreSQL.  Data model is available https://dbdiagram.io/d/5db0a60602e6e93440f28f98

![data model](https://github.com/adam-grandt-tts/data-driven-acquisition/blob/master/docs/images/data_model.png)

Design concepts:

- Files will be kept inside a PostgreSQL blob
  - Documents will be represented in Markdown. TODO: selected markdown editor and link here.
  - Sheets will be represented in a JSON string defined by the javascript sheet editor. TODO: Select a sheet editor and link here.
  - Other document will be saves as binary blobs and will not be editable.
  - Each file can belong to one folder
  - We will use HTML comment notation to insert and update properties in all editable files like so for a property named 'name':

    ```html
    <!--PROPERTY:name-->Value of name goes here<!--/PROPERTY:name-->
    ```

- A Folder object contains files.
  - Folders can have have other folders as parents.
  - If folder dose not have a parent folder it will be considered a package.
  - Packages are folders that wil have the following attribute enabled:
    - The project URL of the trello board.
    - The properties JSON array that will include all configured properties for this package.
- Access control is managed vua the ACL table.
  - An ACL item connects a User or Group to a document or a Folder with a defined access level.
  - Access should be propagated down, that is to say, if a User has access to a folder they should also have access to all sub folders and document in those folders.
  - A user will be presented with all items that he has any access to upon login.

### Third party libraries

- [Django Easy Audit](https://github.com/soynatan/django-easy-audit): Audit trail for all authentication and model change events.
- [Django Admin Plus](https://github.com/jsocol/django-adminplus): Adding custom views to the django admin.
- [Django Extension](https://django-extensions.readthedocs.io/en/latest/): Django Extensions is a collection of custom extensions for the Django Framework. These include management commands, additional database fields, admin extensions and much more.
- [Django Model Utils](https://django-model-utils.readthedocs.io/en/latest/): Django model mix-ins and utilities.
- df

## Quickstart

1. Database Setup
   1. install [PostgreSQL](https://www.postgresql.org/docs/9.3/tutorial-install.html).
   2. Create [database](https://www.postgresql.org/docs/9.0/sql-createdatabase.html)
   3. [Configure your](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04) new daba and create the role. e.g.:

    ```sql
    $ psql
    CREATE DATABASE myproject;
    CREATE USER myprojectuser WITH PASSWORD 'password';
    ALTER ROLE myprojectuser SET client_encoding TO 'utf8';
    ALTER ROLE myprojectuser SET default_transaction_isolation TO 'read committed';
    ALTER ROLE myprojectuser SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE myproject TO myprojectuser;
    \q

    ```

2. Project set up
   1. Create project folder

   ```shell
   mkdir data-driven-acquisition
   ```

   1. Create virtual environment (using [virtual env wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/install.html) in this example).

   ```shell
   mkvirtualenv data-driven-acquisition --python=python3
   ```

   1. Install the requirements

   ```shell
   pip install -r requirements.txt
   ```

   1. Optional: Install the development and testing requirements if needed.

   ```shell
   pip install -r requirements_dev.txt
   pip install -r requirements_test.txt
   ```

   1. Create a .env file looking like so
  
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
