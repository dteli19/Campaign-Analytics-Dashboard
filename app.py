# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---------------- Page Setup ----------------
st.set_page_config(page_title="Campaign Analytics — Portfolio", page_icon="📊", layout="wide")
st.title("📊 Campaign Analytics Dashboard — Portfolio App")
st.write("---")

# ---------------- Hardcoded Dummy Data (500 HCPs, 2 brands, 4 campaigns, 1 year) ----------------
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
    hcp_pool = [f"HCP{str(i).zfill(5)}" for i in range(1000, 1500)]  # exactly 500 HCPs

    hcp_ids = rng.choice(hcp_pool, size=n_rows, replace=True)
    brand_name = rng.choice(brands, size=n_rows, replace=True)
    campaign_name = [rng.choice(campaigns_by_brand[b]) for b in brand_name]
    date_of_campaign = rng.choice(dates, size=n_rows, replace=True)
    hcp_specialty = rng.choice(specialties, size=n_rows, replace=True)
    hcp_region = rng.choice(regions, size=n_rows, replace=True, p=[0.3, 0.25, 0.25, 0.2])

    # Funnel dependencies
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

# ---------------- Sections ----------------
st.header("Context")
st.markdown(
    """
Pharma brands use multi-touch campaigns to engage healthcare professionals (HCPs). Stakeholders need a simple,
repeatable view to understand how well campaigns move HCPs through the funnel (**Target → Reach → Open → Click**),
and which segments (brand, campaign, region, specialty) drive the most engagement.
"""
)

st.header("Problem Statement")
st.markdown(
    """
**Goal:** Provide a compact analytics app to:
- Evaluate campaign effectiveness over a year  
- Compare two brands and their campaigns (2 each)  
- Spot high-engagement HCP segments by region/specialty  
- Summarize results for a portfolio-ready narrative
"""
)

st.header("About the Data (Dummy)")
st.markdown(
    """
This dataset is **simulated** for demonstration:
- **500 HCPs** across **6 specialties** and **4 regions (N/S/E/W)**
- **2 brands** (*Brand A*, *Brand B*), **4 campaigns** (2 per brand)
- 1 year of touchpoints (2024) with binary funnel events: **target**, **reach**, **open**, **click**
"""
)

st.header("Actions")
st.markdown(
    """
1) Generated a realistic dummy dataset with dependencies between funnel stages.  
2) Built filters for brand, campaign, region, and specialty.  
3) Computed KPIs and constructed a quarterly engagement trend and funnel summary.
"""
)

# ---------------- Filters ----------------
st.write("---")
st.subheader("Interactive Filters")
c1, c2, c3, c4 = st.columns(4)
with c1:
    f_brands = st.multiselect("Brand", sorted(df["brand name"].unique()), default=sorted(df["brand name"].unique()))
with c2:
    # Filter campaign choices by selected brands
    possible_camps = df[df["brand name"].isin(f_brands)]["campaign name"].unique() if f_brands else []
    f_campaigns = st.multiselect("Campaign", sorted(possible_camps), default=sorted(possible_camps))
with c3:
    f_regions = st.multiselect("Region (N/S/E/W)", sorted(df["hcp region (N/S/E/W)"].unique()),
                               default=sorted(df["hcp region (N/S/E/W)"].unique()))
with c4:
    f_specs = st.multiselect("HCP Specialty", sorted(df["hcp specialty"].unique()),
                             default=sorted(df["hcp specialty"].unique()))

mask = (
    df["brand name"].isin(f_brands) &
    df["campaign name"].isin(f_campaigns if f_campaigns else df["campaign name"].unique()) &
    df["hcp region (N/S/E/W)"].isin(f_regions) &
    df["hcp specialty"].isin(f_specs)
)
df_f = df[mask].copy()

# ---------------- KPIs ----------------
def calc_kpis(d):
    tgt = int((d["target (1 or 0)"] == 1).sum())
    rch = int((d["reach (1 or 0)"] == 1).sum())
    opn = int((d["open (1 or 0)"] == 1).sum())
    clk = int((d["click (1 or 0)"] == 1).sum())
    reach_rate = (rch / tgt) if tgt else 0
    open_rate = (opn / rch) if rch else 0
    ctor = (clk / opn) if opn else 0
    return tgt, rch, opn, clk, reach_rate, open_rate, ctor

tgt, rch, opn, clk, reach_rate, open_rate, ctor = calc_kpis(df_f)

st.header("Results")
st.markdown("Key funnel metrics for the current selection:")

m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
m1.metric("Target Count", f"{tgt:,}")
m2.metric("Reach Count", f"{rch:,}")
m3.metric("Open Count", f"{opn:,}")
m4.metric("Click Count", f"{clk:,}")
m5.metric("Reach Rate", f"{reach_rate:.0%}")
m6.metric("Open Rate", f"{open_rate:.0%}")
m7.metric("Click-to-Open (CTOR)", f"{ctor:.0%}")

# ---------------- Quarterly Trend ----------------
st.markdown("#### Annual Engagement Trend (Quarterly)")
qdf = df_f.copy()
qdf["quarter"] = qdf["date of campaign"].dt.to_period("Q").astype(str)
trend = (qdf.groupby("quarter")[["target (1 or 0)", "reach (1 or 0)", "open (1 or 0)", "click (1 or 0)"]]
         .sum()
         .rename(columns={
             "target (1 or 0)": "Target",
             "reach (1 or 0)": "Reach",
             "open (1 or 0)": "Open",
             "click (1 or 0)": "Click"
         })
         .reset_index())

trend_long = trend.melt("quarter", var_name="Stage", value_name="Count")

chart = (
    alt.Chart(trend_long)
    .mark_bar()
    .encode(
        x=alt.X("quarter:N", title="Quarter", sort=["2024Q1", "2024Q2", "2024Q3", "2024Q4"]),
        y=alt.Y("Count:Q"),
        color="Stage:N",
        column=alt.Column("Stage:N", header=alt.Header(labelOrient="bottom", title=""))
    )
    .properties(height=250)
)
st.altair_chart(chart, use_container_width=True)

# ---------------- Funnel Summary Table ----------------
st.markdown("#### Funnel Summary")
funnel_tbl = pd.DataFrame({
    "Stage": ["Target", "Reach", "Open", "Click"],
    "Count": [tgt, rch, opn, clk],
    "Rate vs Previous": [
        1.0,
        (rch / tgt) if tgt else np.nan,
        (opn / rch) if rch else np.nan,
        (clk / opn) if opn else np.nan
    ]
})
st.dataframe(funnel_tbl.style.format({"Count": "{:,.0f}", "Rate vs Previous": "{:.0%}"}), use_container_width=True)

# ---------------- Closing Note ----------------
st.caption(
    "Demo with dummy data. For production, connect to CRM/marketing platforms and schedule refreshes in Power BI/Streamlit."
)
