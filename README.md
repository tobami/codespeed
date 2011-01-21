# Codespeed

A web application to monitor and analyze the performance of your code.

It is known to be used by [PyPy](http://speed.pypy.org) and
[Twisted](http://speed.twistedmatrix.com).

# Requirements

You will need Python 2.6+ and Django 1.1+.

In Ubuntu, they can be installed with:

    sudo apt-get install python-django

If you need SVN integration, pysvn is also required:

    sudo apt-get install python-svn

# Installation

* Download the last stable release from
  [http://github.com/tobami/codespeed/downloads](http://github.com/tobami/codespeed/downloads)
  and unpack it
* For simplicity, you can use the default sqlite configuration, which will save
  the data to a database named `speedcenter/data.db`.
* Create the DB by changing to the `speedcenter/` directory and running:

        python manage.py syncdb

* Create an admin user in the process.

* For testing purposes, you can now start the development server:

        python manage.py runserver 8000

The codespeed installation can now be accessed by navigating to `http://localhost:8000/`.

**Note**: for production, you should configure a real server like Apache,
lighttpd, etc... (refer to the Django docs:
`http://docs.djangoproject.com/en/dev/howto/deployment/`). You should also
modify `speedcenter/settings.py` and set `DEBUG = False`.

# Codespeed configuration

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

# Saving data

Data is saved POSTing to `http://localhost:8000/result/add/`.

You can use the script `tools/save_single_result.py` as a guide.

When trying to save data and the given executable, benchmark, project, or
revision do not yet exist, they will be automatically created, together with the
actual result entry. The only model which won't be created automatically is the
environment. It must always exist or the data won't be saved (that is the reason
it is described as a necessary step in the previous "Codespeed configuration"
section).

# Further customization

You may customize many of the speed center settings by creating files within
an `override` directory at the same level as `speedcenter`.

## Custom Settings

You may override any of the default settings by creating the file
`override/settings.py`. It is strongly recommended that you only override the
settings you need by importing the default settings and replacing only the
values needed for your customizations:

        from speedcenter.settings import *

        DATABASES = {"default": … standard Django db config …}

        ADMINS = (…)

## Templates and images

Many details may be changed for every speedcenter using standard Django
template override techniques. All of the templates mentioned below should be
contained in the `override/templates` directory.

### Site-wide Changes

All of the speedcenter pages inherit from the `site_base.html` template, which
extends `base.html`. To change every page on the site simply create a new file
(`override/templates/site_base.html`) which extends `base.html` and override
the appropriate block:

* Custom title: you may replace the default "My Speed Center" for the title
  block with your prefered value:

        {% block title}
            My Project's Speed Center
        {% endblock %}

* Custom logo: Place your logo in `override/media/img` and add a block like
  this:

        {% block logo %}
            <img src="{{ MEDIA_URL }}override/img/my-logo.png" width="120" height="48" alt="My Project">
        {% endblock logo %}

  n.b. the layout will stay exactly the same for any image with a height of
  48px (any width will do)

* Custom JavaScript or CSS: add your files to the `override/media` directory
  and extend the `extra_head` template block:

        {% block extra_head %}
            {{ block.super }}
            <script type="text/javascript" src="{{ MEDIA_URL }}override/js/my_cool_tweaks.js">
        {% endblock extra_head %}

### Specific Pages

Since `override/templates` is the first entry in `settings.TEMPLATE_DIRS` you
may override any template on the site simply by creating a new one with the
same name.

* About page: create `override/templates/speedcenter/about.html`:

        {% extends "site_base.html" %}
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
The file `speedcenter/codespeed/settings.py` can contain customizations of
several parameters (the file includes comments with full examples).

General settings:
* `website_name`: The RSS results feed will use this parameter as the site name
* `def_baseline`: Defines which baseline option will be chosen as default in
  the Timeline and Changes views.
* `def_environment`: Defines which environment should be selected as default
  in the Changes and Timeline views.
* `change_threshold`
* `trend_threshold`

* `defaultexecutable`: in the Changes view, a random executable is chosen as
  default. It that doesn't suite you, you can specify here which one should be
  selected. You need to specify its id (since the name alone is not unique).
* `defaultbaseline`: Defines which baseline option will be chosen as default in
  the Timeline and Changes views.
* `defaultenvironment`: Defines which environment should be selected as
  default in the Changes and Timeline views.

Comparison view settings:

* `charttype`: Chooses the default chart type (normal bars, stacked bars or
  relative bars)
* `normalization`: Defines whether normalization should be enabled as default
  in the Comparison view.
* `orientation`: horizontal or vertical
* `comp_executables`: per default all executables will be checked. When there
  are a large number of tags or executables, it is better to only select a few
  so that the plots are not too cluttered.

## Getting help
For help regarding the configuration of Codespeed, or to share any ideas or
suggestions you may have, please post on Codespeed's [discussion
group](http://groups.google.com/group/codespeed)

## Reporting bugs

If you find any bug in Codespeed please report it on the
[Github issue tracker](https://github.com/tobami/codespeed/issues)
