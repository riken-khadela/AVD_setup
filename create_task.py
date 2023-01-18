import argparse
import tempfile

from conf import PRJ_PATH, TASKS_DIR
from main import LOGGER
from utils import run_cmd

parser = argparse.ArgumentParser(description='Create crontab tasks')
parser.add_argument(
    '--override_envfile',
    type=bool,
    nargs='?',
    const=True,
    default=False,
    help='Whether to override the environment variable file environment.sh',
)
parser.add_argument(
    '--refer_cmd_args',
    type=bool,
    nargs='?',
    const=True,
    default=False,
    help=('Whether to refer to the arguments of the original command'
          '(e.g. auto_engage.py)'),
)
parser.add_argument(
    '--cmds',
    nargs='*',
    default=['auto_engage', 'update_profile', 'create_accounts'],
    help=('The command names to be used to create the corresponding task files'
          '. Separated by blank space.'
          ' Default: auto_engage update_profile create_accounts.'
          ' e.g. auto_engage, it will be used to create a file auto_engage.sh'),
)
parser.add_argument(
    '--args',
    nargs='*',
    default=['', '', ''],
    help=('The arguments for the commands in the option --cmds respectively.'
          ' Separated by blank space. Default: no arguments for all commands.'
          ' The arguments of one command should be quoted by \' or "'),
)
parser.add_argument(
    '--jobs',
    nargs='*',
    default=['', '', ''],
    help=('The jobs in crontab for the commands in the option --cmds respectively.'
          ' Separated by blank space. Default: empty string'
          '(empty string means it will not create crontab job for the command).'
          ' The job of one command should be quoted by \' or "'
          '. The job just is the time part, for example "* * * * *"'
          ', do not include the command part.'),
)
parser.add_argument(
    '--venv_activate_path',
    nargs='?',
    default='env/bin/activate',
    help=('The path of "bin/activate" for python virtual environment. '
          'Default: env/bin/activate'),
)
parser.add_argument(
    '--override_job',
    type=bool,
    nargs='?',
    const=True,
    default=False,
    help='Whether to override the existing job in crontab',
)
args = parser.parse_args()

# create environment variable file
env_file_name = 'environment.sh'
env_file = TASKS_DIR / env_file_name

if args.override_envfile or not env_file.exists():
    LOGGER.info(f'Override the file "{env_file}"')
    cmd = 'env'
    verbose = False
    result = run_cmd(cmd, verbose=verbose)
    if result:
        (returncode, output) = result
        #  LOGGER.debug(output)
        outs = output.strip().split('\n')
        new_outs = ['export ' + e + '\n' for e in outs]
        new_output = ''.join(new_outs)
        #  LOGGER.debug(new_output)
        # write the new output
        env_file.write_text(new_output)
        LOGGER.info(f'Wrote the environment variables into the file')
    else:
        LOGGER.error('Cannot get environment variables')
else:
    LOGGER.info(f'The file "{env_file}" has existed already')

# common part of task files
common_part = f"""# project path
export CURRENT_DIR=`dirname $(readlink -f $0)`
export PRJ_DIR=`dirname $CURRENT_DIR`
# go to project root directory
cd $PRJ_DIR
#. ./tasks/environment.sh
. {str(env_file.relative_to(PRJ_PATH))}

# Kill python and AVD process
killall -9 python qemu-system-x86_64

# activate the virtual environment for python
#. env/bin/activate
. {args.venv_activate_path}

# update code
git pull origin $(git rev-parse --abbrev-ref HEAD)
"""


def create_task(name, file, args, common_part=common_part):
    task = f'python manage.py {name} {args}'
    file.write_text(common_part + '\n' + task)


# create task <cmd>.sh
i = 0
#  LOGGER.debug(f'args: {args.args}')
for cmd in args.cmds:
    LOGGER.info('-' * 40)
    file_name = f'{cmd}.sh'
    file = TASKS_DIR / file_name
    log_file = TASKS_DIR / f'{cmd}.log'

    LOGGER.info(f'Create the file "{file}"')
    cmd_args = args.args[i]
    if cmd_args == '':
        if args.refer_cmd_args:
            LOGGER.warning(f'The arguments of command {cmd} are empty')
            cmds = f'python manage.py {cmd} -h'
            verbose = False
            result = run_cmd(cmds, verbose=verbose)
            if result:
                (returncode, output) = result
                LOGGER.info('Please refer to the arguments of command '
                            f'{cmd}')
                LOGGER.info(output)

    LOGGER.info(f'Create the task {cmd} with arguments "{cmd_args}"')
    create_task(cmd, file, cmd_args)

    job = args.jobs[i]
    if job:
        cmds = 'crontab -l'
        verbose = True
        result = run_cmd(cmds, verbose=verbose)
        if result:
            (returncode, output) = result
            #  LOGGER.info(output)
            outs = output.strip().split('\n')
            outs_all = [e + '\n' for e in outs]
            effective_outs = [
                e + '\n' for e in outs if not e.strip().startswith('#')]
            if 'no crontab for' in output:
                #  outs_all = ['\n']
                outs_all = []
                effective_outs = []
            exist_flag = False
            exist_job = ''
            for item in effective_outs:
                if cmd in item:
                    LOGGER.info(f'There has already been one job for command {cmd}')
                    exist_flag = True
                    exist_job = item
                    break

            if args.override_job and exist_flag:
                LOGGER.info(f'Override the existing job: {exist_job}')
                outs_all.remove(exist_job)

            if not exist_flag or (exist_flag and args.override_job):
                new_output = ''.join(outs_all)
                job_text = f'{job} /bin/bash {str(file)} >> {str(log_file)} 2>&1'
                jobs_text = new_output + job_text + '\n'
                LOGGER.debug(jobs_text)
                with tempfile.NamedTemporaryFile(mode='w+t') as fp:
                    #  LOGGER.debug(f'jobs_text: {jobs_text}')
                    LOGGER.debug(f'Write jobs to file {fp.name}')
                    fp.write(jobs_text)
                    fp.flush()
                    # import crontab job
                    cmds = f'crontab {fp.name}'
                    verbose = True
                    result = run_cmd(cmds, verbose=verbose)
                    if result:
                        (returncode, output) = result
                        if returncode == 0:
                            LOGGER.info('Imported jobs into crontab')
                        else:
                            LOGGER.info('Failed to importe jobs into crontab')
                    else:
                        LOGGER.info('Cannot importe jobs into crontab')
                #  LOGGER.debug(new_output)
        else:
            LOGGER.error('Cannot get crontab jobs')
    else:
        LOGGER.info(f'Do not create crontab job for {cmd}')

    i += 1
