# Aplicación Python — Planes de Gestión

Aplicación de escritorio para consultar el Plan Anual de SST y el Plan Anual de Gestión Ambiental.

## Cómo abrirla

**Requisito:** Python 3.8 o superior ([python.org/downloads](https://www.python.org/downloads/)). En Windows, al instalar, marque *"Add python.exe to PATH"*. No hay que instalar ninguna librería: usa solo lo que trae Python.

| Sistema | Forma más simple | Desde la terminal |
|---|---|---|
| Windows | Doble clic en `abrir_app_windows.bat` | `python ejecutar.py` |
| macOS / Linux | `./abrir_app_mac_linux.sh` | `python3 ejecutar.py` |
| Visual Studio Code | Abrir `ejecutar.py` y presionar ▷ *Run Python File* | — |

Ejecútela siempre desde la carpeta `app_python`, dentro del repositorio completo.

## Qué incluye

- **Inicio:** elección del plan y ficha de sedes.
- **Secciones:** índice de capítulos y contenido completo, con navegación anterior/siguiente.
- **Política**, **Indicadores** (filtrables por familia) y **Anexos**.
- **Calculadora:** índices de frecuencia, severidad y accidentabilidad (constante 1 000 000 HHT) e indicadores de cumplimiento con semáforo verde/ámbar/rojo, conforme a los numerales 14.2, 14.8 y 14.9 del Plan de SST y 9.4 del Plan Ambiental.
- **Búsqueda** de términos en todo el plan.

## De dónde saca el contenido

Lee la carpeta `datos/` del repositorio: **los mismos archivos que la versión web**. Corregir un capítulo en `datos/<plan>/secciones/` actualiza la web y la aplicación Python a la vez.

## Estructura

```
app_python/
├── ejecutar.py              Punto de entrada
├── abrir_app_windows.bat    Lanzador de doble clic (Windows)
├── abrir_app_mac_linux.sh   Lanzador (macOS / Linux)
└── planes/
    ├── datos.py             Lectura de datos/ (manifiesto, índices, capítulos)
    ├── renderizador.py      Convierte cada capítulo en texto con formato
    ├── calculadora.py       Fórmulas de indicadores y semáforo
    └── ventana.py           Interfaz gráfica (tkinter)
```

Las fórmulas de `calculadora.py` son funciones independientes (`indice_frecuencia`, `indice_severidad`, `indice_accidentabilidad`, `porcentaje`, `semaforo`) que pueden reutilizarse o probarse por separado.

## Si no abre

| Mensaje | Solución |
|---|---|
| `python no se reconoce como comando` | Reinstale Python marcando *Add python.exe to PATH*, o use `py ejecutar.py`. |
| `No se encontró tkinter` | Windows/macOS: reinstale Python desde python.org con la opción *tcl/tk*. Ubuntu: `sudo apt install python3-tk`. |
| `No se encontró la carpeta "datos"` | La carpeta `app_python` fue sacada del repositorio. Debe estar junto a `datos/`. |
