from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# Generar clave privada EC
private_key = ec.generate_private_key(ec.SECP256R1())

# Serializar clave privada en formato DER
private_key_der = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Generar clave pública y codificar en Base64 URL-safe
public_key = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Mostrar claves codificadas en base64-url
print("VAPID_PUBLIC_KEY:", base64.urlsafe_b64encode(public_key).decode('utf-8'))
print("VAPID_PRIVATE_KEY:", base64.urlsafe_b64encode(private_key_der).decode('utf-8'))
