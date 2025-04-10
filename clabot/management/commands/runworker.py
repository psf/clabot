import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload


def restart_worker():
    db_worker_cmd = "python manage.py db_worker"
    cmd = f'pkill -f "{db_worker_cmd}"'

    subprocess.call(shlex.split(cmd))
    subprocess.call(shlex.split(f"{db_worker_cmd}"))


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Starting db worker with autoreload...")
        autoreload.run_with_reloader(restart_worker)
