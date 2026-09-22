#!/usr/bin/env python3
"""
Genera los archivos de datos del sitio a partir de los planes en Markdown.

Cada capítulo del plan se convierte en un archivo HTML independiente dentro de
datos/<plan>/secciones/. De este modo, actualizar un punto del plan consiste en
editar un solo archivo pequeno, sin tocar el resto del sitio.

Uso:
    python3 herramientas/generar_secciones.py

Entradas:
    ../contenido/plan_sst_p*.md
    ../contenido/plan_ma_p*.md
    ../config_plan_v03.json
    ../config_ma_v01.json

Salidas:
    datos/manifiesto.json
    datos/<plan>/indice.json
    datos/<plan>/indicadores.json
    datos/<plan>/anexos.json
    datos/<plan>/secciones/NN-slug.html
"""

import json
import os
import re
import glob
import shutil
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # web/
BASE = os.path.dirname(RAIZ)                                          # forcemovil/
DATOS = os.path.join(RAIZ, 'datos')


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------

def slug(texto, largo=48):
    t = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    t = re.sub(r'[^a-zA-Z0-9]+', '-', t).strip('-').lower()
    return t[:largo].rstrip('-')


def escapar(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def enriquecer(t):
    """Negritas, itálicas y fórmulas en línea."""
    t = escapar(t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    return t


def formula(linea):
    f = linea.replace('$$', '')
    f = re.sub(r'\\text\{([^}]*)\}', r'\1', f)
    f = f.replace('\\times', '×').replace('\\,', ' ')
    f = re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}',
               lambda m: m.group(1).strip() + ' ÷ ' + m.group(2).strip(), f)
    return re.sub(r'\s+', ' ', f).strip()


# --------------------------------------------------------------------------
# markdown -> html (subconjunto usado por los planes)
# --------------------------------------------------------------------------

def md_a_html(lineas):
    out = []
    i = 0
    lista_abierta = None

    def cerrar_lista():
        nonlocal lista_abierta
        if lista_abierta:
            out.append(f'</{lista_abierta}>')
            lista_abierta = None

    while i < len(lineas):
        L = lineas[i]

        if not L.strip():
            cerrar_lista()
            i += 1
            continue

        if L.startswith('---'):
            cerrar_lista()
            i += 1
            continue

        # tablas
        if L.startswith('|'):
            cerrar_lista()
            filas = []
            while i < len(lineas) and lineas[i].startswith('|'):
                crudo = lineas[i].strip().strip('|')
                if not re.fullmatch(r'[\s:|-]+', crudo):
                    filas.append([c.strip() for c in crudo.split('|')])
                i += 1
            if filas:
                out.append('<div class="tabla-wrap"><table>')
                out.append('<thead><tr>' + ''.join(
                    f'<th>{enriquecer(c)}</th>' for c in filas[0]) + '</tr></thead>')
                out.append('<tbody>')
                for f in filas[1:]:
                    out.append('<tr>' + ''.join(
                        f'<td>{enriquecer(c)}</td>' for c in f) + '</tr>')
                out.append('</tbody></table></div>')
            continue

        # fórmulas
        if L.startswith('$$'):
            cerrar_lista()
            out.append(f'<p class="formula">{escapar(formula(L))}</p>')
            i += 1
            continue

        # encabezados internos
        m = re.match(r'^###\s+(.*)', L)
        if m:
            cerrar_lista()
            out.append(f'<h4 id="{slug(m.group(1))}">{enriquecer(m.group(1))}</h4>')
            i += 1
            continue
        m = re.match(r'^##\s+(.*)', L)
        if m:
            cerrar_lista()
            out.append(f'<h3 id="{slug(m.group(1))}">{enriquecer(m.group(1))}</h3>')
            i += 1
            continue

        # listas
        m = re.match(r'^[-*]\s+(.*)', L)
        if m:
            if lista_abierta != 'ul':
                cerrar_lista()
                out.append('<ul>')
                lista_abierta = 'ul'
            out.append(f'<li>{enriquecer(m.group(1))}</li>')
            i += 1
            continue

        m = re.match(r'^(\d+)\.\s+(.*)', L)
        if m:
            if lista_abierta != 'ol':
                cerrar_lista()
                out.append('<ol>')
                lista_abierta = 'ol'
            out.append(f'<li>{enriquecer(m.group(2))}</li>')
            i += 1
            continue

        cerrar_lista()
        out.append(f'<p>{enriquecer(L)}</p>')
        i += 1

    cerrar_lista()
    return '\n'.join(out)


# --------------------------------------------------------------------------
# partir el plan en capítulos
# --------------------------------------------------------------------------

def partir_en_capitulos(md):
    """Devuelve [(numero, titulo, [lineas de cuerpo]), ...]"""
    caps = []
    actual = None
    for L in md.split('\n'):
        m = re.match(r'^#\s+(.*)', L)
        if m:
            if actual:
                caps.append(actual)
            titulo_bruto = m.group(1).strip()
            mm = re.match(r'^(\d+)\.\s*(.*)', titulo_bruto)
            if mm:
                actual = [mm.group(1), mm.group(2).strip(), []]
            else:
                actual = ['', titulo_bruto, []]
        elif actual:
            actual[2].append(L)
    if actual:
        caps.append(actual)
    return caps


def subsecciones(lineas):
    subs = []
    for L in lineas:
        m = re.match(r'^##\s+(.*)', L)
        if m:
            t = m.group(1).strip()
            subs.append({'titulo': t, 'ancla': slug(t)})
    return subs


# --------------------------------------------------------------------------
# extracción de indicadores desde las tablas de los planes
# --------------------------------------------------------------------------

def extraer_indicadores(md, plan):
    """Recoge las tablas cuyo encabezado sea Indicador | Fórmula | Frecuencia."""
    indicadores = []
    grupo = None
    lineas = md.split('\n')
    i = 0
    while i < len(lineas):
        L = lineas[i]
        m = re.match(r'^##+\s+(.*)', L)
        if m:
            grupo = re.sub(r'^\d+(\.\d+)*\.\s*', '', m.group(1).strip())
        if re.match(r'^\*\*Indicadores', L):
            grupo = L.strip().strip('*').strip()
        if L.startswith('|'):
            filas = []
            while i < len(lineas) and lineas[i].startswith('|'):
                crudo = lineas[i].strip().strip('|')
                if not re.fullmatch(r'[\s:|-]+', crudo):
                    filas.append([c.strip().replace('**', '') for c in crudo.split('|')])
                i += 1
            if filas and len(filas[0]) == 3 and filas[0][0].lower().startswith('indicador'):
                for f in filas[1:]:
                    indicadores.append({
                        'grupo': grupo or 'General',
                        'indicador': f[0],
                        'formula': f[1],
                        'frecuencia': f[2],
                    })
            continue
        i += 1

    # índices estadísticos del plan de SST (se describen con fórmula $$)
    if plan == 'sst':
        # Los índices estadísticos se declaran como "### N.N.N. Título" seguido,
        # pocas líneas después, de una fórmula entre $$. Se recorre línea a línea
        # para no arrastrar texto de otros apartados.
        resultado = []
        for j, L in enumerate(lineas):
            m = re.match(r'^###\s+[\d.]+\.\s*(.+)$', L)
            if not m:
                continue
            titulo = m.group(1).strip()
            for k in range(j + 1, min(j + 5, len(lineas))):
                sig = lineas[k].strip()
                if sig.startswith('###') or sig.startswith('##'):
                    break
                if sig.startswith('$$'):
                    resultado.append({
                        'grupo': 'Indicadores de resultado',
                        'indicador': titulo,
                        'formula': formula(sig),
                        'frecuencia': 'Mensual',
                    })
                    break
        indicadores = resultado + indicadores
    return indicadores


def extraer_anexos(md):
    anexos = []
    bloque = md.split('# ANEXOS')
    if len(bloque) < 2:
        return anexos
    for L in bloque[1].split('\n'):
        if L.startswith('|'):
            c = [x.strip() for x in L.strip().strip('|').split('|')]
            if len(c) >= 2 and re.fullmatch(r'\d+', c[0]):
                anexos.append({'numero': c[0], 'titulo': c[1]})
    return anexos


# --------------------------------------------------------------------------
# proceso principal
# --------------------------------------------------------------------------

PLANES = [
    {
        'id': 'sst',
        'nombre': 'Plan Anual de Seguridad y Salud en el Trabajo',
        'nombre_corto': 'Plan de SST',
        'descripcion': 'Prevención de accidentes de trabajo, incidentes peligrosos y enfermedades ocupacionales.',
        'patron': 'contenido/plan_sst_p*_v01.md',
        'config': 'config_plan_v03.json',
        'color': 'sst',
    },
    {
        'id': 'ma',
        'nombre': 'Plan Anual de Gestión Ambiental',
        'nombre_corto': 'Plan de Medio Ambiente',
        'descripcion': 'Prevención, control y mitigación de los impactos ambientales de la operación.',
        'patron': 'contenido/plan_ma_p*_v01.md',
        'config': 'config_ma_v01.json',
        'color': 'ma',
    },
]


def main():
    manifiesto = {'organizacion': None, 'planes': []}

    for plan in PLANES:
        archivos = sorted(glob.glob(os.path.join(BASE, plan['patron'])))
        if not archivos:
            print(f"  ! sin fuentes para {plan['id']}")
            continue

        md = '\n'.join(open(a, encoding='utf8').read() for a in archivos)
        cfg = json.load(open(os.path.join(BASE, plan['config']), encoding='utf8'))
        md = md.replace('{{PERIODO}}', str(cfg['periodo']))

        dir_plan = os.path.join(DATOS, plan['id'])
        dir_sec = os.path.join(dir_plan, 'secciones')
        if os.path.isdir(dir_sec):
            shutil.rmtree(dir_sec)
        os.makedirs(dir_sec, exist_ok=True)

        indice = {
            'id': plan['id'],
            'titulo': plan['nombre'],
            'titulo_corto': plan['nombre_corto'],
            'descripcion': plan['descripcion'],
            'codigo': cfg['codigo_documento'],
            'version': cfg['version'],
            'periodo': cfg['periodo'],
            'secciones': [],
        }

        for numero, titulo, cuerpo in partir_en_capitulos(md):
            if titulo.upper().startswith('ANEXOS'):
                continue
            nombre = f"{(numero or '00').zfill(2)}-{slug(titulo)}.html"
            html = md_a_html(cuerpo)
            with open(os.path.join(dir_sec, nombre), 'w', encoding='utf8') as fh:
                fh.write(html)
            indice['secciones'].append({
                'numero': numero,
                'titulo': titulo,
                'archivo': f'secciones/{nombre}',
                'vacia': len(html.strip()) == 0,
                'subsecciones': subsecciones(cuerpo),
            })

        with open(os.path.join(dir_plan, 'indice.json'), 'w', encoding='utf8') as fh:
            json.dump(indice, fh, ensure_ascii=False, indent=2)

        with open(os.path.join(dir_plan, 'indicadores.json'), 'w', encoding='utf8') as fh:
            json.dump(extraer_indicadores(md, plan['id']), fh, ensure_ascii=False, indent=2)

        with open(os.path.join(dir_plan, 'anexos.json'), 'w', encoding='utf8') as fh:
            json.dump(extraer_anexos(md), fh, ensure_ascii=False, indent=2)

        manifiesto['organizacion'] = {
            'razon_social': cfg['razon_social'],
            'giro': cfg.get('giro', ''),
            'sedes': cfg.get('sedes', []),
            'total_trabajadores': cfg.get('total_trabajadores'),
        }
        manifiesto['planes'].append({
            'id': plan['id'],
            'titulo': plan['nombre'],
            'titulo_corto': plan['nombre_corto'],
            'descripcion': plan['descripcion'],
            'codigo': cfg['codigo_documento'],
            'version': cfg['version'],
            'periodo': cfg['periodo'],
            'color': plan['color'],
            'n_secciones': len(indice['secciones']),
        })

        print(f"  {plan['id']}: {len(indice['secciones'])} secciones")

    os.makedirs(DATOS, exist_ok=True)
    with open(os.path.join(DATOS, 'manifiesto.json'), 'w', encoding='utf8') as fh:
        json.dump(manifiesto, fh, ensure_ascii=False, indent=2)
    print('manifiesto.json generado')


if __name__ == '__main__':
    main()
