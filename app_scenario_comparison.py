"""
Bond Risk AI Agent — Zetheta Project
Run from your project environment:
    pip install streamlit pandas plotly
    streamlit run app.py

Expected data files:
- bond_portfolio_data.csv
- monte_carlo_scenarios.csv
- yield_curve_history.csv

The app searches the project folder and common subfolders for these CSV files.
All outputs are analytical estimates based on the supplied project data, not investment advice.
"""
from pathlib import Path
import re
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Bond Risk AI Agent", page_icon="📊", layout="wide")

st.title("📊 Bond Risk AI Agent")
st.caption("Bond portfolio analytics • Yield-shock sensitivity • Monte Carlo risk • Yield curve insights")

# ---------- Data loading ----------
def find_csv(filename):
    """Find a data file without relying on a hard-coded absolute path."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / filename,
        here.parent / "02_Raw_Data" / filename,
        here / "02_Raw_Data" / filename,
        here.parent / filename,
    ]
    for p in candidates:
        if p.exists():
            return p
    # Search a few project subfolders, excluding virtual environments.
    for base in [here, here.parent]:
        if base.exists():
            for p in base.rglob(filename):
                if ".venv" not in str(p) and "site-packages" not in str(p):
                    return p
    return None

@st.cache_data
def load_csv(path_string):
    return pd.read_csv(path_string)

portfolio_path = find_csv("bond_portfolio_data.csv")
mc_path = find_csv("monte_carlo_scenarios.csv")
curve_path = find_csv("yield_curve_history.csv")

# Allow users to upload files if automatic discovery did not find them.
with st.sidebar:
    st.header("Data files")
    st.write("Automatic file discovery is used first. Upload a CSV only if a file is not found.")
    portfolio_upload = st.file_uploader("Bond portfolio CSV", type="csv")
    mc_upload = st.file_uploader("Monte Carlo scenarios CSV", type="csv")
    curve_upload = st.file_uploader("Yield curve history CSV", type="csv")

def load_or_upload(path, upload):
    if upload is not None:
        return pd.read_csv(upload)
    if path is not None:
        return load_csv(str(path))
    return None

portfolio = load_or_upload(portfolio_path, portfolio_upload)
scenarios = load_or_upload(mc_path, mc_upload)
curve = load_or_upload(curve_path, curve_upload)

if portfolio is None:
    st.error("Bond portfolio CSV was not found. Place bond_portfolio_data.csv in 02_Raw_Data or upload it in the sidebar.")
    st.stop()

# Normalize numeric columns where present.
for col in portfolio.columns:
    if col in {
        "FaceValue", "CouponRate", "YearsToMaturity", "YieldToMaturity", "CleanPrice",
        "DirtyPrice", "MacaulayDuration", "ModifiedDuration", "Convexity",
        "DV01_Per100Face", "EffectiveDuration", "EffectiveConvexity", "Quantity",
        "MarketValue_INR", "PortfolioWeight", "SpreadOverBenchmark_bps"
    }:
        portfolio[col] = pd.to_numeric(portfolio[col], errors="coerce")

required = ["BondID", "YieldToMaturity", "CleanPrice"]
missing = [c for c in required if c not in portfolio.columns]
if missing:
    st.error(f"Portfolio file is missing required columns: {', '.join(missing)}")
    st.stop()

# ---------- Sidebar filters ----------
with st.sidebar:
    st.header("Portfolio filters")
    rating_values = sorted(portfolio["CreditRating"].dropna().astype(str).unique()) if "CreditRating" in portfolio else []
    selected_ratings = st.multiselect("Credit rating", rating_values, default=rating_values)
    currency_values = sorted(portfolio["Currency"].dropna().astype(str).unique()) if "Currency" in portfolio else []
    selected_currencies = st.multiselect("Currency", currency_values, default=currency_values)

filtered = portfolio.copy()
if "CreditRating" in filtered and selected_ratings:
    filtered = filtered[filtered["CreditRating"].astype(str).isin(selected_ratings)]
if "Currency" in filtered and selected_currencies:
    filtered = filtered[filtered["Currency"].astype(str).isin(selected_currencies)]

if filtered.empty:
    st.warning("No bonds match the selected filters. Adjust the sidebar filters.")
    st.stop()

# ---------- KPI row ----------
def safe_sum(df, col):
    return float(df[col].fillna(0).sum()) if col in df.columns else 0.0

def safe_mean(df, col):
    return float(df[col].dropna().mean()) if col in df.columns and df[col].notna().any() else 0.0

total_mv = safe_sum(filtered, "MarketValue_INR")
avg_duration = safe_mean(filtered, "ModifiedDuration")
avg_convexity = safe_mean(filtered, "Convexity")
avg_ytm = safe_mean(filtered, "YieldToMaturity")
portfolio_dv01 = safe_sum(filtered, "DV01_Per100Face")  # per-100-face metric; not total portfolio DV01

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Bonds", f"{len(filtered):,}")
c2.metric("Market value (INR)", f"₹{total_mv:,.0f}" if total_mv else "Not available")
c3.metric("Avg. YTM", f"{avg_ytm:.2%}")
c4.metric("Avg. modified duration", f"{avg_duration:.2f} years")
c5.metric("Avg. convexity", f"{avg_convexity:.2f}")

tab_chat, tab_sensitivity, tab_mc, tab_scenarios, tab_curve, tab_data = st.tabs([
    "Ask the Risk Agent", "Yield Sensitivity", "Monte Carlo Risk",
    "Scenario Comparison", "Yield Curve", "Portfolio Data"
])

# ---------- Analytical response engine ----------
def build_answer(question, df):
    q = question.lower().strip()
    mv = safe_sum(df, "MarketValue_INR")
    dur = safe_mean(df, "ModifiedDuration")
    conv = safe_mean(df, "Convexity")
    ytm = safe_mean(df, "YieldToMaturity")

    if any(k in q for k in ["duration", "interest-rate sensitivity", "rate sensitivity"]):
        return (
            f"The filtered portfolio contains {len(df):,} bonds. Its simple average modified duration is "
            f"{dur:.2f} years. A duration of this size indicates meaningful sensitivity to yield changes. "
            "For a portfolio-level estimate, use market-value-weighted duration rather than a simple average."
        )
    if "convex" in q:
        return (
            f"The simple average convexity is {conv:.2f}. Convexity adds a second-order correction to the "
            "duration estimate, especially for larger yield changes. Callable bonds may require effective "
            "duration/convexity because embedded options can change the price-yield relationship."
        )
    if "var" in q or "cvar" in q or "expected shortfall" in q or "monte carlo" in q:
        if scenarios is None or "PnL_Total_INR" not in scenarios.columns:
            return "The Monte Carlo CSV is not available or does not contain PnL_Total_INR. Upload the scenario CSV in the sidebar."
        pnl = pd.to_numeric(scenarios["PnL_Total_INR"], errors="coerce").dropna()
        if pnl.empty:
            return "The scenario P&L column contains no usable numeric values."
        loss = -pnl
        var95 = max(0.0, float(loss.quantile(0.95)))
        tail = loss[loss >= loss.quantile(0.95)]
        cvar95 = max(0.0, float(tail.mean())) if not tail.empty else var95
        return (
            f"From {len(pnl):,} supplied scenarios, the empirical 95% loss VaR is approximately ₹{var95:,.0f} "
            f"and 95% Expected Shortfall/CVaR is approximately ₹{cvar95:,.0f}. These are calculated from "
            "the supplied scenario P&L distribution; confirm whether positive P&L means gains in your source data."
        )
    if any(k in q for k in ["yield", "ytm", "coupon"]):
        return f"The simple average yield to maturity for the filtered portfolio is {ytm:.2%}. Yield to maturity is not the same as the coupon rate."
    if any(k in q for k in ["top bond", "highest duration", "longest duration"]):
        if "ModifiedDuration" in df.columns:
            cols = [c for c in ["BondID", "Issuer", "CreditRating", "YearsToMaturity", "ModifiedDuration", "Convexity"] if c in df.columns]
            top = df.sort_values("ModifiedDuration", ascending=False)[cols].head(5)
            return "The bonds with the highest modified duration in the current filter are:\n\n" + top.to_string(index=False)
        return "ModifiedDuration is not available in the portfolio file."
    if "market value" in q or "portfolio value" in q or "value" in q:
        return f"The sum of MarketValue_INR for the filtered portfolio is ₹{mv:,.0f}."
    return (
        "I can answer questions about duration, convexity, yield/YTM, market value, the highest-duration bonds, "
        "and Monte Carlo VaR/CVaR. Try: 'What is the duration risk?', 'What happens if yields rise 100 bps?', "
        "or 'Show Monte Carlo VaR and CVaR'."
    )

with tab_chat:
    st.subheader("Ask a bond-risk question")
    st.write("This first version uses a transparent rule-based response engine over your project data. It does not call an external LLM API.")
    question = st.text_input(
        "Your question",
        placeholder="Example: What happens if yields rise by 100 bps?"
    )
    if st.button("Analyze question", type="primary"):
        if question.strip():
            shock_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:bps|bp|basis points)", question.lower())
            if shock_match and any(word in question.lower() for word in ["yield", "rate", "rise", "fall", "increase", "decrease", "shock"]):
                bps = float(shock_match.group(1))
                dy = bps / 10000
                w = filtered["MarketValue_INR"] if "MarketValue_INR" in filtered.columns else pd.Series(1.0, index=filtered.index)
                if "ModifiedDuration" in filtered.columns and "Convexity" in filtered.columns and "MarketValue_INR" in filtered.columns:
                    dur_eff = (-filtered["ModifiedDuration"].fillna(0) * dy * w).sum()
                    conv_eff = (0.5 * filtered["Convexity"].fillna(0) * (dy ** 2) * w).sum()
                    pnl = dur_eff + conv_eff
                    st.markdown(f"**Scenario:** yield shift {bps:+.1f} bps")
                    a, b, c = st.columns(3)
                    a.metric("Duration effect", f"₹{dur_eff:,.0f}")
                    b.metric("Convexity effect", f"₹{conv_eff:,.0f}")
                    c.metric("Estimated total P&L", f"₹{pnl:,.0f}")
                    st.caption("Estimate uses each bond's ModifiedDuration, Convexity and MarketValue_INR. It is a duration-convexity approximation, not full repricing.")
                else:
                    st.info("The required duration, convexity, or market-value columns are unavailable.")
            else:
                st.write(build_answer(question, filtered))
        else:
            st.warning("Enter a question first.")

with tab_sensitivity:
    st.subheader("Parallel yield-shock analysis")
    shock_bps = st.slider("Yield change (basis points)", min_value=-300, max_value=300, value=100, step=25)
    dy = shock_bps / 10000
    if all(c in filtered.columns for c in ["ModifiedDuration", "Convexity", "MarketValue_INR"]):
        detail = filtered.copy()
        detail["DurationEffect_INR"] = -detail["ModifiedDuration"].fillna(0) * dy * detail["MarketValue_INR"].fillna(0)
        detail["ConvexityEffect_INR"] = 0.5 * detail["Convexity"].fillna(0) * (dy ** 2) * detail["MarketValue_INR"].fillna(0)
        detail["EstimatedPnL_INR"] = detail["DurationEffect_INR"] + detail["ConvexityEffect_INR"]
        d1, d2, d3 = st.columns(3)
        d1.metric("Duration effect", f"₹{detail['DurationEffect_INR'].sum():,.0f}")
        d2.metric("Convexity effect", f"₹{detail['ConvexityEffect_INR'].sum():,.0f}")
        d3.metric("Estimated total P&L", f"₹{detail['EstimatedPnL_INR'].sum():,.0f}")
        plot_cols = [c for c in ["BondID", "DurationEffect_INR", "ConvexityEffect_INR", "EstimatedPnL_INR"] if c in detail.columns]
        st.dataframe(detail[plot_cols].sort_values("EstimatedPnL_INR").head(20), use_container_width=True)
        st.download_button("Download bond-level sensitivity CSV", detail.to_csv(index=False).encode("utf-8"), "bond_sensitivity_results.csv", "text/csv")
    else:
        st.warning("Sensitivity requires ModifiedDuration, Convexity and MarketValue_INR columns.")

with tab_mc:
    st.subheader("Monte Carlo scenario risk")
    if scenarios is None:
        st.warning("Monte Carlo scenario file not found. Put monte_carlo_scenarios.csv in 02_Raw_Data or upload it in the sidebar.")
    elif "PnL_Total_INR" not in scenarios.columns:
        st.error("Scenario file must contain PnL_Total_INR.")
    else:
        sc = scenarios.copy()
        sc["PnL_Total_INR"] = pd.to_numeric(sc["PnL_Total_INR"], errors="coerce")
        sc = sc.dropna(subset=["PnL_Total_INR"])
        # The source brief uses P&L, where negative values are losses. VaR is shown as a positive loss amount.
        losses = -sc["PnL_Total_INR"]
        q95 = losses.quantile(0.95)
        q99 = losses.quantile(0.99)
        cvar95 = losses[losses >= q95].mean()
        m1, m2, m3 = st.columns(3)
        m1.metric("Empirical 95% loss VaR", f"₹{max(0, q95):,.0f}")
        m2.metric("Empirical 99% loss VaR", f"₹{max(0, q99):,.0f}")
        m3.metric("Empirical 95% CVaR", f"₹{max(0, cvar95):,.0f}")
        st.caption("Loss is defined as negative P&L. If your source file uses a different sign convention, verify this interpretation.")
        st.plotly_chart(px.histogram(sc, x="PnL_Total_INR", nbins=40, title="Monte Carlo total P&L distribution"), use_container_width=True)
        show_cols = [c for c in ["ScenarioID", "ParallelShift_bps", "TwistFactor_bps", "ButterflyFactor_bps", "PnL_Total_INR", "PnL_Pct"] if c in sc.columns]
        st.dataframe(sc[show_cols].head(100), use_container_width=True)

with tab_scenarios:
    st.subheader("Portfolio risk scenario comparison")
    st.write(
        "Compare estimated portfolio P&L under parallel yield shifts. "
        "These are duration-convexity approximations, not full bond repricing."
    )
    scenario_specs = [
        ("Normal market", 25),
        ("Stress market", 100),
        ("Crisis market", 200),
    ]

    needed = ["ModifiedDuration", "Convexity", "MarketValue_INR"]
    if not all(c in filtered.columns for c in needed):
        st.warning(
            "Scenario comparison requires ModifiedDuration, Convexity, "
            "and MarketValue_INR columns in the portfolio CSV."
        )
    else:
        scenario_rows = []
        for label, bps in scenario_specs:
            dy_scenario = bps / 10000
            market_values = pd.to_numeric(
                filtered["MarketValue_INR"], errors="coerce"
            ).fillna(0)
            durations = pd.to_numeric(
                filtered["ModifiedDuration"], errors="coerce"
            ).fillna(0)
            convexities = pd.to_numeric(
                filtered["Convexity"], errors="coerce"
            ).fillna(0)

            duration_effect = float(
                (-durations * dy_scenario * market_values).sum()
            )
            convexity_effect = float(
                (0.5 * convexities * (dy_scenario ** 2) * market_values).sum()
            )
            total_pnl = duration_effect + convexity_effect

            scenario_rows.append({
                "Scenario": label,
                "Yield shift (bps)": bps,
                "Duration effect (INR)": duration_effect,
                "Convexity effect (INR)": convexity_effect,
                "Estimated total P&L (INR)": total_pnl,
            })

        scenario_results = pd.DataFrame(scenario_rows)
        st.dataframe(
            scenario_results.style.format({
                "Duration effect (INR)": "₹{:,.0f}",
                "Convexity effect (INR)": "₹{:,.0f}",
                "Estimated total P&L (INR)": "₹{:,.0f}",
            }),
            use_container_width=True,
        )
        st.plotly_chart(
            px.bar(
                scenario_results,
                x="Scenario",
                y="Estimated total P&L (INR)",
                title="Estimated portfolio P&L by yield-shock scenario",
                hover_data=["Yield shift (bps)", "Duration effect (INR)", "Convexity effect (INR)"],
            ),
            use_container_width=True,
        )
        st.download_button(
            "Download scenario comparison CSV",
            scenario_results.to_csv(index=False).encode("utf-8"),
            "bond_risk_scenario_comparison.csv",
            "text/csv",
        )
        st.caption(
            "Assumes a parallel yield shift and uses each bond's modified duration, "
            "convexity, and market value. Validate against your Excel/Python outputs "
            "before using these estimates in the final submission."
        )

with tab_curve:
    st.subheader("Yield curve history")
    if curve is None:
        st.warning("Yield curve history file not found. Put yield_curve_history.csv in 02_Raw_Data or upload it in the sidebar.")
    elif all(c in curve.columns for c in ["CurveDate", "Tenor_Years", "Yield"]):
        cc = curve.copy()
        cc["CurveDate"] = pd.to_datetime(cc["CurveDate"], errors="coerce")
        cc["Tenor_Years"] = pd.to_numeric(cc["Tenor_Years"], errors="coerce")
        cc["Yield"] = pd.to_numeric(cc["Yield"], errors="coerce")
        currencies = sorted(cc["Currency"].dropna().astype(str).unique()) if "Currency" in cc else []
        selected_currency = st.selectbox("Currency", currencies, index=currencies.index("INR") if "INR" in currencies else 0) if currencies else None
        if selected_currency and "Currency" in cc:
            cc = cc[cc["Currency"].astype(str) == selected_currency]
        dates = sorted(cc["CurveDate"].dropna().unique())
        if dates:
            latest_date = st.selectbox("Curve date", dates, index=len(dates)-1, format_func=lambda x: pd.Timestamp(x).strftime("%Y-%m-%d"))
            curve_day = cc[cc["CurveDate"] == latest_date].sort_values("Tenor_Years")
            st.plotly_chart(px.line(curve_day, x="Tenor_Years", y="Yield", markers=True, title=f"Yield curve — {pd.Timestamp(latest_date).strftime('%Y-%m-%d')}"), use_container_width=True)
            st.dataframe(curve_day, use_container_width=True)
    else:
        st.error("Yield curve CSV must contain CurveDate, Tenor_Years and Yield.")

with tab_data:
    st.subheader("Filtered portfolio records")
    st.dataframe(filtered, use_container_width=True)
    st.download_button("Download filtered portfolio CSV", filtered.to_csv(index=False).encode("utf-8"), "filtered_bond_portfolio.csv", "text/csv")

st.divider()
st.caption("Model limitation: this app provides analytical estimates from supplied CSVs. Validate financial calculations independently before relying on them.")
