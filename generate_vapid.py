import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Generar clave privada
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

# Obtener clave pública
public_key = private_key.public_key()

# Serializar claves
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Convertir a formato URL-safe base64
private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')

print("\n=== CLAVES VAPID GENERADAS ===")
print(f"VAPID_PUBLIC_KEY={public_key_b64}")
print(f"VAPID_PRIVATE_KEY={private_key_b64}")
print("\nGuarda estas claves en tu archivo .env")
