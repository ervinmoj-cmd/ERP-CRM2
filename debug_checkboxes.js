// DEBUG SCRIPT - Copiar y pegar en consola del navegador

console.log("=== DEBUG CHECKBOXES ===");

// 1. Verificar que los checkboxes existen
const checkboxes = document.querySelectorAll('input[type="checkbox"][name^="act_"]');
console.log(`Encontrados ${checkboxes.length} checkboxes con name="act_*"`);

// 2. Verificar cuáles están marcados
let marcados = 0;
checkboxes.forEach(cb => {
    if (cb.checked) {
        console.log(`✓ ${cb.name} está marcado`);
        marcados++;
    }
});
console.log(`Total marcados: ${marcados}`);

// 3. Simular guardado (llamar a serializeForm manualmente)
console.log("\n=== SIMULANDO GUARDADO ===");
const form = document.getElementById("frm-reporte");
if (form) {
    const data = {};
    const elements = form.querySelectorAll("input, select, textarea");

    elements.forEach(el => {
        if (el.name && el.name.startsWith('act_') && el.type === 'checkbox') {
            data[el.name] = el.checked ? "1" : "";
            console.log(`Guardaría: ${el.name} = "${data[el.name]}" (checked: ${el.checked})`);
        }
    });

    console.log("\nDatos que se guardarían:", data);
} else {
    console.error("❌ Form 'frm-reporte' no encontrado");
}

// 4. Verificar localStorage
console.log("\n=== VERIFICANDO LOCALSTORAGE ===");
const folioInput = document.querySelector('input[name="folio"]');
const folio = folioInput ? folioInput.value : "sin-folio";
const key = `inair_reporte_draft_${folio}`;
const draft = localStorage.getItem(key);
if (draft) {
    try {
        const parsed = JSON.parse(draft);
        const actKeys = Object.keys(parsed).filter(k => k.startsWith('act_'));
        console.log(`Checkboxes en localStorage (${actKeys.length}):`);
        actKeys.forEach(k => {
            console.log(`  ${k} = "${parsed[k]}"`);
        });
    } catch (e) {
        console.error("Error parseando draft:", e);
    }
} else {
    console.warn("⚠️ No hay draft en localStorage para folio:", folio);
}

console.log("\n=== FIN DEBUG ===");
