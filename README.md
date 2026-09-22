# Planes de Gestión — FORCEMOVIL S.A.C.

Sitio web de consulta del **Plan Anual de Seguridad y Salud en el Trabajo** y del **Plan Anual de Gestión Ambiental**.

Es un sitio estático: no necesita base de datos, servidor de aplicaciones ni instalación de dependencias. Funciona en GitHub Pages tal como está.

---

## 1. Cómo ver el sitio

### En GitHub Pages

1. Suba el contenido de esta carpeta a un repositorio de GitHub.
2. En el repositorio, entre a **Settings → Pages**.
3. En *Source*, elija **Deploy from a branch**; rama `main` y carpeta `/ (root)`.
4. Guarde. A los pocos minutos el sitio estará disponible en
   `https://<usuario>.github.io/<repositorio>/`

### En su computadora

El sitio lee su contenido desde archivos externos, por lo que **abrir `index.html` con doble clic no funciona**: el navegador bloquea esas lecturas cuando la página se abre desde el disco (protocolo `file://`). Es una restricción de seguridad del navegador, no un error del sitio.

Para verlo localmente, abra una terminal en esta carpeta y ejecute:

```bash
python3 servir.py
```

Luego abra `http://localhost:8000` en el navegador. Para usar otro puerto: `python3 servir.py 8080`.

---

## 2. Estructura del proyecto

```
.
├── index.html                  Única página del sitio
├── servir.py                   Servidor local para revisión (no se usa en GitHub)
├── .nojekyll                   Evita que GitHub Pages procese el sitio con Jekyll
│
├── assets/
│   ├── css/estilos.css         Todos los estilos del sitio
│   └── js/app.js               Toda la lógica de navegación
│
├── datos/                      ← AQUÍ SE ACTUALIZA EL CONTENIDO
│   ├── manifiesto.json         Datos de la organización y lista de planes
│   ├── sst/
│   │   ├── indice.json         Lista de capítulos del plan de SST
│   │   ├── indicadores.json    Indicadores del plan
│   │   ├── anexos.json         Anexos del plan
│   │   └── secciones/          Un archivo HTML por capítulo
│   │       ├── 01-introduccion.html
│   │       ├── 02-objetivo-y-alcance-del-plan.html
│   │       └── …
│   └── ma/                     Misma estructura para el plan ambiental
│
└── herramientas/
    └── generar_secciones.py    Regenera datos/ a partir de los planes en Markdown
```

---

## 3. Cómo actualizar un punto del plan

Cada capítulo vive en **su propio archivo**. Para corregir un punto no hay que tocar el resto del sitio ni el código.

### Opción A — editar directamente el capítulo (lo habitual)

1. Abra el archivo del capítulo en `datos/sst/secciones/` o `datos/ma/secciones/`.
2. Edite el texto. Es HTML simple: `<p>`, `<h3>`, `<ul>`, `<table>`.
3. Guarde y haga commit.

El cambio queda publicado en cuanto GitHub Pages procese el commit. No hay que regenerar nada.

### Opción B — editar el plan completo en Word/Markdown y regenerar

Si el equipo mantiene los planes en los archivos Markdown de origen:

```bash
python3 herramientas/generar_secciones.py
```

El script reconstruye toda la carpeta `datos/` a partir de los Markdown. **Atención:** este comando sobrescribe los archivos de `datos/<plan>/secciones/`, de modo que cualquier edición hecha con la Opción A se perderá. Use una u otra forma de trabajo, no ambas a la vez.

### Cómo agregar un capítulo nuevo

1. Cree el archivo HTML en `datos/<plan>/secciones/`.
2. Agregue su entrada en `datos/<plan>/indice.json`:

```json
{
  "numero": "19",
  "titulo": "NUEVO CAPÍTULO",
  "archivo": "secciones/19-nuevo-capitulo.html",
  "vacia": false,
  "subsecciones": []
}
```

El menú lateral y la navegación se actualizan solos.

### Capítulos sin contenido

Un capítulo cuyo archivo esté vacío se marca en el índice con la nota *sin contenido* y muestra un aviso discreto. Para completarlo, basta con escribir dentro de su archivo y cambiar `"vacia": false` en el índice.

---

## 4. Cómo actualizar los indicadores

Los indicadores están en `datos/<plan>/indicadores.json`. Cada entrada tiene cuatro campos:

```json
{
  "grupo": "Indicadores preventivos",
  "indicador": "Cumplimiento del Programa Anual de SST",
  "formula": "(Actividades ejecutadas / Actividades programadas a la fecha) × 100",
  "frecuencia": "Mensual"
}
```

El campo `grupo` genera automáticamente los botones de filtro de la vista de indicadores. Si crea un grupo nuevo, aparece solo.

---

## 5. Cómo cambiar los datos de la empresa

En `datos/manifiesto.json`: razón social, sedes, direcciones, dotación de personal, y código, versión y periodo de cada plan. La portada y los encabezados se actualizan a partir de este archivo.

---

## 6. Direcciones del sitio

El sitio usa rutas con `#`, lo que permite compartir enlaces a un punto concreto:

| Dirección | Muestra |
|---|---|
| `#/` | Portada con los dos planes |
| `#/sst` | Plan de SST desde el primer capítulo |
| `#/sst/12` | Capítulo 12 del plan de SST |
| `#/sst/politica` | Política de SST |
| `#/sst/indicadores` | Indicadores del plan de SST |
| `#/sst/anexos` | Anexos del plan de SST |
| `#/ma/8` | Capítulo 8 del plan ambiental |
| `#/ma/indicadores` | Indicadores ambientales |

Para citar un capítulo en una presentación o en un correo, copie la dirección de la barra del navegador: al abrirla, el sitio va directo a ese punto.

---

## 7. Notas técnicas

- **Sin dependencias externas.** No usa librerías, CDN ni frameworks. El sitio seguirá funcionando aunque cambien servicios de terceros.
- **Carga bajo demanda.** Cada capítulo se descarga solo cuando se abre. La búsqueda es la única función que carga todos los capítulos del plan.
- **`.nojekyll`.** Evita que GitHub Pages intente procesar el sitio con Jekyll, que ignora las carpetas que empiezan con guion bajo y puede alterar los archivos.
- **Impresión.** Cada capítulo puede imprimirse desde el navegador: el menú y la navegación se ocultan automáticamente.
- **Responsive.** En pantallas pequeñas el índice se abre con el botón de la esquina superior izquierda y la navegación pasa a una barra inferior.

---

## 8. Advertencia sobre el contenido

Los planes son documentos de gestión. Cuando se corrija un punto en el sitio, la misma corrección debe aplicarse al documento en Word, y a la inversa. Si ambas versiones se editan por separado, terminan diciendo cosas distintas.

La forma más segura de evitarlo es mantener los archivos Markdown como única fuente y regenerar el sitio con `herramientas/generar_secciones.py` cada vez que el plan cambie.
