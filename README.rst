===============================
GarbageTruck
===============================

.. image:: https://img.shields.io/pypi/v/garbagetruck.svg
        :target: https://pypi.python.org/pypi/garbagetruck

.. image:: https://img.shields.io/travis/bradrf/garbagetruck.svg
        :target: https://travis-ci.org/bradrf/garbagetruck

.. image:: https://readthedocs.org/projects/garbagetruck/badge/?version=latest
        :target: https://garbagetruck.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/bradrf/garbagetruck/shield.svg
     :target: https://pyup.io/repos/github/bradrf/garbagetruck/
     :alt: Updates

A small tool to periodically move old files into the local file system trash.

* Free software: MIT license
* Full documentation (including how to install): https://garbagetruck.readthedocs.io.


Features
--------

Use `GarbageTruck` to build and maintain scheduled cleanup of files in various directories that tend
to collect files over time. `GarbageTruck` will send any files older than a relative period to the
local file system trash using the current user's crontab to schedule checks for old files from
cron_. This makes the utility safe in that any files moved to the trash could be restored simply
without worrying about immediate loss (until the trash is emptied, of course).

For example, let's say one never cleans out their downloaded files. Here's how to set a
`GarbageTruck` job to periodically move files older than six months into the trash::

   $ garbagetruck set --older-than '6 months' --check-every day 'Clean out old downloads' ~/Downloads/

This will set up a schedule (using cron_) to look for files each day that are older than three
montsh and have them moved into the correct trash (courtesy of send2trash_). The details can be
shown like this::

   $ garbagetruck list
   [2016-09-03T15:55:32-0700 #31693] INFO     garbagetruck Job 57d1db0a8b8427c3041ac1af89b0a348: name="Clean out old downloads" dirs=["/Users/brad/Downloads"] files_older_than="3 months" check_every="day"
   [2016-09-03T15:55:32-0700 #31693] DEBUG    garbagetruck * 1 * * * /Users/brad/.virtualenvs/garbage_truck/bin/garbagetruck run 57d1db0a8b8427c3041ac1af89b0a348 # GarbageTruck: Clean out old downloads

Each call to the `set` command will replace the same named job. Alternatively, if the job is no
longer useful, remove it like this::

   $ garbagetruck remove 'Clean out old downloads'

To check on a job, any problems and results will be logged to one of the following locations:

* OS X will use :code:`~/Library/Logs/garbagetruck.log`.
* Other systems will rely on what click_app_dir_ returns.


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _cron: https://pypi.python.org/pypi/python-crontab
.. _send2trash: https://github.com/hsoft/send2trash
.. _click_app_dir: http://click.pocoo.org/6/api/#click.get_app_dir
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
