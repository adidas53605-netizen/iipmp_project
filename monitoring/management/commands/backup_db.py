import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates a timestamped backup copy of the SQLite database into backups/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=7,
            help='Number of daily backup files to keep (default: 7)'
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        if not os.path.exists(db_path):
            self.stderr.write(self.style.ERROR(f"Database file not found at {db_path}"))
            return

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"db_backup_{timestamp}.sqlite3"
        backup_file_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(db_path, backup_file_path)
        self.stdout.write(self.style.SUCCESS(f"Successfully backed up database to: {backup_file_path}"))

        # Retention cleanup
        keep = options['keep']
        backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith('db_backup_')],
            key=os.path.getctime
        )
        if len(backups) > keep:
            for old_backup in backups[:-keep]:
                os.remove(old_backup)
                self.stdout.write(f"Purged old backup file: {old_backup}")
