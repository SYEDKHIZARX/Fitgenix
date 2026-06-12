# ============================================================
# app.py — FITGENIX Adaptive Fitness Planner
# 39 Training Types + Injury-Aware + Rehab + Tier 1 Features
# ============================================================

import os
import json
import datetime
import numpy as np
import joblib
import streamlit as st
from supabase import create_client
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from urllib.parse import quote_plus

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="FITGENIX — Adaptive Fitness Planner",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Barlow:wght@300;400;500;600&display=swap');
:root{--accent:#E8FF00;--accent2:#FF4D00;--dark:#080A0E;--card:#0F1218;
      --card2:#161B24;--border:rgba(232,255,0,0.15);--text:#F0F2F5;--muted:#6B7280;}
html,body,[data-testid="stAppViewContainer"]{
    background:var(--dark)!important;font-family:'Barlow',sans-serif!important;color:var(--text)!important;}
[data-testid="stAppViewContainer"]{
    background:radial-gradient(ellipse 80% 40% at 50% -10%,rgba(232,255,0,0.07) 0%,transparent 60%),
               radial-gradient(ellipse 60% 30% at 80% 100%,rgba(255,77,0,0.05) 0%,transparent 50%),
               var(--dark)!important;}
[data-testid="stHeader"],[data-testid="stToolbar"]{background:transparent!important;}
#MainMenu,footer,[data-testid="stDecoration"]{display:none!important;}
h1,h2,h3,h4{font-family:'Barlow Condensed',sans-serif!important;letter-spacing:0.02em!important;}
[data-testid="stSidebar"]{background:var(--card)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{color:var(--text)!important;}
[data-testid="stNumberInput"] input,[data-baseweb="select"]>div{
    background:var(--card2)!important;border:1px solid var(--border)!important;
    border-radius:8px!important;color:var(--text)!important;}
[data-testid="stSlider"]>div>div>div>div{background:var(--accent)!important;}
.stButton>button{
    background:var(--accent)!important;color:#0A0A0A!important;
    font-family:'Barlow Condensed',sans-serif!important;font-size:1.2rem!important;
    font-weight:900!important;letter-spacing:0.08em!important;text-transform:uppercase!important;
    border:none!important;border-radius:6px!important;padding:0.75rem 2rem!important;
    transition:all 0.2s ease!important;width:100%!important;text-shadow:none!important;}
.stButton>button *{color:#0A0A0A!important;}
[data-testid="stSidebar"] .stButton>button{color:#0A0A0A!important;}
/* Brighten widget labels (Body Type, Select Training Type, etc.) which
   defaulted to a dim gray and looked grayed-out, esp. in the sidebar. */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
.stSelectbox label, .stTextInput label, .stNumberInput label,
.stSlider label, .stCheckbox label, label[data-testid]{
    color:var(--text)!important;opacity:1!important;font-weight:600!important;}
.stButton>button:hover{background:#fff!important;color:#0A0A0A!important;transform:translateY(-2px)!important;
    box-shadow:0 8px 30px rgba(232,255,0,0.3)!important;}
[data-testid="stMetric"]{background:var(--card2)!important;border:1px solid var(--border)!important;
    border-radius:12px!important;padding:1.2rem!important;}
[data-testid="stMetricLabel"]{font-family:'Barlow Condensed',sans-serif!important;
    font-size:0.75rem!important;letter-spacing:0.1em!important;text-transform:uppercase!important;color:var(--muted)!important;}
[data-testid="stMetricValue"]{font-family:'Barlow Condensed',sans-serif!important;
    font-size:2.4rem!important;font-weight:800!important;color:var(--accent)!important;}
[data-testid="stExpander"]{background:var(--card2)!important;border:1px solid var(--border)!important;border-radius:10px!important;}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:10px!important;}
[data-testid="stAlert"]{border-radius:10px!important;font-family:'Barlow',sans-serif!important;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HISTORY
# ============================================================
# ============================================================
# PERSISTENCE (Supabase, per-user) -- same function names/shapes as before,
# but now reading/writing each logged-in user's own rows instead of a
# shared JSON file. USER_ID / supabase are created by the auth gate before
# any of these are ever called.
# ============================================================
def _uid():
    # Resolves the current user id at call time (auth gate guarantees it exists).
    return st.session_state.user.id

def load_history():
    """Return this user's logged days as a list of dicts (oldest -> newest),
    each with a 'date' key, matching the old JSON shape the rest of the app expects."""
    try:
        resp = (supabase.table("workout_history")
                .select("*")
                .eq("user_id", _uid())
                .order("log_date", desc=False)
                .execute())
        rows = resp.data or []
    except Exception:
        return []
    history = []
    for r in rows:
        history.append({
            "date": r.get("log_date"),
            "steps": r.get("steps"),
            "active_minutes": r.get("active_minutes"),
            "fatigue": r.get("fatigue"),
            "calorie_intensity": r.get("calorie_intensity"),
            "rl_recommendation": r.get("rl_recommendation"),
            "goal": r.get("goal"),
            "bmi": r.get("bmi"),
            "calorie_score": r.get("calorie_score"),
        })
    return history

def save_entry(entry):
    """Upsert one day's activity for this user (one row per user per date)."""
    today = datetime.date.today().isoformat()
    row = {
        "user_id": _uid(),
        "log_date": today,
        "steps": int(entry.get("steps") or 0),
        "active_minutes": int(entry.get("active_minutes") or 0),
        "fatigue": entry.get("fatigue"),
        "calorie_intensity": entry.get("calorie_intensity"),
        "rl_recommendation": entry.get("rl_recommendation") or entry.get("rl_rec"),
        "goal": entry.get("goal"),
        "bmi": float(entry["bmi"]) if entry.get("bmi") is not None else None,
        "calorie_score": float(entry["calorie_score"]) if entry.get("calorie_score") is not None else None,
    }
    try:
        # delete any existing row for today, then insert (keeps one-per-day)
        supabase.table("workout_history").delete().eq("user_id", _uid()).eq("log_date", today).execute()
        supabase.table("workout_history").insert(row).execute()
    except Exception:
        pass

def get_streak(history):
    if not history: return 0
    today = datetime.date.today(); streak = 0
    for i in range(len(history)-1,-1,-1):
        if datetime.date.fromisoformat(history[i]["date"]) == today - datetime.timedelta(days=streak):
            streak += 1
        else: break
    return streak

def get_best_streak(history):
    if not history: return 0
    best = current = 1
    for i in range(1,len(history)):
        d1 = datetime.date.fromisoformat(history[i-1]["date"])
        d2 = datetime.date.fromisoformat(history[i]["date"])
        if (d2-d1).days == 1: current += 1; best = max(best,current)
        else: current = 1
    return best

def save_injury_profile(profile):
    """Store the user's injury profile in their profiles row (as JSON in a text column
    is overkill; we keep it light by stashing it in session + profiles update)."""
    try:
        supabase.table("profiles").upsert({
            "id": _uid(),
            "updated_at": datetime.datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass
    # keep the live copy in session so the current run uses it immediately
    st.session_state["injury_profile"] = profile

def load_injury_profile():
    return st.session_state.get("injury_profile", {})

def save_outcome(exercise_name, muscle_group, status, difficulty=None, fatigue_at_time=None):
    """Log one exercise outcome (the feedback-loop signal) to the user's rows.
    status: 'completed' | 'skipped' | 'too_hard' (we store too_hard as completed-with-difficulty)."""
    today = datetime.date.today().isoformat()
    if status == "too_hard":
        row_status, difficulty = "completed", "too_hard"
    else:
        row_status = status
    row = {
        "user_id": _uid(),
        "log_date": today,
        "exercise_name": exercise_name,
        "muscle_group": muscle_group or "",
        "status": row_status,
        "difficulty": difficulty,
        "fatigue_at_time": fatigue_at_time,
    }
    try:
        # one row per user/date/exercise: replace any prior log for it today
        (supabase.table("exercise_outcomes")
         .delete().eq("user_id", _uid()).eq("log_date", today)
         .eq("exercise_name", exercise_name).execute())
        supabase.table("exercise_outcomes").insert(row).execute()
        return True
    except Exception as e:
        st.error(f"Could not save '{exercise_name}': {type(e).__name__}: {e}")
        return False

def load_today_outcomes():
    """Return {exercise_name: {'status':..,'difficulty':..}} for today's logged exercises."""
    today = datetime.date.today().isoformat()
    try:
        resp = (supabase.table("exercise_outcomes").select("*")
                .eq("user_id", _uid()).eq("log_date", today).execute())
        out = {}
        for r in (resp.data or []):
            out[r["exercise_name"]] = {"status": r.get("status"), "difficulty": r.get("difficulty")}
        return out
    except Exception:
        return {}

# ============================================================
# 2C: PERSONALIZED REINFORCEMENT LEARNING (closes the feedback loop)
# Each user gets their own Q-table, seeded from the base pickled q_table,
# then nudged by real logged outcomes (completed / skipped / too_hard).
# Validated Q-learning update + a safety cap so repeated 'too hard' can
# never push the recommendation to a HIGHER intensity.
# ============================================================
RL_ALPHA = 0.25  # learning rate

def get_personal_q():
    """Load this user's personalized Q-table (list-of-lists). Falls back to the
    base pickled q_table for new users. Cached in session for the run."""
    if "personal_q" in st.session_state and st.session_state.get("personal_q_uid") == _uid():
        return np.array(st.session_state["personal_q"], dtype=float)
    pq = None
    try:
        resp = supabase.table("profiles").select("q_table").eq("id", _uid()).execute()
        if resp.data and resp.data[0].get("q_table"):
            pq = np.array(resp.data[0]["q_table"], dtype=float)
    except Exception:
        pq = None
    if pq is None or pq.shape != q_table.shape:
        pq = np.array(q_table, dtype=float).copy()   # seed from base model
    st.session_state["personal_q"] = pq.tolist()
    st.session_state["personal_q_uid"] = _uid()
    return pq

def get_rl_cap(fatigue_level):
    """Safety cap per fatigue state: if the user has logged 'too_hard' for the
    action recommended in this state, never recommend ABOVE that action."""
    caps = st.session_state.get("rl_caps", {})
    return caps.get(str(fatigue_level))

def rl_recommend_index(fatigue_level):
    """Personalized recommendation: argmax over the user's Q row, restricted by
    the safety cap so it never exceeds a known-too-hard intensity."""
    pq = get_personal_q()
    row = pq[fatigue_level]
    cap = get_rl_cap(fatigue_level)
    if cap is not None and cap < len(row) - 1:
        idx = int(np.argmax(row[:cap + 1]))
    else:
        idx = int(np.argmax(row))
    return idx

def rl_learn_from_outcomes(fatigue_level, rec_action, outcomes_list):
    """Apply the validated Q-update from this session's outcomes for one fatigue
    state, persist the personalized table + bump the rl_updates counter.
    outcomes_list: list of {'status','difficulty'} dicts."""
    if not outcomes_list:
        return
    pq = get_personal_q()
    row = pq[fatigue_level].copy()

    too_hard = sum(1 for o in outcomes_list if o.get("difficulty") == "too_hard")
    done     = sum(1 for o in outcomes_list if o.get("status") == "completed" and o.get("difficulty") != "too_hard")
    skipped  = sum(1 for o in outcomes_list if o.get("status") == "skipped")
    n = len(outcomes_list)
    reward = max(-1.0, min(1.0, (done * 1.0 - too_hard * 1.0 - skipped * 0.4) / n))

    # core update toward observed reward
    row[rec_action] += RL_ALPHA * (reward - row[rec_action])
    # directional nudges
    if too_hard > 0 and rec_action > 0:
        row[rec_action - 1] += RL_ALPHA * 0.5 * abs(reward)
    if too_hard == 0 and done == n and rec_action < len(row) - 1:
        row[rec_action + 1] += RL_ALPHA * 0.5 * reward

    pq[fatigue_level] = row

    # update the safety cap for this state
    caps = st.session_state.get("rl_caps", {})
    if too_hard > 0:
        caps[str(fatigue_level)] = rec_action
    st.session_state["rl_caps"] = caps

    # persist personalized table + bump counter
    st.session_state["personal_q"] = pq.tolist()
    try:
        cur = supabase.table("profiles").select("rl_updates").eq("id", _uid()).execute()
        n_updates = (cur.data[0]["rl_updates"] if cur.data and cur.data[0].get("rl_updates") else 0) + 1
        supabase.table("profiles").upsert({
            "id": _uid(),
            "q_table": pq.tolist(),
            "rl_updates": n_updates,
            "updated_at": datetime.datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass

def get_rl_recommendation_personal(fatigue_level):
    """Drop-in personalized version of get_rl_recommendation."""
    actions = {
        0:("REST / RECOVERY",  "#6B7280","Your body needs recovery. Prioritise sleep, hydration, and light stretching."),
        1:("LIGHT ACTIVITY",   "#00B4FF","A gentle session - 20-30 min walk, yoga, or mobility work."),
        2:("MODERATE WORKOUT", "#FF6B35","You are ready. Aim for 45-60 min of steady cardio or strength training."),
        3:("HIGH INTENSITY",   "#E8FF00","Fully rested - push hard today. HIIT, heavy lifts, or interval runs.")
    }
    return actions[rl_recommend_index(fatigue_level)]

def get_model_metrics():
    """Aggregate this user's REAL logged outcomes into live model-performance
    metrics. All numbers come from the exercise_outcomes table -- actual usage,
    not simulation. Returns a dict (safe defaults if there's no data yet)."""
    out = {"total": 0, "completed": 0, "skipped": 0, "too_hard": 0,
           "completion_rate": None, "too_hard_rate": None,
           "rl_updates": 0, "by_fatigue": {}}
    try:
        resp = (supabase.table("exercise_outcomes").select("*")
                .eq("user_id", _uid()).execute())
        rows = resp.data or []
    except Exception:
        rows = []
    out["total"] = len(rows)
    for r in rows:
        status = r.get("status"); diff = r.get("difficulty"); fat = r.get("fatigue_at_time") or "Unknown"
        if diff == "too_hard": out["too_hard"] += 1
        if status == "completed": out["completed"] += 1
        elif status == "skipped": out["skipped"] += 1
        seg = out["by_fatigue"].setdefault(fat, {"total": 0, "completed": 0, "too_hard": 0})
        seg["total"] += 1
        if status == "completed": seg["completed"] += 1
        if diff == "too_hard": seg["too_hard"] += 1
    if out["total"]:
        out["completion_rate"] = out["completed"] / out["total"]
        out["too_hard_rate"] = out["too_hard"] / out["total"]
    try:
        p = supabase.table("profiles").select("rl_updates").eq("id", _uid()).execute()
        if p.data and p.data[0].get("rl_updates"):
            out["rl_updates"] = p.data[0]["rl_updates"]
    except Exception:
        pass
    return out

def render_model_performance():
    """Renders the live Model Performance panel from real usage data."""
    m = get_model_metrics()
    st.markdown("<div style='font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;"
                "text-transform:uppercase;margin:0.5rem 0 0.75rem;'>-- Model Performance (live)</div>",
                unsafe_allow_html=True)
    if m["total"] == 0:
        st.info("No workout outcomes logged yet. Complete and log a session "
                "(tap Done/Skip/Too hard, then 'Train FITGENIX') to start populating live metrics.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Completion rate", f"{m['completion_rate']*100:.0f}%",
              help="Of logged exercises, the share marked completed.")
    c2.metric("Too-hard rate", f"{m['too_hard_rate']*100:.0f}%",
              help="Share flagged too hard. Adaptive RL aims to reduce this.")
    c3.metric("RL adaptations", m["rl_updates"],
              help="Times the personal policy has learned from your sessions.")
    st.caption(f"Based on {m['total']} logged exercise outcomes across your sessions.")

    # per-fatigue-state breakdown (where the RL actually personalises)
    if m["by_fatigue"]:
        rows = []
        for fat, seg in m["by_fatigue"].items():
            if seg["total"]:
                rows.append({"Fatigue state": fat,
                             "Logged": seg["total"],
                             "Completion %": round(seg["completed"]/seg["total"]*100),
                             "Too-hard %": round(seg["too_hard"]/seg["total"]*100)})
        if rows:
            st.markdown("<div style='font-size:0.75rem;color:#9CA3AF;margin:0.75rem 0 0.25rem;'>"
                        "Breakdown by the fatigue state at the time:</div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    # show the personalised vs base policy (proof of adaptation)
    try:
        pq = get_personal_q()
        base = np.array(q_table, dtype=float)
        if not np.allclose(pq, base):
            st.markdown("<div style='font-size:0.75rem;color:#9CA3AF;margin:0.75rem 0 0.25rem;'>"
                        "Your personalised intensity policy has diverged from the base model "
                        "(this is the adaptation):</div>", unsafe_allow_html=True)
            labels = ["Rested", "Slightly Fatigued", "Heavy Fatigue"][:pq.shape[0]]
            acts = ["Rest", "Light", "Moderate", "High"][:pq.shape[1]]
            dfp = pd.DataFrame(np.round(pq, 2), columns=acts)
            dfp.insert(0, "Fatigue", labels)
            st.dataframe(dfp, width='stretch', hide_index=True)
    except Exception:
        pass

def save_profile(user_profile):
    """Silently upsert the user's profile fields to their profiles row."""
    try:
        supabase.table("profiles").upsert({
            "id": _uid(),
            "age": user_profile.get("age"),
            "gender": user_profile.get("gender"),
            "height_cm": user_profile.get("height"),
            "weight_kg": user_profile.get("weight"),
            "bmi": user_profile.get("bmi"),
            "body_type": user_profile.get("body_type"),
            "goal": user_profile.get("goal"),
            "updated_at": datetime.datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass


# ============================================================
# PHASE 5: PLAN LIFECYCLE -- persistence (write side only for now)
# ============================================================
def save_active_plan(plan_days, user_profile, length_days=7, frequency=None,
                     split_type=None, focus=None):
    """Persist the freshly generated plan as this user's ACTIVE plan.
    Archives any prior active plan first, so there is exactly one active plan.
    Write-only at this step -- nothing reads it back yet (no behaviour change)."""
    try:
        # archive any existing active plan
        supabase.table("active_plans").update({"status": "abandoned"}) \
            .eq("user_id", _uid()).eq("status", "active").execute()
        # insert the new active plan
        supabase.table("active_plans").insert({
            "user_id": _uid(),
            "start_date": datetime.date.today().isoformat(),
            "length_days": length_days,
            "frequency": frequency,
            "split_type": split_type,
            "focus": focus,
            "goal": user_profile.get("goal"),
            "plan_json": plan_days,
            "status": "active",
            "current_cycle": 1,
        }).execute()
    except Exception:
        pass
BADGES = [
    (1,  "⚡","First Spark",      "You started your journey!"),
    (3,  "🔥","On Fire",          "3-day streak achieved!"),
    (7,  "💪","Week Warrior",     "7 days straight — incredible!"),
    (14, "🏅","Fortnight Fighter","14 days of consistency!"),
    (30, "🏆","Monthly Champion", "30-day streak — elite level!"),
    (50, "💎","Diamond Grinder",  "50 sessions logged!"),
    (100,"👑","Legend",           "100 days — unstoppable!"),
]
def get_earned_badges(streak, total):
    return [(ic,n,d) for t,ic,n,d in BADGES if streak>=t or total>=t]

# ============================================================
# LOAD MODELS
# ============================================================
@st.cache_resource
def load_models():
    base = os.path.dirname(os.path.abspath(__file__))
    try:
        return (joblib.load(os.path.join(base,"scaler.pkl")),
                joblib.load(os.path.join(base,"ga_model.pkl")),
                joblib.load(os.path.join(base,"q_table.pkl")))
    except Exception as e:
        st.error("FITGENIX could not load its models. Please try again shortly. "
                 "If this persists, the model files may be missing from the deployment.")
        st.stop()

scaler, ga_model, q_table = load_models()

# ============================================================
# GA + RL + BMI
# ============================================================
def predict_calories(steps,distance,intensity_score,active_minutes,scaler,ga_model):
    raw  = np.array([[steps,distance,0,intensity_score,0,active_minutes]])
    norm = scaler.transform(raw)
    x    = np.array([norm[0][0],norm[0][1],norm[0][3],norm[0][5]])
    w,b  = ga_model[:-1], ga_model[-1]
    return float(np.clip(np.dot(x,w)+b, 0, 1))

def get_rl_recommendation(fatigue_level):
    actions = {
        0:("REST / RECOVERY",  "#6B7280","Your body needs recovery. Prioritise sleep, hydration, and light stretching."),
        1:("LIGHT ACTIVITY",   "#00B4FF","A gentle session - 20-30 min walk, yoga, or mobility work."),
        2:("MODERATE WORKOUT", "#FF6B35","You are ready. Aim for 45-60 min of steady cardio or strength training."),
        3:("HIGH INTENSITY",   "#E8FF00","Fully rested - push hard today. HIIT, heavy lifts, or interval runs.")
    }
    return actions[int(np.argmax(q_table[fatigue_level]))]

def calculate_bmi(weight_kg,height_cm):
    h=height_cm/100; bmi=weight_kg/(h**2)
    if   bmi<18.5: cat,col="Underweight","#00B4FF"
    elif bmi<25:   cat,col="Normal weight","#00E676"
    elif bmi<30:   cat,col="Overweight","#FF6B35"
    else:          cat,col="Obese","#FF4D00"
    return round(bmi,1),cat,col

def adaptive_ga_retrain(history):
    if len(history)<7: return None,None
    rows=[[h.get("steps",0),h.get("active_minutes",0),h.get("bmi",22.0),h.get("calorie_score",0.5)] for h in history]
    data=np.array(rows,dtype=float)
    col_min=data.min(axis=0); col_rng=np.where((data.max(axis=0)-col_min)==0,1,data.max(axis=0)-col_min)
    data_n=(data-col_min)/col_rng; X,y=data_n[:,:3],data_n[:,3]
    N_POP,N_GEN,MUT=30,50,0.1
    pop=np.random.randn(N_POP,4)*0.5
    def mae(c): return np.mean(np.abs(X@c[:-1]+c[-1]-y))
    best_c,best_m=pop[0],mae(pop[0])
    for _ in range(N_GEN):
        fit=np.array([mae(c) for c in pop]); idx=np.argsort(fit); pop=pop[idx]
        if fit[idx[0]]<best_m: best_m=fit[idx[0]]; best_c=pop[0].copy()
        new=[pop[0],pop[1]]
        while len(new)<N_POP:
            p1,p2=pop[np.random.randint(0,10)],pop[np.random.randint(0,10)]
            pt=np.random.randint(1,3); child=np.concatenate([p1[:pt],p2[pt:]])
            child+=(np.random.rand(4)<MUT)*np.random.randn(4)*0.1; new.append(child)
        pop=np.array(new)
    return best_c,round(float(best_m),5)

# ============================================================
# INJURY SYSTEM
# ============================================================
# Static data (exercise library, training types, injury maps, rehab, etc.)
from data import *



def get_injury_safe_exercises(body_part, severity):
    sev_key = "moderate" if "Moderate" in severity else "low"
    return INJURY_SAFE_EXERCISES.get(body_part, DEFAULT_SAFE).get(sev_key, DEFAULT_SAFE[sev_key])

def get_blocked_groups(body_part, severity):
    if "Severe" in severity: return INJURY_MUSCLE_MAP.get(body_part, [])
    return []

def get_modified_groups(body_part, severity):
    if "Moderate" in severity or "Low" in severity: return INJURY_MUSCLE_MAP.get(body_part, [])
    return []

# ============================================================
# TRAINING TYPE REGISTRY — 39 types
# ============================================================

ALL_TRAINING_TYPES = sorted(TRAINING_TYPES.keys())

# ============================================================
# EXERCISE LIBRARY — extended pool
# ============================================================

# ============================================================
# EXERCISE COMPREHENSION LAYER (decoupled from the recommendation engine)
# Plain-language descriptor + form cues + common mistake per exercise.
# Anything not listed still gets a universal 'Watch demo' search link.
# ============================================================


def get_exercise_info(name, muscles=""):
    """Decoupled comprehension layer. Returns plain-language descriptor, form
    cues, common mistake and a demo link. Curated entries fall back gracefully
    to a universal YouTube 'how to' search so every exercise has a demo."""
    demo = "https://www.youtube.com/results?search_query=" + quote_plus("how to " + name + " proper form")
    info = EXERCISE_INFO.get(name)
    if info:
        return {"desc": info.get("desc", ""), "cues": info.get("cues", []),
                "mistake": info.get("mistake", ""), "demo": info.get("demo", demo)}
    return {"desc": "",
            "cues": ["Move slowly and with control through a full, pain-free range.",
                     "Keep good posture and a braced core throughout."],
            "mistake": "Rushing the reps or using momentum instead of muscle.",
            "demo": demo}



# ============================================================
# MOVEMENT PREVIEWS (real photographic demonstrations)
# Each exercise maps to two real demo photos (start + finish position)
# from the public-domain free-exercise-db. The two frames cross-fade into
# an honest, accurate movement loop. Exercises without an accurate match
# show NO image (cues + full video only) -- never a misleading visual.
# Images are HTTP-verified; an onerror handler hides the block if a photo
# ever fails to load, so a broken image is never shown.
# ============================================================

def get_exercise_animation(name, color="#E8FF00"):
    """Real two-frame photographic preview (start <-> finish). Returns an
    empty string when we have no accurate image, so beginners never see a
    misleading visual -- the form cues + full video carry those cases."""
    frames = _EXERCISE_IMAGES.get(name)
    if not frames:
        return ""
    u0 = _IMG_BASE + frames[0]
    u1 = _IMG_BASE + frames[1] if len(frames) > 1 else u0
    return (
        "<div class='exa-prev'>"
        "<div class='exa-stage'>"
        f"<img class='exa-f exa-f0' src='{u0}' alt='{name} start position' "
        "onerror=\"var p=this.closest('.exa-prev'); if(p){p.style.display='none';}\">"
        f"<img class='exa-f exa-f1' src='{u1}' alt='{name} finish position'>"
        "</div>"
        "<div class='exa-cap'>Movement preview \u00b7 real demo photos</div>"
        "</div>"
    )

def pick_exercises(group, count=3, blocked=[], modified=[], injury_part=None, severity=None):
    if group in blocked: return []
    if group in modified and injury_part and severity:
        safe = get_injury_safe_exercises(injury_part, severity)
        return safe[:count] if safe else []
    pool = EXERCISE_LIBRARY.get(group, EXERCISE_LIBRARY["rest"])
    return pool[:count]

# ============================================================
# SCHEDULE ENGINE
# ============================================================
def get_schedule(training_type_name, bmi_cat, fatigue, rl_rec):
    meta = TRAINING_TYPES.get(training_type_name, {"cat":"hybrid","intensity":3,"emphasis":"variety"})
    cat  = meta["cat"]
    emph = meta["emphasis"]

    schedules = {
        "strength":{
            "volume":[("Chest & Triceps",["chest","arms"]),("Back & Biceps",["back","arms"]),
                      ("Legs",["legs"]),("Shoulders & Core",["shoulders","core"]),
                      ("Chest & Back",["chest","back"]),("Arms & Core",["arms","core"]),
                      ("Rest & Recovery",["rest"])],
            "maximal":[("Lower Body",["legs"]),("Upper Push",["chest","shoulders"]),
                       ("Rest & Accessory",["core","rest"]),("Lower Body Hinge",["legs","back"]),
                       ("Upper Pull",["back","arms"]),("Full Body",["chest","legs","core"]),
                       ("Rest & Recovery",["rest"])],
            "power":[("Snatch & Accessory",["olympic","legs"]),("Clean & Jerk",["olympic","back"]),
                     ("Strength Accessory",["legs","shoulders"]),("Technique + Pulls",["olympic","core"]),
                     ("Power Development",["power","legs"]),("Active Recovery",["mobility","recovery"]),
                     ("Rest & Recovery",["rest"])],
            "explosive":[("Lower Power",["power","legs"]),("Upper Power",["power","chest","back"]),
                         ("Plyometric Lower",["plyometric","legs"]),("Plyometric Upper",["plyometric","chest"]),
                         ("Full Power Circuit",["power","plyometric","core"]),("Active Recovery",["mobility"]),
                         ("Rest & Recovery",["rest"])],
            "full_body":[("Event Training A",["strongman","legs"]),("Upper Strength",["chest","back","shoulders"]),
                         ("Event Training B",["strongman","core"]),("Accessory Lower",["legs","core"]),
                         ("Event Training C",["strongman","back"]),("Active Recovery",["recovery","mobility"]),
                         ("Rest & Recovery",["rest"])],
            "static":[("Isometric Upper Push",["isometric","chest"]),("Isometric Upper Pull",["isometric","back"]),
                      ("Isometric Lower",["isometric","legs"]),("Isometric Core",["isometric","core"]),
                      ("Full Body Isometric",["isometric","shoulders","arms"]),("Mobility",["mobility"]),
                      ("Rest & Recovery",["rest"])],
            "aesthetic":[("Chest",["chest"]),("Back",["back"]),("Legs",["legs"]),
                         ("Shoulders",["shoulders"]),("Arms",["arms"]),
                         ("Core & Weak Points",["core","chest","back"]),("Rest & Recovery",["rest"])],
            "balanced":[("Upper Push",["chest","shoulders"]),("Lower Body",["legs"]),
                        ("Upper Pull",["back","arms"]),("Core & Cardio",["core","cardio"]),
                        ("Full Body",["chest","back","legs"]),("Active Recovery",["mobility","recovery"]),
                        ("Rest & Recovery",["rest"])],
        },
        "cardio":{
            "aerobic":[("Steady State Cardio",["cardio"]),("Core + Lower",["core","legs"]),
                       ("Cardio + Mobility",["cardio","mobility"]),("Upper + Cardio",["chest","back","cardio"]),
                       ("Long Cardio",["cardio"]),("Full Body + Stretch",["legs","core","mobility"]),
                       ("Rest & Recovery",["rest"])],
            "anaerobic":[("Anaerobic Intervals",["cardio","power"]),("Strength Lower",["legs"]),
                         ("Sprint Work",["cardio","agility"]),("Strength Upper",["chest","back"]),
                         ("Anaerobic Circuit",["cardio","core","power"]),("Active Recovery",["recovery","mobility"]),
                         ("Rest & Recovery",["rest"])],
        },
        "hiit":{
            "interval":[("HIIT Full Body",["cardio","core"]),("Strength + Power",["chest","back","power"]),
                        ("HIIT Lower",["cardio","legs","plyometric"]),("Upper Strength",["shoulders","arms","back"]),
                        ("MetCon Circuit",["cardio","core","power"]),("Legs + Core",["legs","core"]),
                        ("Rest & Recovery",["rest"])],
            "speed":[("Sprint Intervals",["cardio","agility"]),("Lower Strength",["legs","power"]),
                     ("Sprint Technique",["cardio","agility"]),("Upper Body",["chest","back","shoulders"]),
                     ("Speed Endurance",["cardio","legs"]),("Active Recovery",["recovery","mobility"]),
                     ("Rest & Recovery",["rest"])],
            "metabolic":[("MetCon A",["cardio","legs","core"]),("Upper MetCon",["chest","back","cardio"]),
                         ("Lower MetCon",["legs","cardio","plyometric"]),("Full Body MetCon",["cardio","core","power"]),
                         ("MetCon + Strength",["chest","back","legs"]),("Active Recovery",["recovery","mobility"]),
                         ("Rest & Recovery",["rest"])],
            "full_body":[("Bootcamp Circuit A",["cardio","core","legs"]),("Upper Bootcamp",["chest","back","shoulders"]),
                         ("Bootcamp Circuit B",["cardio","plyometric","core"]),("Lower Bootcamp",["legs","cardio"]),
                         ("Full Bootcamp",["chest","back","legs","core"]),("Active Recovery",["recovery"]),
                         ("Rest & Recovery",["rest"])],
        },
        "endurance":{
            "endurance":[("Long Cardio",["cardio"]),("Leg Endurance",["legs","core"]),
                         ("Mid Cardio + Upper",["cardio","chest","back"]),("Core + Mobility",["core","mobility"]),
                         ("Tempo",["cardio"]),("Full Body Endurance",["legs","core","cardio"]),
                         ("Rest & Recovery",["rest"])],
            "circuit":[("Upper Circuit",["chest","back","shoulders","arms"]),("Lower Circuit",["legs","core"]),
                       ("Full Body Circuit A",["chest","legs","cardio"]),("Core + Cardio",["core","cardio"]),
                       ("Full Body Circuit B",["back","legs","core"]),("Active Recovery",["recovery","mobility"]),
                       ("Rest & Recovery",["rest"])],
        },
        "functional":{
            "movement":[("Hinge Pattern",["back","legs"]),("Push Pattern",["chest","shoulders"]),
                        ("Carry + Core",["core","agility"]),("Pull Pattern",["back","arms"]),
                        ("Squat + Lunge",["legs","core"]),("Rotation + Cardio",["core","cardio"]),
                        ("Rest & Recovery",["rest"])],
            "bodyweight":[("Push Skills",["chest","shoulders","arms"]),("Pull Skills",["back","arms"]),
                          ("Lower Skills",["legs","core"]),("Core Skills",["core","chest"]),
                          ("Full Body Skills",["chest","back","legs","core"]),("Skill + Flex",["mobility","core"]),
                          ("Rest & Recovery",["rest"])],
            "performance":[("Speed + Agility",["agility","legs"]),("Power Development",["power","legs"]),
                           ("Upper Strength",["chest","back","shoulders"]),("Change of Direction",["agility","legs","core"]),
                           ("Sport Power",["power","plyometric","core"]),("Active Recovery",["recovery","mobility"]),
                           ("Rest & Recovery",["rest"])],
            "sport":[("Speed + Power",["agility","power","legs"]),("Upper Strength",["chest","back","shoulders"]),
                     ("Agility Drills",["agility","core"]),("Lower Strength",["legs","core"]),
                     ("Sport Simulation",["cardio","power","agility"]),("Recovery + Mobility",["recovery","mobility"]),
                     ("Rest & Recovery",["rest"])],
            "ballistic":[("KB Lower",["kettlebell","legs"]),("KB Upper Push",["kettlebell","chest","shoulders"]),
                         ("KB Full Body A",["kettlebell","core"]),("KB Upper Pull",["kettlebell","back","arms"]),
                         ("KB Full Body B",["kettlebell","legs","core"]),("Active Recovery",["recovery","mobility"]),
                         ("Rest & Recovery",["rest"])],
            "stability":[("TRX Upper Push",["trx","chest","shoulders"]),("TRX Upper Pull",["trx","back","arms"]),
                         ("TRX Lower",["trx","legs"]),("TRX Core",["trx","core"]),
                         ("TRX Full Body",["trx","chest","back","legs"]),("Mobility + Stretch",["mobility"]),
                         ("Rest & Recovery",["rest"])],
            "speed":[("Speed Drills",["agility","cardio"]),("Lower Power",["legs","power","plyometric"]),
                     ("Agility Circuits",["agility","core"]),("Upper Strength",["chest","back","shoulders"]),
                     ("Speed Endurance",["cardio","agility","legs"]),("Active Recovery",["recovery","mobility"]),
                     ("Rest & Recovery",["rest"])],
            "combat":[("Striking + Footwork",["cardio","agility","core"]),("Upper Strength",["chest","back","shoulders"]),
                      ("Kicking + Agility",["legs","agility","cardio"]),("Grappling Conditioning",["core","back","legs"]),
                      ("Pad Work",["cardio","power","core"]),("Active Recovery",["recovery","mobility"]),
                      ("Rest & Recovery",["rest"])],
        },
        "mobility":{
            "stretch":[("Upper Flexibility",["mobility","chest","shoulders"]),("Lower Flexibility",["mobility","legs"]),
                       ("Spine + Core",["mobility","core"]),("Hip & Groin",["mobility","legs"]),
                       ("Full Body Stretch",["mobility"]),("Restorative Yoga",["yoga","recovery"]),
                       ("Rest & Recovery",["rest"])],
            "joint":[("Hip & Ankle Mobility",["mobility","legs"]),("Shoulder Mobility",["mobility","shoulders"]),
                     ("Spine Mobility",["mobility","core","back"]),("Full Body Mobility",["mobility"]),
                     ("Joint Circuit",["mobility","agility"]),("Yoga Flow",["yoga"]),
                     ("Rest & Recovery",["rest"])],
            "mindful":[("Morning Flow",["yoga","mobility"]),("Strength Yoga",["yoga","core","legs"]),
                       ("Restorative",["yoga","recovery"]),("Balance + Focus",["yoga","core"]),
                       ("Hip Opening Flow",["yoga","legs","mobility"]),("Full Body Flow",["yoga","mobility"]),
                       ("Yoga Nidra",["recovery"])],
            "core_flex":[("Pilates Core",["pilates","core"]),("Pilates Lower",["pilates","legs"]),
                         ("Pilates Upper",["pilates","chest","back"]),("Pilates Full Body",["pilates","core","legs"]),
                         ("Pilates + Mobility",["pilates","mobility"]),("Active Recovery",["recovery"]),
                         ("Rest & Recovery",["rest"])],
            "balance":[("Balance Lower",["legs","isometric","core"]),("Balance Upper",["shoulders","core","isometric"]),
                       ("Proprioception Circuit",["agility","core","legs"]),("Full Body Stability",["isometric","core","legs"]),
                       ("Balance + Mobility",["mobility","isometric"]),("Active Recovery",["recovery"]),
                       ("Rest & Recovery",["rest"])],
            "core":[("Anterior Core",["core"]),("Posterior Core",["core","back"]),
                    ("Lateral Core",["core"]),("Core + Cardio",["core","cardio"]),
                    ("Rotational Core",["core","agility"]),("Core + Mobility",["core","mobility"]),
                    ("Rest & Recovery",["rest"])],
        },
        "hybrid":{
            "variety":[("Cardio + Strength",["cardio","chest","back"]),("Legs + Core",["legs","core"]),
                       ("HIIT + Upper",["cardio","shoulders","arms"]),("Mobility + Lower",["legs","mobility"]),
                       ("Full Body Circuit",["chest","legs","cardio","core"]),("Active Recovery",["recovery","mobility"]),
                       ("Rest & Recovery",["rest"])],
            "aesthetics_function":[("Push + Conditioning",["chest","shoulders","cardio"]),
                                   ("Pull + Conditioning",["back","arms","cardio"]),
                                   ("Leg + Power",["legs","power"]),("Shoulder + Core",["shoulders","core","isometric"]),
                                   ("Full Functional Body",["chest","back","legs","core"]),
                                   ("Active Recovery",["recovery","mobility"]),("Rest & Recovery",["rest"])],
            "resistance":[("Band Upper Push",["chest","shoulders"]),("Band Upper Pull",["back","arms"]),
                          ("Band Lower Body",["legs","core"]),("Band Full Body",["chest","back","legs"]),
                          ("Band Core + Cardio",["core","cardio"]),("Mobility + Stretch",["mobility"]),
                          ("Rest & Recovery",["rest"])],
        },
        "recovery":{
            "rest":[("Light Walk + Foam Roll",["recovery","cardio"]),("Upper Mobility",["mobility","shoulders","chest"]),
                    ("Lower Mobility",["mobility","legs"]),("Breathing + Core",["recovery","core"]),
                    ("Full Body Gentle",["recovery","mobility"]),("Yoga / Stretch",["yoga","recovery"]),
                    ("Rest & Recovery",["rest"])],
            "corrective":[("Movement Screen",["mobility","core"]),("Corrective Upper",["isometric","shoulders","back"]),
                          ("Corrective Lower",["isometric","legs","core"]),("Stability Work",["isometric","core","mobility"]),
                          ("Movement Integration",["mobility","agility","core"]),("Active Recovery",["recovery"]),
                          ("Rest & Recovery",["rest"])],
        },
    }

    cat_schedules = schedules.get(cat, schedules["hybrid"])
    schedule = cat_schedules.get(emph, list(cat_schedules.values())[0])

    # BMI injection handled in build_workout_plan
    return schedule, meta

# ============================================================
# WORKOUT PLAN BUILDER
# ============================================================
def get_plan_data(user_profile, injury_profile=None):
    """Returns the 7-day plan as structured data (no HTML), using the exact
    same schedule + exercise-selection logic as build_workout_plan, so the PDF
    can never disagree with what is shown on screen.
    Shape: list of {day, focus, is_rest, exercises:[{name,sets_reps,weight,muscles}]}"""
    goal    = user_profile["goal"]
    bmi_cat = user_profile["bmi_cat"]
    fatigue = user_profile["fatigue"]
    rl_rec  = user_profile["rl_rec"]

    has_injury  = injury_profile and injury_profile.get("has_injury") == "Yes"
    injury_part = injury_profile.get("body_part","") if has_injury else ""
    severity    = injury_profile.get("severity","")  if has_injury else ""
    blocked     = get_blocked_groups(injury_part, severity)  if has_injury else []
    modified    = get_modified_groups(injury_part, severity) if has_injury else []

    schedule, meta = get_schedule(goal, bmi_cat, fatigue, rl_rec)

    if bmi_cat in ["Overweight","Obese"]:
        schedule = [
            (label+(" + Cardio" if "cardio" not in groups and label!="Rest & Recovery" else ""),
             (["cardio"]+groups if "cardio" not in groups and label!="Rest & Recovery" else groups))
            for label,groups in schedule
        ]
    if fatigue == "Very Fatigued":
        schedule[0] = ("Active Recovery",["recovery","cardio"])
    if "REST" in rl_rec.upper() and fatigue != "Fully Rested":
        schedule[0] = ("Active Recovery",["recovery","mobility"])

    days = []
    for i,(focus,groups) in enumerate(schedule):
        is_rest = focus in ("Rest & Recovery","Active Recovery")
        day = {"day": i+1, "focus": focus, "is_rest": is_rest, "exercises": []}
        if not is_rest:
            for group in groups:
                exercises = pick_exercises(group,count=3,blocked=blocked,modified=modified,
                                           injury_part=injury_part,severity=severity)
                for name,sets_reps,weight,muscles,progression in exercises:
                    day["exercises"].append({
                        "name": name, "sets_reps": sets_reps,
                        "weight": weight, "muscles": muscles,
                    })
        days.append(day)
    return days


def get_exercise_reason(group, focus, meta, fatigue, cal_int,
                        injured=False, injury_part="", modified=False):
    """Returns a short, truthful 'why this exercise' string built only from
    signals the recommendation engine already produced -- no invented claims."""
    emph = meta.get("emphasis", "balanced")
    why_emph = _EMPHASIS_WHY.get(emph, "your selected training focus")
    g = (group or "").replace("_", " ")

    bits = []
    # core reason: goal emphasis + the muscle group this slot targets
    if g and g not in ("cardio", "recovery", "mobility"):
        bits.append(f"targets your {g} as part of {why_emph}")
    elif g == "cardio":
        bits.append("conditioning work to support your goal and recovery")
    elif g in ("recovery", "mobility"):
        bits.append("light movement to aid recovery without adding fatigue")
    else:
        bits.append(f"supports {why_emph}")

    # fatigue context (only when it actually shaped the choice)
    if fatigue == "Very Fatigued":
        bits.append("kept lighter today because you logged high fatigue")
    elif fatigue == "Fully Rested":
        bits.append("you're rested, so it's programmed at full effort")

    # injury context
    if modified:
        bits.append(f"adjusted to protect your {injury_part}")

    reason = "; ".join(bits)
    return reason[0].upper() + reason[1:] if reason else ""

def build_workout_plan(user_profile, injury_profile=None):
    goal    = user_profile["goal"]
    bmi_cat = user_profile["bmi_cat"]
    body    = user_profile["body_type"]
    fatigue = user_profile["fatigue"]
    rl_rec  = user_profile["rl_rec"]
    bmi     = user_profile["bmi"]
    age     = user_profile["age"]
    gender  = user_profile["gender"]
    cal_int = user_profile["calorie_intensity"]

    has_injury  = injury_profile and injury_profile.get("has_injury") == "Yes"
    injury_part = injury_profile.get("body_part","") if has_injury else ""
    severity    = injury_profile.get("severity","")  if has_injury else ""
    blocked     = get_blocked_groups(injury_part, severity)  if has_injury else []
    modified    = get_modified_groups(injury_part, severity) if has_injury else []

    schedule, meta = get_schedule(goal, bmi_cat, fatigue, rl_rec)

    # BMI adjustment
    if bmi_cat in ["Overweight","Obese"]:
        schedule = [
            (label+(" + Cardio" if "cardio" not in groups and label!="Rest & Recovery" else ""),
             (["cardio"]+groups if "cardio" not in groups and label!="Rest & Recovery" else groups))
            for label,groups in schedule
        ]

    # Fatigue adjustment
    if fatigue == "Very Fatigued":
        schedule[0] = ("Active Recovery",["recovery","cardio"])

    # RL adjustment
    if "REST" in rl_rec.upper() and fatigue != "Fully Rested":
        schedule[0] = ("Active Recovery",["recovery","mobility"])

    intensity       = meta["intensity"]
    intensity_labels= {1:"Recovery",2:"Light",3:"Moderate",4:"Hard",5:"Maximal"}
    intensity_label = intensity_labels.get(intensity,"Moderate")
    intensity_color = {1:"#6B7280",2:"#00B4FF",3:"#E8FF00",4:"#FF6B35",5:"#FF4D00"}.get(intensity,"#E8FF00")
    dc = ["#E8FF00","#FF6B35","#00B4FF","#00E676","#FF4D00","#E8FF00","#6B7280"]

    # Injury banner
    injury_banner = ""
    if has_injury:
        sev_color = {"Severe - no movement in this area":"#FF4D00",
                     "Moderate - light movement only":"#FF6B35",
                     "Low - can bear weight with caution":"#E8FF00"}.get(severity,"#FF6B35")
        injury_banner = (
            f"<div style='background:rgba(255,77,0,0.08);border:1px solid {sev_color}55;"
            f"border-left:4px solid {sev_color};border-radius:10px;"
            f"padding:1rem 1.3rem;margin-bottom:1.2rem;'>"
            f"<div style='font-size:0.75rem;font-weight:800;color:{sev_color};"
            f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;'>"
            f"Injury-Aware Plan Active - {injury_part} ({severity})</div>"
            f"<div style='font-size:0.85rem;color:#FCA5A5;line-height:1.6;'>"
            f"Plan modified for your {injury_part} injury. "
            f"Affected exercises {'completely removed' if 'Severe' in severity else 'replaced with safe alternatives'}. "
            f"Always consult a physiotherapist. Stop if pain exceeds 3/10.</div></div>"
        )

    html = (
        "<div style='font-family:Arial,sans-serif;color:#F0F2F5;background:#080A0E;padding:8px;'>"
        + injury_banner +
        "<div style='background:linear-gradient(135deg,#0F1218,#161B24);"
        "border:1px solid rgba(232,255,0,0.2);border-radius:16px;"
        "padding:1.5rem 2rem;margin-bottom:1.5rem;"
        "display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;'>"
        f"<div style='font-size:3rem;font-weight:900;color:#E8FF00;line-height:1;'>{bmi}</div>"
        "<div style='flex:1;min-width:200px;'>"
        "<div style='font-size:0.7rem;letter-spacing:0.15em;color:#6B7280;"
        "text-transform:uppercase;margin-bottom:4px;'>Personalised for</div>"
        f"<div style='font-size:1.3rem;font-weight:700;color:#F0F2F5;'>"
        f"{age}-year-old {gender} - {body} - {goal}</div>"
        f"<div style='font-size:0.85rem;color:#6B7280;margin-top:2px;'>"
        f"BMI: {bmi_cat} - Calorie Intensity: {cal_int} - RL: {rl_rec}</div>"
        f"<div style='margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;'>"
        f"<span style='background:{intensity_color}22;border:1px solid {intensity_color}55;"
        f"color:{intensity_color};font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
        f"text-transform:uppercase;padding:3px 10px;border-radius:4px;'>"
        f"Intensity: {intensity_label}</span>"
        f"<span style='background:rgba(232,255,0,0.08);border:1px solid rgba(232,255,0,0.2);"
        f"color:#E8FF00;font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
        f"text-transform:uppercase;padding:3px 10px;border-radius:4px;'>"
        f"{meta['cat'].upper()} - {meta['emphasis'].replace('_',' ').upper()}</span>"
        f"</div></div></div>"
    )

    for i,(focus,groups) in enumerate(schedule):
        color   = dc[i % len(dc)]
        is_rest = focus in ("Rest & Recovery","Active Recovery")

        html += (
            f"<div style='margin-bottom:1rem;border-radius:14px;overflow:hidden;"
            f"border:1px solid rgba(255,255,255,0.06);'>"
            f"<div style='background:linear-gradient(90deg,{color}22,#0F1218);"
            f"padding:1rem 1.5rem;display:flex;align-items:center;gap:1rem;"
            f"border-bottom:1px solid {color}44;'>"
            f"<div style='background:{color};color:#000;font-weight:900;"
            f"font-size:0.75rem;letter-spacing:0.1em;padding:4px 10px;border-radius:4px;'>DAY {i+1}</div>"
            f"<div style='font-size:1.4rem;font-weight:800;color:#F0F2F5;"
            f"letter-spacing:0.03em;'>{focus.upper()}</div></div>"
        )

        if is_rest:
            html += ("<div style='background:#0F1218;padding:1.2rem 1.5rem;"
                     "color:#6B7280;font-size:0.95rem;font-style:italic;'>"
                     "Recovery day. Sleep 7-9 hours, stay hydrated, do light stretching or yoga. "
                     "Growth happens during rest.</div>")
        else:
            html += "<div style='background:#0F1218;padding:1rem 1.5rem;'>"
            day_has = False
            for group in groups:
                exercises = pick_exercises(group,count=3,blocked=blocked,modified=modified,
                                           injury_part=injury_part,severity=severity)
                if not exercises: continue
                day_has = True
                if len(groups)>1:
                    html += (f"<div style='font-size:0.65rem;letter-spacing:0.15em;color:#6B7280;"
                             f"text-transform:uppercase;margin:0.75rem 0 0.5rem;'>-- {group.upper()}</div>")
                _is_mod = (group in modified) if modified else False
                _reason = get_exercise_reason(group, focus, meta, fatigue, cal_int,
                                              injured=has_injury, injury_part=injury_part, modified=_is_mod)
                for name,sets_reps,weight,muscles,progression in exercises:
                    _info = get_exercise_info(name, muscles)
                    _anim = get_exercise_animation(name, color)
                    _cues = "".join(f"<li style='margin-bottom:3px;'>{c}</li>" for c in _info["cues"])
                    _desc = (f"<div style='font-size:0.8rem;color:#C7CDD6;margin-bottom:5px;line-height:1.4;'>{_info['desc']}</div>" if _info["desc"] else "")
                    html += (
                        f"<div style='background:#161B24;border-radius:10px;padding:0.9rem 1.1rem;"
                        f"margin-bottom:0.6rem;border-left:3px solid {color};'>"
                        f"<div style='display:grid;grid-template-columns:1fr auto;gap:0.5rem;align-items:start;'>"
                        f"<div><div style='font-size:1.05rem;font-weight:700;color:#F0F2F5;margin-bottom:3px;'>{name}</div>"
                        f"{_desc}"
                        f"<div style='font-size:0.78rem;color:#9CA3AF;margin-bottom:6px;'>{muscles}</div>"
                        f"<div style='font-size:0.74rem;color:{color};margin-bottom:6px;display:flex;gap:5px;align-items:flex-start;'>"
                        f"<span style='font-weight:800;'>Why this?</span>"
                        f"<span style='color:#B8C0CC;font-weight:400;'>{_reason}</span></div>"
                        f"<div style='font-size:0.75rem;color:#6B7280;font-style:italic;'>^ {progression}</div></div>"
                        f"<div style='text-align:right;flex-shrink:0;'>"
                        f"<div style='font-size:1.1rem;font-weight:800;color:{color};'>{sets_reps}</div>"
                        f"<div style='font-size:0.72rem;color:#6B7280;margin-top:2px;'>{weight}</div>"
                        f"</div></div>"
                        f"<details style='margin-top:0.6rem;'>"
                        f"<summary style='cursor:pointer;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;"
                        f"text-transform:uppercase;color:{color};'>How to do it</summary>"
                        f"<div style='margin-top:0.6rem;padding-top:0.6rem;border-top:1px solid rgba(255,255,255,0.06);'>"
                        f"{_anim}"
                        f"<ul style='margin:0 0 0.5rem 1.1rem;padding:0;font-size:0.8rem;color:#C7CDD6;line-height:1.55;'>{_cues}</ul>"
                        f"<div style='font-size:0.78rem;color:#F2A3A3;margin-bottom:0.6rem;'>Avoid: {_info['mistake']}</div>"
                        f"<a href='{_info['demo']}' target='_blank' style='display:inline-block;font-size:0.72rem;"
                        f"font-weight:700;color:#000;background:{color};padding:6px 12px;border-radius:6px;text-decoration:none;'>\u25b6 Watch full video (online)</a>"
                        f"</div></details>"
                        f"</div>"
                    )
            if not day_has:
                html += (
                    "<div style='background:rgba(255,77,0,0.05);border:1px solid rgba(255,77,0,0.2);"
                    "border-radius:8px;padding:0.8rem 1rem;color:#FCA5A5;font-size:0.88rem;'>"
                    f"All exercises for this day affect your {injury_part} injury. "
                    "Replaced with rest and light mobility work.</div>"
                )
            html += "</div>"
        html += "</div>"

    # Tips
    tips = []
    if bmi_cat=="Underweight":
        tips.append(("FUEL YOUR GROWTH","Aim for a calorie surplus with high-protein meals - eggs, chicken, lentils, and nuts are your allies."))
    elif bmi_cat in ["Overweight","Obese"]:
        tips.append(("EVERY STEP COUNTS","Consistent daily movement compounds into extraordinary results. You do not need to be perfect, just consistent."))
    else:
        tips.append(("CONSISTENCY WINS","Showing up 4 days a week for 3 months destroys an intense week followed by burnout."))

    body_tips = {
        "Ectomorph":("LIFT HEAVY, REST WELL","Focus on compound lifts, eat plenty of protein, and sleep 7-9 hours to trigger muscle growth."),
        "Mesomorph":("PUSH THE OVERLOAD","You respond faster than most. Add weight or reps every single week to maintain your edge."),
        "Endomorph":("CARDIO IS YOUR WEAPON","Your metabolism responds incredibly well to consistent cardio. Keep your heart rate up."),
    }
    tips.append(body_tips.get(body,body_tips["Mesomorph"]))

    training_tips = {
        "strength":  ("PROGRESSIVE OVERLOAD IS THE LAW","Every week, add 1 more rep or a small amount more weight. That micro-improvement creates lasting change."),
        "cardio":    ("TRAIN YOUR HEART LIKE A MUSCLE","60-70% max HR builds aerobic base. 70-85% develops cardiovascular power. Both matter."),
        "hiit":      ("QUALITY OVER QUANTITY","HIIT is only as effective as your recovery. Match every hard interval with genuine rest."),
        "endurance": ("BUILD YOUR BASE SLOWLY","Add no more than 10% volume per week. Patience prevents injury and builds a foundation that lasts."),
        "functional":("MOVE WELL BEFORE YOU MOVE HEAVY","Master the hinge, squat, push, pull, carry, and rotate. Movement efficiency transfers to everything."),
        "mobility":  ("CONSISTENCY BEATS INTENSITY","10 minutes daily produces better results than 1 hour once per week. Make it non-negotiable."),
        "hybrid":    ("VARIETY IS YOUR SUPERPOWER","Cross-training reduces injury risk, breaks plateaus, and keeps you motivated. Keep your body guessing."),
        "recovery":  ("REST IS TRAINING","Elite athletes treat recovery as seriously as their hardest sessions. Sleep and nutrition are not optional extras."),
    }
    tips.append(training_tips.get(meta["cat"],training_tips["hybrid"]))

    tc = ["#E8FF00","#FF6B35","#00B4FF"]
    html += ("<div style='margin-top:1.5rem;'><div style='font-size:1.3rem;font-weight:800;color:#F0F2F5;"
             "margin-bottom:1rem;text-transform:uppercase;'>Your 3 Personal Tips</div>")
    for j,(title,body_text) in enumerate(tips):
        c = tc[j%len(tc)]
        html += (f"<div style='background:#0F1218;border:1px solid {c}44;"
                 f"border-left:4px solid {c};border-radius:10px;padding:1rem 1.3rem;margin-bottom:0.75rem;'>"
                 f"<div style='font-size:0.8rem;font-weight:800;color:{c};"
                 f"letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px;'>{j+1}. {title}</div>"
                 f"<div style='font-size:0.9rem;color:#9CA3AF;line-height:1.6;'>{body_text}</div></div>")
    html += "</div></div>"
    return html

# ============================================================
# REHAB PROTOCOLS
# ============================================================

def render_rehab_html(condition, user_profile):
    protocol = REHAB_PROTOCOLS.get(condition)
    if not protocol:
        return "<div style='color:#9CA3AF;padding:1rem;'>Protocol not found.</div>"
    age=user_profile.get("age",25); gender=user_profile.get("gender","")
    bmi=user_profile.get("bmi",""); bmi_cat=user_profile.get("bmi_cat","")
    dc=["#FF4D00","#FF6B35","#E8FF00","#00E676","#00B4FF","#E8FF00","#6B7280"]
    html=(
        "<div style='font-family:Arial,sans-serif;color:#F0F2F5;background:#080A0E;padding:8px;'>"
        "<div style='background:linear-gradient(135deg,#1a0505,#0F1218);"
        "border:1px solid rgba(255,77,0,0.4);border-radius:16px;padding:1.5rem 2rem;margin-bottom:1.5rem;'>"
        "<div style='font-size:0.65rem;letter-spacing:0.2em;color:#FF4D00;text-transform:uppercase;margin-bottom:6px;'>Rehabilitation Protocol</div>"
        f"<div style='font-size:1.6rem;font-weight:800;color:#F0F2F5;margin-bottom:4px;'>{protocol['phase']}</div>"
        f"<div style='font-size:0.85rem;color:#6B7280;'>For: {age}-year-old {gender} - BMI {bmi} ({bmi_cat})</div></div>"
        f"<div style='background:rgba(255,77,0,0.1);border:1px solid rgba(255,77,0,0.4);"
        f"border-left:4px solid #FF4D00;border-radius:10px;padding:1rem 1.3rem;margin-bottom:1.5rem;'>"
        f"<div style='font-size:0.75rem;font-weight:800;color:#FF4D00;letter-spacing:0.1em;"
        f"text-transform:uppercase;margin-bottom:4px;'>Clinical Safety Warning</div>"
        f"<div style='font-size:0.9rem;color:#FCA5A5;line-height:1.6;'>{protocol['warning']}</div></div>"
    )
    for i,(day_label,exercises) in enumerate(protocol["program"]):
        color=dc[i%len(dc)]
        html+=(f"<div style='margin-bottom:1rem;border-radius:14px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);'>"
               f"<div style='background:linear-gradient(90deg,{color}22,#0F1218);padding:1rem 1.5rem;"
               f"display:flex;align-items:center;gap:1rem;border-bottom:1px solid {color}44;'>"
               f"<div style='background:{color};color:#000;font-weight:900;font-size:0.75rem;"
               f"letter-spacing:0.1em;padding:4px 10px;border-radius:4px;'>REHAB</div>"
               f"<div style='font-size:1.3rem;font-weight:800;color:#F0F2F5;'>{day_label.upper()}</div></div>"
               f"<div style='background:#0F1218;padding:1rem 1.5rem;'>")
        for name,sets_reps,weight,muscles,notes in exercises:
            html+=(f"<div style='background:#161B24;border-radius:10px;padding:0.9rem 1.1rem;"
                   f"margin-bottom:0.6rem;border-left:3px solid {color};"
                   f"display:grid;grid-template-columns:1fr auto;gap:0.5rem;align-items:start;'>"
                   f"<div><div style='font-size:1.05rem;font-weight:700;color:#F0F2F5;margin-bottom:3px;'>{name}</div>"
                   f"<div style='font-size:0.78rem;color:#9CA3AF;margin-bottom:4px;'>{muscles}</div>"
                   f"<div style='font-size:0.75rem;color:#6B7280;font-style:italic;'>Info: {notes}</div></div>"
                   f"<div style='text-align:right;flex-shrink:0;'>"
                   f"<div style='font-size:1.1rem;font-weight:800;color:{color};'>{sets_reps}</div>"
                   f"<div style='font-size:0.72rem;color:#6B7280;margin-top:2px;'>{weight}</div>"
                   f"</div></div>")
        html+="</div></div>"
    principles=[("Pain is your guide","If pain exceeds 3/10 during any exercise - stop immediately."),
                ("Consistency over intensity","5 min daily beats 30 min twice weekly for rehabilitation."),
                ("Sleep is treatment","8-9 hours of sleep accelerates tissue healing significantly."),
                ("Progress is not linear","Some days will feel worse. This is normal. Stay patient."),
                ("See a professional","This program supplements but does not replace physiotherapy."),
                ("Nutrition matters","Protein 1.6g/kg bodyweight supports tissue repair and recovery.")]
    html+=("<div style='background:linear-gradient(135deg,rgba(0,230,118,0.06),#0F1218);"
           "border:1px solid rgba(0,230,118,0.2);border-radius:14px;padding:1.2rem 1.5rem;margin-top:1rem;'>"
           "<div style='font-size:0.75rem;font-weight:800;color:#00E676;letter-spacing:0.1em;"
           "text-transform:uppercase;margin-bottom:0.75rem;'>Clinical Recovery Principles</div>"
           "<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;'>")
    for title,body in principles:
        html+=(f"<div style='background:#0F1218;border:1px solid rgba(0,230,118,0.1);border-radius:8px;padding:0.7rem 0.9rem;'>"
               f"<div style='font-size:0.75rem;font-weight:700;color:#00E676;margin-bottom:3px;'>{title}</div>"
               f"<div style='font-size:0.75rem;color:#6B7280;line-height:1.5;'>{body}</div></div>")
    html+="</div></div></div>"
    return html

# ============================================================
# PROGRESS CHARTS
# ============================================================
def render_progress_charts(history):
    if len(history)<2: st.info("Log at least 2 days to see progress charts."); return
    df=pd.DataFrame(history); df["date"]=pd.to_datetime(df["date"]); df=df.sort_values("date")
    bg,grid,muted="rgba(0,0,0,0)","rgba(255,255,255,0.05)","#6B7280"
    def ly(title):
        return dict(title=dict(text=title,font=dict(color="#F0F2F5",size=13,family="Barlow Condensed"),x=0),
                    paper_bgcolor=bg,plot_bgcolor=bg,font=dict(color=muted,size=11),
                    margin=dict(l=10,r=10,t=40,b=30),height=220,
                    xaxis=dict(gridcolor=grid,showline=False,tickfont=dict(size=10)),
                    yaxis=dict(gridcolor=grid,showline=False,tickfont=dict(size=10)))
    c1,c2=st.columns(2)
    with c1:
        fig=go.Figure(); fig.add_trace(go.Scatter(x=df["date"],y=df["steps"],mode="lines+markers",
            line=dict(color="#E8FF00",width=2),marker=dict(size=5,color="#E8FF00"),
            fill="tozeroy",fillcolor="rgba(232,255,0,0.06)",name="Steps"))
        fig.update_layout(**ly("Daily Steps")); st.plotly_chart(fig,width='stretch',config={"displayModeBar":False})
    with c2:
        fig=go.Figure(); fig.add_trace(go.Bar(x=df["date"],y=df["active_minutes"],marker_color="#00B4FF",opacity=0.85,name="Active Min"))
        fig.update_layout(**ly("Active Minutes")); st.plotly_chart(fig,width='stretch',config={"displayModeBar":False})
    # BMI + GA Score charts only render if those columns have data (older rows may lack them)
    has_bmi = "bmi" in df.columns and df["bmi"].notna().any()
    has_cal = "calorie_score" in df.columns and df["calorie_score"].notna().any()
    if has_bmi or has_cal:
        c3,c4=st.columns(2)
        if has_bmi:
            with c3:
                fig=go.Figure(); fig.add_trace(go.Scatter(x=df["date"],y=df["bmi"],mode="lines+markers",
                    line=dict(color="#FF6B35",width=2),marker=dict(size=5,color="#FF6B35"),name="BMI"))
                fig.add_hrect(y0=18.5,y1=24.9,fillcolor="rgba(0,230,118,0.05)",line_width=0,
                    annotation_text="Normal",annotation_font=dict(size=10,color="#00E676"))
                fig.update_layout(**ly("BMI Trend")); st.plotly_chart(fig,width='stretch',config={"displayModeBar":False})
        if has_cal:
            with c4:
                fig=go.Figure(); fig.add_trace(go.Scatter(x=df["date"],y=df["calorie_score"],mode="lines+markers",
                    line=dict(color="#FF4D00",width=2),marker=dict(size=5,color="#FF4D00"),
                    fill="tozeroy",fillcolor="rgba(255,77,0,0.06)",name="GA Score"))
                fig.update_layout(**ly("GA Calorie Score")); st.plotly_chart(fig,width='stretch',config={"displayModeBar":False})

# ============================================================
# PDF EXPORT — unicode safe
# ============================================================
def generate_pdf(user_profile,bmi,bmi_cat,norm_calories,calorie_intensity,
                 rl_rec,rl_tip,streak,total_sessions,badges,injury_profile=None,
                 plan_days=None):
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        return None

    def clean(text):
        return (str(text).replace("\u2014","-").replace("\u2013","-").replace("\u00b7",".")
                .replace("\u2022","-").replace("\u2019","'").replace("\u2018","'")
                .replace("\u201c",'"').replace("\u201d",'"').replace("\u2026","..."))

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(8,10,14); self.rect(0,0,210,297,'F')
            self.set_font("Helvetica","B",28); self.set_text_color(232,255,0)
            self.cell(0,14,"FITGENIX",new_x=XPos.LMARGIN, new_y=YPos.NEXT,align="C")
            self.set_font("Helvetica","",9); self.set_text_color(107,114,128)
            self.cell(0,6,"Adaptive Fitness Intelligence Report",new_x=XPos.LMARGIN, new_y=YPos.NEXT,align="C"); self.ln(4)
        def section(self,title):
            self.set_font("Helvetica","B",11); self.set_text_color(232,255,0)
            self.cell(0,8,clean(title).upper(),new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_draw_color(232,255,0); self.set_line_width(0.3)
            self.line(10,self.get_y(),200,self.get_y()); self.ln(3)
        def row(self,label,value):
            self.set_font("Helvetica","",9); self.set_text_color(107,114,128)
            self.cell(55,7,clean(label),new_x=XPos.RIGHT, new_y=YPos.TOP); self.set_text_color(240,242,245)
            self.cell(0,7,clean(value),new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        def day_header(self,n,focus):
            self.ln(2); self.set_fill_color(232,255,0); self.set_text_color(0,0,0)
            self.set_font("Helvetica","B",10)
            self.cell(20,8,f"DAY {n}",new_x=XPos.RIGHT, new_y=YPos.TOP,fill=True)
            self.set_text_color(240,242,245); self.set_font("Helvetica","B",11)
            self.cell(0,8,"  "+clean(focus).upper(),new_x=XPos.LMARGIN, new_y=YPos.NEXT); self.ln(1)
        def exercise(self,name,sets_reps,weight,muscles):
            self.set_font("Helvetica","B",9); self.set_text_color(240,242,245)
            self.cell(120,6,clean(name),new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font("Helvetica","B",9); self.set_text_color(232,255,0)
            self.cell(0,6,clean(sets_reps)+("  ("+clean(weight)+")" if weight else ""),new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            if muscles:
                self.set_font("Helvetica","",8); self.set_text_color(107,114,128)
                self.cell(0,5,"   "+clean(muscles),new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        def rest_note(self):
            self.set_font("Helvetica","I",9); self.set_text_color(107,114,128)
            self.multi_cell(0,5,"Recovery day. Sleep 7-9 hours, hydrate, light stretching or yoga.")

    pdf=PDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True,margin=15)
    pdf.set_font("Helvetica","",8); pdf.set_text_color(107,114,128)
    pdf.cell(0,6,f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}",new_x=XPos.LMARGIN, new_y=YPos.NEXT,align="R"); pdf.ln(2)
    pdf.section("Profile")
    pdf.row("Age",f"{user_profile['age']} years"); pdf.row("Gender",user_profile['gender'])
    pdf.row("Height",f"{user_profile['height']} cm"); pdf.row("Weight",f"{user_profile['weight']} kg")
    pdf.row("Body Type",user_profile['body_type']); pdf.row("Training Type",user_profile['goal']); pdf.ln(4)
    pdf.section("Analysis")
    pdf.row("BMI",f"{bmi} - {bmi_cat}")
    pdf.row("Active Minutes",f"{user_profile['active_minutes']} min")
    pdf.row("Total Steps",f"{user_profile['steps']:,}")
    pdf.row("Calorie Intensity",f"{calorie_intensity} (GA Score: {norm_calories:.3f})")
    pdf.row("Fatigue",user_profile['fatigue']); pdf.ln(4)
    if injury_profile and injury_profile.get("has_injury")=="Yes":
        pdf.section("Injury Profile")
        pdf.row("Body Part",injury_profile.get("body_part",""))
        pdf.row("Severity",injury_profile.get("severity","")); pdf.ln(4)
    pdf.section("RL Recommendation"); pdf.row("Action",rl_rec)
    pdf.set_font("Helvetica","I",9); pdf.set_text_color(156,163,175)
    pdf.multi_cell(0,6,clean(rl_tip)); pdf.ln(4)
    pdf.section("Progress"); pdf.row("Current Streak",f"{streak} days")
    pdf.row("Total Sessions",str(total_sessions))
    if badges: pdf.row("Badges","  ".join([n for _,n,_ in badges]))
    if plan_days:
        pdf.ln(2); pdf.section("Your 7-Day Plan")
        for d in plan_days:
            pdf.day_header(d["day"], d["focus"])
            if d["is_rest"] or not d["exercises"]:
                pdf.rest_note()
            else:
                for ex in d["exercises"]:
                    pdf.exercise(ex["name"], ex["sets_reps"], ex.get("weight",""), ex.get("muscles",""))
            pdf.ln(1)
    pdf.set_y(-20); pdf.set_font("Helvetica","",7); pdf.set_text_color(55,65,81)
    pdf.cell(0,5,"FITGENIX - GA + RL + 39 Training Types + Injury-Aware AI Coach",align="C")
    # Coerce to real bytes: fpdf2 may return bytearray/str depending on version,
    # and Streamlit's download_button requires bytes.
    out = pdf.output()
    if isinstance(out, (bytearray, memoryview)):
        out = bytes(out)
    elif isinstance(out, str):
        out = out.encode("latin-1")
    return out

# ============================================================
# AUTHENTICATION GATE  (Supabase) -- must be logged in to use the app
# ============================================================
@st.cache_resource
def _sb_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = _sb_client()
except Exception as _e:
    st.error("Could not connect to the account service. Please try again shortly.")
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

def _do_logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.rerun()

if st.session_state.user is None:
    # ---- Login / Sign-up screen (inherits the app CSS already loaded above) ----
    st.markdown("""
    <div style="text-align:center;padding:2.5rem 0 0.5rem;">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:0.75rem;
                  letter-spacing:0.25em;color:#E8FF00;text-transform:uppercase;margin-bottom:0.5rem;">
        Adaptive Fitness Intelligence
      </div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:4rem;font-weight:900;
                  line-height:0.9;color:#F0F2F5;letter-spacing:-0.02em;">
        FIT<span style="color:#E8FF00;">GENIX</span>
      </div>
      <div style="font-size:0.95rem;color:#6B7280;margin-top:0.6rem;font-weight:300;">
        Log in or create an account to continue
      </div>
    </div>
    """, unsafe_allow_html=True)

    _c1, _c2, _c3 = st.columns([1, 1.4, 1])
    with _c2:
        _tab_login, _tab_signup = st.tabs(["Log in", "Sign up"])

        with _tab_login:
            _le = st.text_input("Email", key="login_email")
            _lp = st.text_input("Password", type="password", key="login_pw")
            if st.button("Log in", width='stretch', key="btn_login"):
                if not _le or not _lp:
                    st.warning("Please enter your email and password.")
                else:
                    try:
                        _r = supabase.auth.sign_in_with_password({"email": _le, "password": _lp})
                        if _r.user:
                            st.session_state.user = _r.user
                            st.rerun()
                        else:
                            st.error("Login failed. Please check your details.")
                    except Exception as _e:
                        st.error("Login failed. Please check your email and password.")

        with _tab_signup:
            _se = st.text_input("Email", key="signup_email")
            _sp = st.text_input("Password (min 6 characters)", type="password", key="signup_pw")
            if st.button("Create account", width='stretch', key="btn_signup"):
                if not _se or len(_sp) < 6:
                    st.warning("Enter an email and a password of at least 6 characters.")
                else:
                    try:
                        _r = supabase.auth.sign_up({"email": _se, "password": _sp})
                        if _r.user:
                            st.session_state.user = _r.user
                            st.rerun()
                        else:
                            st.error("Could not create the account. Please try a different email.")
                    except Exception as _e:
                        _msg = str(_e).lower()
                        if "registered" in _msg or "exists" in _msg:
                            st.error("That email is already registered. Try logging in instead.")
                        else:
                            st.error("Sign up failed. Please try again.")
    st.stop()

# From here on, st.session_state.user is guaranteed to be a logged-in user.
USER = st.session_state.user
USER_ID = USER.id

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1rem;">
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:0.75rem;
              letter-spacing:0.25em;color:#E8FF00;text-transform:uppercase;margin-bottom:0.5rem;">
    Powered by Genetic Algorithm - Reinforcement Learning - 39 Training Modalities
  </div>
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:4.5rem;font-weight:900;
              line-height:0.9;color:#F0F2F5;letter-spacing:-0.02em;">
    FIT<span style="color:#E8FF00;">GENIX</span>
  </div>
  <div style="font-size:1rem;color:#6B7280;margin-top:0.6rem;font-weight:300;">
    Adaptive - Injury-aware - Clinically informed - 39 training modalities
  </div>
</div>
<hr style="border:none;border-top:1px solid rgba(232,255,0,0.15);margin:1rem 0 2rem;">
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"<div style='font-size:0.8rem;color:#9CA3AF;margin-bottom:0.25rem;'>"
                f"Signed in as <span style='color:#E8FF00;'>{USER.email}</span></div>", unsafe_allow_html=True)
    if st.button("Log out", key="btn_logout_sidebar"):
        _do_logout()
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)
    show_metrics = st.checkbox("Show Model Performance", value=False, key="show_metrics_toggle")
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.4rem;font-weight:800;
                color:#E8FF00;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.25rem;">
      Your Data</div>
    <div style="font-size:0.78rem;color:#6B7280;margin-bottom:1rem;">Fill all fields - Hit Generate</div>
    """, unsafe_allow_html=True)

    st.markdown("**TODAY'S ACTIVITY**")
    steps          = st.number_input("Total Steps",        0,    40000, 8000, 100)
    distance       = st.number_input("Distance (km)",      0.0,  30.0,  5.5,  0.1)
    very_active    = st.number_input("Very Active Min",    0,    300,   30)
    fairly_active  = st.number_input("Fairly Active Min",  0,    300,   20)
    lightly_active = st.number_input("Lightly Active Min", 0,    300,   60)
    fatigue_map    = {"Fully Rested":0,"Slightly Fatigued":1,"Very Fatigued":2}
    fatigue_choice = st.select_slider("Energy Level", options=list(fatigue_map.keys()))
    fatigue_level  = fatigue_map[fatigue_choice]

    st.markdown("---")
    st.markdown("**YOUR PROFILE**")
    age       = st.number_input("Age",         10,   100,   25)
    weight_kg = st.number_input("Weight (kg)", 30.0, 250.0, 70.0, 0.5)
    height_cm = st.number_input("Height (cm)",100.0, 250.0,170.0, 0.5)
    gender    = st.selectbox("Gender",["Male","Female","Other"])
    body_type = st.selectbox("Body Type",["Ectomorph","Mesomorph","Endomorph"],
                    help="Ectomorph=slim - Mesomorph=athletic - Endomorph=broader build")

    st.markdown("---")
    st.markdown("**TRAINING TYPE**")
    st.caption(f"{len(ALL_TRAINING_TYPES)} modalities available")
    goal = st.selectbox("Select Training Type", ALL_TRAINING_TYPES,
                        index=ALL_TRAINING_TYPES.index("Hypertrophy Training"))

    # Phase 5: SPLIT-FIRST programme structure (logical, recovery-aligned).
    # Ask the split first, then offer day-counts that fit it -- no arbitrary length.
    st.markdown("---")
    st.markdown("**PROGRAMME STRUCTURE**")
    _split_label = st.selectbox("How do you want to train?",
                                [lbl for lbl, _ in SPLIT_CHOICES],
                                help="Pick your split first; day options will match it.")
    split_type = dict(SPLIT_CHOICES)[_split_label]

    single_mode = None
    focus_muscle = None
    if split_type == "single":
        _mode_label = st.radio(
            "Single-muscle approach",
            ["Focus on one muscle (train it repeatedly)",
             "Rotate one muscle per day (legs today, arms tomorrow...)"],
            help="Specialize to bring up a lagging muscle, or rotate body parts daily.")
        single_mode = "specialize" if _mode_label.startswith("Focus") else "rotate"
        if single_mode == "specialize":
            focus_muscle = st.selectbox("Which muscle?", SPECIALIZE_MUSCLES)

    _day_opts = days_for_split(split_type, single_mode)
    train_frequency = st.selectbox("How many days per week?", _day_opts,
                                   index=len(_day_opts)-1 if len(_day_opts) <= 2 else 0)

    # Honest recovery warning for over-frequent specialization
    if split_type == "single" and single_mode == "specialize":
        _warn = specialization_recovery_warning(train_frequency)
        if _warn:
            st.warning(_warn)

    plan_length = train_frequency  # cycle length follows the split, not an arbitrary number

    # Rehab mode
    rehab_condition = ""
    if goal == "Rehabilitation / Corrective Exercise":
        st.markdown("---")
        st.markdown("**SELECT CONDITION**")
        rehab_condition = st.selectbox("Rehabilitation condition:",list(REHAB_PROTOCOLS.keys()))

    st.markdown("---")
    st.markdown("**INJURY & LIMITATIONS**")
    has_injury  = st.selectbox("Any injury or physical limitation?",["No","Yes"])
    injury_part = ""
    severity    = ""
    if has_injury == "Yes":
        injury_part = st.selectbox("Affected body part:",[
            "Knee","Ankle","Hip","Lower back","Upper back",
            "Shoulder","Elbow","Wrist","Neck","Groin",
            "Hamstring","Quad","Calf","Chest"])
        severity = st.selectbox("Severity level:",[
            "Low - can bear weight with caution",
            "Moderate - light movement only",
            "Severe - no movement in this area"])
        st.markdown(f"""
        <div style="background:rgba(255,77,0,0.08);border:1px solid rgba(255,77,0,0.3);
                    border-radius:8px;padding:0.6rem 0.8rem;margin-top:0.5rem;">
          <div style="font-size:0.7rem;color:#FF4D00;font-weight:700;margin-bottom:2px;">INJURY ACTIVE</div>
          <div style="font-size:0.72rem;color:#FCA5A5;">
            Plan will be modified for {injury_part} ({severity.split('-')[0].strip()})</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    generate = st.button("GENERATE MY REPORT", width='stretch')
    if generate:
        st.session_state.plan_generated = True

# Persist across reruns: once generated, keep showing the plan even when
# later button clicks (Done/Skip/Too hard) trigger a rerun.
if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False
show_plan = st.session_state.plan_generated

# Live model-performance panel (sidebar toggle; off by default)
if st.session_state.get("show_metrics_toggle"):
    render_model_performance()
    st.markdown("<hr style='border:none;border-top:1px solid rgba(232,255,0,0.15);margin:1.5rem 0;'>", unsafe_allow_html=True)


# ============================================================
# STATE
# ============================================================
history        = load_history()
streak         = get_streak(history)
best_streak    = get_best_streak(history)
total_sessions = len(history)
badges         = get_earned_badges(streak, total_sessions)
injury_profile = {"has_injury":has_injury,"body_part":injury_part,"severity":severity}
if has_injury == "Yes": save_injury_profile(injury_profile)

# ============================================================
# STREAK BANNER
# ============================================================
def streak_banner(streak,best_streak,total_sessions,badges):
    fire  = "🔥"*min(streak,5)
    bhtml = "".join([f'<div style="font-size:1.4rem;margin-left:8px;" title="{n}">{ic}</div>' for ic,n,_ in badges])
    return f"""
    <div style="background:linear-gradient(90deg,rgba(232,255,0,0.08),rgba(255,77,0,0.05));
                border:1px solid rgba(232,255,0,0.2);border-radius:14px;
                padding:1rem 1.5rem;margin-bottom:1.5rem;
                display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:2.5rem;font-weight:900;color:#E8FF00;">{streak}</div>
      <div>
        <div style="font-size:0.65rem;letter-spacing:0.15em;color:#6B7280;text-transform:uppercase;">Day Streak {fire}</div>
        <div style="font-size:0.85rem;color:#9CA3AF;margin-top:2px;">Best: {best_streak} days - Total: {total_sessions} sessions</div>
      </div>
      <div style="display:flex;gap:4px;margin-left:auto;">{bhtml}</div>
    </div>"""

# ============================================================
# DEFAULT STATE
# ============================================================
if not show_plan:
    if streak > 0:
        st.markdown(streak_banner(streak,best_streak,total_sessions,badges), unsafe_allow_html=True)
    if badges:
        st.markdown("""<div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;
                    text-transform:uppercase;margin-bottom:0.75rem;">-- Badges Earned</div>""",unsafe_allow_html=True)
        cols=st.columns(min(len(badges),7))
        for idx,(ic,n,d) in enumerate(badges):
            with cols[idx]:
                st.markdown(f"""
                <div style="background:#0F1218;border:1px solid rgba(232,255,0,0.15);
                            border-radius:10px;padding:0.75rem;text-align:center;">
                  <div style="font-size:1.5rem;">{ic}</div>
                  <div style="font-size:0.85rem;font-weight:700;color:#E8FF00;margin-top:4px;">{n}</div>
                  <div style="font-size:0.7rem;color:#6B7280;margin-top:2px;">{d}</div>
                </div>""",unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
    if len(history)>=2:
        st.markdown("""<div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;
                    text-transform:uppercase;margin-bottom:0.75rem;">-- Your Progress</div>""",unsafe_allow_html=True)
        render_progress_charts(history)
    else:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;border:1px dashed rgba(232,255,0,0.15);
                    border-radius:16px;background:rgba(232,255,0,0.02);">
          <div style="font-size:3rem;margin-bottom:1rem;">⚡</div>
          <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.8rem;font-weight:700;color:#F0F2F5;">
            Fill in your data on the left</div>
          <div style="color:#6B7280;margin-top:0.5rem;font-size:0.95rem;">
            GA - RL - 39 training types - Injury-aware AI builds your complete report instantly.
          </div>
        </div>""",unsafe_allow_html=True)

# ============================================================
# GENERATE
# ============================================================
else:
    intensity_score   = (very_active*4)+(fairly_active*3)+(lightly_active*2)
    active_minutes    = very_active+fairly_active+lightly_active
    norm_calories     = predict_calories(steps,distance,intensity_score,active_minutes,scaler,ga_model)
    calorie_intensity = ("Low" if norm_calories<0.33 else "Moderate" if norm_calories<0.66 else "High")
    rl_rec,rl_color,rl_tip = get_rl_recommendation_personal(fatigue_level)
    bmi,bmi_cat,bmi_color  = calculate_bmi(weight_kg,height_cm)

    save_entry({"steps":steps,"active_minutes":active_minutes,"bmi":bmi,
                "calorie_score":round(norm_calories,4),"calorie_intensity":calorie_intensity,
                "rl_rec":rl_rec,"goal":goal,"fatigue":fatigue_choice,"weight":weight_kg,"height":height_cm})
    save_profile({"age":age,"gender":gender,"height":height_cm,"weight":weight_kg,
                  "bmi":bmi,"body_type":body_type,"goal":goal})
    history=load_history(); streak=get_streak(history); best_streak=get_best_streak(history)
    total_sessions=len(history); badges=get_earned_badges(streak,total_sessions)

    st.markdown(streak_banner(streak,best_streak,total_sessions,badges),unsafe_allow_html=True)

    if len(history)>=7 and len(history)%7==0:
        with st.spinner("Your GA model is evolving on your personal data..."):
            new_c,new_m=adaptive_ga_retrain(history)
        if new_c is not None:
            st.markdown(f"""
            <div style="background:linear-gradient(90deg,rgba(232,255,0,0.1),rgba(0,0,0,0));
                        border:1px solid rgba(232,255,0,0.3);border-radius:12px;
                        padding:1rem 1.5rem;margin-bottom:1rem;">
              <div style="font-size:0.65rem;letter-spacing:0.15em;color:#6B7280;text-transform:uppercase;margin-bottom:4px;">
                Model Evolution</div>
              <div style="font-size:1.2rem;font-weight:800;color:#E8FF00;">
                Your GA has evolved on {len(history)} days of YOUR data!</div>
              <div style="font-size:0.85rem;color:#9CA3AF;margin-top:4px;">Personal model MAE: {new_m}</div>
            </div>""",unsafe_allow_html=True)

    st.markdown("""<div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;
                text-transform:uppercase;margin-bottom:1rem;">-- Your Report</div>""",unsafe_allow_html=True)

    m1,m2,m3,m4=st.columns(4)
    with m1: st.metric("BMI",bmi,bmi_cat)
    with m2: st.metric("Calorie Intensity",calorie_intensity,f"GA Score: {norm_calories:.3f}")
    with m3: st.metric("Active Minutes",f"{active_minutes} min",f"{steps:,} steps")
    with m4: st.metric("Energy Level",fatigue_choice,"Today")

    if has_injury=="Yes":
        sev_col={"Severe - no movement in this area":"#FF4D00","Moderate - light movement only":"#FF6B35",
                 "Low - can bear weight with caution":"#E8FF00"}.get(severity,"#FF6B35")
        st.markdown(f"""
        <div style="background:rgba(255,77,0,0.08);border:1px solid {sev_col}55;
                    border-left:4px solid {sev_col};border-radius:12px;padding:1rem 1.5rem;margin:1rem 0;">
          <div style="font-size:0.65rem;letter-spacing:0.15em;color:{sev_col};
                      text-transform:uppercase;margin-bottom:4px;">Injury Profile Active</div>
          <div style="font-size:1.1rem;font-weight:700;color:#F0F2F5;margin-bottom:4px;">{injury_part} - {severity}</div>
          <div style="font-size:0.85rem;color:#FCA5A5;line-height:1.6;">
            All exercise recommendations clinically filtered for your injury.
            Consult a physiotherapist before beginning. Stop if pain exceeds 3/10.</div>
        </div>""",unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{rl_color}22,#0F1218);
                border:1px solid {rl_color}55;border-radius:14px;
                padding:1.2rem 1.8rem;margin:1.2rem 0;
                display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
      <div>
        <div style="font-size:0.65rem;letter-spacing:0.2em;color:#6B7280;text-transform:uppercase;margin-bottom:4px;">
          RL Engine - Today's Recommendation</div>
        <div style="font-size:1.8rem;font-weight:900;color:{rl_color};">{rl_rec}</div>
      </div>
      <div style="flex:1;min-width:200px;font-size:0.9rem;color:#9CA3AF;
                  line-height:1.6;border-left:1px solid {rl_color}44;padding-left:1.5rem;">{rl_tip}</div>
    </div>""",unsafe_allow_html=True)

    bmi_exp={"Underweight":"Below healthy range. Focus on strength training and a calorie surplus.",
             "Normal weight":"Excellent foundation. Channel energy directly into your specific goal.",
             "Overweight":"Slightly above range. Cardio-strength mix and mindful eating will drive results.",
             "Obese":"Higher health risk - every step counts. Low-impact progression is your safest path."}
    st.markdown(f"""
    <div style="background:#0F1218;border:1px solid {bmi_color}44;
                border-left:4px solid {bmi_color};border-radius:12px;padding:1rem 1.5rem;margin-bottom:1.2rem;">
      <div style="font-size:0.65rem;letter-spacing:0.15em;color:#6B7280;text-transform:uppercase;margin-bottom:4px;">
        BMI Analysis</div>
      <div style="font-size:1.3rem;font-weight:800;color:{bmi_color};">{bmi} - {bmi_cat}</div>
      <div style="font-size:0.88rem;color:#9CA3AF;margin-top:4px;line-height:1.6;">{bmi_exp[bmi_cat]}</div>
    </div>""",unsafe_allow_html=True)

    with st.expander("Show RL Q-table (policy details)"):
        q_df=pd.DataFrame(np.round(q_table,3),index=["Rested","Slight Fatigue","Heavy Fatigue"],
                          columns=["Rest","Light","Moderate","Heavy"])
        st.dataframe(q_df,width='stretch')

    if len(history)>=2:
        st.markdown("""<hr style="border:none;border-top:1px solid rgba(232,255,0,0.1);margin:1.5rem 0;">
        <div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;text-transform:uppercase;
                    margin-bottom:0.75rem;">-- Progress Over Time</div>""",unsafe_allow_html=True)
        render_progress_charts(history)

    st.markdown("""
    <hr style="border:none;border-top:1px solid rgba(232,255,0,0.1);margin:1.5rem 0;">
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.8rem;font-weight:900;
                color:#F0F2F5;letter-spacing:0.03em;text-transform:uppercase;margin-bottom:0.25rem;">
    """,unsafe_allow_html=True)

    user_profile={"age":age,"gender":gender,"height":height_cm,"weight":weight_kg,
                  "bmi":bmi,"bmi_cat":bmi_cat,"body_type":body_type,"goal":goal,
                  "steps":steps,"active_minutes":active_minutes,"fatigue":fatigue_choice,
                  "calorie_intensity":calorie_intensity,"rl_rec":rl_rec}

    # Phase 5: persist the active plan with the chosen split + frequency + focus.
    save_active_plan(get_plan_data(user_profile, injury_profile), user_profile,
                     length_days=train_frequency, frequency=train_frequency,
                     split_type=split_type, focus=focus_muscle)

    if goal=="Rehabilitation / Corrective Exercise" and rehab_condition:
        st.markdown("**Rehabilitation Programme**</div>",unsafe_allow_html=True)
        rehab_html=render_rehab_html(rehab_condition,user_profile)
        components.html(
            "<link href='https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Barlow:wght@400;500&display=swap' rel='stylesheet'>"
            + "<style>.exa-prev{background:#0E1218;border:1px solid rgba(255,255,255,0.05);border-radius:9px;padding:8px 8px 6px;margin:0 0 0.6rem 0;text-align:center;}.exa-stage{position:relative;width:100%;max-width:320px;height:210px;margin:0 auto;}.exa-f{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:contain;border-radius:6px;background:#0B0E13;}.exa-f0{animation:exaFadeA 2.6s ease-in-out infinite;}.exa-f1{animation:exaFadeB 2.6s ease-in-out infinite;}@keyframes exaFadeA{0%,38%{opacity:1}50%,92%{opacity:0}100%{opacity:1}}@keyframes exaFadeB{0%,38%{opacity:0}50%,92%{opacity:1}100%{opacity:0}}.exa-cap{font-size:0.62rem;color:#6B7280;margin-top:4px;letter-spacing:0.1em;text-transform:uppercase;}@media (prefers-reduced-motion: reduce){.exa-f0,.exa-f1{animation:none}.exa-f1{opacity:0}}</style>"
            +rehab_html, height=5500, scrolling=True)
    else:
        meta=TRAINING_TYPES.get(goal,{"cat":"hybrid","intensity":3,"emphasis":"variety"})
        st.markdown("**7-Day Training Plan**</div>",unsafe_allow_html=True)
        inj_note=f"- Injury-filtered for {injury_part}" if has_injury=="Yes" else ""
        st.markdown(f"""<div style="font-size:0.82rem;color:#6B7280;margin-bottom:1.2rem;">
        {goal} - {meta['cat'].upper()} - {meta['emphasis'].replace('_',' ').title()} {inj_note}
        </div>""",unsafe_allow_html=True)
        plan_html=build_workout_plan(user_profile,injury_profile)
        components.html(
            "<link href='https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Barlow:wght@400;500&display=swap' rel='stylesheet'>"
            + "<style>.exa-prev{background:#0E1218;border:1px solid rgba(255,255,255,0.05);border-radius:9px;padding:8px 8px 6px;margin:0 0 0.6rem 0;text-align:center;}.exa-stage{position:relative;width:100%;max-width:320px;height:210px;margin:0 auto;}.exa-f{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:contain;border-radius:6px;background:#0B0E13;}.exa-f0{animation:exaFadeA 2.6s ease-in-out infinite;}.exa-f1{animation:exaFadeB 2.6s ease-in-out infinite;}@keyframes exaFadeA{0%,38%{opacity:1}50%,92%{opacity:0}100%{opacity:1}}@keyframes exaFadeB{0%,38%{opacity:0}50%,92%{opacity:1}100%{opacity:0}}.exa-cap{font-size:0.62rem;color:#6B7280;margin-top:4px;letter-spacing:0.1em;text-transform:uppercase;}@media (prefers-reduced-motion: reduce){.exa-f0,.exa-f1{animation:none}.exa-f1{opacity:0}}</style>"
            +plan_html, height=5200, scrolling=True)

        # ---- 2A: Log today's workout (feedback-loop capture) ----
        st.markdown("""<div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;
        text-transform:uppercase;margin:1.5rem 0 0.3rem;">-- Log Today's Workout</div>
        <div style="font-size:0.8rem;color:#6B7280;margin-bottom:1rem;">
        Tap as you go. This trains FITGENIX to adapt to you over time.</div>""",
        unsafe_allow_html=True)

        _plan = get_plan_data(user_profile, injury_profile)
        _logged = load_today_outcomes()
        _fat = user_profile.get("fatigue")
        _row_i = 0  # global counter so widget keys are unique even if an exercise repeats

        for _d in _plan:
            if _d["is_rest"] or not _d["exercises"]:
                continue
            st.markdown(f"<div style='font-size:0.95rem;font-weight:800;color:#F0F2F5;"
                        f"margin:0.8rem 0 0.4rem;'>Day {_d['day']} - {_d['focus']}</div>",
                        unsafe_allow_html=True)
            for _ex in _d["exercises"]:
                _name = _ex["name"]; _mus = _ex.get("muscles","")
                _row_i += 1
                _key = f"{_d['day']}_{_row_i}_{_name}"
                _state = _logged.get(_name, {})
                _status = _state.get("status"); _diff = _state.get("difficulty")

                _c0, _c1, _c2, _c3 = st.columns([3, 1, 1, 1])
                with _c0:
                    if _status == "completed" and _diff == "too_hard":
                        _tag = " &nbsp;<span style='color:#FF6B35;font-size:0.72rem;'>(too hard)</span>"
                    elif _status == "completed":
                        _tag = " &nbsp;<span style='color:#00E676;font-size:0.72rem;'>done</span>"
                    elif _status == "skipped":
                        _tag = " &nbsp;<span style='color:#6B7280;font-size:0.72rem;'>skipped</span>"
                    else:
                        _tag = ""
                    st.markdown(f"<div style='padding-top:0.45rem;font-size:0.9rem;color:#F0F2F5;'>"
                                f"{_name}{_tag}</div>", unsafe_allow_html=True)
                with _c1:
                    if st.button("Done", key=f"done_{_key}", width='stretch'):
                        save_outcome(_name, _mus, "completed", fatigue_at_time=_fat)
                        st.rerun()
                with _c2:
                    if st.button("Skip", key=f"skip_{_key}", width='stretch'):
                        save_outcome(_name, _mus, "skipped", fatigue_at_time=_fat)
                        st.rerun()
                with _c3:
                    if st.button("Too hard", key=f"hard_{_key}", width='stretch'):
                        save_outcome(_name, _mus, "too_hard", fatigue_at_time=_fat)
                        st.rerun()

        _done_n = sum(1 for v in _logged.values() if v.get("status") == "completed")
        if _logged:
            st.markdown(f"<div style='margin-top:1rem;font-size:0.85rem;color:#00E676;'>"
                        f"Logged {len(_logged)} exercise(s) today - {_done_n} completed. "
                        f"This data will power adaptive recommendations.</div>",
                        unsafe_allow_html=True)
            # 2C: one deliberate learning step per session on the batched outcomes
            if st.button("Train FITGENIX on this session", key="rl_train_btn", width='stretch'):
                _outcomes_list = list(_logged.values())
                _rec_idx = rl_recommend_index(fatigue_level)
                rl_learn_from_outcomes(fatigue_level, _rec_idx, _outcomes_list)
                st.success("FITGENIX has learned from this session. Future recommendations are now tuned to you.")
                st.rerun()

    st.markdown("""<hr style="border:none;border-top:1px solid rgba(232,255,0,0.1);margin:1.5rem 0;">
    <div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;text-transform:uppercase;
                margin-bottom:0.75rem;">-- Export Your Report</div>""",unsafe_allow_html=True)

    _plan_days=get_plan_data(user_profile,injury_profile)
    pdf_bytes=generate_pdf(user_profile,bmi,bmi_cat,norm_calories,calorie_intensity,
                           rl_rec,rl_tip,streak,total_sessions,badges,injury_profile,
                           plan_days=_plan_days)
    if pdf_bytes:
        st.download_button(label="Download PDF Report",data=pdf_bytes,
            file_name=f"FITGENIX_Report_{datetime.date.today().isoformat()}.pdf",
            mime="application/pdf",width='stretch')
    else:
        st.info("Run `pip install fpdf2` to enable PDF export.")

    st.markdown("""
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.05);margin:2rem 0 1rem;">
    <div style="text-align:center;font-size:0.75rem;color:#374151;">
      FITGENIX - Genetic Algorithm + Reinforcement Learning + 39 Training Modalities + Injury-Aware AI Coach<br>
      Research: Real-Time Adaptive Fitness Planning with Genetic Algorithms - Fitbit Dataset
    </div>""",unsafe_allow_html=True)
