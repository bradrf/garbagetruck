import click
import logging

@click.command()
@click.option('-l', '--log-level', type=click.Choice(['debug','info','warning','error','critical']),
              help='set logging level', default='info')
@click.option('--log-file', metavar='FILENAME',
              help='write logs to FILENAME', default='STDERR')
@click.argument('name')
@click.argument('dirs', type=click.Path(file_okay=False, resolve_path=True), nargs=-1)
def main(log_level, log_file, name, dirs):
    log_kwargs = {
        'level': getattr(logging, log_level.upper())
    }
    if log_file != 'STDERR':
        log_kwargs['filename'] = log_file
    logging.basicConfig(**log_kwargs)
    logger = logging.getLogger('garbagetruck')

    truck = GarbageTruck()
    truck.set_job(name, dirs)
    truck.save_changes()

if __name__ == "__main__":
    main()
