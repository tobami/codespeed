# Codespeed
[![Build Status](https://travis-ci.org/tobami/codespeed.png?branch=master)](https://travis-ci.org/tobami/codespeed)
[![PyPI version](https://img.shields.io/pypi/v/codespeed.svg)](https://pypi.python.org/pypi/codespeed)

Codespeed is a web application to monitor and analyze the performance of your code.

Known to be used by [CPython](https://speed.python.org), [PyPy](http://speed.pypy.org), [Twisted](http://speed.twistedmatrix.com) and others.

For an overview of some application concepts see the [wiki page](https://github.com/tobami/codespeed/wiki/Overview)

# Installation

You will need Python 2.7 or 3.4+.

To install dependencies and the codespeed Django app:

    pip install codespeed

If you want version control integration, there are additional requirements:

* Subversion needs pysvn: `python-svn`
* Mercurial needs the package `mercurial` to clone the repo locally
* git needs the `git` package to clone the repo
* For Github the isodate package is required, but not git: `pip install isodate`

**Note**: For git or mercurial repos, the first time the changes view is accessed,
Codespeed will try to clone the repo, which depending on the size of the project
can take a long time. Please be patient.

* Download the last stable release from
  [github.com/tobami/codespeed/tags](https://github.com/tobami/codespeed/tags), unpack it and install it with `python setup.py install`.
* To get started, you can use the `sample_project` directory as a starting point for your Django project, which can be normally configured by editing `sample_project/settings.py`.
* For simplicity, you can use the default sqlite configuration, which will save
  the data to a database named `data.db`
* Create the DB by typing from the root directory:

        python manage.py migrate

* Create an admin user in the process.
* For testing purposes, you can now start the development server:

        python manage.py runserver 8000

The codespeed installation can now be accessed by navigating to `http://localhost:8000/`.

**Note**: for production, you should configure a real server like Apache or nginx (refer to the [Django docs](http://docs.djangoproject.com/en/dev/howto/deployment/)). You should also
modify `sample_project/settings.py` and set `DEBUG = False`.
[`sample_project/README.md`](https://github.com/tobami/codespeed/tree/master/sample_project/README.md) also describes some production settings.

# Codespeed configuration

## Using the provided test data

If you want to test drive Codespeed, you can use the testdata.json fixtures to have a working data set to browse.

* From the root directory, type:

        ./manage.py loaddata codespeed/fixtures/testdata.json

## Starting from scratch

Before you can start saving (and displaying) data, you need to first create an
environment and define a default project.

* Go to `http://localhost:8000/admin/codespeed/environment/`
  and create an environment.
* Go to `http://localhost:8000/admin/codespeed/project/`
  and create a project.

Check the field "Track changes" and, in case you want version control
integration, configure the relevant fields.

**Note**: Only executables associated to projects with a checked "track changes"
field will be shown in the Changes and Timeline views.

**Note**: Git and Mercurial need to locally clone the repository. That means that your `sample_project/repos` directory will need to be owned by the server. In the case of a typical Apache installation, you'll need to type `sudo chown www-data:www-data sample_project/repos`

# Saving data

Data is saved POSTing to `http://localhost:8000/result/add/`.

You can use the script `tools/save_single_result.py` as a guide.
When saving large quantities of data, it is recommended to use the JSON API instead:
    `http://localhost:8000/result/add/json/`

An example script is located at `tools/save_multiple_results.py`

**Note**: If the given executable, benchmark, project, or
revision do not yet exist, they will be automatically created, together with the
actual result entry. The only model which won't be created automatically is the
environment. It must always exist or the data won't be saved (that is the reason
it is described as a necessary step in the previous "Codespeed configuration"
section).

# Further customization

## Custom Settings

You may override any of the default settings by setting them in
`sample_project/settings.py`. It is strongly recommended that you only override the
settings you need by importing the default settings and replacing only the
values needed for your customizations:

    from codespeed.settings import *

    DEF_ENVIRONMENT = "Dual Core 64 bits"

### Site-wide Changes

All pages inherit from the `base.html` template. To change every page on the site 
simply edit (`sample_project/templates/codespeed/base_site.html`) and override
the appropriate block:

* Custom title: you may replace the default "My Speed Center" for the title
  block with your prefered value:

        {% block title %}
            My Project's Speed Center
        {% endblock %}

* Replacing logo.png: Place your logo in `sample_project/static/images/logo.png`
* Logo with custom filename: Place your logo in `sample_project/static/images/` and add a block like
  this to `base_site.html`:

        {% block logo %}
            <img src="{{ MEDIA_URL }}images/my-logo.jpg" width="120" height="48" alt="My Project">
        {% endblock logo %}

  n.b. the layout will stay exactly the same for any image with a height of
  48px (any width will do)

* Custom JavaScript or CSS: add your files to the `sample_project/static/js` directory
  and extend the `extra_head` template block:

        {% block extra_head %}
            {{ block.super }}
            <script type="text/javascript" src="{{ MEDIA_URL }}static/js/my_cool_tweaks.js">
        {% endblock extra_head %}

### Specific Pages

Since `sample_project/templates/codespeed` is the first entry in `settings.TEMPLATE_DIRS` you
may override any template on the site simply by creating a new one with the
same name.

* About page: create `sample_project/templates/about.html`:

        {% extends "codespeed/base_site.html" %}
        {% block title %}{{ block.super }}: About this project{% endblock %}
        {% block body %}
            <div id="sidebar"></div>
            <div id="about" class="about_content clearfix">
                Your content here
            </div>
        {% endblock %}


## Baselines and Comparison view executables
* The results associated to an executable and a revision which has a non blank
  tag field will be listed as a baseline option in the Timeline view.
* Additionaly, the Comparison view will show the results of the latest revision
  of projects being tracked as an executable as well.

## Defaults
The file `sample_project/settings.py` can contain customizations of
several parameters (the file includes comments with full examples).

### General settings:
* `WEBSITE_NAME`: The RSS results feed will use this parameter as the site name
* `DEF_BASELINE`: Defines which baseline option will be chosen as default in
  the Timeline and Changes views.
* `DEF_ENVIRONMENT`: Defines which environment should be selected as default
  in the Changes and Timeline views.
* `CHANGE_THRESHOLD`
* `TREND_THRESHOLD`

### Changes View
* `DEF_EXECUTABLE`: in the Changes view, a random executable is chosen as
  default. It that doesn't suite you, you can specify here which one should be
  selected. You need to specify its id (since the name alone is not unique).

### Timeline View
* `DEF_BENCHMARK`: Defines the default timeline view. Possible values:
    * `None`: will show a grid of plot thumbnails, or a text message when the number of plots exceeds 30
    * `grid`: will always show as default the grid of plots
    * `show_none`: will show a text message (better default when there are lots of benchmarks)
    * `mybench`: will select benchmark named "mybench"

### Comparison View
* `CHART_TYPE`: Chooses the default chart type (normal bars, stacked bars or
  relative bars)
* `NORMALIZATION`: Defines whether normalization should be enabled as default
  in the Comparison view.
* `CHART_ORIENTATION`: horizontal or vertical
* `COMP_EXECUTABLES`: per default all executables will be checked. When there
  are a large number of tags or executables, it is better to only select a few
  so that the plots are not too cluttered.
  Given as a list of tuples containing the name of an executable + commitid of a revision. An 'L' denotes the last revision. Example:

```python
COMP_EXECUTABLES = [
    ('myexe', '21df2423ra'),
    ('myexe', 'L'),
]
```

## Getting help
For help regarding the configuration of Codespeed, or to share any ideas or
suggestions you may have, please post on Codespeed's [discussion
group](http://groups.google.com/group/codespeed)

## Reporting bugs

If you find any bug in Codespeed please report it on the
[Github issue tracker](https://github.com/tobami/codespeed/issues)
