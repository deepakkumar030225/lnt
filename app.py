import streamlit as st
import pandas as pd
import numpy as np
import itertools
import json
import os
import random
import copy
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import requests
from typing import Dict, List

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Precast AI Optimizer",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://mourncrow-lnt2.hf.space")

# ─────────────────────────────────────────────
# API CLIENT
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to AI backend…")
def check_api_health():
    """Check if the API backend is healthy and get metadata"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        health = response.json()
        
        # Get metadata
        meta_response = requests.get(f"{API_BASE_URL}/meta", timeout=10)
        meta_response.raise_for_status()
        meta = meta_response.json()
        
        return True, meta, None
    except requests.exceptions.Timeout:
        return False, None, f"Backend timeout. The API at {API_BASE_URL} is not responding."
    except requests.exceptions.ConnectionError:
        return False, None, f"Cannot connect to API backend at {API_BASE_URL}. Backend may be offline."
    except Exception as e:
        return False, None, str(e)


# Initialize with defaults in case backend is temporarily unavailable
features_ordered = []
numerical_cols = []
categorical_cols = []

# Try to connect to backend (non-blocking initialization)
try:
    api_healthy, meta, api_error = check_api_health()
    
    if api_healthy and meta:
        features_ordered = meta.get("features", [])
        numerical_cols = meta.get("numerical_cols", [])
        categorical_cols = meta.get("categorical_cols", [])
    else:
        # Show warning but allow app to continue
        st.warning(f"⚠️ Backend API connection issue: {api_error}")
        st.info(
            f"""**Backend API:** {API_BASE_URL}
            
The app will show limited functionality until the backend is available.
Check that the backend is running and accessible.
            """
        )
except Exception as e:
    st.error(f"Unexpected error during initialization: {str(e)}")
    st.info("The app may have limited functionality. Please refresh the page.")


# ─────────────────────────────────────────────
# CORE INFERENCE HELPERS - API CLIENT
# ─────────────────────────────────────────────
def evaluate_single(inputs: dict) -> dict | None:
    """Run model inference on a single configuration via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/single",
            json=inputs,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            **inputs,
            "Demould_Time_hr": result["Demould_Time_hr"],
            "Cycle_Time_hr": result["Cycle_Time_hr"],
            "Total_Cost_INR": result["Total_Cost_INR"],
        }
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def batch_evaluate(rows: list[dict]) -> pd.DataFrame:
    """Vectorised batch inference via API."""
    if not rows:
        return pd.DataFrame()
    
    try:
        # Send batch request to API
        response = requests.post(
            f"{API_BASE_URL}/predict/batch",
            json={"inputs": rows},
            timeout=120  # Longer timeout for batch requests
        )
        response.raise_for_status()
        batch_result = response.json()
        
        # Convert results to DataFrame
        results_list = []
        for result in batch_result["results"]:
            row_data = result["input_params"].copy()
            row_data["Demould_Time_hr"] = result["Demould_Time_hr"]
            row_data["Cycle_Time_hr"] = result["Cycle_Time_hr"]
            row_data["Total_Cost_INR"] = result["Total_Cost_INR"]
            results_list.append(row_data)
        
        return pd.DataFrame(results_list)
    
    except Exception as e:
        st.error(f"Batch API Error: {str(e)}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
# MULTI-VALUE INPUT PARSER
# ─────────────────────────────────────────────
def _parse_nums(text: str, cast=float, fallback: list | None = None) -> list:
    """Parse a comma-separated string into a list of numbers."""
    result = []
    for tok in text.split(","):
        tok = tok.strip()
        if tok:
            try:
                result.append(cast(tok))
            except ValueError:
                pass
    return result if result else (fallback or [])


# ─────────────────────────────────────────────
# SCORING & PARETO
# ─────────────────────────────────────────────
def score_df(df: pd.DataFrame, w_time: float = 0.5, w_cost: float = 0.5) -> pd.DataFrame:
    df = df.copy()
    t_range = df["Cycle_Time_hr"].max() - df["Cycle_Time_hr"].min() or 1
    c_range = df["Total_Cost_INR"].max() - df["Total_Cost_INR"].min() or 1
    df["Norm_Time"] = (df["Cycle_Time_hr"] - df["Cycle_Time_hr"].min()) / t_range
    df["Norm_Cost"] = (df["Total_Cost_INR"] - df["Total_Cost_INR"].min()) / c_range
    df["Score"] = w_time * df["Norm_Time"] + w_cost * df["Norm_Cost"]
    return df.sort_values("Score")


def pareto_front(df: pd.DataFrame) -> pd.DataFrame:
    pop = df.sort_values("Cycle_Time_hr")
    front, best_cost = [], float("inf")
    for _, row in pop.iterrows():
        if row["Total_Cost_INR"] < best_cost:
            front.append(row)
            best_cost = row["Total_Cost_INR"]
    return pd.DataFrame(front)


# ─────────────────────────────────────────────
# SOP GENERATOR
# ─────────────────────────────────────────────
def generate_sop(row: pd.Series) -> str:
    curing = str(row.get("Curing_method", "N/A")).upper()
    return f"""
### 🏗️ PRECAST PRODUCTION SOP — {curing} CURING

**1 · MIX DESIGN**
- Cement Type: **{row.get('Cement_type', 'N/A')}**
- Cement Content: **{row.get('Cement_content_kgm3', 'N/A')} kg/m³**
- W/C Ratio: **{row.get('Water_cement_ratio', 'N/A')}**
- Fly-Ash: **{row.get('Flyash_percent', 0)} %**

**2 · CASTING & SETTING**
- Clean mould ({row.get('Cleaning_time_min', 15)} min) → Reset ({row.get('Reset_time_min', 10)} min)
- Pour, vibrate and finish; allow ≥ 2 h initial set before curing.

**3 · CURING PROTOCOL**
- Method: **{curing}**
- Peak Temperature: **{row.get('Steam_temp_C', 'Ambient')} °C**
- Duration at Peak: **{row.get('Steam_duration_hr', 'N/A')} h**
- Chamber Humidity: **{row.get('Chamber_humidity_pct', 'N/A')} %**

**4 · DEMOULDING**
- Expected Demould Time: **{row.get('Demould_Time_hr', 0):.1f} h**
- Total Cycle Time: **{row.get('Cycle_Time_hr', 0):.1f} h**
- Estimated Cost: **₹ {row.get('Total_Cost_INR', 0):,.0f}**

⚠️ **QC CHECK** — Verify rebound hammer ≥ {row.get('Target_grade_MPa', 35)} MPa before lifting.
"""


# ─────────────────────────────────────────────
# ── SIDEBAR ──────────────────────────────────
# ─────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/factory.png",
        width=60,
    )
    st.title("Yard Configuration")

    st.subheader("🌤 Site Conditions (sweep values)")
    st.caption("Enter comma-separated values. All combinations will be evaluated.")
    ambient_temp_input = st.text_input("Ambient Temp (°C)  [10–45]", "30")
    humidity_input = st.text_input("Relative Humidity (%)  [20–90]", "60")
    wind_speed_input = st.text_input("Wind Speed (m/s)  [0.0–10.0]", "2.0")
    season_sel = st.multiselect("Season", ["summer", "winter", "monsoon", "mild"], default=["summer"])
    daytime_hrs_input = st.text_input("Daytime Hours  [6–16]", "12")

    st.subheader("🧪 Mix Design (sweep values)")
    st.caption("Enter comma-separated values. All combinations will be evaluated.")
    cement_types_sel = st.multiselect("Cement Type", ["OPC", "PPC", "PSC"], default=["OPC"])
    cement_qty_input = st.text_input("Cement Content (kg/m³)  [300–450]", "300, 350, 380, 400")
    wc_input = st.text_input("W/C Ratio  [0.30–0.55]", "0.30, 0.35")
    flyash_input = st.text_input("Fly-Ash (%)  [0–30]", "0, 10, 20")
    target_grade_input = st.text_input("Target Grade (MPa)  [20–50]", "40")

    st.subheader("⚙️ Operational (sweep values)")
    st.caption("Enter comma-separated values. All combinations will be evaluated.")
    moulds_input = st.text_input("No. of Moulds  [1–30]", "10,15")
    cleaning_time_input = st.text_input("Cleaning Time (min)  [5–60]", "20")
    reset_time_input = st.text_input("Reset Time (min)  [5–60]", "15")
    equip_downtime_input = st.text_input("Equipment Downtime (min)  [0–120]", "10")
    energy_cost_input = st.text_input("Energy Cost (₹/kWh)  [5.0–20.0]", "10.0")
    early_strength_input = st.text_input("Early Strength Req. (MPa)  [10.0–40.0]", "20.0")

    st.subheader("🔥 Curing Strategy (sweep values)")
    st.caption("Enter comma-separated values. All combinations will be evaluated.")
    curing_methods_sel = st.multiselect("Curing Method(s)", ["ambient", "steam", "hot_air"], default=["steam"])
    _need_steam = any(m in curing_methods_sel for m in ("steam", "hot_air"))
    steam_temp_input = st.text_input("Curing Temperature (°C)  [40–80]", "55, 60, 70", disabled=not _need_steam)
    steam_dur_input = st.text_input("Curing Duration (h)  [2–14]", "4, 6, 8", disabled=not _need_steam)
    chamber_humidity_input = st.text_input("Chamber Humidity (%)  [40–100]", "80")
    start_delay_input = st.text_input("Curing Start Delay (h)  [0–8]", "2")

    st.subheader("⚖️ Optimiser Weights")
    w_time = st.number_input("Weight — Time", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    w_cost = 1.0 - w_time
    st.caption(f"Weight — Cost: **{w_cost:.2f}**")

    run_optim = st.button("✨ Run Optimiser", use_container_width=True, type="primary")

# ─────────────────────────────────────────────
# PARSE MULTI-VALUE SIDEBAR INPUTS
# ─────────────────────────────────────────────
# Site conditions
at_list  = _parse_nums(ambient_temp_input, int,   [30])
hum_list = _parse_nums(humidity_input,     int,   [60])
ws_list  = _parse_nums(wind_speed_input,   float, [2.0])
season_list  = season_sel or ["summer"]
dh_list  = _parse_nums(daytime_hrs_input,  int,   [12])

# Mix design
cmt_types = cement_types_sel or ["OPC"]
cmt_list  = _parse_nums(cement_qty_input,     int,   [380])
wc_list   = _parse_nums(wc_input,             float, [0.40])
fa_list   = _parse_nums(flyash_input,         int,   [0])
tg_list   = _parse_nums(target_grade_input,   int,   [40])

# Operational
moulds_list   = _parse_nums(moulds_input,         int,   [10])
clean_list    = _parse_nums(cleaning_time_input,  int,   [20])
reset_list    = _parse_nums(reset_time_input,     int,   [15])
downtime_list = _parse_nums(equip_downtime_input, int,   [10])
ecost_list    = _parse_nums(energy_cost_input,    float, [10.0])
es_list       = _parse_nums(early_strength_input, float, [20.0])

# Curing
cure_methods = curing_methods_sel or ["ambient"]
_st_list     = _parse_nums(steam_temp_input,       int, [60]) if _need_steam else [0]
_sd_list     = _parse_nums(steam_dur_input,        int, [6])  if _need_steam else [0]
ch_list      = _parse_nums(chamber_humidity_input, int, [80])
sd_list      = _parse_nums(start_delay_input,      int, [2])

# ─────────────────────────────────────────────
# BUILD BASE INPUT  (first value of each list → used for baseline display)
# ─────────────────────────────────────────────
_first_cure   = cure_methods[0]
_first_steam  = _st_list[0] if _first_cure in ("steam", "hot_air") else 0
_first_sdur   = _sd_list[0] if _first_cure in ("steam", "hot_air") else 0

base_input = {
    "Ambient_temp_C": at_list[0],
    "Relative_humidity_pct": hum_list[0],
    "Wind_speed_mps": ws_list[0],
    "Season": season_list[0],
    "Daytime_hours": dh_list[0],
    "No_of_moulds": moulds_list[0],
    "Cement_type": cmt_types[0],
    "Cement_content_kgm3": cmt_list[0],
    "Water_cement_ratio": wc_list[0],
    "Flyash_percent": fa_list[0],
    "Target_grade_MPa": tg_list[0],
    "Curing_method": _first_cure,
    "Steam_temp_C": _first_steam,
    "Steam_duration_hr": _first_sdur,
    "Curing_start_delay_hr": sd_list[0],
    "Chamber_humidity_pct": ch_list[0],
    "Cleaning_time_min": clean_list[0],
    "Reset_time_min": reset_list[0],
    "Equipment_downtime_min": downtime_list[0],
    "Energy_cost_rate_INR_per_kWh": ecost_list[0],
    "Early_strength_requirement_MPa": es_list[0],
    # Remaining features — defaults
    "Initial_strength_12hr_MPa": 0.0,
    "Maturity_index": 0.0,
    "Automation_level": 1,
}

# ─────────────────────────────────────────────
# ── MAIN PANEL ───────────────────────────────
# ─────────────────────────────────────────────
st.title("🏭 Precast Yard AI Recommendation Engine")
st.caption(
    "Powered by XGBoost models trained on precast production data. "
    "Adjust yard configuration in the sidebar, then click **Run Optimiser**."
)

# ── BASELINE PERFORMANCE ─────────────────────
st.markdown("---")
st.subheader("📊 Baseline Performance (Current Config)")

base_res = evaluate_single(base_input)
if base_res:
    c1, c2, c3 = st.columns(3)
    c1.metric("⏱ Cycle Time", f"{base_res['Cycle_Time_hr']:.1f} h")
    c2.metric("💰 Total Cost", f"₹ {base_res['Total_Cost_INR']:,.0f}")
    c3.metric("🔩 Demould Time", f"{base_res['Demould_Time_hr']:.1f} h")
else:
    st.warning("Could not compute baseline — check model inputs.")

# ── TAB LAYOUT ───────────────────────────────
tab_optim, tab_pareto, tab_sop, tab_debug, tab_ai_report = st.tabs(
    ["🧬 Optimiser", "📈 Pareto Front", "📋 SOP", "🔍 Debug Explorer", "🤖 AI Report"]
)

# ─────────────────────────────────────────────
# TAB 1 — OPTIMISER
# ─────────────────────────────────────────────
with tab_optim:
    if not run_optim:
        st.info("Configure the sidebar and click **✨ Run Optimiser** to generate recommendations.")
    else:
        st.markdown("### 🧬 Searching Design Space…")
        
        # Debug: Show what input ranges were parsed
        with st.expander("📋 Input Ranges Being Used"):
            st.write(f"**Site Conditions:**")
            st.write(f"- Ambient Temp: {at_list}")
            st.write(f"- Humidity: {hum_list}")
            st.write(f"- Wind Speed: {ws_list}")
            st.write(f"- Season: {season_list}")
            st.write(f"- Daytime Hours: {dh_list}")
            
            st.write(f"**Mix Design:**")
            st.write(f"- Cement Types: {cmt_types}")
            st.write(f"- Cement Content: {cmt_list}")
            st.write(f"- W/C Ratio: {wc_list}")
            st.write(f"- Fly-Ash %: {fa_list}")
            st.write(f"- Target Grade: {tg_list}")
            
            st.write(f"**Curing:**")
            st.write(f"- Methods: {cure_methods}")
            st.write(f"- Steam Temps: {_st_list}")
            st.write(f"- Steam Durations: {_sd_list}")

        candidates_raw = []

        # ── Build curing combos ──
        _curing_combos = []
        for method in cure_methods:
            if method in ("steam", "hot_air"):
                for temp, dur in itertools.product(_st_list, _sd_list):
                    _curing_combos.append((method, temp, dur))
            else:
                _curing_combos.append((method, 0, 0))

        _total = (
            len(at_list) * len(hum_list) * len(ws_list) * len(season_list) * len(dh_list)
            * len(cmt_types) * len(cmt_list) * len(wc_list) * len(fa_list) * len(tg_list)
            * len(moulds_list) * len(clean_list) * len(reset_list) * len(downtime_list)
            * len(ecost_list) * len(es_list)
            * len(_curing_combos) * len(ch_list) * len(sd_list)
        )
        st.caption(f"🔢 Evaluating **{_total:,}** combinations from your inputs…")

        with st.spinner("Simulating scenarios…"):
            _site_ops = itertools.product(
                at_list, hum_list, ws_list, season_list, dh_list,
                moulds_list, clean_list, reset_list, downtime_list, ecost_list, es_list,
            )
            for at, hum, ws, ssn, dh, mld, clt, rst, dnt, ec, es in _site_ops:
                for c_type, c_qty, wc, fa, tg in itertools.product(
                    cmt_types, cmt_list, wc_list, fa_list, tg_list
                ):
                    for method, temp, dur in _curing_combos:
                        for ch, sdl in itertools.product(ch_list, sd_list):
                            var = copy.deepcopy(base_input)  # Deep copy to ensure independence
                            var["Ambient_temp_C"]                  = at
                            var["Relative_humidity_pct"]           = hum
                            var["Wind_speed_mps"]                  = ws
                            var["Season"]                          = ssn
                            var["Daytime_hours"]                   = dh
                            var["Cement_type"]                     = c_type
                            var["Cement_content_kgm3"]             = c_qty
                            var["Water_cement_ratio"]              = wc
                            var["Flyash_percent"]                  = fa
                            var["Target_grade_MPa"]                = tg
                            var["No_of_moulds"]                    = mld
                            var["Cleaning_time_min"]               = clt
                            var["Reset_time_min"]                  = rst
                            var["Equipment_downtime_min"]          = dnt
                            var["Energy_cost_rate_INR_per_kWh"]    = ec
                            var["Early_strength_requirement_MPa"]  = es
                            var["Curing_method"]                   = method
                            var["Steam_temp_C"]                    = temp
                            var["Steam_duration_hr"]               = dur
                            var["Chamber_humidity_pct"]            = ch
                            var["Curing_start_delay_hr"]           = sdl
                            candidates_raw.append(var)

        with st.spinner(f"Running {len(candidates_raw):,} candidates through AI models…"):
            # Debug: Check input diversity BEFORE batch_evaluate
            if len(candidates_raw) > 0:
                st.write("**Debug: Checking input diversity...**")
                sample_inputs = candidates_raw[:5]
                debug_df = pd.DataFrame(sample_inputs)
                st.write("First 5 raw inputs:")
                st.dataframe(debug_df[["Cement_type", "Cement_content_kgm3", "Water_cement_ratio", 
                                       "Curing_method", "Steam_temp_C", "Steam_duration_hr"]])
                
                # Check for uniqueness
                unique_combos = debug_df[["Cement_content_kgm3", "Water_cement_ratio", "Steam_temp_C"]].drop_duplicates()
                st.write(f"Unique combinations in first 5: {len(unique_combos)}")
            
            df_opt = batch_evaluate(candidates_raw)
        
        # Debug: Check for uniqueness in inputs and outputs
        unique_check_cols = ["Steam_temp_C", "Cement_content_kgm3", "Water_cement_ratio", "Curing_method"]
        n_unique_inputs = df_opt[unique_check_cols].drop_duplicates().shape[0]
        n_unique_outputs = df_opt[["Cycle_Time_hr", "Total_Cost_INR"]].drop_duplicates().shape[0]
        
        st.info(f"ℹ️ Debug: {n_unique_inputs} unique input configurations → {n_unique_outputs} unique predictions (out of {len(df_opt)} total)")
        
        # Show sample of input variations
        with st.expander("🔍 View Sample Input Variations (First 20 rows)"):
            sample_cols = ["Cement_type", "Cement_content_kgm3", "Water_cement_ratio", 
                          "Curing_method", "Steam_temp_C", "Steam_duration_hr",
                          "Cycle_Time_hr", "Total_Cost_INR", "Demould_Time_hr"]
            st.dataframe(df_opt[sample_cols].head(20))
        
        # Check if all predictions are identical
        if n_unique_outputs == 1:
            st.error("⚠️ WARNING: All predictions are identical! This suggests an issue with the model pipeline.")
            st.write("**Checking what's being passed to the models:**")
            st.write("Sample of ALL features for first 3 rows:")
            st.dataframe(df_opt[features_ordered].head(3).T)
        
        df_opt = score_df(df_opt, w_time, w_cost)
        df_opt["Is_Safe"] = (df_opt["Cycle_Time_hr"] <= 24) & (df_opt["Total_Cost_INR"] > 0)
        df_opt["Strategy"] = df_opt.apply(
            lambda r: "Ambient" if r["Curing_method"] == "ambient" else f"Steam {int(r['Steam_temp_C'])}°C",
            axis=1,
        )

        st.success(f"✅ Evaluated **{len(df_opt):,}** combinations.")

        # Scatter Plot
        fig = px.scatter(
            df_opt,
            x="Cycle_Time_hr",
            y="Total_Cost_INR",
            color="Strategy",
            size="Cement_content_kgm3",
            symbol="Is_Safe",
            symbol_map={True: "circle", False: "x"},
            title="Optimisation Landscape: Cycle Time vs Total Cost",
            labels={
                "Cycle_Time_hr": "Cycle Time (h)",
                "Total_Cost_INR": "Total Cost (₹)",
            },
            hover_data=["Cement_type", "Water_cement_ratio", "Demould_Time_hr", "Score"],
            opacity=0.7,
        )
        if base_res:
            fig.add_trace(
                go.Scatter(
                    x=[base_res["Cycle_Time_hr"]],
                    y=[base_res["Total_Cost_INR"]],
                    mode="markers",
                    marker=dict(size=16, color="black", symbol="star"),
                    name="Your Baseline",
                )
            )
        st.plotly_chart(fig, use_container_width=True)

        # Recommendations table
        st.subheader("🏆 Top-5 Recommended Recipes")
        safe = df_opt[df_opt["Is_Safe"]].head(5)
        if safe.empty:
            st.warning("No candidates meet the safety threshold (cycle time ≤ 24 h). Showing fastest overall:")
            safe = df_opt.head(5)

        # Improvement vs baseline
        if base_res:
            safe = safe.copy()
            safe["∆ Cost vs Baseline"] = safe["Total_Cost_INR"] - base_res["Total_Cost_INR"]
            safe["∆ Time vs Baseline"] = safe["Cycle_Time_hr"] - base_res["Cycle_Time_hr"]

        display_cols = [
            "Strategy", "Cement_type", "Cement_content_kgm3",
            "Water_cement_ratio", "Cycle_Time_hr", "Total_Cost_INR",
            "Demould_Time_hr", "Score",
        ]
        if "∆ Cost vs Baseline" in safe.columns:
            display_cols += ["∆ Cost vs Baseline", "∆ Time vs Baseline"]

        st.dataframe(
            safe[display_cols].reset_index(drop=True).style.format(
                {
                    "Cycle_Time_hr": "{:.2f}",
                    "Total_Cost_INR": "₹{:,.0f}",
                    "Demould_Time_hr": "{:.2f}",
                    "Score": "{:.4f}",
                    "∆ Cost vs Baseline": "₹{:+,.0f}",
                    "∆ Time vs Baseline": "{:+.2f} h",
                }
            ),
            use_container_width=True,
        )

        # Store best result in session state for SOP tab
        if not safe.empty:
            st.session_state["best_row"] = safe.iloc[0]
            st.session_state["df_opt"] = df_opt

# ─────────────────────────────────────────────
# TAB 2 — PARETO FRONT
# ─────────────────────────────────────────────
with tab_pareto:
    if "df_opt" not in st.session_state:
        st.info("Run the Optimiser first to view the Pareto Front.")
    else:
        df_opt = st.session_state["df_opt"]
        pf = pareto_front(df_opt)

        fig_p = go.Figure()
        fig_p.add_trace(
            go.Scatter(
                x=df_opt["Cycle_Time_hr"],
                y=df_opt["Total_Cost_INR"],
                mode="markers",
                marker=dict(color="lightgray", size=5),
                name="All Candidates",
                opacity=0.5,
            )
        )
        fig_p.add_trace(
            go.Scatter(
                x=pf["Cycle_Time_hr"],
                y=pf["Total_Cost_INR"],
                mode="markers+lines",
                marker=dict(color="crimson", size=10),
                line=dict(color="crimson", dash="dash"),
                name="Pareto Front",
            )
        )
        if base_res:
            fig_p.add_trace(
                go.Scatter(
                    x=[base_res["Cycle_Time_hr"]],
                    y=[base_res["Total_Cost_INR"]],
                    mode="markers",
                    marker=dict(size=14, color="black", symbol="star"),
                    name="Your Baseline",
                )
            )
        fig_p.update_layout(
            title="Pareto Front: Cycle Time vs Total Cost",
            xaxis_title="Cycle Time (h)",
            yaxis_title="Total Cost (₹)",
            legend=dict(x=0.01, y=0.99),
        )
        st.plotly_chart(fig_p, use_container_width=True)

        st.subheader(f"Pareto-Optimal Solutions ({len(pf)})")
        st.dataframe(
            pf[["Strategy", "Cement_type", "Cement_content_kgm3",
                "Water_cement_ratio", "Cycle_Time_hr", "Total_Cost_INR",
                "Demould_Time_hr"]].reset_index(drop=True).style.format(
                {
                    "Cycle_Time_hr": "{:.2f} h",
                    "Total_Cost_INR": "₹{:,.0f}",
                    "Demould_Time_hr": "{:.2f} h",
                }
            ),
            use_container_width=True,
        )

# ─────────────────────────────────────────────
# TAB 3 — SOP
# ─────────────────────────────────────────────
with tab_sop:
    if "best_row" not in st.session_state:
        # Fall back to baseline for SOP preview
        if base_res:
            st.info("Showing SOP for your **current baseline** config. Run the Optimiser to generate an SOP for the recommended recipe.")
            sop_row = pd.Series({**base_input, **{
                "Demould_Time_hr": base_res["Demould_Time_hr"],
                "Cycle_Time_hr": base_res["Cycle_Time_hr"],
                "Total_Cost_INR": base_res["Total_Cost_INR"],
            }})
            st.markdown(generate_sop(sop_row))
        else:
            st.info("Run the Optimiser first to view the recommended SOP.")
    else:
        best = st.session_state["best_row"]
        st.success(f"**Recommended Recipe** — Cycle Time: {best['Cycle_Time_hr']:.1f} h | Cost: ₹{best['Total_Cost_INR']:,.0f}")
        sop_text = generate_sop(best)
        st.markdown(sop_text)

        st.download_button(
            label="📥 Download SOP as Markdown",
            data=sop_text,
            file_name="precast_SOP_recommended.md",
            mime="text/markdown",
        )

# ─────────────────────────────────────────────
# TAB 4 — DEBUG EXPLORER
# ─────────────────────────────────────────────
with tab_debug:
    st.subheader("🔍 Random Scenario Explorer")
    st.caption("Push 50 random scenarios through the model to verify sensitivity.")

    n_debug = st.number_input("Number of random scenarios", min_value=20, max_value=200, value=50, step=10)
    if st.button("🚀 Run Random Simulation", key="debug_run"):
        debug_results = []
        with st.spinner("Simulating…"):
            for _ in range(n_debug):
                s_temp = random.choice([0, 45, 55, 60, 70, 80])
                s_dur = random.choice([4, 6, 8, 12]) if s_temp > 0 else 0
                c_method = "ambient" if s_temp == 0 else "steam"
                sim = {
                    "Ambient_temp_C": random.randint(15, 42),
                    "Relative_humidity_pct": random.randint(30, 85),
                    "Wind_speed_mps": round(random.uniform(0, 8), 1),
                    "Season": random.choice(["summer", "winter", "monsoon", "mild"]),
                    "Daytime_hours": random.choice([8, 10, 12, 14]),
                    "No_of_moulds": random.randint(5, 20),
                    "Cement_type": random.choice(["OPC", "PPC", "PSC"]),
                    "Cement_content_kgm3": random.choice([300, 350, 380, 400, 450]),
                    "Water_cement_ratio": random.choice([0.30, 0.35, 0.40, 0.45, 0.50]),
                    "Flyash_percent": random.choice([0, 10, 20]),
                    "Target_grade_MPa": random.choice([30, 35, 40, 45]),
                    "Curing_method": c_method,
                    "Steam_temp_C": s_temp,
                    "Steam_duration_hr": s_dur,
                    "Curing_start_delay_hr": random.choice([1, 2, 3]),
                    "Chamber_humidity_pct": random.randint(60, 100),
                    "Cleaning_time_min": random.randint(10, 40),
                    "Reset_time_min": random.randint(5, 30),
                    "Equipment_downtime_min": random.randint(0, 60),
                    "Energy_cost_rate_INR_per_kWh": round(random.uniform(6, 18), 1),
                    "Early_strength_requirement_MPa": round(random.uniform(15, 35), 1),
                    "Initial_strength_12hr_MPa": 0.0,
                    "Maturity_index": 0.0,
                    "Automation_level": random.choice([0, 1, 2]),
                }
                r = evaluate_single(sim)
                if r:
                    debug_results.append(r)

        df_debug = pd.DataFrame(debug_results)
        st.success(f"✅ {len(df_debug)} scenarios evaluated.")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.scatter(
                df_debug,
                x="Cycle_Time_hr",
                y="Total_Cost_INR",
                color="Curing_method",
                size="Cement_content_kgm3",
                title="Cycle Time vs Cost",
                labels={"Cycle_Time_hr": "Cycle Time (h)", "Total_Cost_INR": "Total Cost (₹)"},
            )
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.scatter(
                df_debug,
                x="Steam_temp_C",
                y="Cycle_Time_hr",
                color="Curing_method",
                title="Steam Temp vs Cycle Time",
                labels={"Steam_temp_C": "Steam Temp (°C)", "Cycle_Time_hr": "Cycle Time (h)"},
            )
            st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.histogram(
            df_debug,
            x="Total_Cost_INR",
            color="Cement_type",
            title="Cost Distribution by Cement Type",
            nbins=20,
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(
            df_debug[
                ["Curing_method", "Cement_type", "Steam_temp_C",
                 "Water_cement_ratio", "Demould_Time_hr",
                 "Cycle_Time_hr", "Total_Cost_INR"]
            ].sort_values("Cycle_Time_hr").reset_index(drop=True).style.format(
                {
                    "Cycle_Time_hr": "{:.2f} h",
                    "Demould_Time_hr": "{:.2f} h",
                    "Total_Cost_INR": "₹{:,.0f}",
                }
            ),
            use_container_width=True,
        )

# ─────────────────────────────────────────────
# TAB 5 — AI REPORT GENERATOR
# ─────────────────────────────────────────────
with tab_ai_report:
    st.header("🤖 AI-Powered Report & Analysis")
    
    # Initialize Gemini API
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(model_name="gemini-3-flash-preview")
        api_configured = True
    except Exception as e:
        st.error(f"⚠️ Failed to configure Gemini API: {e}")
        st.info("Please add your GOOGLE_API_KEY to Streamlit secrets (.streamlit/secrets.toml)")
        api_configured = False
    
    if not api_configured:
        st.stop()
    
    # Check if optimization data is available
    if "df_opt" not in st.session_state:
        st.info("Run the Optimiser first to generate data for AI analysis.")
    else:
        df_opt = st.session_state["df_opt"]
        best_row = st.session_state.get("best_row", None)
        
        # Initialize chat history in session state
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        if "report_generated" not in st.session_state:
            st.session_state["report_generated"] = False
        if "report_text" not in st.session_state:
            st.session_state["report_text"] = ""
        
        # Prepare data summary for AI
        def prepare_data_summary():
            # Get top 5 recommendations
            safe = df_opt[df_opt["Is_Safe"]].head(5)
            if safe.empty:
                safe = df_opt.head(5)
            
            # Get Pareto front
            pf = pareto_front(df_opt)
            
            # Baseline data
            baseline_info = ""
            if base_res:
                baseline_info = f"""
**Baseline Configuration:**
- Cycle Time: {base_res['Cycle_Time_hr']:.2f} hours
- Total Cost: ₹{base_res['Total_Cost_INR']:,.0f}
- Demould Time: {base_res['Demould_Time_hr']:.2f} hours
"""
            
            # Summary statistics
            summary = f"""
=== PRECAST OPTIMIZATION ANALYSIS DATA ===

**Total Combinations Evaluated:** {len(df_opt):,}

{baseline_info}
**Top 5 Recommended Configurations:**
{safe[['Strategy', 'Cement_type', 'Cement_content_kgm3', 'Water_cement_ratio', 'Cycle_Time_hr', 'Total_Cost_INR', 'Demould_Time_hr']].to_string()}

**Pareto-Optimal Solutions ({len(pf)} configurations):**
{pf[['Strategy', 'Cement_type', 'Cement_content_kgm3', 'Water_cement_ratio', 'Cycle_Time_hr', 'Total_Cost_INR']].head(10).to_string()}

**Optimization Thresholds:**
- Time Weight: {w_time:.2f}
- Cost Weight: {w_cost:.2f}
- Maximum Acceptable Cycle Time: 24 hours

**Input Parameter Ranges:**
- Cement Content: {df_opt['Cement_content_kgm3'].min():.0f} - {df_opt['Cement_content_kgm3'].max():.0f} kg/m³
- W/C Ratio: {df_opt['Water_cement_ratio'].min():.2f} - {df_opt['Water_cement_ratio'].max():.2f}
- Steam Temperature: {df_opt['Steam_temp_C'].min():.0f} - {df_opt['Steam_temp_C'].max():.0f} °C
- Cement Types: {', '.join(df_opt['Cement_type'].unique())}
- Curing Methods: {', '.join(df_opt['Curing_method'].unique())}
- Seasons: {', '.join(df_opt['Season'].unique())}

**Results Summary:**
- Minimum Cycle Time: {df_opt['Cycle_Time_hr'].min():.2f} hours
- Maximum Cycle Time: {df_opt['Cycle_Time_hr'].max():.2f} hours
- Minimum Cost: ₹{df_opt['Total_Cost_INR'].min():,.0f}
- Maximum Cost: ₹{df_opt['Total_Cost_INR'].max():,.0f}
- Average Cycle Time: {df_opt['Cycle_Time_hr'].mean():.2f} hours
- Average Cost: ₹{df_opt['Total_Cost_INR'].mean():,.0f}
"""
            return summary
        
        # Generate AI Report Section
        st.subheader("📊 Generate Comprehensive Report")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            report_focus = st.multiselect(
                "Report Focus Areas",
                ["Cost Optimization", "Time Efficiency", "Material Analysis", 
                 "Curing Strategy Comparison", "Seasonal Impact", "Risk Assessment"],
                default=["Cost Optimization", "Time Efficiency"]
            )
        with col2:
            report_length = st.selectbox("Report Length", ["Brief", "Detailed", "Comprehensive"], index=1)
        
        if st.button("🚀 Generate AI Report", type="primary"):
            with st.spinner("Generating comprehensive AI report..."):
                data_summary = prepare_data_summary()
                
                prompt = f"""
You are an expert in precast concrete production optimization. Analyze the following optimization results and generate a comprehensive, professional report.

{data_summary}

**Report Requirements:**
- Length: {report_length}
- Focus on: {', '.join(report_focus)}
- Include executive summary, key findings, detailed analysis, and actionable recommendations
- Use professional language suitable for production managers and engineers
- Highlight cost savings, time improvements, and efficiency gains
- Provide specific recommendations for implementation
- Include risk assessment and mitigation strategies
- Format the report in clear sections with bullet points and tables where appropriate

Generate a well-structured, professional report based on this data.
"""
                
                try:
                    response = model.generate_content(prompt)
                    st.session_state["report_text"] = response.text
                    st.session_state["report_generated"] = True
                    st.session_state["data_summary"] = data_summary
                    st.success("✅ Report generated successfully!")
                except Exception as e:
                    st.error(f"Error generating report: {e}")
        
        # Display generated report
        if st.session_state["report_generated"]:
            st.markdown("---")
            st.subheader("📄 Generated Report")
            st.markdown(st.session_state["report_text"])
            
            # Download button for report
            st.download_button(
                label="📥 Download Report as Markdown",
                data=st.session_state["report_text"],
                file_name="precast_optimization_report.md",
                mime="text/markdown"
            )
            
            # Cross-Questioning Section
            st.markdown("---")
            st.subheader("💬 Ask Questions About Your Data")
            st.caption("Ask follow-up questions about the optimization results, recommendations, or any specific aspect of the analysis.")
            
            # Display chat history
            for i, chat in enumerate(st.session_state["chat_history"]):
                with st.chat_message("user"):
                    st.write(chat["question"])
                with st.chat_message("assistant"):
                    st.write(chat["answer"])
            
            # Chat input
            user_question = st.chat_input("Ask a question about the optimization results...")
            
            if user_question:
                with st.chat_message("user"):
                    st.write(user_question)
                
                with st.spinner("Analyzing your question..."):
                    context_prompt = f"""
You are an expert assistant helping analyze precast concrete optimization results.

Context - Optimization Data:
{st.session_state.get('data_summary', prepare_data_summary())}

Previous Report Generated:
{st.session_state['report_text'][:1000]}...

User Question: {user_question}

Provide a clear, specific answer based on the optimization data. Include specific numbers, configurations, or recommendations where relevant. If the question is about comparing options, provide a detailed comparison. If it's about implementation, give practical steps.
"""
                    
                    try:
                        response = model.generate_content(context_prompt)
                        answer = response.text
                        
                        with st.chat_message("assistant"):
                            st.write(answer)
                        
                        # Save to chat history
                        st.session_state["chat_history"].append({
                            "question": user_question,
                            "answer": answer
                        })
                    except Exception as e:
                        st.error(f"Error processing question: {e}")
            
            # Clear chat button
            if st.session_state["chat_history"] and st.button("🗑️ Clear Chat History"):
                st.session_state["chat_history"] = []
                st.rerun()

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Precast AI Optimizer · Phase 1 & 2 Pipeline · XGBoost models trained on synthetic yard data"
)
