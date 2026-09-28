"""
Carga de datos de los planes.

La aplicación Python lee exactamente los mismos archivos que la versión web
(carpeta datos/ en la raíz del repositorio). Así existe una sola fuente de
contenido: si se corrige un capítulo, el cambio aparece en la web y en Python.
"""

import json
from pathlib import Path

# app_python/planes/datos.py  ->  raíz del repositorio = dos niveles arriba de app_python
RAIZ_REPO = Path(__file__).resolve().parents[2]
CARPETA_DATOS = RAIZ_REPO / 'datos'


class ErrorDatos(Exception):
    """Se lanza cuando falta la carpeta de datos o algún archivo obligatorio."""


def _leer_json(ruta: Path):
    if not ruta.exists():
        raise ErrorDatos(f'No se encontró el archivo:\n{ruta}')
    with open(ruta, encoding='utf-8') as fh:
        return json.load(fh)


class Plan:
    """Un plan (SST o Medio Ambiente) con sus secciones, indicadores y anexos."""

    def __init__(self, id_plan: str):
        self.id = id_plan
        self.carpeta = CARPETA_DATOS / id_plan
        self.indice = _leer_json(self.carpeta / 'indice.json')
        self.indicadores = self._opcional('indicadores.json')
        self.anexos = self._opcional('anexos.json')
        self._cache = {}

    def _opcional(self, nombre):
        ruta = self.carpeta / nombre
        return _leer_json(ruta) if ruta.exists() else []

    # --- datos generales -------------------------------------------------

    @property
    def titulo(self):
        return self.indice.get('titulo', '')

    @property
    def titulo_corto(self):
        return self.indice.get('titulo_corto', self.titulo)

    @property
    def secciones(self):
        return self.indice.get('secciones', [])

    @property
    def ficha(self):
        i = self.indice
        return f"{i.get('codigo', '')} · v{i.get('version', '')} · Periodo {i.get('periodo', '')}"

    # --- contenido --------------------------------------------------------

    def html_seccion(self, seccion: dict) -> str:
        archivo = seccion['archivo']
        if archivo not in self._cache:
            ruta = self.carpeta / archivo
            self._cache[archivo] = ruta.read_text(encoding='utf-8') if ruta.exists() else ''
        return self._cache[archivo]

    def seccion_politica(self):
        for s in self.secciones:
            if 'POLÍTICA' in s['titulo'].upper() or 'POLITICA' in s['titulo'].upper():
                return s
        return None

    def grupos_indicadores(self):
        vistos = []
        for d in self.indicadores:
            if d['grupo'] not in vistos:
                vistos.append(d['grupo'])
        return vistos

    def buscar(self, texto: str):
        """Devuelve [(seccion, fragmento)] de los capítulos que contienen el texto."""
        import re
        import unicodedata

        def norm(t):
            t = unicodedata.normalize('NFD', t)
            return ''.join(c for c in t if unicodedata.category(c) != 'Mn').lower()

        q = norm(texto.strip())
        if len(q) < 3:
            return []
        resultados = []
        for s in self.secciones:
            plano = re.sub(r'<[^>]+>', ' ', self.html_seccion(s))
            plano = re.sub(r'\s+', ' ', s['titulo'] + ' ' + plano)
            pos = norm(plano).find(q)
            if pos >= 0:
                ini = max(0, pos - 80)
                frag = ('…' if ini else '') + plano[ini:pos + len(texto) + 120].strip() + '…'
                resultados.append((s, frag))
        return resultados


def cargar_manifiesto():
    if not CARPETA_DATOS.exists():
        raise ErrorDatos(
            'No se encontró la carpeta "datos".\n\n'
            f'Se buscó en:\n{CARPETA_DATOS}\n\n'
            'La carpeta app_python debe estar dentro del repositorio, '
            'al mismo nivel que la carpeta datos.'
        )
    return _leer_json(CARPETA_DATOS / 'manifiesto.json')
