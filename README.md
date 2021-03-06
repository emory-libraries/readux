# Readux

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3572679.svg)](https://doi.org/10.5281/zenodo.3572679)[![Build Status](https://travis-ci.com/ecds/readux.svg?branch=develop)](https://travis-ci.com/ecds/readux)

Readux is a platform developed by the Emory Center for Digital Scholarship which allows users to read, take notes on, and publish with digitized texts from libraries’ archival collections. With Readux, users are able to:
-	browse digitized page images,
-	search and select the texts of these digitized books,
-	annotate text or illustrations in these works, and then
-	publish digital copies of the texts with their annotations.
Administrators can organize digitized books into collections, facilitating user access to digitized books available through the platform. Since its release, Readux has proved to be an innovative research and pedagogy tool for scholars and faculty at Emory University and beyond, with an array of use-cases ranging from teaching to publishing.


## Motivation

...

### Deployment

...


## Installation (development)

### Requirements

1. Python 3
2. PostgreSQL

### Set up development environment

1. Clone this repository.
2. Navigate to the readux directory.
3. Create virtual environment and activate it.

~~~bash
python3 -m venv venv
source venv/bin/activate
~~~

4. Install the dependencies.

~~~bash
pip install -r requirements/local.txt
bundle install
~~~

5. Copy and set up your local settings.

~~~bash
cp config/settings/local.dst config/settings/local.py
~~~

6. Add your database settings to the local.py file or set an environment variable. For example:

~~~bash
export DATABASE_URL=postgres://<database user>:<database password>@127.0.0.1:5432/<database name>
~~~

7. Run the migrations and load the example data.

~~~bash
python manage.py migrate
python manage.py loaddata apps/fixtures/dump.json
~~~

### Running local development server

Run the development under https to avoid mix content errors. Note: this will generate a self-signed certificate. There are ways to tell your browser to trust these certs, but that is beyond the scope of this README.

~~~bash
python manage.py runserver_plus --cert-file cert.crt  0.0.0.0:3000
~~~

### Running the tests

[![Coverage Status](https://coveralls.io/repos/github/ecds/readux/badge.svg?branch=release)](https://coveralls.io/github/ecds/readux?branch=release)

Readux uses Django's default test framework, but is configured to use pytest.

Your database user will need to be able to create a database:

~~~bash
alter user readux createdb;
~~~

To run the tests, simply run:

~~~bash
pytest apps/
~~~

Readux is configured to use [Travis CI](https://api.travis-ci.com/ecds/readux.svg?branch=release). Any push will trigger build.

### Deploy

For dev:

~~~bash
fab deploy:branch=develop -H readux.ecdsdev.org
~~~

For public alpha:

~~~bash
fab deploy:branch=release -H readux2.ecdsdev.org
~~~

Note: if no branch is passed, the deploy will default to release.

### Start Background Job

A background job needs to be started to handel creating the static site zip export and notify the person when the export is ready to be downloaded. The job also cleans up the export after 24 hours.

There are many ways to background a job. For example:

~~~bash
nohup python manage.py process_tasks &
~~~

## Contribute

We use the [Git-Flow](https://danielkummer.github.io/git-flow-cheatsheet/) branching model. Please submit pull requests against the develop branch.

### Code of conduct

[Code of Conduct](CODE_OF_CONDUCT.md)

## Tech/framework used

[![Build with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg)](https://github.com/pydanny/cookiecutter-django/)

[Mirador](http://projectmirador.org/) for displaying and annotating [IIIF](http://iiif.io) images.

??? for exporting.

## License

This software is distributed under the Apache 2.0 License.

## Autocomplete

Use the fork of Wagtail Autocomplete because of UUID. https://github.com/jcmundy/wagtail-autocomplete

## When importing with Import-Export

Import Collections, then Manifests, then I Servers, then Canvases.  Annotations will populate based on Canvases.
When importing collections, images for the "Original" field must already be in the apps/media/originals/ folder.  List `originals/filename.jpg` in the column for original.
