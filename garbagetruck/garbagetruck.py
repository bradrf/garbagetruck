import os
import re
import logging

from hashlib import md5
from configparser import SafeConfigParser
from datetime import timedelta, datetime

from crontab import CronTab
from send2trash import send2trash

class GarbageTruck:
    def __init__(self):
        self._logger = logging.getLogger('garbagetruck')
        self._cron = CronTab(user=True)
        self._config = SafeConfigParser()
        self._config_fn = os.path.join(os.path.expanduser('~'), '.garbagetruckrc')
        if os.path.exists(self._config_fn):
            self._config.read(self._config_fn)

    def set_job(self, run_command_format, name, dirs, files_older_than='90 days', check_every='week'):
        '''Set a job by adding or replacing based on the name.
        :param run_command_format: Command called for running job (will interpolate %s with a job ID).
        :param name: Unique (to calling user) name for this job.
        :param dirs: List of directories to iterate looking for old files.
        :param files_older_than: Period to use to determine what "old" is for each file.
        :param check_every: Period to use for when to trigger looking for old files.
        '''
        section_name = GarbageTruck._section_name_for(name)
        self._logger.debug('Setting job: %s (%s)', name, section_name)
        self.remove_job(name)
        job = self._cron.new(command=run_command_format % section_name,
                             comment=GarbageTruck._comment_for(name))
        job_period = GarbageTruck._cron_safe_period_from(check_every)
        period_method = getattr(job, job_period[1])
        period_method.every(job_period[0])
        # replace any pre-existing session
        self._config.remove_section(section_name)
        self._config.add_section(section_name)
        self._config.set(section_name, 'name', name)
        self._config.set(section_name, 'files_older_than', files_older_than)
        count = 0
        for dirname in dirs:
            count += 1
            optname = 'dir' + str(count)
            self._config.set(section_name, optname, dirname)

    def remove_job(self, name):
        section_name = GarbageTruck._section_name_for(name)
        self._logger.debug('Removing job: %s (%s)', name, section_name)
        self._cron.remove_all(comment=GarbageTruck._comment_for(name))
        self._config.remove_section(section_name)

    def save_changes(self):
        self._logger.debug('Saving: %s', self._config_fn)
        self._cron.write()
        with open(self._config_fn, 'wb') as configfile:
            self._config.write(configfile)

    def run_job(self, id):
        section_name = id
        if not self._config.has_section(section_name):
            self._logger.warn('Unable to run job %s: Does not exist', section_name)
            return
        name = self._config.get(section_name, 'name')
        self._logger.debug('Running: %s (%s)', name, section_name)
        files_older_than = self._config.get(section_name, 'files_older_than')
        period = GarbageTruck._period_from(files_older_than)
        lab = period[1] + 's'
        kwargs = {lab: period[0]}
        delta = timedelta(**kwargs)
        count = 0
        while True:
            count += 1
            optname = 'dir' + str(count)
            if not self._config.has_option(section_name, optname):
                break
            self._run_job(delta, self._config.get(section_name, optname))

    ######################################################################
    # private

    @staticmethod
    def _section_name_for(name):
        return md5(name).hexdigest()

    @staticmethod
    def _comment_for(name):
        return 'GarbageTruck: ' + name

    PERIOD_RE = re.compile('^\s*(\d*)\s*(.+?)s?\s*$')
    @staticmethod
    def _period_from(str):
        match = GarbageTruck.PERIOD_RE.match(str)
        if not match:
            raise "Unable to parse period from " + str
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
            period[0] *= 12
            period[1] = 'month'
        return period

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
