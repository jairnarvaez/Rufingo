#!/bin/bash

echo "🚀 Configurando Rufingo..."

# Crear entorno virtual
# python -m venv venv
source venv/bin/activate

# Instalar dependencias
# pip install -r requirements.txt

# Crear .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cat > .env << EOF
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
VAPID_PUBLIC_KEY=""
VAPID_PRIVATE_KEY=""
VAPID_CLAIM_EMAIL="admin@rufingo.com"
EOF
    echo "⚠️  Recuerda generar las claves VAPID con: python generate_vapid_correct.py"
fi

# Aplicar migraciones
python manage.py migrate

# Crear superusuario si no existe
echo "👤 Creando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@rufingo.com', 'admin123');
    print('✅ Superusuario creado: admin / admin123');
else:
    print('⚠️  El superusuario ya existe');
"

# Crear usuario normal si no existe
echo "👤 Creando usuario normal..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='guest').exists():
    User.objects.create_user('guest', 'guest@rufingo.com', 'guest');
    print('✅ Usuario normal creado: guest / guest');
else:
    print('⚠️  El usuario normal ya existe');
"

# Crear directorio de backups
mkdir -p backups

# Verificar integridad
python manage.py check_integrity

echo ""
echo "✅ Configuración completada"
echo ""
echo "Para iniciar el servidor:"
echo "  python manage.py runserver"
echo ""
echo "Para crear un backup:"
echo "  python manage.py backup_db"
echo ""


python manage.py collectstatic --noinput     
