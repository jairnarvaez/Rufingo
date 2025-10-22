from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserSettings


@receiver(post_save, sender=User)
def crear_user_settings(sender, instance, created, **kwargs):
    """Crea automáticamente UserSettings cuando se crea un usuario"""
    if created:
        UserSettings.objects.create(usuario=instance)
