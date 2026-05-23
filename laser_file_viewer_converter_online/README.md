# Laser File Viewer & Converter — Online Bilingual Version

Mini app online para visualizar y convertir archivos simples de diseños láser en madera.

This is a bilingual online tool for previewing and converting simple laser design files.

## Idiomas / Languages

La app incluye selector de idioma:

- Español
- English

Idioma por defecto:

```txt
English
```

También podés abrir la app directamente con parámetro de idioma:

```txt
?lang=en
?lang=es
```

## Formatos incluidos / Included formats

Entrada / Input:

- DXF
- SVG
- PDF
- PNG

Salida según formato cargado / Output depends on the uploaded file:

- SVG
- DXF
- PDF
- PNG

## Archivos principales / Main files

```txt
app.py
requirements.txt
laser_converter/
assets/logo_biblioteca_laser.png
assets/logo_laser_design_library.png
.streamlit/config.toml
.streamlit/secrets.toml.example
```

## Clave de acceso / Access code

Clave por defecto:

```txt
LASER2026
```

En Streamlit Community Cloud, configurar en **Secrets**:

```toml
APP_ACCESS_CODE = "LASER2026"
```

Podés cambiar `LASER2026` por la clave que quieras entregar dentro del infoproducto.

## Subir a GitHub

1. Crear un repositorio en GitHub.
2. Subir todos los archivos de esta carpeta.
3. No subir un archivo real llamado `.streamlit/secrets.toml` si el repositorio es público.
4. Mantener `.streamlit/secrets.toml.example` como ejemplo.

## Publicar en Streamlit Community Cloud

1. Entrar a Streamlit Community Cloud.
2. Crear una nueva app.
3. Elegir el repositorio de GitHub.
4. Main file path:

```txt
app.py
```

5. Deploy.
6. Agregar el Secret `APP_ACCESS_CODE`.

## Links sugeridos para entregar

Español:

```txt
https://laserconverterviz.streamlit.app/?lang=es
```

English:

```txt
https://laserconverterviz.streamlit.app/?lang=en
```

## Texto sugerido en español

**BONUS: Laser File Viewer & Converter**

Usá esta mini app para subir archivos DXF, SVG, PDF o PNG, visualizarlos antes de trabajar y descargarlos en otros formatos útiles para tus proyectos de corte láser en madera.

Clave:

```txt
LASER2026
```

## Suggested English delivery text

**BONUS: Laser File Viewer & Converter**

Use this included online tool to upload DXF, SVG, PDF, or PNG files, preview them before working, and download them in useful formats for your wood laser cutting projects.

Access code:

```txt
LASER2026
```

## Recomendación / Recommendation

Antes de cortar o grabar madera, revisar siempre escala, capas y líneas en el software de láser habitual.

Before cutting or engraving wood, always check scale, layers, and lines in your usual laser software.
