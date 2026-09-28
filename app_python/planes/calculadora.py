"""
Herramienta computacional de procesamiento de indicadores.

Implementa las fórmulas del capítulo 14 del Plan Anual de SST (índices de
frecuencia, severidad y accidentabilidad con constante de 1 000 000 de
horas-hombre) y el semáforo de desempeño del numeral 14.8.1 (verde >= 90 %,
ámbar 70-89 %, rojo < 70 %). Para el plan ambiental aplica el mismo semáforo
del numeral 9.4.
"""

import tkinter as tk
from tkinter import ttk

CONSTANTE = 1_000_000

VERDE, AMBAR, ROJO = '#2f7a56', '#b7791f', '#c0392b'


# ---------------------------------------------------------------------------
# cálculo (funciones puras, fáciles de probar)
# ---------------------------------------------------------------------------

def indice_frecuencia(accidentes_incapacitantes, hht):
    return accidentes_incapacitantes * CONSTANTE / hht


def indice_severidad(dias_perdidos, hht):
    return dias_perdidos * CONSTANTE / hht


def indice_accidentabilidad(i_f, i_s):
    return i_f * i_s / 1000


def porcentaje(ejecutado, programado):
    return ejecutado / programado * 100


def semaforo(valor, meta_total=False):
    """Devuelve (nivel, color). meta_total=True: indicadores que exigen 100 %."""
    if meta_total:
        return ('Verde', VERDE) if valor >= 100 else ('Rojo', ROJO)
    if valor >= 90:
        return 'Verde', VERDE
    if valor >= 70:
        return 'Ámbar', AMBAR
    return 'Rojo', ROJO


def _numero(texto):
    t = texto.strip().replace(' ', '').replace(',', '.')
    if not t:
        raise ValueError('vacío')
    v = float(t)
    if v < 0:
        raise ValueError('negativo')
    return v


# ---------------------------------------------------------------------------
# interfaz
# ---------------------------------------------------------------------------

class Calculadora(ttk.Frame):
    def __init__(self, padre, plan_id, color):
        super().__init__(padre, padding=(28, 22))
        self.color = color
        self.plan_id = plan_id

        ttk.Label(self, text='Calculadora de indicadores', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(
            self, style='Nota.TLabel', wraplength=720, justify='left',
            text=('Ingrese los datos del periodo y presione Calcular. '
                  'Los índices estadísticos usan la constante de 1 000 000 de horas-hombre '
                  'trabajadas; los porcentajes se evalúan con el semáforo del plan '
                  '(verde ≥ 90 %, ámbar 70–89 %, rojo < 70 %).'),
        ).pack(anchor='w', pady=(4, 16))

        if plan_id == 'sst':
            self._bloque_indices()
        self._bloque_porcentajes()

    # --- índices de resultado (solo SST) ---------------------------------
    def _bloque_indices(self):
        caja = ttk.LabelFrame(self, text='  Índices de resultado  ', padding=14)
        caja.pack(fill='x', pady=(0, 16))

        self.e_hht = self._campo(caja, 0, 'Horas-hombre trabajadas del periodo')
        self.e_acc = self._campo(caja, 1, 'N.° de accidentes incapacitantes')
        self.e_dias = self._campo(caja, 2, 'N.° de días perdidos por accidente')

        ttk.Button(caja, text='Calcular', style='Acento.TButton',
                   command=self._calc_indices).grid(row=3, column=0, sticky='w', pady=(10, 6))

        self.res_indices = tk.Frame(caja, bg='white')
        self.res_indices.grid(row=4, column=0, columnspan=2, sticky='we', pady=(6, 0))

    def _calc_indices(self):
        for w in self.res_indices.winfo_children():
            w.destroy()
        try:
            hht = _numero(self.e_hht.get())
            acc = _numero(self.e_acc.get())
            dias = _numero(self.e_dias.get())
            if hht == 0:
                raise ZeroDivisionError
        except ZeroDivisionError:
            self._error(self.res_indices, 'Las horas-hombre trabajadas deben ser mayores que cero.')
            return
        except ValueError:
            self._error(self.res_indices, 'Complete los tres campos con números no negativos.')
            return

        i_f = indice_frecuencia(acc, hht)
        i_s = indice_severidad(dias, hht)
        i_a = indice_accidentabilidad(i_f, i_s)
        for col, (nombre, valor, formula) in enumerate([
            ('Índice de frecuencia (IF)', i_f, 'Acc. incap. × 1 000 000 ÷ HHT'),
            ('Índice de severidad (IS)', i_s, 'Días perdidos × 1 000 000 ÷ HHT'),
            ('Índice de accidentabilidad (IA)', i_a, 'IF × IS ÷ 1 000'),
        ]):
            self._tarjeta(self.res_indices, col, nombre, f'{valor:,.2f}'.replace(',', ' '), formula)

    # --- porcentajes de cumplimiento --------------------------------------
    def _bloque_porcentajes(self):
        caja = ttk.LabelFrame(self, text='  Indicadores de cumplimiento  ', padding=14)
        caja.pack(fill='x')

        if self.plan_id == 'sst':
            opciones = [
                ('Cumplimiento del Programa Anual de SST', False),
                ('Cumplimiento del Programa de Inspecciones', False),
                ('Cumplimiento del Programa Anual de Capacitación', False),
                ('Cobertura de capacitación', False),
                ('Cobertura de exámenes médicos ocupacionales', False),
                ('Cumplimiento del programa de simulacros', False),
                ('Cierre de acciones correctivas', False),
                ('Cobertura de inducción al ingreso (exige 100 %)', True),
                ('Cobertura de inducción a contratistas (exige 100 %)', True),
            ]
        else:
            opciones = [
                ('Cumplimiento del Programa Anual de Manejo Ambiental', False),
                ('Cumplimiento del programa de inspecciones ambientales', False),
                ('Levantamiento de hallazgos ambientales', False),
                ('Tasa de valorización de residuos', False),
                ('Cobertura de capacitación ambiental', False),
                ('Cumplimiento legal ambiental', False),
                ('Disposición de peligrosos vía EO-RS con manifiesto (exige 100 %)', True),
            ]
        self.opciones = dict(opciones)

        ttk.Label(caja, text='Indicador').grid(row=0, column=0, sticky='w', pady=4)
        self.cb = ttk.Combobox(caja, values=[o[0] for o in opciones], state='readonly', width=58)
        self.cb.current(0)
        self.cb.grid(row=0, column=1, sticky='w', pady=4, padx=(12, 0))

        self.e_ejec = self._campo(caja, 1, 'Valor ejecutado / logrado')
        self.e_prog = self._campo(caja, 2, 'Valor programado / total')

        ttk.Button(caja, text='Calcular', style='Acento.TButton',
                   command=self._calc_pct).grid(row=3, column=0, sticky='w', pady=(10, 6))

        self.res_pct = tk.Frame(caja, bg='white')
        self.res_pct.grid(row=4, column=0, columnspan=2, sticky='we', pady=(6, 0))

    def _calc_pct(self):
        for w in self.res_pct.winfo_children():
            w.destroy()
        try:
            ejec = _numero(self.e_ejec.get())
            prog = _numero(self.e_prog.get())
            if prog == 0:
                raise ZeroDivisionError
        except ZeroDivisionError:
            self._error(self.res_pct, 'El valor programado debe ser mayor que cero.')
            return
        except ValueError:
            self._error(self.res_pct, 'Complete ambos campos con números no negativos.')
            return

        nombre = self.cb.get()
        valor = porcentaje(ejec, prog)
        nivel, color = semaforo(valor, self.opciones.get(nombre, False))
        self._tarjeta(self.res_pct, 0, nombre, f'{valor:.1f} %',
                      f'({ejec:g} ÷ {prog:g}) × 100', nivel=nivel, color_nivel=color, ancho=3)

    # --- utilidades de interfaz ----------------------------------------------
    def _campo(self, padre, fila, etiqueta):
        ttk.Label(padre, text=etiqueta).grid(row=fila, column=0, sticky='w', pady=4)
        e = ttk.Entry(padre, width=22)
        e.grid(row=fila, column=1, sticky='w', pady=4, padx=(12, 0))
        return e

    def _tarjeta(self, padre, col, nombre, valor, formula, nivel=None, color_nivel=None, ancho=1):
        f = tk.Frame(padre, bg='#f7f8fa', highlightbackground='#dde1e7', highlightthickness=1)
        f.grid(row=0, column=col, columnspan=ancho, sticky='nsew', padx=(0, 10))
        padre.grid_columnconfigure(col, weight=1)
        tk.Label(f, text=nombre, bg='#f7f8fa', fg='#4a5058', font=('Segoe UI', 9),
                 wraplength=260, justify='left').pack(anchor='w', padx=12, pady=(10, 0))
        tk.Label(f, text=valor, bg='#f7f8fa', fg=self.color,
                 font=('Segoe UI', 20, 'bold')).pack(anchor='w', padx=12)
        tk.Label(f, text=formula, bg='#f7f8fa', fg='#767c85',
                 font=('Consolas', 9)).pack(anchor='w', padx=12, pady=(0, 8 if not nivel else 2))
        if nivel:
            tk.Label(f, text=f'  {nivel}  ', bg=color_nivel, fg='white',
                     font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(2, 10))

    def _error(self, padre, msg):
        tk.Label(padre, text=msg, bg='white', fg=ROJO, font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w')
