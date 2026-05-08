# Laser File Viewer & Converter — Versión Online

Mini app online para visualizar y convertir archivos simples de diseños láser en madera.

## Formatos incluidos

Entrada:

- DXF
- SVG
- PDF
- PNG

Salida según formato cargado:

- SVG
- DXF
- PDF
- PNG

## Archivos principales

```txt
app.py
requirements.txt
laser_converter/
.streamlit/config.toml
.streamlit/secrets.toml.example
```

## Subir a GitHub

1. Crear un repositorio en GitHub.
2. Subir todos los archivos de esta carpeta.
3. No subir un archivo real llamado `.streamlit/secrets.toml` si el repositorio es público.

## Publicar en Streamlit Community Cloud

1. Entrar a Streamlit Community Cloud.
2. Crear una nueva app.
3. Elegir el repositorio de GitHub.
4. Main file path:

```txt
app.py
```

5. Deploy.

## Configurar clave de acceso

En Streamlit Cloud, abrir la sección **Secrets** y agregar:

```toml
APP_ACCESS_CODE = "LASER2026"
```

Podés cambiar `LASER2026` por la clave que quieras entregar dentro del infoproducto.

Si no configurás Secrets, la app usa por defecto:

```txt
LASER2026
```

## Texto sugerido para entregar al cliente

**BONUS: Laser File Viewer & Converter**

Usá esta mini app para subir archivos DXF, SVG, PDF o PNG, visualizarlos antes de trabajar y descargarlos en otros formatos útiles para tus proyectos de corte láser en madera.

Acceso:

```txt
PEGAR_ACA_EL_LINK_DE_STREAMLIT
```

Clave:

```txt
LASER2026
```

## Recomendación

Antes de cortar o grabar madera, revisar siempre escala, capas y líneas en el software de láser habitual.
