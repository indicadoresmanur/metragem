import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

st.set_page_config(
    page_title="Casa Mansur | Indicadores M²",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Força sidebar aberto via JS (uma vez por sessão)
if "sb_init" not in st.session_state:
    st.session_state.sb_init = True
    components.html("""<script>
    (function(){
      function tryOpen(){
        var doc=window.parent.document;
        var sb=doc.querySelector('[data-testid="stSidebar"]');
        if(!sb)return false;
        if(sb.getAttribute('aria-expanded')==='false'){
          var btn=doc.querySelector('[data-testid="collapsedControl"]');
          if(btn)btn.click();
        }
        return true;
      }
      var i=setInterval(function(){if(tryOpen())clearInterval(i);},80);
      setTimeout(function(){clearInterval(i);},3000);
    })();
    </script>""", height=0, scrolling=False)

# ── Helpers ───────────────────────────────────────────────────────────────

def period_for_date(d):
    if pd.isna(d): return None
    if d.day <= 20:
        end = pd.Timestamp(d.year, d.month, 20)
    else:
        m = d.month % 12 + 1
        y = d.year + (1 if d.month == 12 else 0)
        end = pd.Timestamp(y, m, 20)
    sm = end.month - 1 if end.month > 1 else 12
    sy = end.year if end.month > 1 else end.year - 1
    return end, f"21/{sm:02d}/{sy} a 20/{end.month:02d}/{end.year}"

def build_periods(year):
    ends, labels = [], []
    for m in range(1, 13):
        end = pd.Timestamp(year, m, 20)
        sm  = m - 1 if m > 1 else 12
        sy  = year  if m > 1 else year - 1
        ends.append(end)
        labels.append(f"21/{sm:02d}/{sy} a 20/{m:02d}/{year}")
    return ends, labels

def n(v, dec=0):
    if v is None or (isinstance(v, float) and (pd.isna(v) or np.isinf(v))): return "–"
    return f"{v:,.{dec}f}".replace(",","X").replace(".",",").replace("X",".")

def ic(p):
    return "#059669" if p >= 100 else ("#d97706" if p >= 80 else "#dc2626")

def ib(p):
    return "rgba(5,150,105,.18)" if p >= 100 else ("rgba(217,119,6,.18)" if p >= 80 else "rgba(220,38,38,.18)")

def il(p):
    return "✓ Atingido" if p >= 100 else ("⚠ Em Risco" if p >= 80 else "✗ Abaixo")

DEFAULT_METAS = {
    2026: [3944, 4995, 4620, 5334, 5371, 5048, 5976, 5634, 5716, 5730, 5120, 4708]
}

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""<style>
  .block-container{padding-top:.4rem;padding-bottom:.5rem;max-width:100%}
  footer,#MainMenu,[data-testid="stToolbar"]{display:none!important}
  header[data-testid="stHeader"]{display:none!important}

  /* Sidebar */
  section[data-testid="stSidebar"],
  section[data-testid="stSidebar"]>div{background:#0b1520!important}
  section[data-testid="stSidebar"]{border-right:1px solid #1a2535!important}
  section[data-testid="stSidebar"] label{color:#4a6278!important;font-size:.72rem!important;font-weight:600!important}
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] small{color:#8da4b8!important}
  section[data-testid="stSidebar"] input,
  section[data-testid="stSidebar"] textarea{
    background:#060d14!important;color:#e6edf3!important;
    border:1px solid #1a2535!important;border-radius:6px!important}
  section[data-testid="stSidebar"] [data-baseweb="select"] div{
    background:#060d14!important;color:#e6edf3!important;border-color:#1a2535!important}
  section[data-testid="stSidebar"] [data-baseweb="tag"]{background:#1a2535!important;color:#8da4b8!important}
  section[data-testid="stSidebar"] hr{border-color:#1a2535!important}
  [data-testid="collapsedControl"]{background:#0b1520!important;color:#4a6278!important;border:none!important}
  section[data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"]{color:#1a2535!important}

  /* KPI card */
  .kpi{background:#0b1520;border-radius:8px;padding:11px 13px;
    border:1px solid #1a2535;height:100%}
  .kpi-lbl{font-size:.55rem;font-weight:700;color:#ffffff;
    text-transform:uppercase;letter-spacing:.9px;margin-bottom:5px}
  .kpi-val{font-size:1.3rem;font-weight:900;color:#e6edf3;
    line-height:1;letter-spacing:-.5px}
  .kpi-sub{font-size:.6rem;color:#6b8299;margin-top:3px}

  /* Divider */
  .sdiv{font-size:.58rem;font-weight:700;color:#ffffff;
    text-transform:uppercase;letter-spacing:1.5px;margin:12px 0 5px;
    display:flex;align-items:center;gap:8px}
  .sdiv::after{content:'';flex:1;height:1px;background:#1a2535}
</style>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:18px 8px 16px;text-align:center;
      border-bottom:1px solid #1a2535;margin-bottom:14px">
      <div style="font-size:.52rem;font-weight:600;color:#4a6278;
        letter-spacing:3px;margin-bottom:6px">CASA</div>
      <div style="font-size:1.8rem;font-weight:900;color:#c9a227;
        letter-spacing:-3px;line-height:1">MANSUR</div>
      <div style="font-size:.48rem;color:#2e4258;letter-spacing:3px;margin-top:5px">
        INDICADORES M² E METAS
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="color:#2e4258;font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px">📂 Dados</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")
    year = int(st.number_input("Ano", value=2026, min_value=2000, max_value=2100))

    st.markdown('<div style="height:1px;background:#1a2535;margin:10px 0"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#2e4258;font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px">🎯 Metas</p>', unsafe_allow_html=True)
    _hint = ",".join(str(v) for v in DEFAULT_METAS[year]) if year in DEFAULT_METAS else ""
    targets_text = st.text_area("12 valores por vírgula", height=68,
        placeholder=_hint or "5000,5200,...")
    if year in DEFAULT_METAS and not targets_text:
        st.markdown(f'<div style="color:#059669;font-size:.65rem;margin-top:2px">✓ Metas oficiais {year}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:#1a2535;margin:10px 0"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#2e4258;font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px">🖼 Exportação</p>', unsafe_allow_html=True)
    png_dpi   = st.selectbox("Resolução PNG", [150, 300, 600], index=1)
    multi_dpi = st.multiselect("Múltiplas resoluções (ZIP)", [150, 300, 600], default=[300])

# ── Load data ─────────────────────────────────────────────────────────────
@st.cache_data
def load(src, is_upload: bool):
    df = pd.read_csv(src, sep=";", encoding="latin1", dtype=str)
    df.columns = [c.strip().replace("﻿","") for c in df.columns]
    date_col = next((c for c in ["DATA TÉRMINO","INSTALAÇÃO ENCERRADA EM",
        "INSTALACAO ENCERRADA EM","DATA VISTORIA"] if c in df.columns), df.columns[0])
    m2_col = next((c for c in df.columns if c.strip().lower()=="m2"), None)
    inst_col = next((c for c in df.columns if "INSTALADOR" in c.upper()), None)
    df[date_col] = pd.to_datetime(df[date_col].str.strip(), dayfirst=True, errors="coerce")
    if m2_col:
        df[m2_col] = (df[m2_col].str.replace(".",  "", regex=False)
                                 .str.replace(",", ".", regex=False))
        df[m2_col] = pd.to_numeric(df[m2_col], errors="coerce").fillna(0)
    ends, labels = [], []
    for d in df[date_col]:
        r = period_for_date(d)
        if r: ends.append(r[0]); labels.append(r[1])
        else: ends.append(pd.NaT); labels.append(None)
    df["_pend"]   = ends
    df["_plabel"] = labels
    return df, date_col, m2_col, inst_col

src = uploaded if uploaded else "MARCELO.ARAUJO_CONTRATOS.CSV"
df, date_col, m2_col, inst_col = load(src, uploaded is not None)

# ── Period table ──────────────────────────────────────────────────────────
fdf = df[df["_pend"].dt.year == year].copy()
grp = fdf.groupby(["_pend","_plabel"], dropna=True)[m2_col].sum().reset_index()
p_ends, p_labels = build_periods(year)
base = pd.DataFrame({"_pend": p_ends, "_plabel": p_labels})
tbl  = base.merge(grp, on=["_pend","_plabel"], how="left")
tbl[m2_col] = tbl[m2_col].fillna(0)

# ── Targets ───────────────────────────────────────────────────────────────
if targets_text:
    toks = [t.strip() for t in targets_text.split(",") if t.strip()]
    if len(toks) == 12:
        try: tbl["meta"] = [float(t.replace(",",".")) for t in toks]
        except: tbl["meta"] = tbl[m2_col][tbl[m2_col]>0].mean() or 0
    else: tbl["meta"] = tbl[m2_col][tbl[m2_col]>0].mean() or 0
elif year in DEFAULT_METAS:
    tbl["meta"] = DEFAULT_METAS[year]
else:
    avg = tbl[m2_col][tbl[m2_col]>0].mean()
    tbl["meta"] = avg if pd.notna(avg) else 0

tbl["m2_acum_t"]   = tbl[m2_col].cumsum()
tbl["meta_acum_t"] = tbl["meta"].cumsum()
tbl["icm_t"]       = np.where(tbl["meta"]>0, tbl[m2_col]/tbl["meta"]*100, 0)

# ── Key metrics ───────────────────────────────────────────────────────────
today    = pd.Timestamp.today().normalize()
meta_geral = float(tbl["meta"].sum())
days_y   = 366 if year % 4 == 0 else 365
start_y  = pd.Timestamp(year, 1, 1)
elapsed  = max(1, (today - start_y).days)
remain   = max(1, days_y - elapsed)

# M² HOJE / META DIA
m2_hoje  = float(df[df[date_col].dt.normalize() == today][m2_col].sum())
meta_dia = meta_geral / days_y
icm_dia  = m2_hoje / meta_dia * 100 if meta_dia > 0 else 0

# M² MÊS (mês calendário atual)
m2_mes   = float(df[(df[date_col].dt.month == today.month) &
                     (df[date_col].dt.year  == today.year) &
                     df[date_col].notna()][m2_col].sum())
days_mes = pd.Timestamp(year, today.month, 1).days_in_month
meta_mes = (meta_geral / days_y) * days_mes
icm_mes  = m2_mes / meta_mes * 100 if meta_mes > 0 else 0

# M² PERÍODO (21/MM a 20/MM)
cur_r = period_for_date(today)
if cur_r:
    cur_end, cur_label = cur_r
    cur_row  = tbl[tbl["_pend"] == cur_end]
    m2_per   = float(cur_row[m2_col].values[0]) if len(cur_row) else 0.0
    meta_per = float(cur_row["meta"].values[0])  if len(cur_row) else meta_geral / 12
else:
    cur_label = "–"; m2_per = 0.0; meta_per = meta_geral / 12
icm_per = m2_per / meta_per * 100 if meta_per > 0 else 0

# M² ACUMULADO / META ACUMULADA
m2_acum    = float(tbl[m2_col].sum())
meta_acum  = meta_geral * (elapsed / days_y)
icm_acum_p = m2_acum / meta_acum   * 100 if meta_acum   > 0 else 0  # vs meta proporcional
icm_geral  = m2_acum / meta_geral  * 100 if meta_geral  > 0 else 0  # vs meta anual total

# FORECAST / PROJEÇÃO
media_dia      = m2_acum / elapsed
forecast       = media_dia * days_y
nec_dia        = (meta_geral - m2_acum) / remain if remain > 0 else 0
icm_forecast   = forecast / meta_geral * 100 if meta_geral > 0 else 0

# ── HEADER ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#060d14 0%,#0e2340 55%,#060d14 100%);
  border-radius:10px;padding:12px 22px;margin-bottom:10px;
  display:flex;align-items:center;gap:18px;border:1px solid #1a2535">
  <div style="flex-shrink:0;line-height:1">
    <div style="font-size:.48rem;font-weight:700;color:#4a6278;letter-spacing:3px">CASA</div>
    <div style="font-size:1.4rem;font-weight:900;color:#c9a227;
      letter-spacing:-2px;margin-top:-3px">MANSUR</div>
    <div style="font-size:.42rem;color:#2e4258;letter-spacing:2px;margin-top:2px">
      INDICADORES M²
    </div>
  </div>
  <div style="width:1px;height:38px;background:#1a2535;flex-shrink:0"></div>
  <div style="flex:1">
    <div style="color:#e6edf3;font-size:1rem;font-weight:800;letter-spacing:.5px">
      ACOMPANHAMENTO DE M² E METAS
    </div>
    <div style="color:#2e4258;font-size:.68rem;margin-top:2px">
      Período vigente: {cur_label} &nbsp;·&nbsp; {today.strftime('%d/%m/%Y')}
    </div>
  </div>
  <div style="display:flex;gap:18px;flex-shrink:0">
    <div style="text-align:center">
      <div style="color:#c9a227;font-size:1.35rem;font-weight:900;line-height:1">{n(m2_acum)}</div>
      <div style="color:#2e4258;font-size:.55rem">m² acumulados</div>
    </div>
    <div style="text-align:center">
      <div style="color:{ic(icm_geral)};font-size:1.35rem;font-weight:900;line-height:1">{icm_geral:.1f}%</div>
      <div style="color:#2e4258;font-size:.55rem">ICM meta geral</div>
    </div>
    <div style="text-align:center">
      <div style="color:{ic(icm_forecast)};font-size:1.35rem;font-weight:900;line-height:1">{icm_forecast:.1f}%</div>
      <div style="color:#2e4258;font-size:.55rem">ICM forecast</div>
    </div>
    <div style="text-align:center">
      <div style="color:#e6edf3;font-size:1.35rem;font-weight:900;line-height:1">{n(meta_geral)}</div>
      <div style="color:#2e4258;font-size:.55rem">meta geral</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ICM DONUTS ────────────────────────────────────────────────────────────
def donut(pct, title):
    c   = ic(pct)
    cap = min(pct, 100)
    fig = go.Figure(go.Pie(
        values=[max(cap, 0.5), max(100 - cap, 0.5)],
        hole=0.72, marker_colors=[c, "#1a2535"],
        textinfo="none", hoverinfo="skip",
        showlegend=False, sort=False,
        direction="clockwise", rotation=90,
        domain=dict(x=[0.08, 0.92], y=[0.08, 0.92]),
    ))
    fig.add_annotation(text=f"<b>{pct:.1f}%</b>",
        x=0.5, y=0.56, showarrow=False,
        font=dict(size=12, color=c, family="Arial Black"),
        xanchor="center", yanchor="middle")
    fig.add_annotation(text="ICM",
        x=0.5, y=0.38, showarrow=False,
        font=dict(size=7, color="#ffffff"),
        xanchor="center", yanchor="middle")
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=9, color="#ffffff"), x=0.5),
        height=115, margin=dict(l=0, r=0, t=24, b=0),
        paper_bgcolor="#0b1520",
    )
    return fig

st.markdown('<div class="sdiv">índices de cumprimento de meta — ICM</div>', unsafe_allow_html=True)
da, db, dc, dd, de, df_ = st.columns(6)
with da: st.plotly_chart(donut(icm_geral,    "ICM META GERAL"),             use_container_width=True)
with db: st.plotly_chart(donut(icm_dia,      "ICM META DIA"),               use_container_width=True)
with dc: st.plotly_chart(donut(icm_per,      "ICM META PERÍODO"),           use_container_width=True)
with dd: st.plotly_chart(donut(icm_mes,      "ICM META MÊS"),               use_container_width=True)
with de: st.plotly_chart(donut(icm_geral,    "ICM ACUMULADO"),              use_container_width=True)
with df_: st.plotly_chart(donut(icm_forecast, "ICM FORECAST / META GERAL"), use_container_width=True)

# ── KPI CARD helper ───────────────────────────────────────────────────────
def kpi(label, value, sub="", color="#e6edf3"):
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""<div class="kpi">
      <div class="kpi-lbl">{label}</div>
      <div class="kpi-val" style="color:{color}">{value}</div>{s}
    </div>"""

# ── M² CARDS ─────────────────────────────────────────────────────────────
# M² ATUAL = M² ACUMULADO  |  M² DO PERÍODO = período vigente (21/MM-20/MM)
st.markdown('<div class="sdiv">m² realizados</div>', unsafe_allow_html=True)
r1c1,r1c2,r1c3,r1c4,r1c5,r1c6 = st.columns(6)
with r1c1: st.markdown(kpi("M²",            n(m2_acum)+" m²",   f"Total acumulado {year}"), unsafe_allow_html=True)
with r1c2: st.markdown(kpi("M² DIA",        n(m2_hoje)+" m²",   f"Meta dia: {n(meta_dia,1)} m²"), unsafe_allow_html=True)
with r1c3: st.markdown(kpi("M² ATUAL",      n(m2_acum)+" m²",   "= M² Acumulado", ic(icm_acum_p)), unsafe_allow_html=True)
with r1c4: st.markdown(kpi("M² DO MÊS",     n(m2_mes)+" m²",    today.strftime("%B/%Y")), unsafe_allow_html=True)
with r1c5: st.markdown(kpi("M² DO PERÍODO", n(m2_per)+" m²",    cur_label), unsafe_allow_html=True)
with r1c6: st.markdown(kpi("M² ACUMULADO",  n(m2_acum)+" m²",   f"Meta acum: {n(meta_acum)} m²"), unsafe_allow_html=True)

# ── META CARDS ────────────────────────────────────────────────────────────
# META ATUAL = META ACUMULADA (proporcional aos dias decorridos)
st.markdown('<div class="sdiv">metas</div>', unsafe_allow_html=True)
r2c1,r2c2,r2c3,r2c4,r2c5,r2c6 = st.columns(6)
with r2c1: st.markdown(kpi("META GERAL",      n(meta_geral)+" m²",  f"Ano {year}"), unsafe_allow_html=True)
with r2c2: st.markdown(kpi("META DIA",        n(meta_dia,1)+" m²",  f"Meta geral ÷ {days_y} dias"), unsafe_allow_html=True)
with r2c3: st.markdown(kpi("META ATUAL",      n(meta_acum)+" m²",   "= Meta Acumulada"), unsafe_allow_html=True)
with r2c4: st.markdown(kpi("META MÊS",        n(meta_mes)+" m²",    today.strftime("%B/%Y")), unsafe_allow_html=True)
with r2c5: st.markdown(kpi("META DO PERÍODO", n(meta_per)+" m²",    cur_label), unsafe_allow_html=True)
with r2c6: st.markdown(kpi("META ACUMULADA",  n(meta_acum)+" m²",   f"Proporcional {elapsed} de {days_y}d"), unsafe_allow_html=True)

# ── FORECAST CARD ─────────────────────────────────────────────────────────
st.markdown('<div class="sdiv">forecast</div>', unsafe_allow_html=True)
fc1 = st.columns([1, 2, 2])[0]
with fc1:
    st.markdown(kpi("FORECAST", n(forecast)+" m²",
        f"ICM {icm_forecast:.1f}% — {il(icm_forecast)} | {n(nec_dia,1)} m²/dia necessário",
        ic(icm_forecast)), unsafe_allow_html=True)

# ── Chart helpers ─────────────────────────────────────────────────────────
BG    = "#0b1520"
PAPER = "#060d14"
GRID  = "#1a2535"
TICK  = "#ffffff"

def clayout(title, height=260, barmode="group"):
    return dict(
        title=dict(text=f"<b>{title}</b>", font=dict(size=10, color="#ffffff")),
        height=height, margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor=PAPER, plot_bgcolor=BG, barmode=barmode,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=8, color="#ffffff")),
        xaxis=dict(showgrid=False,
            tickfont=dict(size=7, color="#ffffff"), tickangle=-35),
        yaxis=dict(showgrid=True, gridcolor=GRID,
            tickfont=dict(size=8, color="#ffffff"), tickformat=",.0f"),
        hovermode="x unified",
    )

# ── GRÁFICO M² DIÁRIO / META DIA ──────────────────────────────────────────
st.markdown('<div class="sdiv">gráficos</div>', unsafe_allow_html=True)
ch1, ch2 = st.columns(2)

with ch1:
    daily = (df[df[date_col].notna()]
        .assign(day=df[date_col].dt.normalize())
        .query(f"day >= @start_y and day <= @today")
        .groupby("day")[m2_col].sum().reset_index()
        .tail(60))
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=daily["day"], y=daily[m2_col],
        name="M² Diário", marker_color="#c9a227", opacity=0.85,
        hovertemplate="%{x|%d/%m}<br><b>%{y:,.0f} m²</b><extra></extra>"))
    fig1.add_trace(go.Scatter(x=daily["day"], y=[meta_dia]*len(daily),
        name=f"Meta/Dia ({n(meta_dia,1)})", mode="lines",
        line=dict(color="#3b82f6", width=2, dash="dot"),
        hovertemplate="Meta: <b>%{y:,.1f}</b><extra></extra>"))
    fig1.update_layout(**clayout("GRÁFICO M² DIÁRIO / META DIA"))
    fig1.update_xaxes(tickformat="%d/%m")
    st.plotly_chart(fig1, use_container_width=True)

# ── GRÁFICO M² ACUMULADO / META ACUMULADA ────────────────────────────────
with ch2:
    tbl_v = tbl.copy()
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=tbl_v["_plabel"], y=tbl_v["m2_acum_t"],
        name="M² Acumulado", marker_color="#c9a227", opacity=0.75,
        hovertemplate="%{x}<br>Acum: <b>%{y:,.0f} m²</b><extra></extra>"))
    fig2.add_trace(go.Scatter(x=tbl_v["_plabel"], y=tbl_v["meta_acum_t"],
        name="Meta Acumulada", mode="lines+markers",
        line=dict(color="#3b82f6", width=2),
        hovertemplate="Meta: <b>%{y:,.0f}</b><extra></extra>"))
    lyt2 = clayout("GRÁFICO M² ACUMULADO / META ACUMULADA (PROGRESSO)")
    fig2.update_layout(**lyt2)
    st.plotly_chart(fig2, use_container_width=True)

ch3, ch4 = st.columns(2)

# ── GRÁFICO FORECAST / M² ACUMULADO ──────────────────────────────────────
with ch3:
    completed = tbl[tbl[m2_col] > 0].copy()
    remaining = tbl[tbl[m2_col] == 0].copy()
    n_rem     = max(len(remaining), 1)
    fc_per    = (forecast - m2_acum) / n_rem

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=completed["_plabel"], y=completed[m2_col],
        name="M² Realizado", marker_color="#c9a227", opacity=0.9,
        hovertemplate="%{x}<br><b>%{y:,.0f} m²</b><extra></extra>"))
    if len(remaining):
        fig3.add_trace(go.Bar(x=remaining["_plabel"],
            y=[fc_per]*len(remaining),
            name="Forecast (projeção)", marker_color="#059669", opacity=0.5,
            hovertemplate="%{x}<br>Forecast: <b>%{y:,.0f} m²</b><extra></extra>"))
    fig3.add_trace(go.Scatter(x=tbl["_plabel"], y=tbl["meta"],
        name="Meta Período", mode="lines",
        line=dict(color="#3b82f6", width=2, dash="dot")))
    lyt3 = clayout("FORECAST / M² ACUMULADO", barmode="overlay")
    fig3.update_layout(**lyt3)
    st.plotly_chart(fig3, use_container_width=True)

# ── GRÁFICO PROJEÇÃO M² / M² ACUMULADO ───────────────────────────────────
with ch4:
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=tbl["_plabel"], y=tbl["meta_acum_t"],
        name="Meta Acumulada", mode="lines",
        line=dict(color="#3b82f6", width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,.08)"))
    completed4 = tbl[tbl[m2_col] > 0]
    if len(completed4):
        fig4.add_trace(go.Scatter(
            x=completed4["_plabel"], y=completed4["m2_acum_t"],
            name="M² Acumulado", mode="lines+markers",
            line=dict(color="#c9a227", width=2.5),
            fill="tozeroy", fillcolor="rgba(201,162,39,.12)"))
        # Linha de projeção a partir do último ponto real
        last_idx   = completed4.index[-1]
        last_acum  = float(completed4["m2_acum_t"].iloc[-1])
        rem_rows   = tbl[tbl.index >= last_idx]
        n_r        = max(len(rem_rows) - 1, 1)
        proj_y     = [last_acum + (i / n_r) * (forecast - last_acum)
                      for i in range(len(rem_rows))]
        fig4.add_trace(go.Scatter(
            x=rem_rows["_plabel"], y=proj_y,
            name="Projeção (forecast)", mode="lines",
            line=dict(color="#059669", width=2, dash="dash")))
    lyt4 = clayout("PROJEÇÃO M² / M² ACUMULADO")
    fig4.update_layout(**lyt4)
    st.plotly_chart(fig4, use_container_width=True)

# ── GRÁFICO DESEMPENHO DOS PERÍODOS ───────────────────────────────────────
st.markdown('<div class="sdiv">desempenho por período</div>', unsafe_allow_html=True)
colors5 = ["#059669" if v >= 100 else ("#d97706" if v >= 80 else "#dc2626")
           for v in tbl["icm_t"]]
fig5 = go.Figure()
fig5.add_trace(go.Bar(
    x=tbl["_plabel"], y=tbl[m2_col],
    name="M² Realizado", marker_color=colors5, opacity=0.9,
    text=[f"{v:.0f}%" if v > 0 else "" for v in tbl["icm_t"]],
    textposition="outside", textfont=dict(size=8, color="#ffffff"),
    hovertemplate="%{x}<br>M²: <b>%{y:,.0f}</b><extra></extra>"))
fig5.add_trace(go.Scatter(
    x=tbl["_plabel"], y=tbl["meta"],
    name="Meta Período", mode="lines+markers",
    line=dict(color="#3b82f6", width=2, dash="dot"),
    hovertemplate="Meta: <b>%{y:,.0f}</b><extra></extra>"))
lyt5 = clayout("DESEMPENHO POR PERÍODO — M² vs META", height=270)
lyt5["showlegend"] = True
fig5.update_layout(**lyt5)
st.plotly_chart(fig5, use_container_width=True)

# ── Sidebar — resultados (injetado após cálculos) ─────────────────────────
_fc  = ic(icm_forecast);  _fb  = ib(icm_forecast);  _fl  = il(icm_forecast)
_ac  = ic(icm_acum_p);    _al  = il(icm_acum_p)

st.sidebar.markdown(f"""
<div style="margin-top:4px">
  <div style="height:1px;background:#1a2535;margin-bottom:10px"></div>
  <p style="color:#2e4258;font-size:.62rem;font-weight:700;text-transform:uppercase;
    letter-spacing:1px;margin-bottom:8px">📊 Resultado</p>

  <div style="background:#060d14;border-radius:7px;padding:9px 11px;
    border:1px solid #1a2535;margin-bottom:5px">
    <div style="color:#2e4258;font-size:.58rem;font-weight:600;margin-bottom:4px">Acumulado</div>
    <div style="display:flex;justify-content:space-between;margin-bottom:2px">
      <span style="color:#2e4258;font-size:.58rem">M² realizado</span>
      <span style="color:#e6edf3;font-size:.75rem;font-weight:800">{n(m2_acum)} m²</span>
    </div>
    <div style="display:flex;justify-content:space-between;margin-bottom:5px">
      <span style="color:#2e4258;font-size:.58rem">Meta acumulada</span>
      <span style="color:#8da4b8;font-size:.75rem;font-weight:600">{n(meta_acum)} m²</span>
    </div>
    <div style="background:#1a2535;border-radius:99px;height:4px;overflow:hidden">
      <div style="width:{min(icm_acum_p,100):.1f}%;height:100%;
        background:{_ac};border-radius:99px"></div>
    </div>
    <div style="color:{_ac};font-size:.65rem;font-weight:800;text-align:right;margin-top:2px">
      {icm_acum_p:.1f}% — {_al}
    </div>
  </div>

  <div style="background:{_fb};border-radius:7px;padding:9px 11px;
    border:1px solid {_fc}40;margin-bottom:5px">
    <div style="color:#2e4258;font-size:.58rem;font-weight:600;margin-bottom:4px">Forecast {year}</div>
    <div style="display:flex;justify-content:space-between;margin-bottom:2px">
      <span style="color:#2e4258;font-size:.58rem">Projeção ano</span>
      <span style="color:#e6edf3;font-size:.75rem;font-weight:800">{n(forecast)} m²</span>
    </div>
    <div style="display:flex;justify-content:space-between;margin-bottom:5px">
      <span style="color:#2e4258;font-size:.58rem">Meta geral</span>
      <span style="color:#8da4b8;font-size:.75rem;font-weight:600">{n(meta_geral)} m²</span>
    </div>
    <div style="background:#1a2535;border-radius:99px;height:4px;overflow:hidden">
      <div style="width:{min(icm_forecast,100):.1f}%;height:100%;
        background:{_fc};border-radius:99px"></div>
    </div>
    <div style="color:{_fc};font-size:.65rem;font-weight:800;text-align:right;margin-top:2px">
      {icm_forecast:.1f}% — {_fl}
    </div>
  </div>

  <div style="background:#060d14;border-radius:7px;padding:8px 11px;
    border:1px solid #1a2535;text-align:center">
    <div style="color:#2e4258;font-size:.55rem">Necessário/dia p/ meta</div>
    <div style="color:#60a5fa;font-size:1rem;font-weight:900">{n(nec_dia,1)} m²/dia</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Ranking instaladores ───────────────────────────────────────────────────
if inst_col:
    st.markdown('<div class="sdiv">ranking instaladores</div>', unsafe_allow_html=True)
    ranking = (fdf.groupby(inst_col)[m2_col].sum()
               .sort_values(ascending=False).reset_index())
    ranking.columns = ["Instalador","M²"]
    ranking["M² fmt"] = ranking["M²"].apply(n)
    ranking["ICM (%)"] = (ranking["M²"] / (meta_geral / max(len(ranking),1)) * 100).round(1)
    st.dataframe(ranking[["Instalador","M² fmt","ICM (%)"]].rename(columns={"M² fmt":"M²"}),
        use_container_width=True, hide_index=True, height=min(36 * len(ranking) + 38, 600))

# ── Exportar ──────────────────────────────────────────────────────────────
st.markdown('<div class="sdiv">exportar</div>', unsafe_allow_html=True)
exp = tbl[["_plabel",m2_col,"meta","icm_t","m2_acum_t","meta_acum_t"]].copy()
exp.columns = ["Período","M² Realizado","Meta","ICM (%)","M² Acumulado","Meta Acumulada"]
csv_b = exp.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
st.download_button("⬇ Download CSV", csv_b, f"indicadores_{year}.csv",
    "text/csv", use_container_width=True)

# ── Entry point ───────────────────────────────────────────────────────────
import os, sys
if __name__ == "__main__":
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx() is None:
        os.execv(sys.executable,
            [sys.executable, "-m", "streamlit", "run", __file__] + sys.argv[1:])
