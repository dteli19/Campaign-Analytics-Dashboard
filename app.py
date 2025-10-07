# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Campaign Analytics — Portfolio", page_icon="📊", layout="wide")

# ---------------- DUMMY DATA ----------------
def build_dummy(seed=17, n_rows=6000):
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    brands = ["Brand A", "Brand B"]
    campaigns_by_brand = {"Brand A": ["Awareness", "Engagement"],
                          "Brand B": ["Retention", "New Launch"]}
    specialties = ["Cardiologist", "Oncologist", "Pediatrician", "Dermatologist",
                   "Endocrinologist", "Neurologist"]
    regions = ["N", "S", "E", "W"]

    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    hcp_pool = [f"HCP{str(i).zfill(5)}" for i in range(1000, 1500)]

    hcp_ids = rng.choice(hcp_pool, size=n_rows, replace=True)
    brand_name = rng.choice(brands, size=n_rows, replace=True)
    campaign_name = [rng.choice(campaigns_by_brand[b]) for b in brand_name]
    date_of_campaign = rng.choice(dates, size=n_rows, replace=True)
    hcp_specialty = rng.choice(specialties, size=n_rows, replace=True)
    hcp_region = rng.choice(regions, size=n_rows, replace=True, p=[0.3, 0.25, 0.25, 0.2])

    target = rng.choice([0, 1], size=n_rows, replace=True, p=[0.15, 0.85])
    reach = np.where(target == 1, rng.choice([0, 1], size=n_rows, replace=True, p=[0.32, 0.68]), 0)

    open_base = np.where(reach == 1, rng.choice([0, 1], size=n_rows, replace=True, p=[0.58, 0.42]), 0)
    open_lift = (
        (pd.Series(campaign_name).isin(["Engagement", "New Launch"]).astype(int)
         * rng.choice([0, 1], size=n_rows, p=[0.65, 0.35])) |
        (pd.Series(brand_name).eq("Brand A").astype(int)
         * rng.choice([0, 1], size=n_rows, p=[0.78, 0.22]))
    ).astype(int)
    open_ = np.where((reach == 1) & (open_base + open_lift > 0), 1, open_base)

    click_base = np.where(open_ == 1, rng.choice([0, 1], size=n_rows, replace=True, p=[0.80, 0.20]), 0)
    click_lift = (
        (pd.Series(hcp_specialty).isin(["Pediatrician", "Dermatologist"]).astype(int)
         * rng.choice([0, 1], size=n_rows, p=[0.82, 0.18]))
    ).astype(int)
    click = np.where((open_ == 1) & (click_base + click_lift > 0), 1, click_base)

    df = pd.DataFrame({
        "hcp id": hcp_ids,
        "brand name": brand_name,
        "campaign name": campaign_name,
        "date of campaign": pd.to_datetime(date_of_campaign),
        "target (1 or 0)": target.astype(int),
        "reach (1 or 0)": reach.astype(int),
        "open (1 or 0)": open_.astype(int),
        "click (1 or 0)": click.astype(int),
        "hcp specialty": hcp_specialty,
        "hcp region (N/S/E/W)": hcp_region,
    })
    return df

df = build_dummy()

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center; color:#2F5496;'>📊 Campaign Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center; color:gray;'>Portfolio Demo — Dhwani Teli</h5>", unsafe_allow_html=True)
st.write("---")

# ---------------- CONTEXT SECTIONS ----------------
with st.expander("🧩 Context & Problem Statement", expanded=True):
    st.markdown("""
**Context:**  
Two pharmaceutical brands — *Brand A* and *Brand B* — ran a total of four digital campaigns in 2024 targeting 500 healthcare professionals (HCPs).  
The goal is to evaluate how effectively each campaign moved HCPs through the marketing funnel (**Target → Reach → Open → Click**)  
and identify which segments (region or specialty) performed best.  

**Problem Statement:**  
Marketing teams need a clear view of campaign performance to:
- Measure overall engagement across campaigns  
- Compare effectiveness by brand and campaign  
- Identify audience segments driving higher engagement  
""")

# ---------------- FILTERS ----------------
st.write("---")
st.markdown("### 🔍 Filter Campaign Data")

c1, c2, c3, c4 = st.columns(4)
with c1:
    f_brand = st.multiselect("Select Brand(s)", df["brand name"].unique(), default=list(df["brand name"].unique()))
with c2:
    f_campaign = st.multiselect("Select Campaign(s)", df["campaign name"].unique(), default=list(df["campaign name"].unique()))
with c3:
    f_region = st.multiselect("Select Region(s)", df["hcp region (N/S/E/W)"].unique(), default=list(df["hcp region (N/S/E/W)"].unique()))
with c4:
    f_specialty = st.multiselect("Select Specialty(s)", df["hcp specialty"].unique(), default=list(df["hcp specialty"].unique()))

mask = (
    df["brand name"].isin(f_brand) &
    df["campaign name"].isin(f_campaign) &
    df["hcp region (N/S/E/W)"].isin(f_region) &
    df["hcp specialty"].isin(f_specialty)
)
filtered = df[mask]

# ---------------- KPI CALCULATIONS ----------------
def kpis(d):
    tgt = int(d["target (1 or 0)"].sum())
    rch = int(d["reach (1 or 0)"].sum())
    opn = int(d["open (1 or 0)"].sum())
    clk = int(d["click (1 or 0)"].sum())
    reach_rate = rch / tgt if tgt else 0
    open_rate = opn / rch if rch else 0
    ctor = clk / opn if opn else 0
    return tgt, rch, opn, clk, reach_rate, open_rate, ctor

tgt, rch, opn, clk, reach_rate, open_rate, ctor = kpis(filtered)

# ---------------- KPI CARDS ----------------
st.write("---")
st.subheader("📈 Engagement KPIs")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div style='background-color:#E8EEF9;padding:20px;border-radius:10px;text-align:center;'><h3>{tgt:,}</h3><p>Targeted HCPs</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div style='background-color:#DDEFE2;padding:20px;border-radius:10px;text-align:center;'><h3>{reach_rate:.0%}</h3><p>Reach Rate</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div style='background-color:#FFF3CD;padding:20px;border-radius:10px;text-align:center;'><h3>{open_rate:.0%}</h3><p>Open Rate</p></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div style='background-color:#F8D7DA;padding:20px;border-radius:10px;text-align:center;'><h3>{ctor:.0%}</h3><p>Click-to-Open (CTOR)</p></div>", unsafe_allow_html=True)

# ---------------- FUNNEL CHART ----------------
st.write("---")
st.subheader("🎯 Funnel Summary")
funnel_df = pd.DataFrame({
    "Stage": ["Target", "Reach", "Open", "Click"],
    "Count": [tgt, rch, opn, clk]
})
bar = (
    alt.Chart(funnel_df)
    .mark_bar(size=60, color="#4E79A7")
    .encode(x=alt.X("Stage:N", sort=["Target", "Reach", "Open", "Click"]),
            y=alt.Y("Count:Q", title="HCP Count"),
            tooltip=["Stage", "Count"])
    .properties(height=300)
)
st.altair_chart(bar, use_container_width=True)

# ---------------- MONTHLY TREND ----------------
st.subheader("📅 Monthly Engagement Trend")
trend = filtered.copy()
trend["month"] = trend["date of campaign"].dt.to_period("M").astype(str)
monthly = trend.groupby("month")[["target (1 or 0)", "reach (1 or 0)", "open (1 or 0)", "click (1 or 0)"]].sum().reset_index()
monthly_long = monthly.melt("month", var_name="Stage", value_name="Count")

line_chart = (
    alt.Chart(monthly_long)
    .mark_line(point=True)
    .encode(
        x="month:N",
        y="Count:Q",
        color="Stage:N",
        strokeDash="Stage:N",
        tooltip=["month", "Stage", "Count"]
    )
    .properties(height=350)
)
st.altair_chart(line_chart, use_container_width=True)

# ---------------- TABLE ----------------
st.subheader("📊 Funnel Detail Table")
tbl = pd.DataFrame({
    "Stage": ["Target", "Reach", "Open", "Click"],
    "Count": [tgt, rch, opn, clk],
    "Rate vs Previous": [1.0,
                         rch / tgt if tgt else np.nan,
                         opn / rch if rch else np.nan,
                         clk / opn if opn else np.nan]
})
st.dataframe(tbl.style.format({"Count": "{:,.0f}", "Rate vs Previous": "{:.0%}"}).highlight_max(subset=["Count"], color="#D0E0FF"), use_container_width=True)

st.write("---")
st.caption("💡 Demo project with dummy data for portfolio visualization — Dhwani Teli (MS Business Analytics)")
