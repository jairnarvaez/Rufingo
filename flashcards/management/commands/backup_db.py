from django.core.management.base import BaseCommand
from django.conf import settings
import shutil
from pathlib import Path
from datetime import datetime


class Command(BaseCommand):
    help = 'Crea un backup de la base de datos SQLite'
    
    def handle(self, *args, **options):
        # Ruta de la base de datos
        db_path = settings.DATABASES['default']['NAME']
        
        # Crear directorio de backups
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        # Nombre del backup con fecha
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'db_backup_{timestamp}.sqlite3'
        backup_path = backup_dir / backup_name
        
        try:
            # Copiar base de datos
            shutil.copy2(db_path, backup_path)
            
            # Obtener tamaño
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Backup creado exitosamente: {backup_name} ({size_mb:.2f} MB)'
                )
            )
            
            # Limpiar backups antiguos (mantener solo los últimos 7)
            backups = sorted(backup_dir.glob('db_backup_*.sqlite3'))
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    old_backup.unlink()
                    self.stdout.write(
                        self.style.WARNING(f'🗑️ Backup antiguo eliminado: {old_backup.name}')
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando backup: {e}')
            )
