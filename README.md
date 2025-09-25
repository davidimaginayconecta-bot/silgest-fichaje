# Silgest Fichaje

Esta aplicación permite a los empleados fichar su jornada laboral, registrar pausas y solicitar ausencias. Utiliza Firebase (Firestore y Authentication) como backend y una interfaz de escritorio en Python/PyQt5. Para ejecutarla necesitas Python 3.9 o superior, una cuenta de servicio de Firebase y usuarios autenticados en Firebase Authentication.

## Pre-requisitos

- Python 3.9 o superior instalado.
- Clave de servicio de Firebase: descarga tu `serviceAccountKey.json` desde la consola de Firebase y colócalo en la raíz del proyecto.
- Firestore y Authentication activados en modo producción.

## Instalación

1. Clona este repositorio o crea la estructura de archivos según este proyecto.
2. Copia `serviceAccountKey.json` en la carpeta raíz.
3. En una terminal:

```
python -m venv venv
venv\Scripts\activate   # en Windows
pip install --upgrade pip
pip install -r requirements.txt
```

4. Ejecuta:

```
python main.py
```

Se abrirá la ventana de inicio de sesión; introduce tu correo y contraseña registrados en Firebase para empezar a fichar, pausar, finalizar tu jornada y solicitar ausencias.

## Compilación para Windows

Si deseas generar un ejecutable para Windows, puedes instalar PyInstaller y ejecutar:

```
pip install pyinstaller
pyinstaller --noconsole --onefile main.py
```

Esto generará un archivo `dist/main.exe` sin firma digital. Para firmar digitalmente el ejecutable necesitarás tu propio certificado y hacerlo en tu equipo.

## Personalización

- Los colores de la interfaz están definidos en `main.py` mediante las constantes `COLOR_PRIMARIO`, `COLOR_SECUNDARIO`, `COLOR_ALERTA` y `COLOR_FONDO`.
- El logotipo de la aplicación se codifica en Base64 dentro de `main.py`. Puedes reemplazar la cadena Base64 por otra generada a partir de tu propio logotipo.
