import json
import os


env_variables = {
    "SECRET_KEY": "",
    "DATABASE_URL": "",
    "CLOUDINARY_URL": "",
    "HP_SPECTRE_360_IP": "",
    "CSRF_TRUSTED_ORIGINS": [
        "",
        "",
    ],
    "DEBUG": True,
    "ALLOWED_HOSTS": [
        "",
        "",
    ]
}

# Setăm variabilele în mediul de sistem folosind os.environ
for key, value in env_variables.items():
    if isinstance(value, list) or isinstance(value, dict):
        os.environ[key] = json.dumps(value)  
    else:
        os.environ[key] = str(value) 
