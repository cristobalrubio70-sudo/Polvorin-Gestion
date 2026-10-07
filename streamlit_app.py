import streamlit as st
import pandas as pd
import numpy as np
import random
import uuid
from datetime import date, datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Sistema Polvorín Minero",
    page_icon="🧨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card{background:white;border-radius:10px;padding:16px;
  box-shadow:0 2px 8px rgba(0,0,0,0.08);text-align:center;margin-bottom:8px;}
.metric-val{font-size:2.2em;font-weight:bold;color:#1F3864;}
.metric-lbl{font-size:0.82em;color:#666;margin-top:2px;}
.alert-critica{background:#FFCCCC;border-left:5px solid #C00000;
  padding:10px 14px;border-radius:4px;margin:4px 0;}
.alert-alta{background:#FFEB9C;border-left:5px solid #BF8F00;
  padding:10px 14px;border-radius:4px;margin:4px 0;}
.alert-ok{background:#C6EFCE;border-left:5px solid #1F5C1F;
  padding:10px 14px;border-radius:4px;margin:4px 0;}
.alert-media{background:#FFF2CC;border-left:5px solid #7F6000;
  padding:10px 14px;border-radius:4px;margin:4px 0;}
.seccion{background:white;border-radius:10px;padding:20px;
  box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:16px;}
</style>
""", unsafe_allow_html=True)

# ── Configuración normativa ───────────────────────────────────────────────────
EXPLOSIVOS = {
    "ANFO":               {"tipo":"Secundario","unidad":"saco",  "peso_kg":25.0,"stock_min":5, "vida_dias":365,"almacen":"Container secundarios","temp_max":35,"hum_max":70},
    "Emulsion":           {"tipo":"Secundario","unidad":"caja",  "peso_kg":20.0,"stock_min":3, "vida_dias":180,"almacen":"Container secundarios","temp_max":30,"hum_max":65},
    "Mecha de seguridad": {"tipo":"Secundario","unidad":"rollo", "peso_kg":5.0, "stock_min":2, "vida_dias":730,"almacen":"Container secundarios","temp_max":40,"hum_max":75},
    "Fulminante N8":      {"tipo":"Primario",  "unidad":"caja",  "peso_kg":0.5, "stock_min":2, "vida_dias":365,"almacen":"Boveda enterrada (primarios)","temp_max":30,"hum_max":60},
}

OPERADORES = ["Juan Pérez","Ana López","Carlos Ruiz","María González","Pedro Soto","Camila Araya"]
VEHICULOS  = ["Camión F-150 · PAT-001","Camioneta Hilux · PAT-002","Camión Mercedes · PAT-003"]
DESTINOS   = ["Tronadura Nivel 1","Tronadura Nivel 2","Banco Norte","Banco Sur","Rajo principal"]
RUTAS = {
    "Polvorín → Nivel 1": {"dist_km":3.2,"tiempo_min":12,"limite_kmh":30},
    "Polvorín → Nivel 2": {"dist_km":4.8,"tiempo_min":18,"limite_kmh":30},
    "Polvorín → Banco Norte": {"dist_km":2.1,"tiempo_min":8,"limite_kmh":25},
    "Polvorín → Banco Sur":   {"dist_km":5.5,"tiempo_min":20,"limite_kmh":30},
    "Polvorín → Rajo principal": {"dist_km":7.2,"tiempo_min":28,"limite_kmh":35},
}

# ── Estado de sesión ──────────────────────────────────────────────────────────
def init_state():
    hoy = date.today()
    if "inv" not in st.session_state:
        lotes = []
        movs  = []
        for exp, cfg in EXPLOSIVOS.items():
            for i in range(random.randint(2,4)):
                dias_ing = random.randint(10,200)
                f_ing = hoy - timedelta(days=dias_ing)
                escenario = random.choices(
                    ["vigente","vencido","por_vencer","stock_bajo"],
                    weights=[60,10,15,15])[0]
                if escenario=="vencido":
                    f_venc = hoy - timedelta(days=random.randint(1,60))
                elif escenario=="por_vencer":
                    f_venc = hoy + timedelta(days=random.randint(1,25))
                else:
                    f_venc = f_ing + timedelta(days=cfg["vida_dias"])
                cant = (random.randint(1,cfg["stock_min"]-1)
                        if escenario=="stock_bajo"
                        else random.randint(cfg["stock_min"], cfg["stock_min"]*6))
                pref = exp[:4].upper().replace(" ","_")
                id_l = pref+"-"+str(hoy.year)+"-"+str(i+1).zfill(3)
                lotes.append({
                    "id_lote":id_l,"explosivo":exp,"tipo":cfg["tipo"],
                    "cantidad":cant,"unidad":cfg["unidad"],
                    "peso_kg_total":round(cant*cfg["peso_kg"],2),
                    "fecha_ingreso":str(f_ing),
                    "fecha_vencimiento":str(f_venc),
                    "proveedor":random.choice(["Enaex S.A.","Famesa","Orica Chile"]),
                    "n_guia":"GU-"+str(hoy.year)+"-"+str(random.randint(1000,9999)),
                    "operador":random.choice(OPERADORES),
                    "almacen":cfg["almacen"],
                })
                movs.append({
                    "id_mov":"MOV-"+uuid.uuid4().hex[:6].upper(),
                    "id_lote":id_l,"explosivo":exp,
                    "tipo":"Ingreso","cantidad":cant,
                    "fecha_hora":str(f_ing)+" 08:00",
                    "operador":random.choice(OPERADORES),
                    "destino":"-","n_orden":"GU-"+str(hoy.year)+"-"+str(random.randint(1000,9999)),
                })
        st.session_state["inv"]  = pd.DataFrame(lotes)
        st.session_state["movs"] = pd.DataFrame(movs)

    if "accesos" not in st.session_state:
        accesos = []
        for i in range(20):
            dt = datetime.now() - timedelta(hours=random.randint(1,72))
            accesos.append({
                "id":str(i+1).zfill(3),
                "operador":random.choice(OPERADORES),
                "tipo":random.choice(["Ingreso","Egreso"]),
                "fecha_hora":dt.strftime("%Y-%m-%d %H:%M"),
                "motivo":random.choice(["Despacho","Inventario","Inspección","Recepción"]),
                "autorizado":"Sí",
            })
        st.session_state["accesos"] = pd.DataFrame(accesos)

    if "viajes" not in st.session_state:
        viajes = []
        for i in range(12):
            ruta_nombre = random.choice(list(RUTAS.keys()))
            ruta = RUTAS[ruta_nombre]
            dt_s = datetime.now() - timedelta(hours=random.randint(1,96))
            demora = random.choices([0, random.randint(2,15)], weights=[70,30])[0]
            t_real = ruta["tiempo_min"] + demora
            dt_e = dt_s + timedelta(minutes=t_real)
            viajes.append({
                "id_viaje":"VJ-"+str(i+1).zfill(3),
                "vehiculo":random.choice(VEHICULOS),
                "ruta":ruta_nombre,
                "operador":random.choice(OPERADORES),
                "explosivo":random.choice(list(EXPLOSIVOS.keys())),
                "cantidad":random.randint(1,5),
                "inicio":dt_s.strftime("%Y-%m-%d %H:%M"),
                "fin":dt_e.strftime("%Y-%m-%d %H:%M"),
                "dist_km":ruta["dist_km"],
                "t_esperado_min":ruta["tiempo_min"],
                "t_real_min":t_real,
                "demora_min":demora,
                "estado":"Con demora" if demora>0 else "En tiempo",
            })
        st.session_state["viajes"] = pd.DataFrame(viajes)

    if "condiciones" not in st.session_state:
        st.session_state["condiciones"] = generar_condiciones()

def generar_condiciones():
    ahora = datetime.now()
    registros = []
    for h in range(24):
        dt = ahora - timedelta(hours=23-h)
        temp_s = round(random.uniform(14,38),1)
        hum_s  = round(random.uniform(45,85),1)
        temp_p = round(random.uniform(10,26),1)
        hum_p  = round(random.uniform(40,70),1)
        registros.append({
            "hora":dt.strftime("%H:%M"),
            "temp_secundarios":temp_s,"hum_secundarios":hum_s,
            "temp_primarios":temp_p,"hum_primarios":hum_p,
        })
    return pd.DataFrame(registros)

# ── Funciones de análisis ─────────────────────────────────────────────────────
def clasificar(row):
    exp  = str(row.get("explosivo",""))
    cfg  = EXPLOSIVOS.get(exp,{})
    hoy  = date.today()
    est  = []
    try:
        fv = date.fromisoformat(str(row["fecha_vencimiento"]))
        d  = (fv-hoy).days
        if d<0:    est.append("Vencido")
        elif d<=30: est.append("Por vencer")
    except: est.append("Fecha inválida")
    try:
        if int(row["cantidad"])<cfg.get("stock_min",0): est.append("Stock bajo")
    except: pass
    if str(row.get("almacen",""))!=cfg.get("almacen",""): est.append("Almacén incorrecto")
    return " | ".join(est) if est else "Vigente"

def generar_alertas(inv):
    alertas = []
    hoy = date.today()
    for _,row in inv.iterrows():
        exp = str(row["explosivo"])
        cfg = EXPLOSIVOS.get(exp,{})
        lote= str(row["id_lote"])
        try:
            fv = date.fromisoformat(str(row["fecha_vencimiento"]))
            d  = (fv-hoy).days
            if d<0:
                alertas.append({"gravedad":"🚨 CRÍTICA","lote":lote,"exp":exp,
                    "mensaje":"Lote VENCIDO hace "+str(abs(d))+" días",
                    "accion":"Destrucción autorizada — Ley Armas Cap. VIII"})
            elif d<=30:
                alertas.append({"gravedad":"⚠️ ALTA","lote":lote,"exp":exp,
                    "mensaje":"Vence en "+str(d)+" días",
                    "accion":"Notificar a Autoridad Fiscalizadora (DGMN)"})
        except: pass
        try:
            if int(row["cantidad"])<cfg.get("stock_min",0):
                alertas.append({"gravedad":"⚡ MEDIA","lote":lote,"exp":exp,
                    "mensaje":"Stock bajo: "+str(row["cantidad"])+" / mín "+str(cfg["stock_min"])+" "+cfg.get("unidad",""),
                    "accion":"Solicitar reabastecimiento al proveedor"})
        except: pass
        if str(row.get("almacen",""))!=cfg.get("almacen",""):
            alertas.append({"gravedad":"🚨 CRÍTICA","lote":lote,"exp":exp,
                "mensaje":"Almacén incorrecto: "+str(row.get("almacen","")),
                "accion":"Reubicar inmediatamente — DS 132 / Ley 17.798"})
    cond = st.session_state.get("condiciones", pd.DataFrame())
    if not cond.empty:
        ult = cond.iloc[-1]
        for alm,tk,hk in [
            ("Container secundarios","temp_secundarios","hum_secundarios"),
            ("Bóveda primarios","temp_primarios","hum_primarios"),
        ]:
            temp_lim = 35; hum_lim = 75
            if ult[tk]>temp_lim:
                alertas.append({"gravedad":"⚠️ ALTA","lote":"-","exp":alm,
                    "mensaje":"Temperatura alta: "+str(ult[tk])+"°C (máx "+str(temp_lim)+"°C)",
                    "accion":"Revisar ventilación del almacén"})
            if ult[hk]>hum_lim:
                alertas.append({"gravedad":"⚡ MEDIA","lote":"-","exp":alm,
                    "mensaje":"Humedad elevada: "+str(ult[hk])+"% (máx "+str(hum_lim)+"%)",
                    "accion":"Activar deshumidificador"})
    for _,v in st.session_state.get("viajes",pd.DataFrame()).iterrows():
        if str(v.get("estado",""))=="Con demora" and int(v.get("demora_min",0))>10:
            alertas.append({"gravedad":"⚠️ ALTA","lote":str(v["id_viaje"]),"exp":str(v["vehiculo"]),
                "mensaje":"Demora de "+str(v["demora_min"])+" min en ruta "+str(v["ruta"]),
                "accion":"Verificar estado del vehículo y la ruta"})
    return alertas

# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("## 🧨 Polvorín Minero")
        st.markdown("**Memoria de Título · UNAB 2026**")
        st.divider()
        modulo = st.radio("Módulo", [
            "🏠 Dashboard",
            "📥 Inventario y Kardex",
            "🚨 Alertas",
            "🚪 Control de Acceso",
            "🌡️ Condiciones Ambientales",
            "🚛 Flota y Traslados",
            "📋 Reportes",
            "⚙️ Configuración",
        ])
        st.divider()
        inv = st.session_state.get("inv", pd.DataFrame())
        if not inv.empty:
            inv["estado"] = inv.apply(clasificar, axis=1)
            nc = len([a for a in generar_alertas(inv) if "CRÍTICA" in a["gravedad"]])
            if nc>0:
                st.error("🚨 "+str(nc)+" alerta(s) crítica(s)")
            else:
                st.success("✅ Sin alertas críticas")
        st.caption("DS 132 · Ley 17.798 · DGMN 003048/2020")
    return modulo

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULOS
# ══════════════════════════════════════════════════════════════════════════════

def mod_dashboard():
    st.title("🏠 Dashboard General — Polvorín Minero")
    st.caption("Actualización: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    inv = st.session_state["inv"].copy()
    inv["estado"] = inv.apply(clasificar, axis=1)
    alertas = generar_alertas(inv)
    viajes  = st.session_state["viajes"]
    cond    = st.session_state["condiciones"]

    def ce(kw): return len(inv[inv["estado"].str.contains(kw,na=False)])
    nc = len([a for a in alertas if "CRÍTICA" in a["gravedad"]])
    na = len([a for a in alertas if "ALTA"    in a["gravedad"]])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("📦 Total lotes",    len(inv))
    c2.metric("✅ Vigentes",        ce("Vigente"))
    c3.metric("❌ Vencidos",        ce("Vencido"),  delta="-"+str(ce("Vencido")),  delta_color="inverse")
    c4.metric("⚠️ Por vencer",      ce("Por vencer"),delta="-"+str(ce("Por vencer")),delta_color="inverse")
    c5.metric("🚨 Alertas críticas",nc,             delta="-"+str(nc),              delta_color="inverse")
    c6.metric("🚛 Viajes hoy",      len(viajes[viajes["inicio"].str.startswith(str(date.today()))]))

    st.divider()
    col_a, col_b = st.columns([1,1])

    with col_a:
        st.subheader("🚨 Alertas activas")
        if not alertas:
            st.markdown('<div class="alert-ok">✅ Sin alertas activas</div>', unsafe_allow_html=True)
        for a in alertas[:6]:
            cls = "alert-critica" if "CRÍTICA" in a["gravedad"] else (
                  "alert-alta"    if "ALTA"    in a["gravedad"] else "alert-media")
            st.markdown(
                '<div class="'+cls+'"><b>'+a["gravedad"]+'</b> · '+a["lote"]+' — '+a["exp"]+'<br>'
                '<small>'+a["mensaje"]+'</small><br>'
                '<small><i>→ '+a["accion"]+'</i></small></div>',
                unsafe_allow_html=True)

    with col_b:
        st.subheader("📊 Stock por explosivo")
        resumen = inv.groupby("explosivo").agg(
            total_unidades=("cantidad","sum"),
            lotes=("id_lote","count")
        ).reset_index()
        st.dataframe(resumen, use_container_width=True, hide_index=True)

        st.subheader("🌡️ Condiciones actuales")
        ult = cond.iloc[-1]
        cc1,cc2,cc3,cc4 = st.columns(4)
        cc1.metric("Temp. Secundarios", str(ult["temp_secundarios"])+"°C",
                   delta="↑" if ult["temp_secundarios"]>30 else "✓",
                   delta_color="inverse" if ult["temp_secundarios"]>30 else "normal")
        cc2.metric("Hum. Secundarios",  str(ult["hum_secundarios"])+"%")
        cc3.metric("Temp. Primarios",   str(ult["temp_primarios"])+"°C")
        cc4.metric("Hum. Primarios",    str(ult["hum_primarios"])+"%")


def mod_inventario():
    st.title("📥 Inventario y Kardex")
    inv  = st.session_state["inv"].copy()
    movs = st.session_state["movs"].copy()
    inv["estado"] = inv.apply(clasificar, axis=1)

    tab1,tab2,tab3 = st.tabs(["📦 Inventario actual","➕ Registrar ingreso","📤 Registrar despacho"])

    with tab1:
        filtro = st.selectbox("Filtrar por estado",
            ["Todos"]+sorted(inv["estado"].unique().tolist()))
        df_f = inv if filtro=="Todos" else inv[inv["estado"]==filtro]
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        st.caption("Total: "+str(len(df_f))+" lotes · "+str(inv["cantidad"].sum())+" unidades totales")

        st.subheader("📋 Historial de movimientos (Libro Control)")
        st.dataframe(movs.sort_values("fecha_hora",ascending=False),
                     use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Registrar nuevo lote")
        with st.form("form_ingreso"):
            c1,c2 = st.columns(2)
            exp   = c1.selectbox("Explosivo", list(EXPLOSIVOS.keys()))
            cant  = c2.number_input("Cantidad", min_value=1, value=5)
            c3,c4 = st.columns(2)
            prov  = c3.text_input("Proveedor", "Enaex S.A.")
            guia  = c4.text_input("N° Guía", "GU-"+str(date.today().year)+"-")
            c5,c6 = st.columns(2)
            f_venc= c5.date_input("Fecha vencimiento",
                                  value=date.today()+timedelta(days=365))
            oper  = c6.selectbox("Operador", OPERADORES)
            obs   = st.text_area("Observaciones", height=60)
            submit= st.form_submit_button("✅ Registrar lote", type="primary")

        if submit:
            cfg   = EXPLOSIVOS[exp]
            pref  = exp[:4].upper().replace(" ","_")
            id_l  = pref+"-"+str(date.today().year)+"-"+uuid.uuid4().hex[:4].upper()
            nuevo = {"id_lote":id_l,"explosivo":exp,"tipo":cfg["tipo"],
                     "cantidad":int(cant),"unidad":cfg["unidad"],
                     "peso_kg_total":round(int(cant)*cfg["peso_kg"],2),
                     "fecha_ingreso":str(date.today()),
                     "fecha_vencimiento":str(f_venc),
                     "proveedor":prov,"n_guia":guia,"operador":oper,
                     "almacen":cfg["almacen"]}
            st.session_state["inv"]  = pd.concat([inv, pd.DataFrame([nuevo])], ignore_index=True)
            mov = {"id_mov":"MOV-"+uuid.uuid4().hex[:6].upper(),
                   "id_lote":id_l,"explosivo":exp,"tipo":"Ingreso",
                   "cantidad":int(cant),
                   "fecha_hora":datetime.now().strftime("%Y-%m-%d %H:%M"),
                   "operador":oper,"destino":"-","n_orden":guia}
            st.session_state["movs"] = pd.concat([movs, pd.DataFrame([mov])], ignore_index=True)
            st.success("✅ Lote "+id_l+" registrado en "+cfg["almacen"])
            st.rerun()

    with tab3:
        st.subheader("Registrar despacho")
        lotes_disp = inv[inv["estado"]=="Vigente"]["id_lote"].tolist()
        if not lotes_disp:
            st.warning("No hay lotes vigentes disponibles para despacho.")
        else:
            with st.form("form_despacho"):
                c1,c2 = st.columns(2)
                id_sel= c1.selectbox("Lote a despachar", lotes_disp)
                row_s = inv[inv["id_lote"]==id_sel].iloc[0]
                c2.info("Stock: "+str(row_s["cantidad"])+" "+str(row_s["unidad"]))
                c3,c4 = st.columns(2)
                cant_d= c3.number_input("Cantidad a despachar",
                                        min_value=1, max_value=int(row_s["cantidad"]))
                dest  = c4.selectbox("Destino", DESTINOS)
                c5,c6 = st.columns(2)
                oper_d= c5.selectbox("Operador", OPERADORES)
                orden = c6.text_input("N° Orden","ORD-"+str(date.today().year)+"-")
                sub_d = st.form_submit_button("📤 Registrar despacho", type="primary")

            if sub_d:
                if int(cant_d)>int(row_s["cantidad"]):
                    st.error("❌ Cantidad supera el stock disponible.")
                else:
                    idx = st.session_state["inv"][st.session_state["inv"]["id_lote"]==id_sel].index[0]
                    st.session_state["inv"].at[idx,"cantidad"] -= int(cant_d)
                    mov = {"id_mov":"MOV-"+uuid.uuid4().hex[:6].upper(),
                           "id_lote":id_sel,"explosivo":row_s["explosivo"],
                           "tipo":"Despacho","cantidad":int(cant_d),
                           "fecha_hora":datetime.now().strftime("%Y-%m-%d %H:%M"),
                           "operador":oper_d,"destino":dest,"n_orden":orden}
                    st.session_state["movs"] = pd.concat(
                        [st.session_state["movs"], pd.DataFrame([mov])], ignore_index=True)
                    st.success("✅ Despacho registrado. Stock restante: "+
                               str(int(row_s["cantidad"])-int(cant_d)))
                    st.rerun()


def mod_alertas():
    st.title("🚨 Alertas del Sistema")
    inv = st.session_state["inv"].copy()
    inv["estado"] = inv.apply(clasificar, axis=1)
    alertas = generar_alertas(inv)

    nc = len([a for a in alertas if "CRÍTICA" in a["gravedad"]])
    na = len([a for a in alertas if "ALTA"    in a["gravedad"]])
    nm = len([a for a in alertas if "MEDIA"   in a["gravedad"]])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total alertas",   len(alertas))
    c2.metric("🚨 Críticas",     nc)
    c3.metric("⚠️ Altas",        na)
    c4.metric("⚡ Medias",        nm)

    st.divider()
    filtro = st.selectbox("Filtrar por gravedad",
        ["Todas","🚨 CRÍTICA","⚠️ ALTA","⚡ MEDIA"])

    alertas_f = alertas if filtro=="Todas" else [
        a for a in alertas if filtro.split()[1] in a["gravedad"]]

    if not alertas_f:
        st.markdown('<div class="alert-ok">✅ Sin alertas en esta categoría</div>',
                    unsafe_allow_html=True)
    for a in alertas_f:
        cls = ("alert-critica" if "CRÍTICA" in a["gravedad"] else
               "alert-alta"    if "ALTA"    in a["gravedad"] else "alert-media")
        st.markdown(
            '<div class="'+cls+'">'
            '<b>'+a["gravedad"]+'</b> &nbsp;|&nbsp; <b>Lote:</b> '+a["lote"]+
            ' &nbsp;|&nbsp; <b>Explosivo:</b> '+a["exp"]+'<br>'
            '<b>Detalle:</b> '+a["mensaje"]+'<br>'
            '<b>Acción normativa:</b> <i>'+a["accion"]+'</i>'
            '</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 Historial de alertas (últimas 24 h)")
    hist = []
    for a in alertas:
        hist.append({"Hora":datetime.now().strftime("%H:%M"),
                     "Gravedad":a["gravedad"],"Lote":a["lote"],
                     "Explosivo":a["exp"],"Mensaje":a["mensaje"]})
    if hist:
        st.dataframe(pd.DataFrame(hist), use_container_width=True, hide_index=True)


def mod_acceso():
    st.title("🚪 Control de Acceso al Polvorín")
    accesos = st.session_state["accesos"].copy()

    tab1,tab2 = st.tabs(["📋 Registro de accesos","➕ Nuevo acceso"])

    with tab1:
        c1,c2 = st.columns(2)
        c1.metric("Accesos hoy", len(accesos[accesos["fecha_hora"].str.startswith(str(date.today()))]))
        c2.metric("Total registros", len(accesos))
        st.dataframe(accesos.sort_values("fecha_hora",ascending=False),
                     use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Registrar nuevo acceso")
        st.info("En el sistema real este registro se activa mediante lectura de credencial o huella digital. En el prototipo se ingresa manualmente.")
        with st.form("form_acceso"):
            c1,c2 = st.columns(2)
            oper  = c1.selectbox("Operador", OPERADORES)
            tipo  = c2.selectbox("Tipo", ["Ingreso","Egreso"])
            motivo= st.selectbox("Motivo", ["Despacho","Inventario","Inspección","Recepción","Otro"])
            sub   = st.form_submit_button("✅ Registrar", type="primary")
        if sub:
            nuevo = {"id":str(len(accesos)+1).zfill(3),"operador":oper,
                     "tipo":tipo,"fecha_hora":datetime.now().strftime("%Y-%m-%d %H:%M"),
                     "motivo":motivo,"autorizado":"Sí"}
            st.session_state["accesos"] = pd.concat(
                [accesos, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("✅ Acceso de "+tipo+" registrado para "+oper)
            st.rerun()


def mod_condiciones():
    st.title("🌡️ Condiciones Ambientales")
    st.caption("Datos simulados — en producción conectar sensores IoT via API")

    if st.button("🔄 Actualizar lecturas"):
        st.session_state["condiciones"] = generar_condiciones()
        st.rerun()

    cond = st.session_state["condiciones"]
    ult  = cond.iloc[-1]

    c1,c2,c3,c4 = st.columns(4)
    ts = ult["temp_secundarios"]; hs = ult["hum_secundarios"]
    tp = ult["temp_primarios"];   hp = ult["hum_primarios"]
    c1.metric("🌡️ Temp. Container",  str(ts)+"°C",
              delta="⚠️ Alta" if ts>35 else "✓ Normal",
              delta_color="inverse" if ts>35 else "normal")
    c2.metric("💧 Hum. Container",   str(hs)+"%",
              delta="⚠️ Alta" if hs>70 else "✓ Normal",
              delta_color="inverse" if hs>70 else "normal")
    c3.metric("🌡️ Temp. Bóveda",     str(tp)+"°C",
              delta="⚠️ Alta" if tp>30 else "✓ Normal",
              delta_color="inverse" if tp>30 else "normal")
    c4.metric("💧 Hum. Bóveda",      str(hp)+"%",
              delta="⚠️ Alta" if hp>60 else "✓ Normal",
              delta_color="inverse" if hp>60 else "normal")

    st.divider()
    st.subheader("📈 Histórico últimas 24 horas")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Container Secundarios**")
        st.line_chart(cond.set_index("hora")[["temp_secundarios","hum_secundarios"]])
    with col_r:
        st.markdown("**Bóveda Primarios**")
        st.line_chart(cond.set_index("hora")[["temp_primarios","hum_primarios"]])

    st.divider()
    st.subheader("📋 Límites normativos por explosivo")
    limites = [(exp,cfg["temp_max"],cfg["hum_max"],cfg["almacen"])
               for exp,cfg in EXPLOSIVOS.items()]
    df_lim = pd.DataFrame(limites,
        columns=["Explosivo","Temp. máx (°C)","Hum. máx (%)","Almacén"])
    st.dataframe(df_lim, use_container_width=True, hide_index=True)


def mod_flota():
    st.title("🚛 Flota y Traslados")
    viajes = st.session_state["viajes"].copy()

    tab1,tab2,tab3 = st.tabs(["📋 Registro de viajes","➕ Nuevo viaje","📊 Optimización"])

    with tab1:
        c1,c2,c3 = st.columns(3)
        c1.metric("Total viajes",  len(viajes))
        c2.metric("En tiempo",     len(viajes[viajes["estado"]=="En tiempo"]))
        c3.metric("Con demora",    len(viajes[viajes["estado"]=="Con demora"]),
                  delta="-"+str(len(viajes[viajes["estado"]=="Con demora"])),
                  delta_color="inverse")
        filtro = st.selectbox("Filtrar", ["Todos","En tiempo","Con demora"])
        df_f   = viajes if filtro=="Todos" else viajes[viajes["estado"]==filtro]
        st.dataframe(df_f, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Registrar nuevo viaje")
        st.info("En producción este registro se activa automáticamente al salir del polvorín mediante GPS. En el prototipo se ingresa manualmente.")
        with st.form("form_viaje"):
            c1,c2 = st.columns(2)
            veh   = c1.selectbox("Vehículo", VEHICULOS)
            oper  = c2.selectbox("Operador", OPERADORES)
            c3,c4 = st.columns(2)
            ruta  = c3.selectbox("Ruta", list(RUTAS.keys()))
            exp_v = c4.selectbox("Explosivo transportado", list(EXPLOSIVOS.keys()))
            c5,c6 = st.columns(2)
            cant_v= c5.number_input("Cantidad", min_value=1, value=2)
            t_real= c6.number_input("Tiempo real (min)", min_value=1,
                                    value=RUTAS[ruta]["tiempo_min"])
            sub_v = st.form_submit_button("✅ Registrar viaje", type="primary")
        if sub_v:
            r     = RUTAS[ruta]
            demora= max(0, int(t_real)-r["tiempo_min"])
            nuevo = {
                "id_viaje":"VJ-"+uuid.uuid4().hex[:5].upper(),
                "vehiculo":veh,"ruta":ruta,"operador":oper,
                "explosivo":exp_v,"cantidad":int(cant_v),
                "inicio":datetime.now().strftime("%Y-%m-%d %H:%M"),
                "fin":(datetime.now()+timedelta(minutes=int(t_real))).strftime("%Y-%m-%d %H:%M"),
                "dist_km":r["dist_km"],
                "t_esperado_min":r["tiempo_min"],
                "t_real_min":int(t_real),
                "demora_min":demora,
                "estado":"Con demora" if demora>0 else "En tiempo",
            }
            st.session_state["viajes"] = pd.concat(
                [viajes, pd.DataFrame([nuevo])], ignore_index=True)
            msg = ("⚠️ Viaje registrado con demora de "+str(demora)+" min."
                   if demora>0 else "✅ Viaje registrado en tiempo.")
            st.success(msg)
            st.rerun()

    with tab3:
        st.subheader("📊 Análisis de optimización de rutas")
        resumen_rutas = []
        for ruta_n, r in RUTAS.items():
            viajes_r = viajes[viajes["ruta"]==ruta_n]
            if not viajes_r.empty:
                t_prom = viajes_r["t_real_min"].mean()
                demora_prom = viajes_r["demora_min"].mean()
                pct_ok = len(viajes_r[viajes_r["estado"]=="En tiempo"])/len(viajes_r)*100
            else:
                t_prom=r["tiempo_min"]; demora_prom=0; pct_ok=100
            resumen_rutas.append({
                "Ruta":ruta_n,
                "Dist. (km)":r["dist_km"],
                "T. esperado (min)":r["tiempo_min"],
                "T. promedio real (min)":round(t_prom,1),
                "Demora prom. (min)":round(demora_prom,1),
                "% En tiempo":str(round(pct_ok,0))+"%",
                "Velocidad límite (km/h)":r["limite_kmh"],
            })
        df_opt = pd.DataFrame(resumen_rutas)
        st.dataframe(df_opt, use_container_width=True, hide_index=True)
        st.markdown("**🔑 Ruta más eficiente:** "+
            df_opt.loc[df_opt["Demora prom. (min)"].idxmin(),"Ruta"])
        st.markdown("**⚠️ Ruta con mayor demora:** "+
            df_opt.loc[df_opt["Demora prom. (min)"].idxmax(),"Ruta"])


def mod_reportes():
    import io, openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    st.title("📋 Generación de Reportes")
    st.info("Reportes automáticos listos para entregar a la Autoridad Fiscalizadora (DGMN/SERNAGEOMIN)")

    tipo = st.selectbox("Tipo de reporte", [
        "Reporte mensual completo",
        "Reporte de discrepancias",
        "Reporte de movimientos",
        "Reporte de condiciones ambientales",
        "Reporte de flota y traslados",
    ])
    periodo = st.date_input("Período", value=date.today())

    if st.button("📥 Generar y descargar reporte Excel", type="primary"):
        inv  = st.session_state["inv"].copy()
        inv["estado"] = inv.apply(clasificar, axis=1)
        movs = st.session_state["movs"]
        viajes = st.session_state["viajes"]
        cond   = st.session_state["condiciones"]
        alertas= generar_alertas(inv)

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        HF = PatternFill("solid",fgColor="1F3864")
        FF = Font(bold=True,color="FFFFFF",size=10)
        BD = Border(left=Side(style="thin"),right=Side(style="thin"),
                    top=Side(style="thin"),bottom=Side(style="thin"))
        FILL = {
            "CRÍTICA":PatternFill("solid",fgColor="FFCCCC"),
            "ALTA":   PatternFill("solid",fgColor="FFEB9C"),
            "MEDIA":  PatternFill("solid",fgColor="FFF2CC"),
            "VIGENTE":PatternFill("solid",fgColor="C6EFCE"),
            "VENCIDO":PatternFill("solid",fgColor="FFCCCC"),
        }

        def escribir(ws, df, titulo):
            ws.append([titulo])
            ws.cell(1,1).font=Font(bold=True,size=13,color="1F3864")
            ws.append(["Generado: "+str(datetime.now().strftime("%Y-%m-%d %H:%M"))])
            ws.cell(2,1).font=Font(italic=True,size=10,color="595959")
            ws.append([])
            ws.append(list(df.columns))
            for ci,_ in enumerate(df.columns,1):
                c=ws.cell(4,ci); c.fill=HF; c.font=FF; c.border=BD
                c.alignment=Alignment(horizontal="center",wrap_text=True)
            for ri,row in enumerate(df.itertuples(index=False),5):
                for ci,val in enumerate(row,1):
                    c=ws.cell(ri,ci,value=str(val) if val is not None else "")
                    c.border=BD; c.alignment=Alignment(wrap_text=True,vertical="center")
                    vs=str(val).upper()
                    for k,f in FILL.items():
                        if k in vs: c.fill=f; break
            for col in ws.columns:
                ml=max((len(str(c.value)) if c.value else 0) for c in col)
                ws.column_dimensions[get_column_letter(col[0].column)].width=min(ml+4,40)

        ws1=wb.active; ws1.title="Inventario"
        escribir(ws1,inv,"INVENTARIO — "+str(periodo))

        if tipo in ["Reporte mensual completo","Reporte de movimientos"]:
            ws2=wb.create_sheet("Movimientos")
            escribir(ws2,movs,"MOVIMIENTOS — "+str(periodo))

        if tipo in ["Reporte mensual completo","Reporte de discrepancias"]:
            ws3=wb.create_sheet("Alertas y Discrepancias")
            df_a=pd.DataFrame(alertas) if alertas else pd.DataFrame(
                columns=["gravedad","lote","exp","mensaje","accion"])
            escribir(ws3,df_a,"ALERTAS Y DISCREPANCIAS — "+str(periodo))

        if tipo in ["Reporte mensual completo","Reporte de condiciones ambientales"]:
            ws4=wb.create_sheet("Condiciones Ambientales")
            escribir(ws4,cond,"CONDICIONES AMBIENTALES — "+str(periodo))

        if tipo in ["Reporte mensual completo","Reporte de flota y traslados"]:
            ws5=wb.create_sheet("Flota y Traslados")
            escribir(ws5,viajes,"FLOTA Y TRASLADOS — "+str(periodo))

        ws_r=wb.create_sheet("Resumen Ejecutivo")
        def ce(kw): return len(inv[inv["estado"].str.contains(kw,na=False)])
        nc=len([a for a in alertas if "CRÍTICA" in a["gravedad"]])
        for fila in [
            ["REPORTE OFICIAL — POLVORÍN MINERO",""],
            ["Período",str(periodo)],
            ["Generado",datetime.now().strftime("%Y-%m-%d %H:%M")],["",""],
            ["INVENTARIO",""],
            ["Total lotes",len(inv)],["Vigentes",ce("Vigente")],
            ["Vencidos",ce("Vencido")],["Por vencer",ce("Por vencer")],["",""],
            ["ALERTAS",""],
            ["Total alertas",len(alertas)],["Críticas",nc],["",""],
            ["TRASLADOS",""],
            ["Total viajes",len(viajes)],
            ["Con demora",len(viajes[viajes["estado"]=="Con demora"])],["",""],
            ["NORMATIVA APLICABLE",""],
            ["DS 132 SERNAGEOMIN","Reglamento de Seguridad Minera"],
            ["Ley 17.798","Control de Armas y Explosivos"],
            ["DGMN 003048/2020","Almacenamiento productos Ley 17.798"],
        ]:
            ws_r.append(fila)
        ws_r["A1"].font=Font(bold=True,size=13,color="1F3864")
        ws_r.column_dimensions["A"].width=35
        ws_r.column_dimensions["B"].width=45

        wb.save(output); output.seek(0)
        st.download_button(
            label="📥 Descargar "+tipo,
            data=output,
            file_name="reporte_polvorin_"+str(periodo)+".xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("✅ Reporte generado correctamente.")


def mod_config():
    st.title("⚙️ Configuración del Sistema")
    st.subheader("📋 Parámetros del polvorín")
    st.info("En producción estos parámetros se guardan en base de datos. En el prototipo se muestran los valores del caso hipotético.")
    df_cfg = pd.DataFrame([
        {"Explosivo":exp,"Tipo":cfg["tipo"],"Unidad":cfg["unidad"],
         "Peso/unidad (kg)":cfg["peso_kg"],"Stock mínimo":cfg["stock_min"],
         "Vida útil (días)":cfg["vida_dias"],"Almacén":cfg["almacen"],
         "Temp. máx (°C)":cfg["temp_max"],"Hum. máx (%)":cfg["hum_max"]}
        for exp,cfg in EXPLOSIVOS.items()
    ])
    st.dataframe(df_cfg, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🛣️ Rutas de traslado")
    df_rut = pd.DataFrame([
        {"Ruta":k,"Distancia (km)":v["dist_km"],
         "Tiempo esperado (min)":v["tiempo_min"],
         "Velocidad límite (km/h)":v["limite_kmh"]}
        for k,v in RUTAS.items()
    ])
    st.dataframe(df_rut, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("ℹ️ Acerca del sistema")
    st.markdown("""
    **Sistema de Gestión de Polvorín Minero**
    - Versión: 1.0.0 (prototipo)
    - Autor: Cristóbal Rubio — UNAB 2026
    - Normativa: DS 132 SERNAGEOMIN · Ley 17.798 · DGMN 003048/2020
    - Estado: Prototipo funcional con datos simulados
    - Próxima versión: conexión a sensores IoT y GPS real
    """)

    if st.button("🔄 Reiniciar todos los datos simulados", type="secondary"):
        for key in ["inv","movs","accesos","viajes","condiciones"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Datos reiniciados. Recarga la página para ver los nuevos datos.")
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
init_state()
modulo = sidebar()

if   "Dashboard"    in modulo: mod_dashboard()
elif "Inventario"   in modulo: mod_inventario()
elif "Alertas"      in modulo: mod_alertas()
elif "Acceso"       in modulo: mod_acceso()
elif "Condiciones"  in modulo: mod_condiciones()
elif "Flota"        in modulo: mod_flota()
elif "Reportes"     in modulo: mod_reportes()
elif "Configuración" in modulo: mod_config()
