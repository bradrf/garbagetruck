import sys
import click
import logging

from .garbagetruck import GarbageTruck

@click.group()
@click.option('-l', '--log-level', type=click.Choice(['debug','info','warning','error','critical']),
              help='set logging level', default='info')
@click.option('--log-file', metavar='FILENAME',
              help='write logs to FILENAME', default='STDERR')
def main(log_level, log_file):
    log_kwargs = {
        'level': getattr(logging, log_level.upper())
    }
    if log_file != 'STDERR':
        log_kwargs['filename'] = log_file
    logging.basicConfig(**log_kwargs)
    logger = logging.getLogger('garbagetruck')

@main.command()
@click.argument('job_name')
@click.argument('dirs', type=click.Path(file_okay=False, resolve_path=True), nargs=-1)
def set(job_name, dirs):
    run_command_format = sys.argv[0] + ' run %s'
    truck = GarbageTruck()
    truck.set_job(run_command_format, job_name, dirs)
    truck.save_changes()

@main.command()
@click.argument('job_name')
def remove(job_name):
    truck = GarbageTruck()
    truck.remove_job(job_name)
    truck.save_changes()

@main.command()
@click.argument('job_id')
def run(job_id):
    truck = GarbageTruck()
    truck.run_job(job_id)

if __name__ == "__main__":
    main()
