/* === Marca: mostrar campo “otra marca” cuando eligen OTROS === */
function onMarcaChange() {
  const sel = document.getElementById("marca_select");
  const otherWrap = document.getElementById("otra_marca_wrap");
  if (!sel || !otherWrap) return;
  const v = (sel.value || "").toLowerCase();
  otherWrap.style.display = (v === "otros" ? "block" : "none");
}

/* ============= Firmas en alta densidad + compresión ============= */
/* Guarda PNG por defecto; si quieres ahorrar espacio en localStorage,
   cambia USE_JPEG_FOR_DRAFT a true para guardar JPEG de ~85% calidad */
const USE_JPEG_FOR_DRAFT = true;

function enableSignaturePadHDPI(canvasId, clearBtnId, hiddenInputId) {
  const canvas = document.getElementById(canvasId);
  const clearBtn = document.getElementById(clearBtnId);
  const hidden = document.getElementById(hiddenInputId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function paintWhiteBG() {
    const rect = canvas.getBoundingClientRect();
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, rect.width, rect.height);
  }
  function resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    paintWhiteBG();
  }
  resize(); window.addEventListener("resize", resize);

  let drawing = false;
  function pos(e) {
    const r = canvas.getBoundingClientRect(); const t = e.touches ? e.touches[0] : e;
    return { x: t.clientX - r.left, y: t.clientY - r.top };
  }
  function start(e) { drawing = true; const p = pos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); e.preventDefault(); }
  function move(e) { if (!drawing) return; const p = pos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); e.preventDefault(); }
  function end(e) {
    drawing = false; e.preventDefault();
    if (!hidden) return;
    // Para el *submit* al servidor guardamos PNG (fondo blanco)
    hidden.value = canvas.toDataURL("image/png");
  }

  canvas.addEventListener("mousedown", start);
  canvas.addEventListener("mousemove", move);
  canvas.addEventListener("mouseup", end);
  canvas.addEventListener("mouseleave", end);
  canvas.addEventListener("touchstart", start, { passive: false });
  canvas.addEventListener("touchmove", move, { passive: false });
  canvas.addEventListener("touchend", end, { passive: false });
  canvas.style.touchAction = "none";

  clearBtn?.addEventListener("click", () => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    resize();
    if (hidden) hidden.value = "";
  });
}

/* === Descripción según tipo de servicio (incluye Bitácora) === */
function updateDescripcionOptions() {
  const tipo = document.getElementById('tipo_servicio');
  const desc = document.getElementById('descripcion_servicio');
  if (!tipo || !desc) return;
  const t = (tipo.value || "").toLowerCase();

  const preventivo = ["2000 HORAS", "4000 HORAS", "6000 HORAS", "8000 HORAS", "16000 HORAS"];
  const otros = ["Correctivo", "Revisión", "Diagnóstico"];
  const bitacora = ["Bitácora"];

  let lista = preventivo;
  if (t === "bitácora" || t === "bitacora") lista = bitacora;
  else if (t !== "preventivo") lista = otros;

  desc.innerHTML = "";
  lista.forEach(v => {
    const opt = document.createElement("option");
    opt.textContent = v; opt.value = v;
    desc.appendChild(opt);
  });
}

/* === Helper: saber si el equipo seleccionado es un secador === */
function getTipoEquipoValor() {
  const sel = document.getElementById("tipo_equipo_select");
  const inp = document.getElementById("tipo_equipo_input");

  // Si el input está visible, usamos su valor (modo manual)
  if (inp && inp.style.display !== "none") {
    return (inp.value || "").toLowerCase();
  }
  // Si no, usamos el select
  return (sel ? sel.value : "").toLowerCase();
}

function esSecadorSeleccionado() {
  const txt = getTipoEquipoValor();
  return txt.includes("secador");
}

/* === Cambiar el texto de ayuda de Potencia (HP / CFM) === */
function updatePotenciaHint() {
  const span = document.getElementById("potencia_unidad_hint");
  if (!span) return;
  span.textContent = esSecadorSeleccionado() ? "“CFM”" : "“HP”";
}

/* === Mostrar/ocultar bloques de actividades por tipo (incluye Bitácora + Secador) === */
function toggleBloquesPorTipo() {
  const t = document.getElementById('tipo_servicio')?.value?.toLowerCase() || "preventivo";
  const prev = document.getElementById('bloque_preventivo');
  const prevSec = document.getElementById('bloque_preventivo_secador');
  const corr = document.getElementById('bloque_correctivo');
  if (!prev || !corr) return;

  const esBitacora = (t === "bitácora" || t === "bitacora");
  const esSecador = esSecadorSeleccionado();
  const esPreventivo = (t === "preventivo");

  // Bitácora: siempre ocultar actividades, aunque sea secador
  if (esBitacora) {
    prev.style.display = "none";
    if (prevSec) prevSec.style.display = "none";
    corr.style.display = "none";
  } else if (esPreventivo) {
    if (esSecador && prevSec) {
      prev.style.display = "none";
      prevSec.style.display = "";
    } else {
      prev.style.display = "";
      if (prevSec) prevSec.style.display = "none";
    }
    corr.style.display = "none";
  } else {
    prev.style.display = "none";
    if (prevSec) prevSec.style.display = "none";
    corr.style.display = "";
  }
}

/* === Mostrar/ocultar lecturas para secador vs compresor === */
function toggleLecturasSecador() {
  const cardComp = document.getElementById("card_lecturas_compresor");
  const cardSec = document.getElementById("card_lecturas_secador");
  const cardAltaPresion = document.getElementById("card_lecturas_alta_presion");
  if (!cardComp || !cardSec) return;

  const t = document.getElementById('tipo_servicio')?.value?.toLowerCase() || "preventivo";
  const esSecador = esSecadorSeleccionado();
  const esBitacora = (t === "bitácora" || t === "bitacora");
  const esPreventivo = (t === "preventivo");
  const txt = getTipoEquipoValor();
  const esAltaPresion = txt.toLowerCase().includes("alta presión") || txt.toLowerCase().includes("alta presion");

  // Buscar la sección completa de "Lecturas del equipo" para ocultarla cuando sea Alta Presión
  const seccionLecturas = cardComp?.closest('.mb-4');

  // Si es Alta Presión + (Preventivo o Bitácora), ocultar sección normal y mostrar lecturas de alta presión
  if (esAltaPresion && (esPreventivo || esBitacora)) {
    if (seccionLecturas) seccionLecturas.style.display = "none";
    if (cardAltaPresion) cardAltaPresion.style.display = "";
  } else {
    // Mostrar sección normal de lecturas
    if (seccionLecturas) seccionLecturas.style.display = "";
    if (cardAltaPresion) cardAltaPresion.style.display = "none";

    if (esSecador && (esPreventivo || esBitacora)) {
      // Si es Preventivo + Secador O Bitácora + Secador, mostrar lecturas de secador
      cardComp.style.display = "none";
      cardSec.style.display = "";
    } else {
      cardComp.style.display = "";
      cardSec.style.display = "none";
    }
  }
}

/* === Limitar fotos según tipo (Bitácora = 2; resto = 4) === */
function ajustarFotosPorTipo() {
  const t = document.getElementById('tipo_servicio')?.value?.toLowerCase() || "preventivo";
  const esBitacora = (t === "bitácora" || t === "bitacora");
  const hint = document.getElementById("fotos_hint");
  const items = document.querySelectorAll("#fotos_grid .foto-item");
  if (hint) hint.textContent = esBitacora ? "(máx. 2)" : "(máx. 4)";

  items.forEach(it => {
    const idx = Number(it.dataset.index || "0");
    const show = esBitacora ? (idx <= 2) : (idx <= 4);
    it.style.display = show ? "" : "none";
    if (!show) {
      // limpiar inputs ocultos
      it.querySelectorAll("input").forEach(inp => { inp.value = ""; });
    }
  });

  // En Bitácora, fuerza la descripción a "Bitácora"
  if (esBitacora) {
    const desc = document.getElementById('descripcion_servicio');
    if (desc) {
      desc.innerHTML = "";
      const opt = document.createElement("option");
      opt.value = "Bitácora"; opt.textContent = "Bitácora";
      desc.appendChild(opt);
    }
  }
}

/* === R30 / SPM === */
function toggleAnalisisRuido() {
  const chk = document.getElementById('chk_ruido');
  const opts = document.getElementById('ruido_opts');
  const tipoSel = document.getElementById('ruido_tipo');
  const spm = document.getElementById('spm_grid');
  const r30 = document.getElementById('ruido_r30');
  if (!chk || !opts) return;

  if (chk.checked) {
    opts.style.display = "";
    if (tipoSel?.value === "SPM") { if (spm) spm.style.display = "block"; if (r30) r30.style.display = "none"; }
    else { if (spm) spm.style.display = "none"; if (r30) r30.style.display = "block"; }
  } else {
    opts.style.display = "none";
    if (spm) spm.style.display = "none";
    if (r30) r30.style.display = "none";
  }
}

/* === Unidades automáticas (Hrs / Psi,Bar / °C,°F) === */
function poblarUnidadesInline() {
  document.querySelectorAll("select.unidad-select").forEach(sel => {
    const tipo = sel.getAttribute("data-tipo"); // 'horas', 'presion', 'temp'
    sel.innerHTML = "";
    const opcionesPorTipo = {
      horas: ["Hrs"],
      presion: ["Psi", "Bar"],
      temp: ["°C", "°F"],
      voltaje: ["V"],
      amperaje: ["A"],
      frecuencia: ["RPM", "Hz"],
      otro: ["-"]
    };
    (opcionesPorTipo[tipo] || ["N/A"]).forEach(u => {
      const opt = document.createElement("option");
      opt.value = u; opt.textContent = u;
      sel.appendChild(opt);
    });
  });
}

/* === Mostrar/ocultar “Compresor (oil free)” según tipo de equipo === */
function toggleOilFree() {
  const card = document.getElementById("card_oilfree");
  if (!card) return;
  const txt = getTipoEquipoValor();
  card.style.display = txt.includes("libre de aceite") ? "" : "none";
}

/* === Datos eléctricos: vista especial para Secador o Alta Presión (Preventivo o Bitácora) === */
function toggleDatosElectricosSecador() {
  const cardComp = document.getElementById("card_electrico_compresor");
  const cardSec = document.getElementById("card_electrico_secador");
  const cardAltaPresion = document.getElementById("card_electrico_alta_presion");
  const tipoServEl = document.getElementById("tipo_servicio");

  // Usamos nuestro helper para obtener el tipo de equipo real
  const txt = getTipoEquipoValor();

  if (!cardComp || !cardSec || !tipoServEl) return;

  const tipoServ = (tipoServEl.value || "").toLowerCase();

  const esPreventivo = (tipoServ === "preventivo");
  const esBitacora = (tipoServ === "bitácora" || tipoServ === "bitacora");
  const esSecador = txt.toLowerCase().includes("secador");
  const esAltaPresion = txt.toLowerCase().includes("alta presión") || txt.toLowerCase().includes("alta presion");

  // Si es Alta Presión + (Preventivo o Bitácora): mostramos tabla de alta presión
  if (esAltaPresion && (esPreventivo || esBitacora)) {
    cardComp.style.display = "none";
    cardSec.style.display = "none";
    if (cardAltaPresion) cardAltaPresion.style.display = "";
  } else if (esSecador && (esPreventivo || esBitacora)) {
    // Si es Preventivo + Secador O Bitácora + Secador: mostramos tabla recortada
    cardComp.style.display = "none";
    cardSec.style.display = "";
    if (cardAltaPresion) cardAltaPresion.style.display = "none";
  } else {
    // Todo lo demás: tabla completa normal
    cardComp.style.display = "";
    cardSec.style.display = "none";
    if (cardAltaPresion) cardAltaPresion.style.display = "none";
  }
}

/* =========================
   BOOTSTRAP
   ========================= */
document.addEventListener("DOMContentLoaded", () => {
  // Marca “OTROS”
  onMarcaChange();
  document.getElementById("marca_select")?.addEventListener("change", onMarcaChange);

  // Descripciones, bloques de actividades, lecturas y fotos por tipo
  updateDescripcionOptions();
  toggleBloquesPorTipo();
  ajustarFotosPorTipo();
  toggleLecturasSecador();
  updatePotenciaHint();
  toggleDatosElectricosSecador();
  document.getElementById('tipo_servicio')?.addEventListener("change", () => {
    updateDescripcionOptions();
    toggleBloquesPorTipo();
    ajustarFotosPorTipo();
    toggleLecturasSecador();
    toggleDatosElectricosSecador();
  });

  // Análisis de ruido
  toggleAnalisisRuido();
  document.getElementById('chk_ruido')?.addEventListener("change", toggleAnalisisRuido);
  document.getElementById('ruido_tipo')?.addEventListener("change", toggleAnalisisRuido);

  // Firmas HDPI
  enableSignaturePadHDPI("firma_tecnico_canvas", "btn_clear_tecnico", "firma_tecnico_data");
  enableSignaturePadHDPI("firma_cliente_canvas", "btn_clear_cliente", "firma_cliente_data");

  // Unidades, Oil Free, Potencia, lecturas y datos eléctricos para secador
  poblarUnidadesInline();
  toggleOilFree();
  toggleLecturasSecador();
  toggleDatosElectricosSecador();
  updatePotenciaHint();

  // Escuchar cambios en SELECT e INPUT de tipo de equipo
  const refreshUI = () => {
    toggleOilFree();
    toggleBloquesPorTipo();
    toggleLecturasSecador();
    toggleDatosElectricosSecador();
    updatePotenciaHint();
  };

  document.getElementById("tipo_equipo_select")?.addEventListener("change", refreshUI);
  document.getElementById("tipo_equipo_input")?.addEventListener("input", refreshUI);
  // También escuchar el toggle si es necesario, pero el cambio de valor suele dispararse por eventos

  // Load deals when client is selected (initialize on page load)
  const clienteSelect = document.getElementById('cliente_select');
  const dealSelect = document.getElementById('deal_select');

  if (clienteSelect && dealSelect) {
    const loadDealsForClient = function (clienteId) {
      console.log('🔄 Loading deals for client ID:', clienteId);
      dealSelect.innerHTML = '<option value="">No vincular a ningún trato</option>';

      if (clienteId) {
        fetch(`/api/deals/by_client/${clienteId}`)
          .then(r => {
            console.log('📡 Response status:', r.status);
            return r.json();
          })
          .then(data => {
            console.log('📦 Deals data received:', data);
            if (data.success && data.deals && data.deals.length > 0) {
              console.log(`✅ Found ${data.deals.length} deals for client`);
              data.deals.forEach(deal => {
                const option = document.createElement('option');
                option.value = deal.id;
                const tipoLabel = deal.tipo_deal === 'servicio' ? 'Servicio' : 'Venta';
                option.textContent = `${deal.folio || `ID-${deal.id}`} - ${deal.titulo} (${tipoLabel})`;
                dealSelect.appendChild(option);
              });
            } else {
              console.log('ℹ️ No deals found for this client');
            }
          })
          .catch(err => {
            console.error('❌ Error loading deals:', err);
          });
      }
    };

    clienteSelect.addEventListener('change', function () {
      console.log('👤 Client changed to:', this.value);
      loadDealsForClient(this.value);
    });

    // If client is already selected on page load, load deals immediately
    if (clienteSelect.value) {
      console.log('👤 Client already selected on load:', clienteSelect.value);
      // Small delay to ensure DOM is ready
      setTimeout(() => {
        loadDealsForClient(clienteSelect.value);
      }, 100);
    }
  }
});

/* =========================
   AUTO-GUARDADO (localStorage)
   ========================= */
(function () {
  const form = document.getElementById("frm-reporte");
  if (!form) return;

  // Usamos el folio como parte de la llave para no mezclar borradores
  const folioInput = form.querySelector('input[name="folio"]');
  const FOLIO = (folioInput ? folioInput.value : (window.__FOLIO__ || "sin-folio")) || "sin-folio";
  const AUTOSAVE_KEY = `inair_reporte_draft_${FOLIO}`;
  const INDEX_KEY = "inair_reporte_drafts_index"; // índice (folio → {cliente, fecha, saved_at})

  // Campos que NO guardamos (fotos subidas)
  const shouldSkip = (el) =>
    el.type === "file" ||
    el.name === "foto1" || el.name === "foto2" || el.name === "foto3" || el.name === "foto4";

  // Si el storage se llena por firmas pesadas, pasamos a NO guardar firmas y avisamos una sola vez
  let skipSignaturesRuntime = false;
  let alreadyWarned = false;

  // Toma un dataURL y si es para draft y está activada la compresión, intenta convertir a JPEG con calidad 0.85
  function maybeCompressDataUrl(dataUrl) {
    if (!USE_JPEG_FOR_DRAFT || !dataUrl?.startsWith("data:image/")) return dataUrl;
    try {
      // Convertimos solo si originalmente es PNG
      if (dataUrl.startsWith("data:image/png")) {
        // No tenemos el bitmap crudo aquí; para simplicidad, devolvemos PNG (ya suele ser liviano con fondo blanco)
        return dataUrl;
      }
      return dataUrl;
    } catch (_) { return dataUrl; }
  }

  function readIndex() {
    try { return JSON.parse(localStorage.getItem(INDEX_KEY) || "{}"); } catch (_) { return {}; }
  }
  function writeIndex(idx) {
    try { localStorage.setItem(INDEX_KEY, JSON.stringify(idx)); } catch (_) { }
  }

  // Tomar todos los valores del form
  function serializeForm() {
    const data = {};
    const elements = form.querySelectorAll("input, select, textarea");

    // Temporarily enable all disabled elements to capture their values
    const disabledElements = [];
    elements.forEach(el => {
      if (el.disabled) {
        disabledElements.push(el);
        el.disabled = false;
      }
    });

    elements.forEach(el => {
      if (!el.name) return;
      if (shouldSkip(el)) return;

      // saltar firmas si el modo runtime está activo
      if ((skipSignaturesRuntime) && (el.name === "firma_tecnico_data" || el.name === "firma_cliente_data")) return;

      // IMPORTANTE: Saltar campos eléctricos del secador aquí, los capturaremos después
      // para asegurarnos de que se capturen correctamente aunque estén ocultos
      // Ahora usamos nombres con prefijo sec_ para evitar conflictos con campos de compresor
      if (el.name.startsWith('sec_i_carga_') || el.name.startsWith('sec_v_carga_') ||
        (el.name.includes('sec_i_carga') && el.name.endsWith('_u')) ||
        (el.name.includes('sec_v_carga') && el.name.endsWith('_u'))) {
        return; // Los capturaremos después
      }

      if (el.type === "checkbox") {
        data[el.name] = el.checked ? "1" : "";
      } else if (el.type === "radio") {
        if (el.checked) data[el.name] = el.value;
      } else {
        // Para las firmas: opcionalmente comprimir para el borrador
        if (USE_JPEG_FOR_DRAFT && (el.name === "firma_tecnico_data" || el.name === "firma_cliente_data") && el.value) {
          data[el.name] = maybeCompressDataUrl(el.value);
        } else {
          data[el.name] = el.value;
        }
      }
    });

    // IMPORTANTE: Asegurar que los campos eléctricos del secador se capturen aunque estén ocultos
    const cardElectricoSecador = document.getElementById('card_electrico_secador');
    const form = document.getElementById('frm-reporte');

    let electricInputs = [];
    let electricSelects = [];

    if (cardElectricoSecador) {
      electricInputs = Array.from(cardElectricoSecador.querySelectorAll('input[name^="sec_i_carga_"], input[name^="sec_v_carga_"]'));
      electricSelects = Array.from(cardElectricoSecador.querySelectorAll('select[name$="_u"]'));
    }

    if (form) {
      const formInputs = Array.from(form.querySelectorAll('input[name^="sec_i_carga_"], input[name^="sec_v_carga_"]'));
      const formSelects = Array.from(form.querySelectorAll('select[name$="_u"]'));

      formInputs.forEach(input => {
        if (!electricInputs.find(i => i.name === input.name)) {
          electricInputs.push(input);
        }
      });

      formSelects.forEach(select => {
        if (select.name && (select.name.includes('sec_i_carga') || select.name.includes('sec_v_carga'))) {
          if (!electricSelects.find(s => s.name === select.name)) {
            electricSelects.push(select);
          }
        }
      });
    }

    // Forzar captura de valores, sobrescribiendo si ya existen
    console.log(`[SAVE SECADOR] 🔍 Iniciando captura de campos eléctricos...`);
    console.log(`[SAVE SECADOR] card_electrico_secador existe:`, !!cardElectricoSecador);
    console.log(`[SAVE SECADOR] Total inputs encontrados: ${electricInputs.length}, selects: ${electricSelects.length}`);

    let capturedCount = 0;
    electricInputs.forEach(field => {
      if (field.name && (field.name.startsWith('sec_i_carga_') || field.name.startsWith('sec_v_carga_'))) {
        const val = (field.value || '').trim();
        data[field.name] = val;
        capturedCount++;
        console.log(`[SAVE SECADOR] ✅ Campo eléctrico input capturado: ${field.name} = "${val}"`);
      }
    });

    electricSelects.forEach(field => {
      if (field.name && (field.name.includes('sec_i_carga') || field.name.includes('sec_v_carga'))) {
        const val = (field.value || '').trim();
        data[field.name] = val;
        capturedCount++;
        console.log(`[SAVE SECADOR] ✅ Campo eléctrico select capturado: ${field.name} = "${val}"`);
      }
    });

    console.log(`[SAVE SECADOR] 🎯 Total campos eléctricos capturados: ${capturedCount}`);

    // Re-disable elements
    disabledElements.forEach(el => {
      el.disabled = true;
    });

    data.__saved_at = new Date().toISOString();
    return data;
  }

  // Volcar valores guardados al form
  function applyDraft(draft) {
    // Obtener el form dinámicamente
    const currentForm = document.getElementById("frm-reporte");
    if (!currentForm) {
      console.warn("⚠️ Formulario no encontrado en applyDraft");
      return;
    }

    const elements = currentForm.querySelectorAll("input, select, textarea");

    // First pass: temporarily enable ALL disabled elements
    const disabledElements = [];
    elements.forEach(el => {
      if (el.disabled) {
        disabledElements.push(el);
        el.disabled = false;
      }
    });

    // Second pass: set values
    let checkboxesRestored = 0;
    elements.forEach(el => {
      if (!el.name) return;
      if (!(el.name in draft)) return;

      const val = draft[el.name];
      if (el.type === "checkbox") {
        // Asegurarse de que el checkbox esté habilitado antes de marcarlo
        const wasDisabled = el.disabled;
        if (wasDisabled) {
          el.disabled = false;
        }

        el.checked = (val === "1" || val === "on" || val === true || val === 1);

        if (el.name.startsWith('act_')) {
          checkboxesRestored++;
          console.log(`✅ Checkbox ${el.name} restaurado: ${el.checked} (valor: ${val})`);
        }

        // No volver a deshabilitar aquí, se hace en el Third pass
      } else if (el.type === "radio") {
        el.checked = (el.value === val);
      } else {
        el.value = val;
      }
    });

    if (checkboxesRestored > 0) {
      console.log(`✅ Total checkboxes de actividades restaurados: ${checkboxesRestored}`);
    }

    // Third pass: re-disable elements that were disabled
    disabledElements.forEach(el => {
      el.disabled = true;
    });

    // Fourth pass: Smart UI Restoration for Composite Fields (Tipo, Modelo, Serie)
    // We need to decide whether to show the Select or the Input based on the loaded value

    // Helper to restore composite field
    const restoreComposite = (fieldName, selectId, inputId, toggleId) => {
      const val = draft[fieldName];
      if (!val) return;

      const select = document.getElementById(selectId);
      const input = document.getElementById(inputId);
      const toggle = document.getElementById(toggleId);

      if (!select || !input || !toggle) return;

      // Check if value exists in select options
      let matchFound = false;
      Array.from(select.options).forEach(opt => {
        if (opt.value === val) matchFound = true;
      });

      if (matchFound) {
        // Mode: LIST
        select.value = val;
        select.style.display = 'block';
        select.disabled = false;

        input.style.display = 'none';
        input.disabled = true;
        input.value = val; // Sync just in case

        toggle.textContent = '✏️';
        toggle.title = 'Entrada Manual';

        // Update global state vars if they exist (accessed via window or just rely on UI state)
      } else {
        // Mode: MANUAL
        input.value = val;
        input.style.display = 'block';
        input.disabled = false;

        select.style.display = 'none';
        select.disabled = true;
        select.value = "";

        toggle.textContent = '📋';
        toggle.title = 'Seleccionar de Lista';
      }
    };

    restoreComposite('tipo_equipo', 'tipo_equipo_select', 'tipo_equipo_input', 'toggle_tipo_equipo');
    restoreComposite('modelo', 'modelo_select', 'modelo_input', 'toggle_modelo');
    restoreComposite('serie', 'serie_select', 'serie_input', 'toggle_serie_manual');

    // Restore Client Toggle State
    const clienteVal = draft['cliente'];
    const clienteSelect = document.getElementById('cliente_select');
    const clienteInput = document.getElementById('cliente_input');
    const clienteToggle = document.getElementById('toggle_manual_client');
    const dealSelect = document.getElementById('deal_select');

    // Load deals when client is selected (also trigger if client is already selected)
    if (clienteSelect && dealSelect) {
      const loadDealsForClient = function (clienteId) {
        dealSelect.innerHTML = '<option value="">No vincular a ningún trato</option>';

        if (clienteId) {
          fetch(`/api/deals/by_client/${clienteId}`)
            .then(r => r.json())
            .then(data => {
              if (data.success && data.deals && data.deals.length > 0) {
                data.deals.forEach(deal => {
                  const option = document.createElement('option');
                  option.value = deal.id;
                  const tipoLabel = deal.tipo_deal === 'servicio' ? 'Servicio' : 'Venta';
                  option.textContent = `${deal.folio || `ID-${deal.id}`} - ${deal.titulo} (${tipoLabel})`;
                  dealSelect.appendChild(option);
                });
              }
            })
            .catch(err => console.error('Error loading deals:', err));
        }
      };

      clienteSelect.addEventListener('change', function () {
        loadDealsForClient(this.value);
      });

      // If client is already selected when loading draft, load deals immediately
      if (clienteSelect.value) {
        loadDealsForClient(clienteSelect.value);
      }
    }

    if (clienteVal && clienteSelect && clienteInput && clienteToggle) {
      let match = false;
      Array.from(clienteSelect.options).forEach(opt => {
        if (opt.text === clienteVal) {
          clienteSelect.value = opt.value;
          match = true;
        }
      });

      if (match) {
        clienteSelect.style.display = 'block';
        clienteSelect.disabled = false;
        clienteInput.style.display = 'none';
        clienteInput.disabled = true;
        clienteToggle.textContent = '✏️';
      } else {
        clienteInput.value = clienteVal;
        clienteInput.style.display = 'block';
        clienteInput.disabled = false;
        clienteSelect.style.display = 'none';
        clienteSelect.disabled = true;
        clienteToggle.textContent = '📋';
      }
    }

    // Resincro de UI dependiente (ruido / oil-free / marca / lecturas / potencia / eléctricos secador, etc.)
    try {
      onMarcaChange?.();
      updateDescripcionOptions?.();
      // Restaurar descripcion_servicio después de regenerar las opciones
      if (draft.descripcion_servicio) {
        const descSelect = document.getElementById('descripcion_servicio');
        if (descSelect) descSelect.value = draft.descripcion_servicio;
      }
      toggleBloquesPorTipo?.();
      toggleAnalisisRuido?.();
      toggleOilFree?.();
      ajustarFotosPorTipo?.();
      toggleLecturasSecador?.();
      toggleDatosElectricosSecador?.();
      updatePotenciaHint?.();
    } catch (_) { }

    // IMPORTANTE: Restaurar campos eléctricos del secador después de mostrar la sección
    // Esto asegura que los valores se apliquen incluso si los campos estaban ocultos inicialmente
    // Esperar un momento para que toggleDatosElectricosSecador haya terminado
    setTimeout(() => {
      const cardElectricoSecador = document.getElementById('card_electrico_secador');
      if (cardElectricoSecador) {
        // Los campos ya deberían estar visibles después de toggleDatosElectricosSecador
        const electricInputs = cardElectricoSecador.querySelectorAll('input[name^="sec_i_carga_"], input[name^="sec_v_carga_"]');
        const electricSelects = cardElectricoSecador.querySelectorAll('select[name$="_u"]');

        // DEBUG: Mostrar qué campos se encontraron y qué hay en el draft
        console.log(`[RESTORE SECADOR] 🔍 Campos encontrados en DOM:`, Array.from(electricInputs).map(f => f.name));
        const draftKeys = Object.keys(draft).filter(k => k.includes('sec_i_carga') || k.includes('sec_v_carga'));
        console.log(`[RESTORE SECADOR] 🔍 Campos en draft:`, draftKeys);

        let restoredCount = 0;
        electricInputs.forEach(field => {
          if (field.name) {
            // Usar el nombre real del campo del DOM
            const fieldName = field.getAttribute('name') || field.name;
            if (fieldName in draft) {
              const val = draft[fieldName] || '';
              field.value = val;
              restoredCount++;
              console.log(`[RESTORE SECADOR] ✅ Campo eléctrico input restaurado: ${fieldName} = "${val}"`);
            } else {
              console.warn(`[RESTORE SECADOR] ⚠️ Campo ${fieldName} NO encontrado en draft`);
            }
          }
        });

        electricSelects.forEach(field => {
          const fieldName = field.getAttribute('name') || field.name;
          if (fieldName && (fieldName.includes('sec_i_carga') || fieldName.includes('sec_v_carga'))) {
            if (fieldName in draft) {
              const val = draft[fieldName] || '';
              field.value = val;
              restoredCount++;
              console.log(`[RESTORE SECADOR] ✅ Campo eléctrico select restaurado: ${fieldName} = "${val}"`);
            } else {
              console.warn(`[RESTORE SECADOR] ⚠️ Campo ${fieldName} NO encontrado en draft`);
            }
          }
        });

        if (restoredCount > 0) {
          console.log(`✅ Total campos eléctricos del secador restaurados: ${restoredCount}`);
        } else {
          console.warn(`[RESTORE SECADOR] ⚠️ NO se restauraron campos eléctricos. ¿Están en el draft?`);
        }
      } else {
        console.warn(`[RESTORE SECADOR] ⚠️ card_electrico_secador NO existe`);
      }
    }, 150);
  }

  // Función para obtener el folio actual dinámicamente
  function getCurrentFolio() {
    const currentForm = document.getElementById("frm-reporte");
    const currentFolioInput = currentForm ? currentForm.querySelector('input[name="folio"]') : null;
    return (currentFolioInput ? currentFolioInput.value : (window.__FOLIO__ || "sin-folio")) || "sin-folio";
  }

  // Función para obtener la clave de autoguardado dinámicamente
  function getAutosaveKey() {
    return `inair_reporte_draft_${getCurrentFolio()}`;
  }

  // Función para mostrar estado de guardado
  function showSaveStatus(msg, isError = false) {
    let el = document.getElementById('autosave-status');
    if (!el) {
      el = document.createElement('div');
      el.id = 'autosave-status';
      el.style.position = 'fixed';
      el.style.bottom = '20px';
      el.style.right = '20px';
      el.style.padding = '8px 12px';
      el.style.background = 'rgba(0,0,0,0.8)';
      el.style.color = '#fff';
      el.style.borderRadius = '4px';
      el.style.fontSize = '13px';
      el.style.zIndex = '9999';
      el.style.transition = 'opacity 0.3s';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.backgroundColor = isError ? 'rgba(220, 53, 69, 0.9)' : 'rgba(0,0,0,0.8)';
    el.style.opacity = '1';

    // Ocultar después de 2 segundos
    if (window.saveStatusTimeout) clearTimeout(window.saveStatusTimeout);
    window.saveStatusTimeout = setTimeout(() => {
      el.style.opacity = '0';
    }, 2000);
  }

  // Guardado con debounce
  let t = null;
  function scheduleSave() {
    if (t) clearTimeout(t);
    t = setTimeout(() => {
      try {
        const data = serializeForm();
        const currentFolio = getCurrentFolio();
        const currentAutosaveKey = getAutosaveKey();
        localStorage.setItem(currentAutosaveKey, JSON.stringify(data));

        // Actualizar índice (folio → cliente/fecha/saved_at)
        try {
          const idx = readIndex();
          idx[currentFolio] = {
            cliente: form.querySelector('input[name="cliente"]')?.value || "",
            fecha: form.querySelector('input[name="fecha"]')?.value || "",
            saved_at: data.__saved_at
          };
          writeIndex(idx);
        } catch (_) { }

        // Mostrar notificación de guardado
        showSaveStatus("Guardado localmente");

      } catch (e) {
        // Si falla por tamaño, quitamos firmas del draft y volvemos a intentar una vez
        if (!skipSignaturesRuntime) {
          skipSignaturesRuntime = true;
          try {
            const data = serializeForm();
            const currentAutosaveKey = getAutosaveKey();
            localStorage.setItem(currentAutosaveKey, JSON.stringify(data));
            showSaveStatus("Guardado localmente");
          } catch (e2) {
            // seguimos sin poder guardar, pero no mostramos error
          }
          if (!alreadyWarned) {
            alreadyWarned = true;
            console.warn("Borrador sin firmas para ahorrar espacio.");
          }
        } else {
          // No mostrar error, solo continuar
        }
      }
    }, 400);
  }

  // Modified applyDraft wrapper for server load
  async function loadDraftFromServer(folio) {
    console.log("🔄 Intentando cargar borrador del servidor para folio:", folio);
    try {
      const response = await fetch(`/api/load_draft/${encodeURIComponent(folio)}`);
      console.log("📡 Respuesta del servidor:", response.status, response.ok);
      if (response.ok) {
        const draft = await response.json();
        console.log("📦 Borrador recibido:", draft ? "Sí" : "No", draft?.form_data ? "con datos" : "sin datos");
        if (draft.form_data) {
          const formData = draft.form_data;

          // 1. Wait for clients list to be populated
          const waitForClients = new Promise((resolve) => {
            const check = setInterval(() => {
              const sel = document.getElementById('cliente_select');
              // Load deals for selected client
              if (sel && sel.value) {
                const dealSelect = document.getElementById('deal_select');
                if (dealSelect) {
                  fetch(`/api/deals/by_client/${sel.value}`)
                    .then(r => r.json())
                    .then(data => {
                      if (data.success && data.deals && data.deals.length > 0) {
                        dealSelect.innerHTML = '<option value="">No vincular a ningún trato</option>';
                        data.deals.forEach(deal => {
                          const option = document.createElement('option');
                          option.value = deal.id;
                          const tipoLabel = deal.tipo_deal === 'servicio' ? 'Servicio' : 'Venta';
                          option.textContent = `${deal.folio || `ID-${deal.id}`} - ${deal.titulo} (${tipoLabel})`;
                          dealSelect.appendChild(option);
                        });
                      }
                    })
                    .catch(err => console.error('Error loading deals:', err));
                }
              }
              // Reuse sel variable (already declared above)
              if (sel && sel.options.length > 1) {
                clearInterval(check);
                resolve();
              }
            }, 100);
            // Timeout 5s
            setTimeout(() => { clearInterval(check); resolve(); }, 5000);
          });

          await waitForClients;

          // 2. Set Client and Trigger Data Load
          const clienteVal = formData['cliente'];
          const clienteSelect = document.getElementById('cliente_select');
          const clienteInput = document.getElementById('cliente_input');
          const clienteToggle = document.getElementById('toggle_manual_client');

          console.log("🔍 Buscando cliente en borrador:", clienteVal);

          if (clienteVal) {
            // Primero intentar encontrar en el select
            if (clienteSelect) {
              let clientOption = Array.from(clienteSelect.options).find(opt => opt.text === clienteVal || opt.text.trim() === clienteVal.trim());

              if (clientOption) {
                console.log("✅ Cliente encontrado en select:", clientOption.text);
                // Set value
                clienteSelect.value = clientOption.value;
                clienteSelect.style.display = 'block';
                clienteSelect.disabled = false;

                if (clienteInput) {
                  clienteInput.style.display = 'none';
                  clienteInput.disabled = true;
                }
                if (clienteToggle) {
                  clienteToggle.textContent = '✏️';
                }

                // Trigger loadClientData and WAIT for it
                if (window.loadClientData) {
                  console.log("📞 Cargando datos del cliente...");
                  await window.loadClientData(clientOption.value);
                }
              } else if (clienteInput) {
                // Si no se encuentra en el select, usar el input manual
                console.log("📝 Usando modo manual para cliente:", clienteVal);
                clienteInput.value = clienteVal;
                clienteInput.style.display = 'block';
                clienteInput.disabled = false;

                if (clienteSelect) {
                  clienteSelect.style.display = 'none';
                  clienteSelect.disabled = true;
                }
                if (clienteToggle) {
                  clienteToggle.textContent = '📋';
                }
              }
            } else if (clienteInput) {
              // Solo modo manual disponible
              console.log("📝 Usando modo manual para cliente:", clienteVal);
              clienteInput.value = clienteVal;
              clienteInput.style.display = 'block';
              clienteInput.disabled = false;
            }
          }

          // 3. Now apply the rest of the draft (Equipment fields will now find their options!)
          // Excluir 'cliente' del formData porque ya lo manejamos arriba
          const formDataWithoutCliente = { ...formData };
          delete formDataWithoutCliente['cliente'];

          console.log("📋 Aplicando datos del borrador (excluyendo cliente)...");
          console.log("📋 Campos en borrador:", Object.keys(formDataWithoutCliente).filter(k => k.startsWith('act_')).length, "checkboxes de actividades");

          // Aplicar el draft
          applyDraft(formDataWithoutCliente);

          console.log("✅ Datos aplicados al formulario");

          // Load images - restore photos from draft
          console.log("🖼️ Restaurando imágenes...");
          const currentForm = document.getElementById("frm-reporte");

          // Asegurarse de que los hidden inputs existan y tengan los datos
          for (let i = 1; i <= 4; i++) {
            const fotoDataKey = `foto${i}_data`;
            const fotoData = draft[fotoDataKey];

            if (fotoData && currentForm) {
              console.log(`📷 Restaurando foto ${i}...`);

              // Buscar o crear hidden input
              let hiddenData = document.getElementById(`foto${i}_data`);
              if (!hiddenData) {
                hiddenData = document.createElement('input');
                hiddenData.type = 'hidden';
                hiddenData.id = `foto${i}_data`;
                hiddenData.name = `foto${i}_data`;
                currentForm.appendChild(hiddenData);
                console.log(`✅ Hidden input creado para foto ${i}`);
              }

              // Establecer el valor (asegurarse de que sea data URL completo)
              let dataUrl = fotoData;
              if (!dataUrl.startsWith('data:')) {
                dataUrl = `data:image/png;base64,${fotoData}`;
              }
              hiddenData.value = dataUrl;
              console.log(`✅ Datos de foto ${i} guardados en hidden input (longitud: ${dataUrl.length})`);

              // Buscar elementos existentes primero
              const previewContainer = document.getElementById(`foto${i}_preview_container`);
              const previewImg = document.getElementById(`foto${i}_preview`);
              const fotoInput = document.querySelector(`input[name="foto${i}"]`);

              // Si ya existe preview container, actualizarlo
              if (previewContainer && previewImg) {
                previewImg.src = dataUrl;
                previewContainer.style.display = 'block';
                if (fotoInput) {
                  fotoInput.style.display = 'none';
                }
                console.log(`✅ Preview actualizado para foto ${i}`);
              } else if (fotoInput && fotoInput.parentElement) {
                // Crear preview dinámicamente si no existe
                const fotoItem = fotoInput.closest('.foto-item');
                if (fotoItem) {
                  // Eliminar preview anterior si existe (por si acaso)
                  const oldPreview = fotoItem.querySelector(`#foto${i}_preview_container`);
                  if (oldPreview) {
                    oldPreview.remove();
                  }

                  // Crear elementos de preview
                  const previewDiv = document.createElement('div');
                  previewDiv.id = `foto${i}_preview_container`;
                  previewDiv.style.cssText = 'margin-top: 10px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;';

                  const img = document.createElement('img');
                  img.id = `foto${i}_preview`;
                  img.src = dataUrl;
                  img.style.cssText = 'max-width: 100%; max-height: 200px; display: block;';
                  img.onerror = () => {
                    console.error(`❌ Error cargando imagen ${i}`);
                  };

                  const removeBtn = document.createElement('button');
                  removeBtn.type = 'button';
                  removeBtn.className = 'btn btn-sm btn-danger mt-2';
                  removeBtn.textContent = 'Eliminar';
                  removeBtn.onclick = () => {
                    hiddenData.value = '';
                    previewDiv.remove();
                    if (fotoInput) fotoInput.style.display = 'block';
                  };

                  previewDiv.appendChild(img);
                  previewDiv.appendChild(removeBtn);
                  fotoItem.appendChild(previewDiv);

                  if (fotoInput) {
                    fotoInput.style.display = 'none';
                  }
                  console.log(`✅ Preview creado y mostrado para foto ${i}`);
                }
              } else {
                console.log(`⚠️ No se pudo crear preview para foto ${i} - elementos no encontrados`);
              }
            } else if (!fotoData) {
              console.log(`ℹ️ No hay datos para foto ${i}`);
            }
          }

          // También intentar usar restorePhotosFromDraft si existe (puede tener lógica adicional)
          if (window.restorePhotosFromDraft) {
            console.log("📷 Llamando restorePhotosFromDraft adicional...");
            window.restorePhotosFromDraft(draft);
          }

          if (draft.firma_tecnico_data) {
            const canvas = document.getElementById('firma_tecnico_canvas');
            if (canvas) {
              const ctx = canvas.getContext('2d');
              const img = new Image();
              img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                document.getElementById('firma_tecnico_data').value = draft.firma_tecnico_data;
              };
              img.src = draft.firma_tecnico_data;
            }
          }

          if (draft.firma_cliente_data) {
            const canvas = document.getElementById('firma_cliente_canvas');
            if (canvas) {
              const ctx = canvas.getContext('2d');
              const img = new Image();
              img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                document.getElementById('firma_cliente_data').value = draft.firma_cliente_data;
              };
              img.src = draft.firma_cliente_data;
            }
          }
          return true;
        }
      }
    } catch (e) {
      console.warn('Could not load draft from server:', e);
    }
    return false;
  }

  // Cargar borrador desde el servidor primero (si estamos en modo edición), luego desde localStorage
  async function loadDraft() {
    // Obtener el form de nuevo para asegurarnos de que esté disponible
    const currentForm = document.getElementById("frm-reporte");
    if (!currentForm) {
      console.warn("Formulario no encontrado en loadDraft");
      return;
    }

    // Obtener folio dinámicamente cuando se ejecuta la función
    const urlParams = new URLSearchParams(window.location.search);
    let folioParam = urlParams.get('folio');

    // Si no está en query params, intentar obtenerlo de window.__FOLIO__ o del input
    if (!folioParam) {
      const folioFromWindow = window.__FOLIO__;
      const currentFolioInput = currentForm.querySelector('input[name="folio"]');
      const folioFromInput = currentFolioInput ? currentFolioInput.value : null;

      // Usar el folio de window.__FOLIO__ o del input si está disponible y no es "sin-folio"
      if (folioFromWindow && folioFromWindow !== "sin-folio" && folioFromWindow.trim() !== "") {
        folioParam = folioFromWindow;
      } else if (folioFromInput && folioFromInput !== "sin-folio" && folioFromInput.trim() !== "") {
        folioParam = folioFromInput;
      }
    }

    console.log("loadDraft ejecutando para folio:", folioParam);

    // Si tenemos un folio válido, intentar cargar desde el servidor
    if (folioParam && folioParam !== "sin-folio" && folioParam.trim() !== "") {
      const loaded = await loadDraftFromServer(folioParam);
      if (loaded) {
        console.log("✅ Datos cargados del servidor.");
        return; // Si se cargó exitosamente desde el servidor, no cargar desde localStorage
      }
    }

    // Segundo: intentar cargar desde localStorage como fallback
    try {
      const currentAutosaveKey = getAutosaveKey();
      const raw = localStorage.getItem(currentAutosaveKey);
      if (!raw) return;
      const data = JSON.parse(raw);
      applyDraft(data);
      console.log('Draft loaded from localStorage');
    } catch (e) {
      console.warn("No se pudo restaurar borrador:", e);
    }
  }

  // Limpiar borrador
  function clearDraft() {
    const currentAutosaveKey = getAutosaveKey();
    const currentFolio = getCurrentFolio();
    localStorage.removeItem(currentAutosaveKey);
    // limpiar del índice
    try {
      const idx = readIndex();
      delete idx[currentFolio];
      writeIndex(idx);
    } catch (_) { }
  }

  // Eventos para guardar
  form.addEventListener("input", scheduleSave, true);
  form.addEventListener("change", scheduleSave, true);

  // Al enviar (PDF), aseguramos que TODOS los valores se envíen, incluso de campos disabled/hidden
  form.addEventListener("submit", (e) => {
    console.log("Form submitting - ensuring all fields are included");

    // Strategy: For each toggle group, copy the value from the active field (even if disabled)
    // to a temporary hidden input that WILL be submitted

    // 0. CLIENTE: Get value from either select (text) or input
    const clienteSelect = document.getElementById('cliente_select');
    const clienteInput = document.getElementById('cliente_input');
    if (clienteSelect || clienteInput) {
      const activeValue = (clienteInput && clienteInput.style.display !== 'none')
        ? clienteInput.value
        : (clienteSelect ? clienteSelect.options[clienteSelect.selectedIndex]?.text || '' : '');

      let hiddenCliente = document.getElementById('_cliente_submit');
      if (!hiddenCliente) {
        hiddenCliente = document.createElement('input');
        hiddenCliente.type = 'hidden';
        hiddenCliente.id = '_cliente_submit';
        hiddenCliente.name = 'cliente';
        form.appendChild(hiddenCliente);
      }
      hiddenCliente.value = activeValue;
      console.log("Cliente capturado para envío:", activeValue);
    }

    // 1. TIPO DE EQUIPO: Get value from either select or input
    const tipoSelect = document.getElementById('tipo_equipo_select');
    const tipoInput = document.getElementById('tipo_equipo_input');
    if (tipoSelect || tipoInput) {
      const activeValue = (tipoInput && tipoInput.style.display !== 'none')
        ? tipoInput.value
        : (tipoSelect ? tipoSelect.value : '');

      // Create/update hidden field for submission
      let hiddenTipo = document.getElementById('_tipo_equipo_submit');
      if (!hiddenTipo) {
        hiddenTipo = document.createElement('input');
        hiddenTipo.type = 'hidden';
        hiddenTipo.id = '_tipo_equipo_submit';
        hiddenTipo.name = 'tipo_equipo';
        form.appendChild(hiddenTipo);
      }
      hiddenTipo.value = activeValue;
    }

    // 2. MODELO: Get value from either select or input
    const modeloSelect = document.getElementById('modelo_select');
    const modeloInput = document.getElementById('modelo_input');
    if (modeloSelect || modeloInput) {
      const activeValue = (modeloInput && modeloInput.style.display !== 'none')
        ? modeloInput.value
        : (modeloSelect ? modeloSelect.value : '');

      let hiddenModelo = document.getElementById('_modelo_submit');
      if (!hiddenModelo) {
        hiddenModelo = document.createElement('input');
        hiddenModelo.type = 'hidden';
        hiddenModelo.id = '_modelo_submit';
        hiddenModelo.name = 'modelo';
        form.appendChild(hiddenModelo);
      }
      hiddenModelo.value = activeValue;
    }

    // 3. SERIE: Get value from either select or input
    const serieSelect = document.getElementById('serie_select');
    const serieInput = document.getElementById('serie_input');
    if (serieSelect || serieInput) {
      const activeValue = (serieInput && serieInput.style.display !== 'none')
        ? serieInput.value
        : (serieSelect ? serieSelect.value : '');

      let hiddenSerie = document.getElementById('_serie_submit');
      if (!hiddenSerie) {
        hiddenSerie = document.createElement('input');
        hiddenSerie.type = 'hidden';
        hiddenSerie.id = '_serie_submit';
        hiddenSerie.name = 'serie';
        form.appendChild(hiddenSerie);
      }
      hiddenSerie.value = activeValue;
    }

    // 4. Enable all readonly fields temporarily
    const readonlyFields = form.querySelectorAll('[readonly]');
    readonlyFields.forEach(el => {
      el.readOnly = false;
    });

    console.log("Form submission prepared - all values should be included now");
    clearDraft();
  });

  // Botón manual para borrar
  document.getElementById("btn-clear-draft")?.addEventListener("click", () => {
    clearDraft();
    alert("Borrador eliminado.");
  });

  // ========== INICIALIZACIÓN AL FINAL ==========
  // Esta sección se ejecuta DESPUÉS de que todas las funciones estén definidas

  // Función para inicializar la carga del borrador
  function startDraftLoading() {
    const currentForm = document.getElementById("frm-reporte");
    if (!currentForm) {
      setTimeout(startDraftLoading, 100);
      return;
    }

    // Verificar que window.__FOLIO__ esté disponible o usar el folio del input
    const folio = window.__FOLIO__;
    const currentFolioInput = currentForm.querySelector('input[name="folio"]');
    const folioValue = currentFolioInput ? currentFolioInput.value : null;
    const hasFolio = (folio && folio !== "sin-folio" && folio.trim() !== "") ||
      (folioValue && folioValue !== "sin-folio" && folioValue.trim() !== "");

    if (hasFolio || document.readyState === 'complete') {
      // Tenemos folio o el DOM está completo, cargar el borrador
      console.log("✅ Iniciando carga de borrador...");
      try {
        loadDraft();
      } catch (error) {
        console.error("Error al cargar borrador:", error);
      }
    } else {
      // Esperar un poco más
      setTimeout(startDraftLoading, 100);
    }
  }

  // Inicializar cuando el DOM esté listo
  // Usar un delay para asegurar que todo esté cargado
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(startDraftLoading, 500);
    });
  } else {
    // DOM ya está listo, esperar un poco más para que los scripts se ejecuten
    setTimeout(startDraftLoading, 500);
  }
})();

/* =========================
   LISTA DE BORRADORES (UI)
   ========================= */
(function () {
  const PREFIX = "inair_reporte_draft_";

  function getAllDrafts() {
    const items = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(PREFIX)) {
        try {
          const data = JSON.parse(localStorage.getItem(k) || "{}");
          const folio = k.replace(PREFIX, "");
          items.push({
            folio,
            savedAt: data.__saved_at || null,
            cliente: data.cliente || "",
            tipo: data.tipo_servicio || ""
          });
        } catch (_) { }
      }
    }
    // más recientes primero
    items.sort((a, b) => (b.savedAt || "").localeCompare(a.savedAt || ""));
    return items;
  }

  function renderDraftList() {
    const cont = document.getElementById("lista-borradores");
    if (!cont) return;
    cont.innerHTML = "";
    const drafts = getAllDrafts();

    if (!drafts.length) {
      cont.innerHTML = '<div class="text-muted">No hay borradores guardados en este dispositivo.</div>';
      return;
    }

    drafts.forEach(d => {
      const saved = d.savedAt ? new Date(d.savedAt).toLocaleString() : "—";
      const el = document.createElement("div");
      el.className = "list-group-item d-flex justify-content-between align-items-start";
      el.innerHTML = `
        <div class="me-2">
          <div><strong>Folio:</strong> ${d.folio}</div>
          <div class="text-muted">Guardado: ${saved}</div>
          ${d.cliente ? `<div class="text-muted">Cliente: ${d.cliente}</div>` : ""}
          ${d.tipo ? `<div class="text-muted">Tipo: ${d.tipo}</div>` : ""}
        </div>
        <div class="btn-group btn-group-sm">
          <a class="btn btn-primary" href="/formulario?folio=${encodeURIComponent(d.folio)}">Abrir</a>
          <button class="btn btn-outline-danger" data-del="${d.folio}">Eliminar</button>
        </div>
      `;
      cont.appendChild(el);
    });

    // eliminar un borrador
    cont.querySelectorAll("button[data-del]").forEach(btn => {
      btn.addEventListener("click", () => {
        const fol = btn.getAttribute("data-del");
        if (confirm(`Eliminar borrador del folio ${fol}?`)) {
          localStorage.removeItem(PREFIX + fol);
          renderDraftList();
        }
      });
    });
  }

  // cuando se abre el modal, refresca la lista
  document.addEventListener("shown.bs.modal", (ev) => {
    if (ev.target && ev.target.id === "modalBorradores") {
      renderDraftList();
    }
  });
})();

/* === Poblar selectores de unidad === */
(function () {
  const UNIDADES = {
    voltaje: ['V', 'kV', 'mV'],
    amperaje: ['A', 'mA', 'kA'],
    temp: ['°C', '°F', 'K'],
    presion: ['PSI', 'Bar', 'kPa', 'MPa'],
    frecuencia: ['Hz', 'kHz'],
    potencia: ['kW', 'HP', 'W'],
    rpm: ['RPM'],
    horas: ['hrs', 'h'],
    general: ['', 'V', 'A', '°C', '°F', 'PSI', 'Bar', 'Hz', 'RPM', 'kW', 'HP']
  };

  function poblarSelectoresUnidad() {
    const selectores = document.querySelectorAll('.unidad-select');
    selectores.forEach(select => {
      const tipo = select.dataset.tipo || 'general';
      const opciones = UNIDADES[tipo] || UNIDADES.general;

      // Limpiar opciones existentes
      select.innerHTML = '';

      // Agregar opciones
      opciones.forEach(unidad => {
        const option = document.createElement('option');
        option.value = unidad;
        option.textContent = unidad || '—';
        select.appendChild(option);
      });

      // Seleccionar primera opción por defecto
      if (opciones.length > 0) {
        select.value = opciones[0];
      }
    });
  }

  // Ejecutar al cargar la página
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', poblarSelectoresUnidad);
  } else {
    poblarSelectoresUnidad();
  }
})();

