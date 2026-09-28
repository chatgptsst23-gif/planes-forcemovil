"""
Ventana principal de la aplicación de consulta de los planes.

Pantallas:
  - Inicio: elección del plan (SST o Medio Ambiente) y ficha de sedes.
  - Plan:   índice de capítulos a la izquierda y, a la derecha, una de estas vistas:
            Secciones · Política · Indicadores · Anexos · Calculadora · Búsqueda
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .datos import Plan, cargar_manifiesto, ErrorDatos
from .renderizador import configurar_estilos, pintar_html, FUENTE
from .calculadora import Calculadora

COLORES = {'sst': '#1f3864', 'ma': '#1e5b3f'}

SIGLAS = {'SST', 'CSST', 'S.A.C.', 'FORCEMOVIL', 'IPERC', 'GES', 'EO-RS', 'EPP', 'RISST'}


def tipo_oracion(titulo):
    """'CARACTERIZACIÓN DE FORCEMOVIL S.A.C.' -> 'Caracterización de FORCEMOVIL S.A.C.'"""
    palabras = []
    for k, w in enumerate(titulo.split()):
        limpio = w.strip(',;:()')
        if limpio.upper() in SIGLAS:
            palabras.append(w.upper())
        else:
            w = w.lower()
            palabras.append(w[:1].upper() + w[1:] if k == 0 else w)
    return ' '.join(palabras)
SUAVES = {'sst': '#eaeff7', 'ma': '#e6f2ec'}


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Planes de Gestión')
        self.geometry('1200x760')
        self.minsize(960, 600)
        self.configure(bg='white')

        try:
            self.manifiesto = cargar_manifiesto()
        except ErrorDatos as e:
            self.withdraw()
            messagebox.showerror('No se encontraron los datos', str(e))
            self.destroy()
            return

        org = self.manifiesto.get('organizacion') or {}
        self.razon = org.get('razon_social', '')
        if self.razon:
            self.title(f'Planes de Gestión — {self.razon}')

        self.planes = {}          # cache de objetos Plan
        self.plan = None
        self.indice_actual = 0

        self._estilos_ttk()
        self.contenedor = tk.Frame(self, bg='white')
        self.contenedor.pack(fill='both', expand=True)
        self.mostrar_inicio()

    # ------------------------------------------------------------------ estilos
    def _estilos_ttk(self, color='#1f3864'):
        s = ttk.Style(self)
        try:
            s.theme_use('clam')
        except tk.TclError:
            pass
        s.configure('.', font=(FUENTE, 10), background='white')
        s.configure('TFrame', background='white')
        s.configure('TLabel', background='white', foreground='#1a1d21')
        s.configure('TLabelframe', background='white')
        s.configure('TLabelframe.Label', background='white', foreground=color, font=(FUENTE, 10, 'bold'))
        s.configure('Titulo.TLabel', font=(FUENTE, 17, 'bold'))
        s.configure('Nota.TLabel', foreground='#4a5058', font=(FUENTE, 9))
        s.configure('Acento.TButton', background=color, foreground='white',
                    font=(FUENTE, 10, 'bold'), padding=(14, 6), borderwidth=0)
        s.map('Acento.TButton', background=[('active', color)])
        s.configure('Nav.TButton', background='white', foreground='#4a5058',
                    font=(FUENTE, 10), padding=(12, 6), borderwidth=0)
        s.map('Nav.TButton', background=[('active', '#f2f4f7')])
        s.configure('NavActivo.TButton', background=SUAVES.get(self.plan.id if self.plan else 'sst'),
                    foreground=color, font=(FUENTE, 10, 'bold'), padding=(12, 6), borderwidth=0)
        s.configure('Treeview', rowheight=46, font=(FUENTE, 9), background='white', fieldbackground='white')
        s.configure('Treeview.Heading', font=(FUENTE, 9, 'bold'), background=color, foreground='white')
        s.map('Treeview.Heading', background=[('active', color)])

    def _limpiar(self):
        for w in self.contenedor.winfo_children():
            w.destroy()

    # =================================================================== INICIO
    def mostrar_inicio(self):
        self.plan = None
        self._estilos_ttk()
        self._limpiar()

        marco = tk.Frame(self.contenedor, bg='white')
        marco.place(relx=0.5, rely=0.46, anchor='center')

        tk.Label(marco, text=self.razon.upper(), bg='white', fg='#1f3864',
                 font=(FUENTE, 10, 'bold')).pack(anchor='w')
        tk.Label(marco, text='Planes de gestión', bg='white', fg='#1a1d21',
                 font=(FUENTE, 26, 'bold')).pack(anchor='w')
        tk.Label(marco, text='Seleccione el plan que desea consultar.', bg='white',
                 fg='#4a5058', font=(FUENTE, 11)).pack(anchor='w', pady=(0, 22))

        fila = tk.Frame(marco, bg='white')
        fila.pack(anchor='w')
        for i, p in enumerate(self.manifiesto.get('planes', [])):
            self._tarjeta_plan(fila, p).grid(row=0, column=i, padx=(0 if i == 0 else 16, 0), sticky='n')

        sedes = (self.manifiesto.get('organizacion') or {}).get('sedes', [])
        if sedes:
            ficha = tk.Frame(marco, bg='#f7f8fa', highlightbackground='#eef0f3', highlightthickness=1)
            ficha.pack(fill='x', pady=(26, 0))
            tk.Label(ficha, text='ALCANCE DE LOS PLANES', bg='#f7f8fa', fg='#767c85',
                     font=(FUENTE, 9, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', padx=16, pady=(12, 6))
            total = 0
            for r, s in enumerate(sedes, start=1):
                nombre = s['nombre'] + (' (principal)' if s.get('principal') else '')
                tk.Label(ficha, text=nombre, bg='#f7f8fa', font=(FUENTE, 9, 'bold')).grid(
                    row=r, column=0, sticky='w', padx=16, pady=2)
                tk.Label(ficha, text=f"{s.get('direccion', '')}  ·  {s.get('trabajadores', '')} trabajadores",
                         bg='#f7f8fa', fg='#4a5058', font=(FUENTE, 9)).grid(row=r, column=1, sticky='w', pady=2)
                total += s.get('trabajadores') or 0
            tk.Label(ficha, text='Total', bg='#f7f8fa', font=(FUENTE, 9, 'bold')).grid(
                row=len(sedes) + 1, column=0, sticky='w', padx=16, pady=(4, 12))
            tk.Label(ficha, text=f'{total} trabajadores', bg='#f7f8fa', font=(FUENTE, 9, 'bold')).grid(
                row=len(sedes) + 1, column=1, sticky='w', pady=(4, 12))

    def _tarjeta_plan(self, padre, p):
        color = COLORES.get(p['id'], '#1f3864')
        suave = SUAVES.get(p['id'], '#eaeff7')
        f = tk.Frame(padre, bg='white', highlightbackground='#dde1e7', highlightthickness=1,
                     cursor='hand2', width=380, height=230)
        f.pack_propagate(False)
        etiqueta = 'MEDIO AMBIENTE' if p['id'] == 'ma' else 'SEGURIDAD Y SALUD'
        tk.Label(f, text=f'  {etiqueta}  ', bg=suave, fg=color,
                 font=(FUENTE, 8, 'bold')).pack(anchor='w', padx=20, pady=(18, 10))
        tk.Label(f, text=p['titulo'], bg='white', fg='#1a1d21', font=(FUENTE, 13, 'bold'),
                 wraplength=330, justify='left').pack(anchor='w', padx=20)
        tk.Label(f, text=p.get('descripcion', ''), bg='white', fg='#4a5058', font=(FUENTE, 9),
                 wraplength=330, justify='left').pack(anchor='w', padx=20, pady=(6, 0))
        datos = tk.Frame(f, bg='white')
        datos.pack(side='bottom', anchor='w', padx=20, pady=16)
        for i, (v, t) in enumerate([(p['periodo'], 'Periodo'), (p['n_secciones'], 'Secciones'),
                                    (f"v{p['version']}", 'Versión'), (p['codigo'], 'Código')]):
            tk.Label(datos, text=str(v), bg='white', font=(FUENTE, 10, 'bold')).grid(row=0, column=i, sticky='w', padx=(0, 16))
            tk.Label(datos, text=t, bg='white', fg='#767c85', font=(FUENTE, 8)).grid(row=1, column=i, sticky='w', padx=(0, 16))

        def abrir(_e=None, pid=p['id']):
            self.abrir_plan(pid)

        for w in [f] + list(f.winfo_children()) + list(datos.winfo_children()):
            w.bind('<Button-1>', abrir)
        f.bind('<Enter>', lambda e: f.configure(highlightbackground=color))
        f.bind('<Leave>', lambda e: f.configure(highlightbackground='#dde1e7'))
        return f

    # ===================================================================== PLAN
    def abrir_plan(self, id_plan):
        try:
            if id_plan not in self.planes:
                self.planes[id_plan] = Plan(id_plan)
        except ErrorDatos as e:
            messagebox.showerror('Error de datos', str(e))
            return
        self.plan = self.planes[id_plan]
        self.color = COLORES.get(id_plan, '#1f3864')
        self._estilos_ttk(self.color)
        self._limpiar()
        self._construir_plan()
        self.ver_seccion(0)

    def _construir_plan(self):
        # --- barra superior
        barra = tk.Frame(self.contenedor, bg='white', height=56)
        barra.pack(fill='x')
        tk.Frame(self.contenedor, bg='#dde1e7', height=1).pack(fill='x')

        tk.Button(barra, text='←  Inicio', bg='white', fg='#4a5058', bd=0, cursor='hand2',
                  activebackground='#f2f4f7', font=(FUENTE, 10),
                  command=self.mostrar_inicio).pack(side='left', padx=(14, 6), pady=12)

        self.botones_nav = {}
        for clave, texto in [('secciones', 'Secciones'), ('politica', 'Política'),
                             ('indicadores', 'Indicadores'), ('anexos', 'Anexos'),
                             ('calculadora', 'Calculadora')]:
            b = ttk.Button(barra, text=texto, style='Nav.TButton',
                           command=lambda c=clave: self._navegar(c))
            b.pack(side='left', padx=1)
            self.botones_nav[clave] = b

        self.var_buscar = tk.StringVar()
        caja = ttk.Entry(barra, textvariable=self.var_buscar, width=28)
        caja.pack(side='right', padx=16)
        caja.bind('<Return>', lambda e: self.ver_busqueda(self.var_buscar.get()))
        tk.Label(barra, text='Buscar', bg='white', fg='#767c85', font=(FUENTE, 9)).pack(side='right')

        # --- cuerpo: índice + contenido
        cuerpo = tk.PanedWindow(self.contenedor, orient='horizontal', bg='#dde1e7',
                                sashwidth=1, bd=0)
        cuerpo.pack(fill='both', expand=True)

        lateral = tk.Frame(cuerpo, bg='white')
        tk.Label(lateral, text=self.plan.titulo, bg='white', fg=self.color, font=(FUENTE, 11, 'bold'),
                 wraplength=330, justify='left').pack(anchor='w', padx=16, pady=(16, 2))
        tk.Label(lateral, text=self.plan.ficha, bg='white', fg='#767c85',
                 font=(FUENTE, 8)).pack(anchor='w', padx=16, pady=(0, 10))

        marco_lista = tk.Frame(lateral, bg='white')
        marco_lista.pack(fill='both', expand=True, padx=(8, 0), pady=(0, 10))
        self.lista = tk.Listbox(marco_lista, bd=0, highlightthickness=0, activestyle='none',
                                font=(FUENTE, 9), fg='#4a5058', selectbackground=SUAVES[self.plan.id],
                                selectforeground=self.color, bg='white')
        sb = ttk.Scrollbar(marco_lista, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=sb.set)
        self.lista.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        for s in self.plan.secciones:
            marca = '   (sin contenido)' if s.get('vacia') else ''
            self.lista.insert('end', f"  {s['numero']:>2}   {tipo_oracion(s['titulo'])}{marca}")
            if s.get('vacia'):
                self.lista.itemconfigure('end', fg='#a8adb5')
        self.lista.bind('<<ListboxSelect>>', self._al_elegir)

        self.area = tk.Frame(cuerpo, bg='white')
        cuerpo.add(lateral, minsize=280, width=370)
        cuerpo.add(self.area, minsize=500)

        # --- pie
        pie = tk.Frame(self.contenedor, bg='#f7f8fa', height=26)
        pie.pack(fill='x', side='bottom')
        tk.Label(pie, text=f'{self.plan.titulo}  ·  {self.plan.ficha}', bg='#f7f8fa',
                 fg='#767c85', font=(FUENTE, 8)).pack(side='left', padx=14, pady=4)

    def _marcar_nav(self, clave):
        for c, b in self.botones_nav.items():
            b.configure(style='NavActivo.TButton' if c == clave else 'Nav.TButton')

    def _navegar(self, clave):
        {'secciones': lambda: self.ver_seccion(self.indice_actual),
         'politica': self.ver_politica,
         'indicadores': self.ver_indicadores,
         'anexos': self.ver_anexos,
         'calculadora': self.ver_calculadora}[clave]()

    def _al_elegir(self, _e):
        sel = self.lista.curselection()
        if sel:
            self.ver_seccion(sel[0])

    def _limpiar_area(self):
        for sec in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self.unbind_all(sec)
        for w in self.area.winfo_children():
            w.destroy()

    def _texto_con_scroll(self):
        self._limpiar_area()
        marco = tk.Frame(self.area, bg='white')
        marco.pack(fill='both', expand=True)
        t = tk.Text(marco, wrap='word', bd=0, highlightthickness=0, padx=34, pady=24,
                    bg='white', fg='#1a1d21', cursor='arrow', spacing2=3)
        sb = ttk.Scrollbar(marco, orient='vertical', command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        t.pack(side='left', fill='both', expand=True)
        configurar_estilos(t, self.color)
        return t

    def _ancho_util(self):
        self.update_idletasks()
        return max(520, self.area.winfo_width() - 110)

    # ------------------------------------------------------------ vistas
    def ver_seccion(self, i):
        secs = self.plan.secciones
        if not secs:
            return
        i = max(0, min(i, len(secs) - 1))
        self.indice_actual = i
        self._marcar_nav('secciones')
        self.lista.selection_clear(0, 'end')
        self.lista.selection_set(i)
        self.lista.see(i)

        s = secs[i]
        t = self._texto_con_scroll()
        t.insert('end', f"{s['numero']}.  {s['titulo']}\n", ('h2',))
        pintar_html(t, self.plan.html_seccion(s), self.color, self._ancho_util())

        # navegación anterior / siguiente
        t.insert('end', '\n')
        nav = tk.Frame(t, bg='white')
        if i > 0:
            ttk.Button(nav, text=f'←  {secs[i-1]["numero"]}. {secs[i-1]["titulo"][:40]}',
                       style='Nav.TButton', command=lambda: self.ver_seccion(i - 1)).pack(side='left')
        if i < len(secs) - 1:
            ttk.Button(nav, text=f'{secs[i+1]["numero"]}. {secs[i+1]["titulo"][:40]}  →',
                       style='Nav.TButton', command=lambda: self.ver_seccion(i + 1)).pack(side='left', padx=20)
        t.window_create('end', window=nav)
        t.configure(state='disabled')

    def ver_politica(self):
        self._marcar_nav('politica')
        s = self.plan.seccion_politica()
        t = self._texto_con_scroll()
        if not s:
            t.insert('end', 'Política\n', ('h2',))
            t.insert('end', 'No se encontró el capítulo de política en este plan.', ('vacio',))
        else:
            t.insert('end', f"{s['numero']}.  {s['titulo']}\n", ('h2',))
            pintar_html(t, self.plan.html_seccion(s), self.color, self._ancho_util())
        t.configure(state='disabled')

    def ver_indicadores(self):
        self._marcar_nav('indicadores')
        self._limpiar_area()
        datos = self.plan.indicadores
        grupos = self.plan.grupos_indicadores()

        cab = ttk.Frame(self.area, padding=(28, 20, 28, 8))
        cab.pack(fill='x')
        ttk.Label(cab, text='Indicadores', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(cab, style='Nota.TLabel',
                  text=f'{len(datos)} indicadores agrupados en {len(grupos)} familias.').pack(anchor='w', pady=(2, 10))

        filtro = ttk.Frame(cab)
        filtro.pack(anchor='w')
        ttk.Label(filtro, text='Familia:').pack(side='left')
        cb = ttk.Combobox(filtro, state='readonly', width=48,
                          values=['Todas'] + grupos)
        cb.current(0)
        cb.pack(side='left', padx=8)

        marco = ttk.Frame(self.area, padding=(28, 4, 28, 20))
        marco.pack(fill='both', expand=True)
        cols = ('indicador', 'formula', 'frecuencia')
        tv = ttk.Treeview(marco, columns=cols, show='headings')
        for c, t, w in [('indicador', 'Indicador', 300), ('formula', 'Fórmula', 460), ('frecuencia', 'Frecuencia', 110)]:
            tv.heading(c, text=t, anchor='w')
            tv.column(c, width=w, anchor='w', stretch=(c == 'formula'))
        sb = ttk.Scrollbar(marco, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        tv.tag_configure('grupo', background=SUAVES[self.plan.id], font=(FUENTE, 9, 'bold'))
        tv.tag_configure('par', background='#f7f8fa')

        def partir(texto, n):
            palabras, lineas, actual = texto.split(), [], ''
            for p in palabras:
                if len(actual) + len(p) + 1 > n:
                    lineas.append(actual)
                    actual = p
                else:
                    actual = (actual + ' ' + p).strip()
            lineas.append(actual)
            return '\n'.join(lineas[:2]) + ('…' if len(lineas) > 2 else '')

        def llenar(*_):
            tv.delete(*tv.get_children())
            elegido = cb.get()
            for g in grupos:
                if elegido not in ('Todas', g):
                    continue
                tv.insert('', 'end', values=(g.upper(), '', ''), tags=('grupo',))
                for k, d in enumerate(x for x in datos if x['grupo'] == g):
                    tv.insert('', 'end', values=(partir(d['indicador'], 40), partir(d['formula'], 66), d['frecuencia']),
                              tags=('par',) if k % 2 else ())

        cb.bind('<<ComboboxSelected>>', llenar)
        llenar()

    def ver_anexos(self):
        self._marcar_nav('anexos')
        t = self._texto_con_scroll()
        t.insert('end', 'Anexos\n', ('h2',))
        t.insert('end', f'El plan contempla {len(self.plan.anexos)} anexos.\n\n', ('p',))
        for a in self.plan.anexos:
            t.insert('end', f"Anexo {a['numero']}.  ", ('h4',))
            t.insert('end', f"{a['titulo']}\n", ('p',))
        t.configure(state='disabled')

    def ver_calculadora(self):
        self._marcar_nav('calculadora')
        self._limpiar_area()
        lienzo = tk.Canvas(self.area, bg='white', highlightthickness=0)
        sb = ttk.Scrollbar(self.area, orient='vertical', command=lienzo.yview)
        lienzo.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        lienzo.pack(side='left', fill='both', expand=True)
        calc = Calculadora(lienzo, self.plan.id, self.color)
        ventana = lienzo.create_window((0, 0), window=calc, anchor='nw')
        calc.bind('<Configure>', lambda e: lienzo.configure(scrollregion=lienzo.bbox('all')))
        lienzo.bind('<Configure>', lambda e: lienzo.itemconfigure(ventana, width=e.width))

        def rueda(e):
            if lienzo.winfo_exists():
                paso = -1 if (getattr(e, 'delta', 0) > 0 or getattr(e, 'num', 0) == 4) else 1
                lienzo.yview_scroll(paso, 'units')
        for sec in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            lienzo.bind_all(sec, rueda)
        self.calculadora = calc

    def ver_busqueda(self, consulta):
        self._marcar_nav('')
        t = self._texto_con_scroll()
        consulta = consulta.strip()
        t.insert('end', f'Búsqueda: “{consulta}”\n', ('h2',))
        if len(consulta) < 3:
            t.insert('end', 'Escriba al menos tres caracteres.', ('vacio',))
            t.configure(state='disabled')
            return
        res = self.plan.buscar(consulta)
        t.insert('end', f'{len(res)} capítulo(s) contienen el término.\n\n', ('p',))
        for s, frag in res:
            idx = self.plan.secciones.index(s)
            etiqueta = f'ir_{idx}'
            t.tag_configure(etiqueta, foreground=self.color, underline=True, font=(FUENTE, 11, 'bold'))
            t.tag_bind(etiqueta, '<Button-1>', lambda e, k=idx: self.ver_seccion(k))
            t.tag_bind(etiqueta, '<Enter>', lambda e: t.configure(cursor='hand2'))
            t.tag_bind(etiqueta, '<Leave>', lambda e: t.configure(cursor='arrow'))
            t.insert('end', f"Capítulo {s['numero']}. {s['titulo']}\n", (etiqueta,))
            ini = t.index('end-1c')
            t.insert('end', frag + '\n\n', ('p',))
            # resaltar coincidencias
            pos = ini
            while True:
                pos = t.search(consulta, pos, stopindex='end', nocase=True)
                if not pos:
                    break
                fin = f'{pos}+{len(consulta)}c'
                t.tag_add('mark', pos, fin)
                pos = fin
        t.configure(state='disabled')
