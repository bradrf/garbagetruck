import os
import re
import logging

from hashlib import md5
from configparser import SafeConfigParser
from datetime import timedelta, datetime

from crontab import CronTab
from send2trash import send2trash

class GarbageTruck:
    class InvalidPeriod(Exception):
        '''Indicates when an invalid period is provided'''
        pass

    def __init__(self):
        self._logger = logging.getLogger('garbagetruck')
        self._cron = CronTab(user=True)
        self._config = SafeConfigParser()
        self._config_fn = os.path.join(os.path.expanduser('~'), '.garbagetruckrc')
        if os.path.exists(self._config_fn):
            self._config.read(self._config_fn)

    def set_job(self, run_command_format, name, dirs,
                files_older_than='90 days', check_every='week'):
        '''Set a job by adding or replacing based on the name.

        A call to `set_job` will either add a new job or replace a previously set job with the new
        parameters. The `name` is the identifier for a job and must be **unique** accross all jobs
        for the same user.

        :param run_command_format: the command called for running job (will interpolate `%s` with a
                                   job ID)
        :param name: a unique name for this job
        :param dirs: a list of directories to iterate looking for old files
        :param files_older_than: the period to use to determine what "old" is for each file
        :param check_every: the period to use for when to trigger looking for old files
        '''
        section_name = GarbageTruck._section_name_for(name)
        self._logger.debug('Setting job: %s (%s)', name, section_name)
        # validate that files_older_than syntax is ok now before we schedule things...
        GarbageTruck._period_from(files_older_than)
        self.remove_job(name)
        job = self._cron.new(command=run_command_format % section_name,
                             comment=GarbageTruck._comment_for(name))
        job_period = GarbageTruck._cron_safe_period_from(check_every)
        smaller_period = GarbageTruck._smaller_period_for(job_period[1])
        if job_period[0] == 1 and smaller_period:
            # e.g. if "1 month", set to run on first of every month (or, hour, or minute)
            period_method = getattr(job, smaller_period)
            period_method.on(1)
        else:
            period_method = getattr(job, job_period[1])
            period_method.every(job_period[0])
        # replace any pre-existing session
        self._config.remove_section(section_name)
        self._config.add_section(section_name)
        self._config.set(section_name, 'name', name)
        self._config.set(section_name, 'files_older_than', files_older_than)
        self._config.set(section_name, 'check_every', check_every)
        count = 0
        for dirname in dirs:
            count += 1
            optname = 'dir' + str(count)
            self._config.set(section_name, optname, dirname)

    def list_jobs(self):
        '''List all jobs.

        All job details will be logged at INFO level. If DEBUG is enabled, each job's check schedule
        will be shown (i.e. the associated crontab entry).
        '''
        for section_name in self._config.sections():
            name = self._config.get(section_name, 'name')
            items = {'dirs': []}
            for key, value in self._config.items(section_name):
                if key == 'name':
                    continue
                if key.startswith('dir'):
                    items['dirs'].append(value)
                else:
                    items[key] = '"' + value + '"'
            items['dirs'] = '[' + ','.join('"%s"' % i for i in items['dirs']) + ']'
            self._logger.info('Job %s: name="%s" %s', section_name, name,
                              ' '.join(['%s=%s' % (k,v) for k,v in items.iteritems()]))
            if self._logger.getEffectiveLevel() <= logging.DEBUG:
                job = next(self._cron.find_comment(GarbageTruck._comment_for(name)))
                self._logger.debug(str(job))

    def remove_job(self, name):
        '''Remove a job.

        Removes a job previously added by `set_job`.

        :param name: the unique name used when the job was created
        '''
        section_name = GarbageTruck._section_name_for(name)
        self._logger.debug('Removing job: %s (%s)', name, section_name)
        self._cron.remove_all(comment=GarbageTruck._comment_for(name))
        self._config.remove_section(section_name)

    def save_changes(self):
        '''Save all changes made to the GarbageTruck.

        Writes out all the configuration and sets up the new schedule for the jobs changed before
        calling `save_changes`.
        '''
        self._logger.debug('Saving: %s', self._config_fn)
        self._cron.write()
        with open(self._config_fn, 'wb') as configfile:
            self._config.write(configfile)

    def run_job(self, id):
        '''Run a job.

        Runs a job added by `set_job`. Not normally called directly, this is what is used when run
        from the job scheduler on the configured interval.

        :param id: the unique identifier assigned to a job (this is **not** the name of the job).
        '''
        section_name = id
        if not self._config.has_section(section_name):
            self._logger.warn('Unable to run job %s: Does not exist', section_name)
            return
        name = self._config.get(section_name, 'name')
        self._logger.debug('Running: %s (%s)', name, section_name)
        files_older_than = self._config.get(section_name, 'files_older_than')
        period = GarbageTruck._delta_safe_period_from(files_older_than)
        kwargs = {period[1]: period[0]}
        delta = timedelta(**kwargs)
        for dirname in self._get_dirs(section_name):
            self._run_job(delta, dirname)

    ######################################################################
    # private

    @staticmethod
    def _section_name_for(name):
        return md5(name).hexdigest()

    @staticmethod
    def _comment_for(name):
        return 'GarbageTruck: ' + name

    _PERIOD_RE = re.compile('^\s*(\d*)\s*(.+?)s?\s*$')
    @staticmethod
    def _period_from(str):
        match = GarbageTruck._PERIOD_RE.match(str)
        if not match:
            raise GarbageTruck.InvalidPeriod("Unable to parse period from " + str)
        period = list(match.groups())
        period[0] = 1 if period[0] == '' else int(period[0])
        return period

    @staticmethod
    def _cron_safe_period_from(str):
        period = GarbageTruck._period_from(str)
        if period[1] == 'week':
            period[0] *= 7
            period[1] = 'day'
        elif period[1] == 'year':
            raise GarbageTruck.InvalidPeriod('Check schedule must be less than a year')
        return period

    @staticmethod
    def _delta_safe_period_from(str):
        period = GarbageTruck._period_from(str)
        if period[1] == 'month':
            period[0] *= 30 # TODO: month-ish?
            period[1] = 'days'
        elif period[1] == 'year':
            period[0] *= 365 # TODO: year-ish?
            period[1] = 'days'
        else:
            period[1] += 's'
        return period

    @staticmethod
    def _smaller_period_for(period):
        return {'hour': 'minute', 'day': 'hour', 'month': 'day'}.get(period)

    def _get_dirs(self, section_name):
        dirs = []
        count = 0
        while True:
            count += 1
            optname = 'dir' + str(count)
            if not self._config.has_option(section_name, optname):
                return dirs
            dirs.append(self._config.get(section_name, optname))

    def _run_job(self, delta, dirname):
        if not os.path.exists(dirname):
            self._logger.warn('Ignoring %s: Does not exist', dirname)
            return
        oldest_mtime = datetime.now() - delta
        self._logger.debug('Checking %s for files older than %s', dirname, oldest_mtime)
        count = 0
        for dirpath, _, filenames in os.walk(dirname):
            for ent in filenames:
                curpath = os.path.join(dirpath, ent)
                file_modified = datetime.fromtimestamp(os.path.getmtime(curpath))
                if file_modified < oldest_mtime:
                    self._logger.debug('Trashing: %s', curpath)
                    send2trash(curpath)
                    count += 1
        if count > 0:
            self._logger.info('Cleaned up %d files', count)
