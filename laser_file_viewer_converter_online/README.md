# Laser File Viewer & Converter — Online Trilingual Version

Mini app online para visualizar y convertir archivos simples de diseños láser en madera.

This online tool lets users preview and convert simple laser design files.

Questa mini app online permette di visualizzare e convertire file semplici per progetti di taglio laser su legno.

## Idiomas / Languages / Lingue

La app incluye selector de idioma:

- English
- Español
- Italiano

Idioma por defecto:

```txt
English
```

También podés abrir la app directamente con parámetro de idioma:

```txt
?lang=en
?lang=es
?lang=it
```

## Formatos incluidos / Included formats / Formati inclusi

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

Nota: Italiano usa el mismo logo que Español: `assets/logo_biblioteca_laser.png`.

## Clave de acceso / Access code / Codice di accesso

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

Italiano:

```txt
https://laserconverterviz.streamlit.app/?lang=it
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

## Testo suggerito in italiano

**BONUS: Laser File Viewer & Converter**

Usa questa mini app inclusa per caricare file DXF, SVG, PDF o PNG, visualizzarli prima di lavorare e scaricarli in formati utili per i tuoi progetti di taglio laser su legno.

Codice di accesso:

```txt
LASER2026
```

## Recomendación / Recommendation / Consiglio

Antes de cortar o grabar madera, revisar siempre escala, capas y líneas en el software de láser habitual.

Before cutting or engraving wood, always check scale, layers, and lines in your usual laser software.

Prima di tagliare o incidere il legno, controlla sempre scala, livelli e linee nel tuo software laser abituale.
