"""
Convierte los capítulos (fragmentos HTML de datos/<plan>/secciones/) en texto
con formato dentro de un widget tk.Text.

Solo usa la biblioteca estándar de Python (html.parser + tkinter).
Soporta las etiquetas que usan los planes: h3, h4, p, ul, ol, li, strong, em,
table, y el párrafo de fórmula (p class="formula").
"""

import tkinter as tk
from html.parser import HTMLParser

FUENTE = 'Segoe UI'
MONO = 'Consolas'


def configurar_estilos(texto: tk.Text, color: str):
    """Define las etiquetas de formato del widget. color = color de acento del plan."""
    texto.tag_configure('h2', font=(FUENTE, 17, 'bold'), foreground='#1a1d21',
                        spacing1=4, spacing3=14)
    texto.tag_configure('h3', font=(FUENTE, 13, 'bold'), foreground=color,
                        spacing1=18, spacing3=8)
    texto.tag_configure('h4', font=(FUENTE, 11, 'bold'), foreground=color,
                        spacing1=12, spacing3=6)
    texto.tag_configure('p', font=(FUENTE, 10), spacing3=8, lmargin1=0, lmargin2=0)
    texto.tag_configure('li', font=(FUENTE, 10), spacing3=4, lmargin1=18, lmargin2=34)
    texto.tag_configure('b', font=(FUENTE, 10, 'bold'))
    texto.tag_configure('i', font=(FUENTE, 10, 'italic'))
    texto.tag_configure('formula', font=(MONO, 10, 'bold'), background='#f2f4f7',
                        spacing1=8, spacing3=10, lmargin1=14, lmargin2=14, rmargin=14,
                        justify='center')
    texto.tag_configure('vacio', font=(FUENTE, 10, 'italic'), foreground='#8a9099',
                        spacing1=10)
    texto.tag_configure('mark', background='#fff3c4')


class _Parser(HTMLParser):
    def __init__(self, texto: tk.Text, color: str, ancho: int):
        super().__init__(convert_charrefs=True)
        self.t = texto
        self.color = color
        self.ancho = ancho
        self.bloque = None          # etiqueta de bloque actual: p, h3, h4, li, formula
        self.en_linea = []          # pila: b, i
        self.listas = []            # pila de ('ul'|'ol', contador)
        self.tabla = None           # lista de filas mientras se lee una tabla
        self.fila = None
        self.celda = None
        self.celda_th = False

    # ---------------- apertura ----------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.tabla is not None:
            if tag == 'tr':
                self.fila = []
            elif tag in ('td', 'th'):
                self.celda = []
                self.celda_th = tag == 'th'
            return
        if tag == 'table':
            self.tabla = []
        elif tag in ('h3', 'h4'):
            self.bloque = tag
        elif tag == 'p':
            self.bloque = 'formula' if 'formula' in a.get('class', '') else 'p'
        elif tag == 'ul':
            self.listas.append(['ul', 0])
        elif tag == 'ol':
            self.listas.append(['ol', 0])
        elif tag == 'li':
            self.bloque = 'li'
            if self.listas:
                self.listas[-1][1] += 1
                tipo, n = self.listas[-1]
                viñeta = '•  ' if tipo == 'ul' else f'{n}.  '
            else:
                viñeta = '•  '
            self.t.insert('end', viñeta, ('li',))
        elif tag == 'strong':
            self.en_linea.append('b')
        elif tag == 'em':
            self.en_linea.append('i')

    # ---------------- cierre ----------------
    def handle_endtag(self, tag):
        if self.tabla is not None:
            if tag in ('td', 'th') and self.celda is not None:
                self.fila.append((''.join(self.celda).strip(), self.celda_th))
                self.celda = None
            elif tag == 'tr' and self.fila is not None:
                self.tabla.append(self.fila)
                self.fila = None
            elif tag == 'table':
                self._pintar_tabla(self.tabla)
                self.tabla = None
            return
        if tag in ('h3', 'h4', 'p', 'li'):
            self.t.insert('end', '\n', (self.bloque or 'p',))
            self.bloque = None
        elif tag in ('ul', 'ol'):
            if self.listas:
                self.listas.pop()
            self.t.insert('end', '\n', ('p',))
        elif tag in ('strong', 'em') and self.en_linea:
            self.en_linea.pop()

    # ---------------- texto ----------------
    def handle_data(self, data):
        if self.tabla is not None:
            if self.celda is not None:
                self.celda.append(data)
            return
        if not data.strip() and self.bloque is None:
            return
        etiquetas = [self.bloque or 'p']
        if 'b' in self.en_linea and self.bloque not in ('h3', 'h4', 'formula'):
            etiquetas.append('b')
        if 'i' in self.en_linea:
            etiquetas.append('i')
        self.t.insert('end', data, tuple(etiquetas))

    # ---------------- tablas ----------------
    def _pintar_tabla(self, filas):
        if not filas:
            return
        n_col = max(len(f) for f in filas)
        marco = tk.Frame(self.t, bg='#dde1e7', bd=0)
        ancho_col = max(90, (self.ancho - 40) // n_col)
        for r, fila in enumerate(filas):
            for c in range(n_col):
                txt, es_th = fila[c] if c < len(fila) else ('', False)
                encabezado = es_th or r == 0
                bg = self.color if encabezado else ('#ffffff' if r % 2 else '#f7f8fa')
                fg = '#ffffff' if encabezado else '#1a1d21'
                lbl = tk.Label(
                    marco, text=txt, bg=bg, fg=fg, justify='left', anchor='nw',
                    wraplength=ancho_col - 14, padx=7, pady=5,
                    font=(FUENTE, 9, 'bold' if encabezado else 'normal'),
                )
                lbl.grid(row=r, column=c, sticky='nsew', padx=(0 if c == 0 else 1, 0), pady=(0 if r == 0 else 1, 0))
        for c in range(n_col):
            marco.grid_columnconfigure(c, weight=1, minsize=ancho_col)
        self.t.window_create('end', window=marco, padx=0, pady=6)
        self.t.insert('end', '\n\n', ('p',))


def pintar_html(texto: tk.Text, html: str, color: str, ancho: int = 760):
    """Escribe el fragmento HTML en el widget (que debe estar en estado normal)."""
    if not html.strip():
        texto.insert('end', 'Este numeral no tiene contenido registrado.\n', ('vacio',))
        return
    _Parser(texto, color, ancho).feed(html)
