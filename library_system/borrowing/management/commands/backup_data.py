"""
Management command: backup database and media files.
    python manage.py backup_data
Creates timestamped backup in backups/ directory.
"""
import os
import shutil
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup database (JSON fixture) and media files'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = settings.BASE_DIR / 'backups' / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 1. Django fixture dump (all data as JSON)
        fixture_path = backup_dir / 'db_backup.json'
        self.stdout.write('Backing up database...')
        try:
            result = subprocess.run(
                ['python', 'manage.py', 'dumpdata', '--indent', '2',
                 '--output', str(fixture_path)],
                cwd=settings.BASE_DIR,
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f'  DB backup: {fixture_path}'))
            else:
                self.stderr.write(f'  DB backup failed: {result.stderr}')
        except Exception as e:
            self.stderr.write(f'  DB backup error: {e}')

        # 2. Media files
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            media_backup = backup_dir / 'media'
            shutil.copytree(media_root, media_backup)
            self.stdout.write(self.style.SUCCESS(f'  Media backup: {media_backup}'))
        else:
            self.stdout.write('  No media directory found, skipping.')

        self.stdout.write(self.style.SUCCESS(f'\nBackup complete: {backup_dir}'))
