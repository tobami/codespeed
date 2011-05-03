# Codespeed Example instance

Codespeed uses the Web framework [Django](http://djangoproject.com/). To get a
Codespeed instance running you need to set up a Django Project. This directory
is just such a project for your reference and a jump start to create your own.

This file is written in Markdown.

## For the impatient

Warning: It is recommended to use [virtualenv](http://pypi.python.org/pypi/virtualenv) to not install
stuff on the root path of your operating system.
However, it works also this way and might be desired in production
environments.
Further, that will give you *just* the Django development server version. Please
refer to *Installing for Production* for serious installations.

It is assumed you are in the root directory of the Codespeed software.

1. Install the Python pip module
   `which pip >/dev/null || easy_install pip`
   (You might be required to use sudo)
2. Copy the example directory to your project. (Prevents updates on
   git tracked files in the future.) Let's call it speedcenter
   `cp -r example speedcenter`
3. Enter that directory
   `cd speedcenter`
4. Install Django, Codespeed and other dependencies using pip
   `pip install -r requirements.txt`
   (You might be required to use sudo)
5. Initialise the Django Database
   python manage.py syncdb
   (Yes, add a superuser.)
6. Finally, start the Django development server.
   `python manage.py runserver`
7. Enjoy.
   `python -m webbrowser -n http://localhost:8000`

## Customisations

### Using your own Templates
Just edit your very own Django templates in `speedcenter/templates`. A good
start is `base.html` the root of all templates.

If you need to change the codespeed templates:
1. Copy the templates from the codespeed module into your Django project folder.
   `cp -r codespeed/templates/codespeed  speedcenter/templates/`
2. Edit the templates in speedcenter/templates/codespeed/*html
Please, also refer to the [Django template docu]
(http://docs.djangoproject.com/en/1.3/ref/templates/)

### Changing the URL Scheme
If you don't want to have your speedcenter in the root url you can change urls.py.
Comment (add a '#' at the beginning) line number 25 `(r'^', include('cod...`
and uncomment the next line `(r'^speed/', include('cod...` (Note, Python is
picky about identation).
Please, also refer to the [Django URL dispatcher docu]
(http://docs.djangoproject.com/en/1.3/topics/http/urls/).

### Codespeed settings
The main config file is `settings.py`. There you configure everything related
to your set up. It FIXME (a8) to be continued...

FIXME (a8 <fb@alien8.de> 2011-04-29): Write more ...

* Point to Django docu for DB, template engine, ...
* Point to codespeed config in settings.py
* Point to wsgi config for Apache ...
* Write up "Installing for production" section
...
