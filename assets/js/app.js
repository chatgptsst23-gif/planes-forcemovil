/* ==========================================================================
   Planes de gestión — FORCEMOVIL S.A.C.
   Aplicación de consulta. Sin dependencias externas.

   Cómo funciona
   -------------
   1. Lee datos/manifiesto.json  -> qué planes existen.
   2. Lee datos/<plan>/indice.json -> qué secciones tiene cada plan.
   3. Carga cada sección bajo demanda desde datos/<plan>/secciones/*.html

   Para actualizar un punto del plan basta con editar su archivo HTML en
   datos/<plan>/secciones/. No hay que tocar este archivo.

   Rutas (hash):
     #/                      portada
     #/sst                   plan de SST, primera sección
     #/sst/5                 capítulo 5 del plan de SST
     #/sst/indicadores       vista de indicadores
     #/sst/politica          vista de política
     #/sst/anexos            vista de anexos
     #/sst/buscar/<texto>    resultados de búsqueda
   ========================================================================== */

'use strict';

const App = {
  manifiesto: null,
  indices: {},        // indice.json por plan
  cacheSecciones: {}, // html por "plan/archivo"
  indicadores: {},
  anexos: {},
  planActual: null,
  seccionActual: null,
};

const $ = (sel) => document.querySelector(sel);
const el = {
  lateral: $('#lateral'),
  indiceNav: $('#indiceNav'),
  lateralTitulo: $('#lateralTitulo'),
  lateralMeta: $('#lateralMeta'),
  navPlan: $('#navPlan'),
  buscador: $('#buscador'),
  inputBuscar: $('#inputBuscar'),
  vistaInicio: $('#vistaInicio'),
  vistaPlan: $('#vistaPlan'),
  contenido: $('#contenido'),
  migas: $('#migas'),
  paginacion: $('#paginacion'),
  tarjetas: $('#tarjetasPlanes'),
  fichaEmpresa: $('#fichaEmpresa'),
  marcaRazon: $('#marcaRazon'),
  portadaEmpresa: $('#portadaEmpresa'),
  piePlan: $('#piePlan'),
  btnMenu: $('#btnMenu'),
  principal: $('#principal'),
  avisoCarga: $('#avisoCarga'),
  avisoDetalle: $('#avisoDetalle'),
};

/* --------------------------------------------------------------------------
   utilidades
   -------------------------------------------------------------------------- */

async function traerJSON(ruta) {
  const r = await fetch(ruta, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${ruta} → HTTP ${r.status}`);
  return r.json();
}

async function traerTexto(ruta) {
  const r = await fetch(ruta, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${ruta} → HTTP ${r.status}`);
  return r.text();
}

function normalizar(t) {
  return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

function escaparHTML(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

/* --------------------------------------------------------------------------
   carga de datos
   -------------------------------------------------------------------------- */

async function cargarPlan(idPlan) {
  if (App.indices[idPlan]) return App.indices[idPlan];
  const [indice, indicadores, anexos] = await Promise.all([
    traerJSON(`datos/${idPlan}/indice.json`),
    traerJSON(`datos/${idPlan}/indicadores.json`).catch(() => []),
    traerJSON(`datos/${idPlan}/anexos.json`).catch(() => []),
  ]);
  App.indices[idPlan] = indice;
  App.indicadores[idPlan] = indicadores;
  App.anexos[idPlan] = anexos;
  return indice;
}

async function cargarSeccion(idPlan, archivo) {
  const clave = `${idPlan}/${archivo}`;
  if (App.cacheSecciones[clave] !== undefined) return App.cacheSecciones[clave];
  const html = await traerTexto(`datos/${idPlan}/${archivo}`);
  App.cacheSecciones[clave] = html;
  return html;
}

/** Carga todas las secciones de un plan. Se usa solo al buscar. */
async function cargarTodasLasSecciones(idPlan) {
  const indice = await cargarPlan(idPlan);
  await Promise.all(indice.secciones.map((s) => cargarSeccion(idPlan, s.archivo)));
  return indice;
}

/* --------------------------------------------------------------------------
   portada
   -------------------------------------------------------------------------- */

function pintarPortada() {
  const m = App.manifiesto;
  const org = m.organizacion || {};

  if (org.razon_social) {
    el.marcaRazon.textContent = org.razon_social;
    el.portadaEmpresa.textContent = org.razon_social;
    document.title = `Planes de Gestión — ${org.razon_social}`;
  }

  el.tarjetas.innerHTML = m.planes.map((p) => {
    const esMA = p.color === 'ma';
    const vars = esMA
      ? '--tc:#1e5b3f;--tb:#e6f2ec'
      : '--tc:#1f3864;--tb:#eaeff7';
    return `
      <a class="tarjeta" href="#/${p.id}" style="${vars}">
        <span class="etiqueta">${esMA ? 'Medio ambiente' : 'Seguridad y salud'}</span>
        <h2>${escaparHTML(p.titulo)}</h2>
        <p>${escaparHTML(p.descripcion)}</p>
        <div class="datos">
          <div><b>${p.periodo}</b>Periodo</div>
          <div><b>${p.n_secciones}</b>Secciones</div>
          <div><b>v${p.version}</b>Versión</div>
          <div><b>${escaparHTML(p.codigo)}</b>Código</div>
        </div>
      </a>`;
  }).join('');

  const sedes = org.sedes || [];
  if (sedes.length) {
    el.fichaEmpresa.innerHTML = `
      <h3>Alcance de los planes</h3>
      <table class="ficha-tabla">
        <tbody>
          ${sedes.map((s) => `
            <tr>
              <th>${escaparHTML(s.nombre)}${s.principal ? ' (principal)' : ''}</th>
              <td>${escaparHTML(s.direccion || '')}${
                s.trabajadores ? ` · <span class="ficha-total">${s.trabajadores}</span> trabajadores` : ''
              }</td>
            </tr>`).join('')}
          ${org.total_trabajadores ? `
            <tr>
              <th>Total</th>
              <td><span class="ficha-total">${org.total_trabajadores}</span> trabajadores</td>
            </tr>` : ''}
        </tbody>
      </table>`;
  } else {
    el.fichaEmpresa.innerHTML = '';
  }
}

/* --------------------------------------------------------------------------
   índice lateral
   -------------------------------------------------------------------------- */

function pintarIndice(indice, numeroActivo, vista) {
  el.lateralTitulo.textContent = indice.titulo;
  el.lateralMeta.textContent = `${indice.codigo} · v${indice.version} · Periodo ${indice.periodo}`;

  el.indiceNav.innerHTML = indice.secciones.map((s) => {
    const activo = vista === 'secciones' && String(s.numero) === String(numeroActivo);
    return `
      <a href="#/${indice.id}/${s.numero}"
         class="${activo ? 'activo' : ''} ${s.vacia ? 'vacia' : ''}">
        <span class="num">${s.numero}</span>
        <span class="txt">${escaparHTML(s.titulo)}</span>
      </a>`;
  }).join('');
}

function marcarNav(vista) {
  el.navPlan.querySelectorAll('a').forEach((a) => {
    a.classList.toggle('activo', a.dataset.vista === vista);
  });
}

/* --------------------------------------------------------------------------
   vistas
   -------------------------------------------------------------------------- */

function modoPortada() {
  App.planActual = null;
  document.body.removeAttribute('data-plan');
  el.vistaInicio.hidden = false;
  el.vistaPlan.hidden = true;
  el.lateral.hidden = true;
  el.navPlan.hidden = true;
  el.buscador.hidden = true;
  el.piePlan.textContent = '';
  el.lateral.classList.remove('abierto');
  pintarPortada();
  window.scrollTo(0, 0);
}

function modoPlan(indice) {
  App.planActual = indice.id;
  document.body.dataset.plan = indice.id;
  el.vistaInicio.hidden = true;
  el.vistaPlan.hidden = false;
  el.lateral.hidden = false;
  el.navPlan.hidden = false;
  el.buscador.hidden = false;
  el.piePlan.textContent =
    `${indice.titulo} · ${indice.codigo} · Versión ${indice.version} · Periodo ${indice.periodo}`;
}

async function verSeccion(idPlan, numero) {
  const indice = await cargarPlan(idPlan);
  modoPlan(indice);

  const i = indice.secciones.findIndex((s) => String(s.numero) === String(numero));
  const idx = i >= 0 ? i : 0;
  const sec = indice.secciones[idx];
  App.seccionActual = sec.numero;

  pintarIndice(indice, sec.numero, 'secciones');
  marcarNav('secciones');

  const html = await cargarSeccion(idPlan, sec.archivo);

  el.migas.innerHTML =
    `<b>${escaparHTML(indice.titulo_corto)}</b> <span>›</span> <span>Capítulo ${sec.numero}</span>`;

  el.contenido.innerHTML = `
    <h2><span class="numcap">${sec.numero}.</span>${escaparHTML(sec.titulo)}</h2>
    ${html.trim() ? html : '<div class="sin-contenido">Este numeral no tiene contenido registrado.</div>'}
  `;

  const ant = indice.secciones[idx - 1];
  const sig = indice.secciones[idx + 1];
  el.paginacion.innerHTML = `
    ${ant ? `<a href="#/${idPlan}/${ant.numero}"><small>← Anterior</small><span>${ant.numero}. ${escaparHTML(ant.titulo)}</span></a>` : '<span></span>'}
    ${sig ? `<a class="sig" href="#/${idPlan}/${sig.numero}"><small>Siguiente →</small><span>${sig.numero}. ${escaparHTML(sig.titulo)}</span></a>` : ''}
  `;

  el.lateral.classList.remove('abierto');
  window.scrollTo(0, 0);
  el.principal.focus({ preventScroll: true });
}

async function verIndicadores(idPlan) {
  const indice = await cargarPlan(idPlan);
  modoPlan(indice);
  pintarIndice(indice, null, 'indicadores');
  marcarNav('indicadores');

  const datos = App.indicadores[idPlan] || [];
  const grupos = [...new Set(datos.map((d) => d.grupo))];

  el.migas.innerHTML = `<b>${escaparHTML(indice.titulo_corto)}</b> <span>›</span> <span>Indicadores</span>`;
  el.paginacion.innerHTML = '';

  el.contenido.innerHTML = `
    <h2>Indicadores</h2>
    <p>El plan define <strong>${datos.length} indicadores</strong>, agrupados en ${grupos.length} familias.
       Cada uno cuenta con su fórmula de cálculo y su frecuencia de medición.</p>
    <div class="filtros" id="filtrosInd">
      <button class="filtro activo" data-g="__todos">Todos (${datos.length})</button>
      ${grupos.map((g) => `<button class="filtro" data-g="${escaparHTML(g)}">${escaparHTML(g)} (${datos.filter((d) => d.grupo === g).length})</button>`).join('')}
    </div>
    <div id="listaInd"></div>
  `;

  const pintar = (filtro) => {
    const visibles = filtro === '__todos' ? datos : datos.filter((d) => d.grupo === filtro);
    const porGrupo = {};
    visibles.forEach((d) => { (porGrupo[d.grupo] ||= []).push(d); });
    $('#listaInd').innerHTML = Object.entries(porGrupo).map(([g, items]) => `
      <div class="grupo-ind">
        <h3>${escaparHTML(g)}</h3>
        <div class="tabla-ind">
          <table class="tabla-datos">
            <thead><tr><th style="width:32%">Indicador</th><th>Fórmula</th><th style="width:15%">Frecuencia</th></tr></thead>
            <tbody>
              ${items.map((d) => `
                <tr>
                  <td><strong>${escaparHTML(d.indicador)}</strong></td>
                  <td class="celda-formula">${escaparHTML(d.formula)}</td>
                  <td><span class="chip-frec">${escaparHTML(d.frecuencia)}</span></td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>`).join('');
  };

  pintar('__todos');
  $('#filtrosInd').addEventListener('click', (e) => {
    const b = e.target.closest('.filtro');
    if (!b) return;
    $('#filtrosInd').querySelectorAll('.filtro').forEach((x) => x.classList.remove('activo'));
    b.classList.add('activo');
    pintar(b.dataset.g);
  });

  el.lateral.classList.remove('abierto');
  window.scrollTo(0, 0);
}

async function verPolitica(idPlan) {
  const indice = await cargarPlan(idPlan);
  modoPlan(indice);
  pintarIndice(indice, null, 'politica');
  marcarNav('politica');

  const sec = indice.secciones.find((s) => /pol[ií]tica/i.test(s.titulo));
  el.migas.innerHTML = `<b>${escaparHTML(indice.titulo_corto)}</b> <span>›</span> <span>Política</span>`;
  el.paginacion.innerHTML = '';

  if (!sec) {
    el.contenido.innerHTML = '<h2>Política</h2><div class="sin-contenido">No se encontró el capítulo de política en este plan.</div>';
    return;
  }

  const html = await cargarSeccion(idPlan, sec.archivo);
  el.contenido.innerHTML = `
    <h2><span class="numcap">${sec.numero}.</span>${escaparHTML(sec.titulo)}</h2>
    ${html}`;

  el.lateral.classList.remove('abierto');
  window.scrollTo(0, 0);
}

async function verAnexos(idPlan) {
  const indice = await cargarPlan(idPlan);
  modoPlan(indice);
  pintarIndice(indice, null, 'anexos');
  marcarNav('anexos');

  const datos = App.anexos[idPlan] || [];
  el.migas.innerHTML = `<b>${escaparHTML(indice.titulo_corto)}</b> <span>›</span> <span>Anexos</span>`;
  el.paginacion.innerHTML = '';

  el.contenido.innerHTML = `
    <h2>Anexos</h2>
    <p>El plan contempla <strong>${datos.length} anexos</strong>.</p>
    <div class="lista-anexos">
      ${datos.map((a) => `
        <div class="anexo">
          <div class="anexo-num">${a.numero}</div>
          <div class="anexo-txt">${escaparHTML(a.titulo)}</div>
        </div>`).join('')}
    </div>`;

  el.lateral.classList.remove('abierto');
  window.scrollTo(0, 0);
}

async function verBusqueda(idPlan, consulta) {
  const indice = await cargarTodasLasSecciones(idPlan);
  modoPlan(indice);
  pintarIndice(indice, null, 'buscar');
  marcarNav('');

  const q = normalizar(consulta.trim());
  el.migas.innerHTML = `<b>${escaparHTML(indice.titulo_corto)}</b> <span>›</span> <span>Búsqueda</span>`;
  el.paginacion.innerHTML = '';

  if (q.length < 3) {
    el.contenido.innerHTML = '<h2>Búsqueda</h2><div class="sin-contenido">Escriba al menos tres caracteres.</div>';
    return;
  }

  const hallazgos = [];
  for (const s of indice.secciones) {
    const html = App.cacheSecciones[`${idPlan}/${s.archivo}`] || '';
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    const texto = (s.titulo + ' ' + (tmp.textContent || '')).replace(/\s+/g, ' ');
    const pos = normalizar(texto).indexOf(q);
    if (pos === -1) continue;

    const ini = Math.max(0, pos - 90);
    const bruto = texto.slice(ini, pos + consulta.length + 130);
    const frag = (ini > 0 ? '…' : '') + escaparHTML(bruto) + '…';
    const re = new RegExp(`(${consulta.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');

    hallazgos.push({ sec: s, frag: frag.replace(re, '<mark>$1</mark>') });
  }

  el.contenido.innerHTML = `
    <h2>Búsqueda: “${escaparHTML(consulta)}”</h2>
    <p>${hallazgos.length} ${hallazgos.length === 1 ? 'capítulo contiene' : 'capítulos contienen'} el término.</p>
    <div class="resultados-busqueda">
      ${hallazgos.length ? hallazgos.map((h) => `
        <a class="resultado" href="#/${idPlan}/${h.sec.numero}">
          <div class="r-cap">Capítulo ${h.sec.numero}</div>
          <div class="r-tit">${escaparHTML(h.sec.titulo)}</div>
          <div class="r-frag">${h.frag}</div>
        </a>`).join('')
        : '<div class="sin-contenido">Sin resultados.</div>'}
    </div>`;

  el.lateral.classList.remove('abierto');
  window.scrollTo(0, 0);
}

/* --------------------------------------------------------------------------
   enrutador
   -------------------------------------------------------------------------- */

async function enrutar() {
  const ruta = (location.hash || '#/').replace(/^#\/?/, '');
  const partes = ruta.split('/').filter(Boolean).map(decodeURIComponent);

  try {
    if (!partes.length) return modoPortada();

    const idPlan = partes[0];
    if (!App.manifiesto.planes.some((p) => p.id === idPlan)) return modoPortada();

    if (partes.length === 1) {
      const indice = await cargarPlan(idPlan);
      return verSeccion(idPlan, indice.secciones[0].numero);
    }

    switch (partes[1]) {
      case 'indicadores': return verIndicadores(idPlan);
      case 'politica':    return verPolitica(idPlan);
      case 'anexos':      return verAnexos(idPlan);
      case 'buscar':      return verBusqueda(idPlan, partes.slice(2).join('/'));
      default:            return verSeccion(idPlan, partes[1]);
    }
  } catch (err) {
    mostrarAvisoCarga(err);
  }
}

function mostrarAvisoCarga(err) {
  el.avisoDetalle.textContent = String(err && err.message ? err.message : err);
  el.avisoCarga.hidden = false;
  console.error('[planes] no se pudieron cargar los datos:', err);
}

/* --------------------------------------------------------------------------
   eventos
   -------------------------------------------------------------------------- */

el.navPlan.addEventListener('click', (e) => {
  const a = e.target.closest('a[data-vista]');
  if (!a || !App.planActual) return;
  e.preventDefault();
  const v = a.dataset.vista;
  location.hash = v === 'secciones'
    ? `#/${App.planActual}/${App.seccionActual || 1}`
    : `#/${App.planActual}/${v}`;
});

el.inputBuscar.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter' || !App.planActual) return;
  const q = e.target.value.trim();
  if (q) location.hash = `#/${App.planActual}/buscar/${encodeURIComponent(q)}`;
});

el.btnMenu.addEventListener('click', () => {
  const abierto = el.lateral.classList.toggle('abierto');
  el.btnMenu.setAttribute('aria-expanded', String(abierto));
});

window.addEventListener('hashchange', enrutar);

/* --------------------------------------------------------------------------
   arranque
   -------------------------------------------------------------------------- */

(async function iniciar() {
  try {
    App.manifiesto = await traerJSON('datos/manifiesto.json');
    await enrutar();
  } catch (err) {
    mostrarAvisoCarga(err);
  }
})();
