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

# --- KPI CALCULATIONS BASED ON UNIQUE HCPs ---
def unique_kpis(d):
    # Unique HCPs at each funnel stage
    tgt_hcps = d.loc[d["target (1 or 0)"] == 1, "hcp id"].nunique()
    rch_hcps = d.loc[d["reach (1 or 0)"] == 1, "hcp id"].nunique()
    opn_hcps = d.loc[d["open (1 or 0)"] == 1, "hcp id"].nunique()
    clk_hcps = d.loc[d["click (1 or 0)"] == 1, "hcp id"].nunique()

    # Funnel metrics
    reach_rate = rch_hcps / tgt_hcps if tgt_hcps else 0
    open_rate = opn_hcps / rch_hcps if rch_hcps else 0
    ctor = clk_hcps / opn_hcps if opn_hcps else 0

    return tgt_hcps, rch_hcps, opn_hcps, clk_hcps, reach_rate, open_rate, ctor


tgt_hcps, rch_hcps, opn_hcps, clk_hcps, reach_rate, open_rate, ctor = unique_kpis(filtered)

# --- KPI CARDS (Refreshed with unique counts) ---
st.write("---")
st.subheader("📈 Unique HCP Engagement KPIs")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div style='background-color:#E8EEF9;padding:20px;border-radius:10px;text-align:center;'><h3>{tgt_hcps:,}</h3><p>Targeted HCPs</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div style='background-color:#DDEFE2;padding:20px;border-radius:10px;text-align:center;'><h3>{reach_rate:.0%}</h3><p>Reach Rate</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div style='background-color:#FFF3CD;padding:20px;border-radius:10px;text-align:center;'><h3>{open_rate:.0%}</h3><p>Open Rate</p></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div style='background-color:#F8D7DA;padding:20px;border-radius:10px;text-align:center;'><h3>{ctor:.0%}</h3><p>Click-to-Open (CTOR)</p></div>", unsafe_allow_html=True)

# ---------------- MONTHLY TREND (Unique HCPs) ----------------
st.write("---")
st.subheader("📅 Monthly Engagement Trend (Unique HCPs)")

# Create month column
trend = filtered.copy()
trend["month"] = trend["date of campaign"].dt.to_period("M").astype(str)

# Calculate unique HCPs for each stage per month
monthly_unique = (
    trend.groupby("month")
    .agg({
        "hcp id": "nunique",
        "target (1 or 0)": lambda x: trend.loc[x.index[x == 1], "hcp id"].nunique(),
        "reach (1 or 0)": lambda x: trend.loc[x.index[x == 1], "hcp id"].nunique(),
        "open (1 or 0)": lambda x: trend.loc[x.index[x == 1], "hcp id"].nunique(),
        "click (1 or 0)": lambda x: trend.loc[x.index[x == 1], "hcp id"].nunique()
    })
    .rename(columns={
        "hcp id": "Total HCPs",
        "target (1 or 0)": "Target",
        "reach (1 or 0)": "Reach",
        "open (1 or 0)": "Open",
        "click (1 or 0)": "Click"
    })
    .reset_index()
)

# Melt data for Altair
monthly_long = monthly_unique.melt("month", var_name="Stage", value_name="Unique HCPs")

# Create line chart
trend_chart = (
    alt.Chart(monthly_long)
    .mark_line(point=True)
    .encode(
        x=alt.X("month:N", title="Month", sort=None),
        y=alt.Y("Unique HCPs:Q", title="Unique HCP Count"),
        color=alt.Color("Stage:N", title="Stage"),
        tooltip=["month", "Stage", "Unique HCPs"]
    )
    .properties(height=350)
    .configure_axis(labelFontSize=12, titleFontSize=13)
)

st.altair_chart(trend_chart, use_container_width=True)

st.caption("Trend shows unique HCP engagement growth across months by funnel stage.")


# --- FUNNEL BAR CHART (Unique HCPs per stage) ---
st.write("---")
st.subheader("🎯 Funnel Summary")

funnel_df = pd.DataFrame({
    "Stage": ["Target", "Reach", "Open", "Click"],
    "Unique HCPs": [tgt_hcps, rch_hcps, opn_hcps, clk_hcps]
})

bar = (
    alt.Chart(funnel_df)
    .mark_bar(size=70, color="#4E79A7")
    .encode(
        x=alt.X("Stage:N", sort=["Target", "Reach", "Open", "Click"], title="Funnel Stage"),
        y=alt.Y("Unique HCPs:Q", title="Unique HCP Count"),
        tooltip=["Stage", "Unique HCPs"]
    )
    .properties(height=350)
)
st.altair_chart(bar, use_container_width=True)

# --- TABLE OF UNIQUE HCP FUNNEL RATES ---
st.subheader("📊 Funnel Detail Table")

tbl = pd.DataFrame({
    "Stage": ["Target", "Reach", "Open", "Click"],
    "Unique HCPs": [tgt_hcps, rch_hcps, opn_hcps, clk_hcps],
    "Rate vs Previous Stage": [
        1.0,
        rch_hcps / tgt_hcps if tgt_hcps else np.nan,
        opn_hcps / rch_hcps if rch_hcps else np.nan,
        clk_hcps / opn_hcps if opn_hcps else np.nan
    ]
})

st.dataframe(
    tbl.style
    .format({"Unique HCPs": "{:,.0f}", "Rate vs Previous Stage": "{:.0%}"})
    .highlight_max(subset=["Unique HCPs"], color="#CFE2F3"),
    use_container_width=True
)

# ---------------- SCREENSHOTS SECTION ----------------
st.write("---")
st.header("📸 Dashboard Screenshots")

st.markdown("""
Below are sample snapshots from this portfolio dashboard illustrating:
- The **Overview KPIs**  
- The **Funnel Summary (Unique HCP Counts)**  
""")

col1, col2 = st.columns(2)
with col1:
    st.image("Overview.png", caption="Overview Page")
    
with col2:
    st.image("Trend.png", caption="Annual Trend")
