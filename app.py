import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Tablero Individual — Prototipo Simple", layout="wide")

# =========================
# ESTILOS
# =========================
st.markdown("""
<style>
.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,.06);
}
.card-title {
  font-weight: 800;
  font-size: 13px;
  letter-spacing: .5px;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.hr-strong {
  border-top: 3px solid #111;
  margin: 10px 0 12px 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
RISK_COLORS = {"Alto": "#E53935", "Medio": "#FB8C00", "Bajo": "#43A047"}

def safe_text(v) -> str:
    """Convierte None/NaN/'nan' a string vacío."""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    s = "" if v is None else str(v)
    return "" if s.strip().lower() == "nan" else s

def risk_badge(text):
    t = safe_text(text)
    color = RISK_COLORS.get(t, "#E53935")
    return f"<span style='background:{color};color:white;padding:2px 8px;border-radius:6px;font-weight:600'>{t}</span>"

def normalize_doc(s: str) -> str:
    """Deja solo dígitos para comparar documentos."""
    s = safe_text(s)
    return "".join(ch for ch in s if ch.isdigit())

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_casos():
    df = pd.read_csv("casos_tablero.csv", dtype=str, keep_default_na=False).fillna("")
    # normalización documento para búsqueda robusta
    if "documento" in df.columns:
        df["documento_norm"] = df["documento"].astype(str).apply(normalize_doc)
    else:
        df["documento_norm"] = ""
    return df

@st.cache_data
def load_seguimientos():
    df = pd.read_csv("seguimientos_tablero.csv", dtype=str, keep_default_na=False).fillna("")
    # parse fecha si existe
    if "fecha" in df.columns:
        df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
    else:
        df["fecha_dt"] = pd.NaT
    return df

casos = load_casos()
seguimientos = load_seguimientos()

# =========================
# BANNER
# =========================
logo_candidates = [
    Path("logo_alcaldia.png"),
    Path("logo_alcaldia.jpg"),
    Path("imagenes/logo_alcaldia.png"),
    Path("imagenes/logo_alcaldia.jpg"),
]
logo_path = next((p for p in logo_candidates if p.exists()), None)

st.markdown(
    """
    <div style='background:#6A00FF;padding:16px 20px;border-radius:6px;
                display:flex;align-items:center;gap:16px;'>
      <div style='color:white;font-size:22px;font-weight:700;'>
        BANNER LOGOS INSTITUCIONALES
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

if logo_path:
    st.image(str(logo_path), width=140)

# =========================
# FILTROS
# =========================
# =========================
# FILTROS (con formulario y botón Buscar)
# =========================
if 'filtro_doc' not in st.session_state:
    st.session_state.filtro_doc = ""
if 'filtro_tipo' not in st.session_state:
    st.session_state.filtro_tipo = "Todas"

with st.form(key="filtros_form"):
    colb1, colb2 = st.columns([2, 1])
    with colb1:
        q = st.text_input(
            "Número de documento",
            st.session_state.filtro_doc,
            placeholder="Escribe el número de documento..."
        )
    with colb2:
        tipos = ["Todas", "CC", "TI", "CE", "RC", "PPT"]
        tipo = st.selectbox("Tipo de documento", tipos, index=tipos.index(st.session_state.filtro_tipo))

    submitted = st.form_submit_button("Buscar")

# Aplica filtros SOLO cuando se presiona el botón
if submitted:
    st.session_state.filtro_doc = q
    st.session_state.filtro_tipo = tipo

# Construcción del subconjunto con los valores persistidos
q_norm = normalize_doc(st.session_state.filtro_doc)
sel = casos.copy()

if q_norm:
    sel = sel[sel["documento_norm"].astype(str).str.contains(q_norm, na=False, regex=False)]

if st.session_state.filtro_tipo != "Todas" and "tipo_documento" in sel.columns:
    sel = sel[sel["tipo_documento"] == st.session_state.filtro_tipo]

if sel.empty:
    st.info("No se encontraron casos con los criterios. Se muestra el primer caso del dataset.")
    sel = casos.iloc[[0]]
else:
    sel = sel.iloc[[0]]

D = {k: safe_text(v) for k, v in sel.iloc[0].to_dict().items()}

# Seguimientos del caso (tabla multi-fila)
id_caso = safe_text(D.get("id_caso", ""))
seg_case = seguimientos[seguimientos["id_caso"].astype(str) == str(id_caso)].copy()
if not seg_case.empty:
    seg_case = seg_case.sort_values("fecha_dt", ascending=False)
    seg_case["fecha"] = seg_case["fecha"].astype(str).apply(safe_text)

# =========================
# IDENTIFICACIÓN
# =========================
st.markdown("### IDENTIFICACIÓN DEL CASO")

c1, c2 = st.columns([1, 1])

with c1:
    st.markdown(
        f"""
        <div style='background:#2F2F2F;color:#fff;padding:12px;border-radius:8px;margin-bottom:10px;width:100%'>
          <b>Nombre:</b> {D.get('nombre','')}
        </div>
        <div style='background:#6A00FF;color:#fff;padding:12px;border-radius:8px;margin-bottom:10px;width:100%'>
          <b>Documento de identidad:</b> {D.get('tipo_documento','')} {D.get('documento','')}
        </div>
        <div style='background:#6A00FF;color:#fff;padding:12px;border-radius:8px;margin-bottom:10px;width:100%'>
          <b># Atenciones asociadas:</b> {D.get('atenciones','')}
        </div>
        <div style='background:#6A00FF;color:#fff;padding:12px;border-radius:8px;margin-bottom:10px;width:100%'>
          <b>Estado actual del caso:</b> {D.get('estado_actual','')}
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div style='background:#6A00FF;color:#fff;padding:12px;border-radius:8px;margin-bottom:10px;width:100%;
                    display:flex;justify-content:space-between;align-items:center;'>
          <div><b>RIESGO GENERAL</b></div>
          <div>{risk_badge(D.get('riesgo_general',''))}</div>
        </div>
        <div style='text-align:right;margin-top:-6px;'>
        </div>
        
        """,
        unsafe_allow_html=True
    )

    # REMISIONES panel
    st.markdown(
        f"""
        <div class='card' style='margin-top:10px;'>
          <div class='card-title'>Remisiones que se han realizado</div>
          <div class='card-title' style='text-transform:none;font-weight:700;letter-spacing:0;'>Observaciones de la remisión</div>
          <div style='background:#f3f4f6;border-radius:10px;padding:12px;min-height:90px;'>
            {D.get('remisiones_observaciones','')}
          </div>
        </div>
        <span style='background:#BDBDBD;color:#111;padding:4px 8px;border-radius:10px;font-size:12px'>
            Fecha de última actualización: {D.get('fecha_ultima_actualizacion','')}
        </span>
        """,
        unsafe_allow_html=True
    )


# =========================
# LÍNEA DE TIEMPO + TABLA SEGUIMIENTOS (MULTIFILA)
# =========================
st.markdown("### Línea de tiempo del seguimiento")

if seg_case.empty:
    st.markdown(
        """
        <div class='card'>
          <div style='font-weight:700;'>No hay seguimientos registrados para este caso.</div>
          <div class='hr-strong'></div>
          <div style='background:#fff;border:1px dashed #d1d5db;border-radius:10px;padding:12px;min-height:70px;'>
            Agrega registros en <b>seguimientos_tablero.csv</b> con el mismo <b>id_caso</b>.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )


else:
    import streamlit.components.v1 as components

    # 1) Ordena por fecha ascendente (antigua -> reciente) y formatea
    fechas_ord = (
        seg_case["fecha_dt"]
        .dropna()
        .sort_values(ascending=True)
        .dt.strftime("%d/%m/%Y")
        .tolist()
    )

    # 2) Toma las 3 últimas (si hay más de 3), conserva el orden asc
    ult3 = fechas_ord[-3:]
    while len(ult3) < 3:
        ult3.insert(0, "")

    # Mapeo solicitado: IZQ = 1ª (más antigua, p.ej. 05/04) | CEN = 2ª | DER = 3ª (más reciente, p.ej. 15/04)
    fecha_izq, fecha_cen, fecha_der = ult3[0], ult3[1], ult3[2]

    # 3) HTML con GRID de 5 columnas (gutter-izq | 3 columnas | gutter-der)
    #    Fila 1: fechas (centradas en col 2,3,4)
    #    Fila 2: línea de tiempo (col 2 a 4)
    #    Fila 3: bloques (CASA / SIVIGILA / COMISARÍAS) alineados exactamente bajo cada fecha
    html_block = f"""
    <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.06);">

      <div style="
        display:grid;
        grid-template-columns: 5% 1fr 1fr 1fr 5%;
        row-gap:8px;
        align-items:center;
        font-weight:700;
      ">
        <!-- Fila 1: Fechas (centro en cada columna) -->
        <div></div>
        <div style="text-align:center;">{fecha_izq}</div>
        <div style="text-align:center;">{fecha_cen}</div>
        <div style="text-align:center;">{fecha_der}</div>
        <div></div>

        <!-- Fila 2: Línea de tiempo (col 2 a 4) -->
        <div></div>
        <div style="grid-column: 2 / span 3; height:3px; background:#111; border-radius:2px;"></div>
        <div></div>

        <!-- Fila 3: Bloques alineados bajo cada fecha -->
        <div></div>

        <!-- IZQUIERDA: CASA MATRÍA -->
        <div style="text-align:center;">
          <div style="width:3px;height:22px;background:#6A00FF;margin:-12px auto 8px auto;border-radius:3px;"></div>
          <div style="font-family:Arial, sans-serif;font-size:15px;letter-spacing:1px;"><b>CASA MATRÍA</b></div>
          <div>Riesgo {risk_badge(D.get('riesgo_casamatria',''))}</div>
        </div>

        <!-- CENTRO: SIVIGILA -->
        <div style="text-align:center;">
          <div style="width:3px;height:22px;background:#6A00FF;margin:-12px auto 8px auto;border-radius:3px;"></div>
          <div style="font-family:Arial, sans-serif;font-size:15px;letter-spacing:1px;"><b>SIVIGILA</b></div>
          <div>Riesgo {risk_badge(D.get('riesgo_sivigila',''))}</div>
        </div>

        <!-- DERECHA: COMISARIAS -->
        <div style="text-align:center;">
          <div style="width:3px;height:22px;background:#6A00FF;margin:-12px auto 8px auto;border-radius:3px;"></div>
          <div style="font-family:Arial, sans-serif;font-size:15px;letter-spacing:1px;"><b>COMISARIAS</b></div>
          <div>Riesgo {risk_badge(D.get('riesgo_comisarias',''))}</div>
        </div>

        <div></div>
      </div>

      <!-- Caja del último seguimiento -->
      <div style="margin-top:10px;background:#fff;border:1px dashed #d1d5db;border-radius:10px;padding:12px;">
        <b>Último seguimiento:</b> {safe_text(seg_case.iloc[0].get('descripcion',''))}
      </div>

    </div>
    """
    components.html(html_block, height=240)


# =========================
# CARACTERÍSTICAS + RIESGOS (2 columnas)
# =========================
st.markdown("")

ib1, ib2 = st.columns(2)

with ib1:
    st.markdown("<div class='card'><div class='card-title'>Características de la mujer</div>", unsafe_allow_html=True)
    st.write(f"Nacionalidad: {D.get('nacion','')}")
    st.write(f"Edad: {D.get('edad','')}")
    st.write(f"Sexo: {D.get('sexo','')}")
    st.write(f"Etnia: {D.get('etnia','')}")
    st.write(f"Orientación sexual: {D.get('orientacion_sexual','')}")
    st.write(f"Barrio: {D.get('barrio','')}")
    st.write(f"Dirección: {D.get('direccion','')}")
    st.write(f"Teléfono: {D.get('telefono','')}")
    st.write(f"Correo: {D.get('correo','')}")
    st.write(f"Tipos de violencia: {D.get('tipo_violencia','')}")
    st.write(f"Sexo del agresor: {D.get('sexo_agresor','')}")
    st.write(f"Parentesco con el agresor: {D.get('parentesco_agresor','')}")
    st.write(f"Observación adicional (características): {D.get('observ_caracteristicas','')}")
    st.markdown("</div>", unsafe_allow_html=True)

with ib2:
    st.markdown("<div class='card'><div class='card-title'>Datos de riesgo</div>", unsafe_allow_html=True)
    st.write(f"Fecha del hecho: {D.get('fecha_hecho','')}")
    st.write(f"Condición de discapacidad: {D.get('discapacidad','')}")
    st.write(f"Tipo de discapacidad: {D.get('tipo_discapacidad','')}")
    st.write(f"Mujer cabeza de familia: {D.get('cabeza_familia','')}")
    st.write(f"Embarazada: {D.get('embarazo','')}")
    st.write(f"Antecedente de violencia (últ. 3 meses): {D.get('antecedente_violencia_ult_3m','')}")
    st.write(f"Víctima del conflicto armado: {D.get('victima_conflicto','')}")
    st.write(f"Consumo de sustancias psicoactivas: {D.get('cons_sust','')}")
    st.write(f"Uso de arma: {D.get('uso_arma','')}")
    st.write(f"Observación adicional (riesgo): {D.get('observ_riesgo','')}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# OBSERVACIONES
# =========================
st.markdown("### INFORMACIÓN DETALLADA DEL CASO Y OBSERVACIONES")

st.markdown(
    f"""
    <div class='card' style='margin-top:10px;'>
      <div class='card-title'>Observaciones generales</div>
      <div style='background:#f3f4f6;border-radius:10px;padding:12px;min-height:90px;'>
        {D.get('observaciones_generales','')}
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write(f"Observaciones de Salud: {D.get('observ_salud','')}")
st.write(f"Observaciones de Comisarías de Familia: {D.get('observ_comisarias','')}")
st.write(f"Observaciones de Casa Matría: {D.get('observ_casamatria','')}")
st.write(f"Observaciones del Equipo de Acción de Emergencias (EAE): {D.get('observ_eae','')}")

# =========================
# ORGANISMOS
# =========================

# Lista fija con los correos y teléfonos
contactos_fijos = [
    {
        "organismo": "Secretaria de Salud",
        "email": "secretariasalud@cali.gov.co",
        "telefono": "6020000001",
    },
    {
        "organismo": "Comisarías de Familia",
        "email": "comisarias-de-familia@cali.gov.co",
        "telefono": "6020000002",
    },
    {
        "organismo": "Casa Matría",
        "email": "casa-matria@cali.gov.co",
        "telefono": "6020000003",
    },
    {
        "organismo": "Equipo de Acción de Emergencia (EAE)",
        "email": "equipo-de-accion-de-emergencia-eae@cali.gov.co",
        "telefono": "6020000004",
    },
    {
        "organismo": "Policia",
        "email": "policia@cali.gov.co",
        "telefono": "6020000005",
    },
    {
        "organismo": "Fiscalia",
        "email": "fiscalia@cali.gov.co",
        "telefono": "6020000006",
    },
]

# Render con tu estilo de “card” en HTML
bloque_md = [
    "<div class='card' style='margin-top:16px;'>",
    "  <div class='card-title'>Contactos de la Ruta de Atención</div>",
    "  <div style='font-size:14px; line-height:1.6;'>",
]
for c in contactos_fijos:
    bloque_md.append(
        "    <div style='margin:8px 0;'>"
        f"      <strong>{c['organismo']}</strong><br>"
        f"      Tel: <code>{c['telefono']}</code> &nbsp;·&nbsp; "
        f"      Correo: <code>{c['email']}</code>"
        "    </div>"
    )
bloque_md += ["  </div>", "</div>"]

st.markdown("\n".join(bloque_md), unsafe_allow_html=True)

st.caption("Prototipo — Fuente: casos_tablero.csv + seguimientos_tablero.csv")