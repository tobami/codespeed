# Codespeed
A web application to monitor and analyze the performance of your code.

It is known to be used by [PyPy](http://speed.pypy.org) and [Twisted](http://speed.twistedmatrix.com).

# Requirements
You will need Python 2.6+ and Django 1.1+.

In Ubuntu, they can be installed with
    sudo apt-get install python-django
If you need SVN integration, pysvn is also requiered:
    sudo apt-get install python-svn

# Installation
* Download the last stable release from [http://github.com/tobami/codespeed/downloads](http://github.com/tobami/codespeed/downloads) and unpack it
* For simplicity, you can use the default sqlite configuration, which will save the data to a database named `speedcenter/data.db`.  
Create the DB by changing to the `speedcenter/` directory and typing `python manage.py syncdb`.  
Create an admin user in the process.

* For testing purposes, you can now start the development server `python manage.py runserver 8000`.  
The codespeed installation can now be accessed by navigating to `http://localhost:8000/`.

**Note**: for production, you should configure a real server like Apache, lighttpd, etc... (refer to the Django docs: `http://docs.djangoproject.com/en/dev/howto/deployment/`). You should also modify `speedcenter/settings.py` and set `DEBUG = False`.

# Codespeed configuration
Before you can start saving (and displaying) data, you need to first create an environment and define a default project.

* Go to `http://localhost:8000/admin/codespeed/environment/`
and create an environment.
* Go to `http://localhost:8000/admin/codespeed/project/`
and create a project.
Check the field "Track changes" and, in case you want version control integration, configure the relevant fields.

**Note**: Only executables associated to projects with a checked "track changes" field will be shown in the Changes and Timeline views.

# Saving data
Data is saved POSTing to `http://localhost:8000/result/add/`.
    
You can use the script `tools/save_single_result.py` as a guide.

When trying to save data and the given executable, benchmark, project, or revision do not yet exist, they will be automatically created, together with the actual result entry. The only model which won't be created automatically is the environment. It must always exist or the data won't be saved (that is the reason it is described as a necessary step in the previous "Codespeed configuration" section).

# Further customization

## Looks
The logo and title can be changed for every speedcenter.

* In `templates/base.html`, subtitute "My Speed Center" by your prefered name.
* The logo is defined in `<img src="/media/images/logo.png" height="48" alt="logo"/>`.  
Either substitute the file `speedcenter/media/images/logo.png" by your own logo, of change the tag to whatever you see fit.  
The layout will stay exactly the same for any image with a height of 48px (any width will do).
* Home page: In `templates/home.html`, modify the line `<p><a href="about/">This site</a> monitors <a href="#">MyProject</a>'s performance</p>`.
* About page: modify `templates/about.html`.

## Baselines and Comparison view executables
* The results associated to an executable and a revision which has a non blank tag field will be listed as a baseline option in the Timeline view.
* Additionaly, the Comparison view will show the results of the latest revision of projects being tracked as an executable as well.

## Defaults
The file `speedcenter/codespeed/settings.py` can contain customizations of several parameters (the file includes comments with full examples).

General settings:
* website_name: The RSS results feed will use this parameter as the site name
* def_baseline: Defines which baseline option will be chosen as default in the Timeline and Changes views.
* def_environment: Defines which environment should be selected as default in the Changes and Timeline views.
* change_threshold
* trend_threshold

Changes view settings:
* def_executable: in the Changes view, a random executable is chosen as default. It that doesn't suite you, you can specify here which one should be selected. You need to specify its id (since the name alone is not unique).
Comparison view settings:

* charttype: Chooses the default chart type (normal bars, stacked bars or relative bars)
* normalization: Defines whether normalization should be enabled as default in the Comparison view.
* orientation: horizontal or vertical
* comp_executables: per default all executables will be checked. When there are a large number of tags or executables, it is better to only select a few so that the plots are not too cluttered.

## Getting help
For help regarding the configuration of Codespeed, or to share any ideas or suggestions you may have, please post on Codespeed's "discussion group":http://groups.google.com/group/codespeed

## Reporting bugs

If you find any bug in Codespeed please report it on "https://github.com/tobami/codespeed/issues":https://github.com/tobami/codespeed/issues
