import os
import firebase_admin
from firebase_admin import credentials, firestore, auth


def initialize_firebase():
    """
    Inicializa Firebase usando un fichero de credenciales JSON.
    Asegúrate de colocar el fichero 'serviceAccountKey.json'
    en la raíz del proyecto o especificar su ruta en la variable
    de entorno GOOGLE_APPLICATION_CREDENTIALS.
    """
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey.json')
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()
