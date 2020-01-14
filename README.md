# Data Driven Acquisition

This system is a POC of a document management tool that will initiate acquisition document packages, and allow the acquisition work force to manage them as data. Handling some of the manual work of keeping the document up to date from an intuitive user interface.

- [Data Driven Acquisition](#data-driven-acquisition)
  - [Documentation](#documentation)
    - [Model Design](#model-design)
    - [Design concepts:](#design-concepts)
      - [Github integration](#github-integration)
      - [Trelo Integration](#trelo-integration)
    - [Third party libraries](#third-party-libraries)
  - [Quickstart](#quickstart)
  - [Features](#features)
  - [Running Tests](#running-tests)
  - [Resources](#resources)


## Documentation

### Model Design

I opted to use relational database to allow rapid development using Django, and PostgreSQL.  Data model is available https://dbdiagram.io/d/5db0a60602e6e93440f28f98

![data model](https://github.com/adam-grandt-tts/data-driven-acquisition/blob/master/docs/images/data_model.png)

### Design concepts:

- Files will be kept inside a [PostgreSQL HStore](https://www.postgresql.org/docs/9.0/hstore.html)
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
    - The properties JSON array stored in HSstore that will include all configured properties for this package.
- Access control is managed vua the ACL table.
  - An ACL item connects a User or Group to a document or a Folder with a defined access level.
  - Access should be propagated down, that is to say, if a User has access to a folder they should also have access to all sub folders and document in those folders.
  - A user will be presented with all items that he has any access to upon login.

#### Github integration 

TODO:

#### Trelo Integration 

TODO: 

https://trello.com/b/SL7jTaz3/oia-acquisition-tracker

### Third party libraries

- [Django Easy Audit](https://github.com/soynatan/django-easy-audit): Audit trail for all authentication and model change events.
- [Django Admin Plus](https://github.com/jsocol/django-adminplus): Adding custom views to the django admin.
- [Django Extension](https://django-extensions.readthedocs.io/en/latest/): Django Extensions is a collection of custom extensions for the Django Framework. These include management commands, additional database fields, admin extensions and much more.
- [Django Model Utils](https://django-model-utils.readthedocs.io/en/latest/): Django model mix-ins and utilities.
- [Django Reversion](https://django-reversion.readthedocs.io/en/stable/): an extension to the Django web framework that provides version control for model instances (like documents :) ).
- [Django Admin Hstore Widget](https://github.com/PokaInc/django-admin-hstore-widget) A nice Hstore editors widget for properties in the django admin.
- [Django Environ](https://github.com/joke2k/django-environ): Take sensitive project settings out of git and save them in `.env` file or the local env for deployment.
- [Django Guardian](https://github.com/django-guardian/django-guardian): Object level permissions in django.

## Quickstart

The easiest way to get rolling is to use Docker:

```
# Build the application and database images
docker-compose build

# Run database migrations
docker-compose run app python manage.py migrate
```

Then, to start the application and its database:

```
docker-compose up
```

Use <kbd>CTRL+C</kbd> to stop.

### Manual setup

Alternatively, follow these setup steps:

1. Database Setup
   1. install [PostgreSQL](https://www.postgresql.org/docs/9.3/tutorial-install.html).
   2. Create [database](https://www.postgresql.org/docs/9.0/sql-createdatabase.html)
   3. [Configure your](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04) Create a new DB and role. e.g.:

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

    4. Create the hsstore extention in the database by running:

        ```sql
        $ psql myproject
        CREATE EXTENSION IF NOT EXISTS hstore;
        ```


2. Project set up
   1. Create project folder

        ```shell
        mkdir data-driven-acquisition
        ```

   2. Create virtual environment (using [virtual env wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/install.html) in this example).

    ```shell
    mkvirtualenv data-driven-acquisition --python=python37
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
        # Set debug settings globally to the app, makes logging very verbose. (on/off)
        DEBUG=on
        # Used for all encryption operations. Use something like this to generate.
        # python -c "import random; ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])"
        SECRET_KEY=your-secret-key
        DATABASE_URL=psql://DB_USER:DB_PASS@DB_IP/URL:DB_PORT/DB_NAME
        ALLOWED_HOSTS=127.0.0.1,0.0.0.0 # Prod IP goes here
        
        # GitHub Config
        # https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line
        GITHUB_ACCESS_KEY=your-key-goes-here
        # MAke sure your github user has access to repo 
        GITHUB_TEMPLATE_REPO=github-repo-containing-templates

        # if you want ot use trello 
        #Do we use trello, def to no
        USER_TRELLO=yes
        # Set trello API Key, required if use trello is yes
        #https://developers.trello.com/reference#api-key-tokens
        TRELLO_APP_KEY=trello-api-key
        TRELLO_APP_SECRET=trello-oauth-secret
        # https://developers.trello.com/page/authorization
        # Get token by running and visiting the URL
        # trello_auth_url = ''.join([
        #             'https://trello.com/1/authorize?expiration=never',
        #            '&name=DataDrivenAcquisition&scope=read,write&response_type=token',
        #            f'&key={settings.TRELLO["APP_KEY"]}'])
        TRELLO_TOKEN=token-goes-here
        # Get the board ID from the URL of your trello board
        TRELLO_BORED_ID=board-id
        

        ```

    1. Collect static and run

        ```shell
        python manage.py collectstatic
        python manage.py migrate
        ```

## Features

* TODO

## Running Tests

Does the code actually work?

    ```shell
        (myenv) $ pip install tox (or -r requirements_test.txt)
        (myenv) $ tox
    ```

## Resources 

- [Print docs with header and footer](https://medium.com/@Idan_Co/the-ultimate-print-html-template-with-header-footer-568f415f6d2a)