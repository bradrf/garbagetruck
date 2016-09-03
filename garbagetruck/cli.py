import os
import sys
import click
import logging

from .garbagetruck import GarbageTruck

def ensure_logdir():
    logdir = os.path.join(os.path.expanduser('~'), 'Library', 'Logs')
    if not os.path.exists(logdir):
        logdir = click.get_app_dir('garbagetruck')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    return os.path.join(logdir, 'garbagetruck.log')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.option('-l', '--log-level', type=click.Choice(['debug','info','warning','error','critical']),
              help='set logging level', default='info')
@click.option('--log-file', metavar='FILENAME',
              help='write logs to FILENAME', default='STDERR')
def main(log_level, log_file):
    '''A small tool to periodically move old files into the local file system trash.

    Use garbagetruck to build and maintain scheduled cleanup of files in various directories like
    "Downloads". Garbagetruck will send any files older than a relative period to the local file
    system trash using the current user's crontab to schedule checks for old files from cron.

    '''
    log_kwargs = {
        'level': getattr(logging, log_level.upper()),
        'format': '[%(asctime)s #%(process)d] %(levelname)-8s %(name)-12s %(message)s',
        'datefmt': '%Y-%m-%dT%H:%M:%S%z',
    }
    if log_file == 'STDERR' and not sys.stdout.isatty():
        log_kwargs['filename'] = ensure_logdir()
    if log_file != 'STDERR':
        log_kwargs['filename'] = log_file
    logging.basicConfig(**log_kwargs)
    logger = logging.getLogger('garbagetruck')

@main.command()
@click.option('--older-than', metavar='AGE_COUNT_PERIOD', default='90 days',
              help='indicate what files should be trashed using relative age like '\
                   '"14 days", "2 weeks", or "6 months"')
@click.option('--check-every', metavar='CHECK_COUNT_PERIOD', default='week',
              help='indicate how often a check should be made to find old files using relative '\
                   'age like "14 days", "2 weeks", or "6 months"')
@click.argument('job_name')
@click.argument('dirs', type=click.Path(file_okay=False, resolve_path=True), nargs=-1)
def set(older_than, check_every, job_name, dirs):
    '''Add or update a scheduled trash job.'''
    run_command_format = sys.argv[0] + ' run %s'
    truck = GarbageTruck()
    truck.set_job(run_command_format, job_name, dirs,
                  files_older_than=older_than, check_every=check_every)
    truck.save_changes()

@main.command()
def list():
    '''List all scheduled jobs.'''
    truck = GarbageTruck()
    truck.list_jobs()

@main.command()
@click.argument('job_names', nargs=-1)
def remove(job_names):
    '''Remove scheduled trash jobs.'''
    truck = GarbageTruck()
    for name in job_names:
        truck.remove_job(name)
    truck.save_changes()

@main.command()
@click.argument('job_id')
def run(job_id):
    '''Run a trash job.

    Usually, this is invoked by the scheduler when it's time to run a trash job. It can also be run
    manually to see the results now instead of waiting for the next scheduled run.

    If the standard output (stdout) is _NOT_ a TTY (a terminal or console), logging will
    automatically be directed into a file.
    '''
    truck = GarbageTruck()
    truck.run_job(job_id)

if __name__ == "__main__":
    main()
