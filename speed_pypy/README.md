# Codespeed Example instance

Codespeed uses the Web framework [Django](http://djangoproject.com/). To get a
Codespeed instance running you need to set up a Django Project. This directory
is just such a project for your reference and a jump start to create your own.

## For the impatient

Warning: It is recommended to use [virtualenv](http://pypi.python.org/pypi/virtualenv) to avoid installing
stuff on the root path of your operating system.
However, it works also this way and might be desired in production
environments.

### Testing with the built-in Development Server
That will give you *just* the Django development server version. Please
refer to *Installing for Production* for serious installations.

It is assumed you are in the root directory of the Codespeed software.

1. Install the Python pip module
   `which pip >/dev/null || easy_install pip`
   (You might be required to use sudo)
2. You *must* copy the `sample_project` directory to your project. (Prevents updates on
   git tracked files in the future.) Let's call it speedcenter
   `cp -r sample_project speedcenter`
3a. (When configuring your own project) `pip install codespeeed`
3b. (For Codespeed development) Install Django and other dependencies using pip
   `pip install -r requirements.txt`. This will not install codespeed itself, as we want runserver to only "see" the local codespeed copy
4. Add codespeed to your Python path
   Either
   `export PYTHONPATH=../:$PYTHONPATH`
   or
   `ln -s ./codespeed ./sample_project`
5. Initialise the Django Database
   `python manage.py syncdb`
   (Yes, add a superuser.)
   `python manage.py migrate`
   Optionally, you may want to load the fixture data for a try
   `python manage.py loaddata ../codespeed/fixtures/testdata.json`
6. Finally, start the Django development server.
   `python manage.py runserver`
7. Enjoy.
   `python -m webbrowser -n http://localhost:8000`

## Installing for production
There are many choices to get Django Web apps served. It all depends on
your preferences and existing set up. Two options are shown. Please do
not hesitate to consult a search engine to tune your set-up.

### NGINX + GUNICORN: Easy as manage.py runserver
Assumed you have a [Debian](http://www.debian.org) like system.

1. Follow the steps from the development server set-up up to the the 6th step (database init).
2. Install [nginx](http://nginx.net/) and [gunicorn](http://gunicorn.org/)
   `sudo apt-get install nginx gunicorn`
3. Tune /etc/nginx/sites-enabled/default to match
   deploy/nginx.default-site.conf
   (Hint: See diff /etc/nginx/sites-enabled/default deploy/nginx.default-site.conf
   for changes)
   Note, the sitestatic dir needs to point to your speedcenter/sitestatic dir!
4. Restart nginx
   /etc/init.d/nginx restart`
5. Prepare static files
   `cd /path/to/speedcenter/`
   `python ./manage.py collectstatic`
6. Add 'gunicorn' to your INSTALLED_APPS in settings.py
   INSTALLED_APPS = (
       'django.contrib.auth',
   [...]
       'south',
       'gunicorn'
   )
6. Run speedcenter by
   `python ./manage.py run_gunicorn`
7. Check your new speedcenter site! Great! But wait, who runs gunicorn after the
   terminal exits?
   There are several options like upstart, runit, or supervisor.
   Let's go with supervisor:
   1. <Ctrl>+<c> to exit gunicorn
   2. `apt-get install supervisor`
   3. `cp deploy/supervisor-speedcenter.conf /etc/supervisor/conf.d/speedcenter.conf`
   4. `$EDITOR /etc/supervisor/conf.d/speedcenter.conf  #adjust the path`
   5. `supervisorctl update`
   6. `supervisorctl status`
       speedcenter                      RUNNING    pid 2036, uptime 0:00:05
8. Warning: You may find another way to run gunicorn using `gunicorn_django`. That might
   have a shebang of `#!/usr/bin/python` bypassing your virtualenv. Run it out of your
   virtualenv by `python $(which gunicorn_django)`

### Good old Apache + mod_wsgi
If you don't like surprises and are not into experimenting go with the old work horse.
Assumed you have a [Debian](http://www.debian.org) like system.

1. Follow the steps from the development server set-up
2. Prepare static files
   `cd /path/to/speedcenter/`
   `python ./manage.py collectstatic`
3. Install apache and mod_wsgi
   `apt-get install apache2 libapache2-mod-wsgi`
4. Copy deploy/apache-speedcenter.conf
   `cp deploy/apache-speedcenter.conf /etc/apache2/sites-available/speedcenter.conf`
5. Edit /etc/apache2/sites-available/speedcenter.conf to match your needs
6. Enable the new vhost
   `a2ensite speedcenter.conf`
7. Restart apache
   `/etc/init.d/apache2 restart`
8. Check your new vhost.

## Customisations

### Using your own Templates
Just edit your very own Django templates in `speedcenter/templates`. A good
start is `codespeed/base.html` the root of all templates.

If you need to change the codespeed templates:
1. Copy the templates from the codespeed module into your Django project folder.
   `cp -r codespeed/templates/codespeed  speedcenter/templates/`
2. Edit the templates in speedcenter/templates/codespeed/*html
Please, also refer to the [Django template docu]
(http://docs.djangoproject.com/en/1.4/ref/templates/)

### Changing the URL Scheme
If you don't want to have your speedcenter in the root url you can change urls.py.
Comment (add a '#' at the beginning) line number 25 `(r'^', include('cod...`
and uncomment the next line `(r'^speed/', include('cod...` (Note, Python is
picky about indentation).
Please, also refer to the [Django URL dispatcher docu]
(http://docs.djangoproject.com/en/1.4/topics/http/urls/).

### Codespeed settings
The main config file is `settings.py`. There you configure everything related
to your set up.
