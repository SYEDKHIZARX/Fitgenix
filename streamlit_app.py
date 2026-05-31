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
    background:var(--accent)!important;color:#000!important;
    font-family:'Barlow Condensed',sans-serif!important;font-size:1.2rem!important;
    font-weight:800!important;letter-spacing:0.08em!important;text-transform:uppercase!important;
    border:none!important;border-radius:6px!important;padding:0.75rem 2rem!important;
    transition:all 0.2s ease!important;width:100%!important;}
.stButton>button:hover{background:#fff!important;transform:translateY(-2px)!important;
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
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_history.json")
INJURY_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "injury_profile.json")

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE,"r") as f: return json.load(f)
    except: return []

def save_entry(entry):
    history = load_history()
    entry["date"]      = datetime.date.today().isoformat()
    entry["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    history = [h for h in history if h.get("date") != entry["date"]]
    history.append(entry)
    history = sorted(history, key=lambda x: x["date"])[-90:]
    with open(HISTORY_FILE,"w") as f: json.dump(history, f, indent=2)

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
    with open(INJURY_FILE,"w") as f: json.dump(profile, f, indent=2)

def load_injury_profile():
    if not os.path.exists(INJURY_FILE): return {}
    try:
        with open(INJURY_FILE,"r") as f: return json.load(f)
    except: return {}

# ============================================================
# BADGES
# ============================================================
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
    return (joblib.load(os.path.join(base,"scaler.pkl")),
            joblib.load(os.path.join(base,"ga_model.pkl")),
            joblib.load(os.path.join(base,"q_table.pkl")))

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
INJURY_MUSCLE_MAP = {
    "Knee":       ["legs"],
    "Ankle":      ["legs","cardio"],
    "Hip":        ["legs","core"],
    "Lower back": ["core","back","legs"],
    "Upper back": ["back"],
    "Shoulder":   ["chest","back","shoulders","arms"],
    "Elbow":      ["arms","chest"],
    "Wrist":      ["arms","chest"],
    "Neck":       ["shoulders","back"],
    "Groin":      ["legs","core"],
    "Hamstring":  ["legs"],
    "Quad":       ["legs"],
    "Calf":       ["legs","cardio"],
    "Chest":      ["chest"],
}

INJURY_SAFE_EXERCISES = {
    "Knee":{
        "moderate":[
            ("Seated Leg Press (light)","3 x 15","Light weight","Quads (controlled)","Keep range of motion pain-free only."),
            ("Straight Leg Raise","3 x 15","Bodyweight","Quads, Hip flexors","No knee bend - fully isometric load."),
            ("Clamshells","3 x 20","Resistance band","Glutes, Hip abductors","Pain-free only. Stop if knee aches."),
            ("Short Arc Quads","3 x 15","Bodyweight","Quads","Only last 30 deg of extension. Very safe."),
            ("Standing Calf Raises","3 x 20","Bodyweight","Calves","Avoid if ankle also affected."),
        ],
        "low":[
            ("Bodyweight Squats (shallow)","3 x 12","Bodyweight","Quads, Glutes","Go only to 45 deg depth. Stop at any pain."),
            ("Step-Ups (low step)","3 x 10","Bodyweight","Quads, Glutes","Use a very low step. Control descent."),
            ("Glute Bridges","3 x 15","Bodyweight","Glutes, Hamstrings","Minimal knee stress - very safe."),
            ("Wall Sit (short)","3 x 20s","Bodyweight","Quads","Reduce duration if discomfort felt."),
        ]
    },
    "Shoulder":{
        "moderate":[
            ("Pendulum Circles","3 x 30s","Bodyweight","Shoulder joint","Lean forward, let arm hang and circle gently."),
            ("Wall Slides","3 x 12","Bodyweight","Rotator cuff, Scapula","Slide arms up wall - no pain allowed."),
            ("External Rotation (band)","3 x 15","Light band","Rotator cuff","Elbow at 90 deg. Tiny range. Pain-free only."),
            ("Scapular Retractions","3 x 15","Bodyweight","Rhomboids, Traps","Squeeze shoulder blades. No arm movement."),
        ],
        "low":[
            ("Dumbbell Lateral Raise","3 x 12","2-4 kg","Side deltoids","Reduce weight significantly. No overhead."),
            ("Face Pulls (band)","3 x 15","Light band","Rear deltoids, Rotator cuff","Keep elbows high. Stop at discomfort."),
            ("Incline Push-Ups","3 x 10","Bodyweight","Chest, Shoulders","Elevated surface reduces shoulder load."),
        ]
    },
    "Lower back":{
        "moderate":[
            ("Pelvic Tilts","3 x 15","Bodyweight","Lower back, Core","Lie on back. Flatten lumbar to floor gently."),
            ("Cat-Cow Stretch","3 x 12","Bodyweight","Spine, Core","Slow and controlled. No forced range."),
            ("Dead Bug","3 x 10","Bodyweight","Core, Lower back","Keep lower back pressed to floor throughout."),
            ("Bird Dog","3 x 10","Bodyweight","Lower back, Glutes","Extend opposite arm and leg. Hold 3 sec."),
            ("Glute Bridges","3 x 15","Bodyweight","Glutes, Lower back","Activates glutes, reduces spinal load."),
        ],
        "low":[
            ("Romanian Deadlift (light)","3 x 10","5-8 kg","Hamstrings, Lower back","Hinge at hips only. Neutral spine always."),
            ("Hyperextensions (gentle)","3 x 12","Bodyweight","Lower back, Glutes","Only to parallel - no excessive extension."),
            ("Plank","3 x 20s","Bodyweight","Core, Lower back","Short duration. Stop if back pain worsens."),
        ]
    },
    "Ankle":{
        "moderate":[
            ("Seated Calf Raises","3 x 20","Bodyweight","Calves","Seated removes weight-bearing from ankle."),
            ("Alphabet Ankle Circles","3 x 1","Bodyweight","Ankle mobility","Trace alphabet with toe. Restore ROM."),
            ("Resistance Band Dorsiflexion","3x15","Light band","Tibialis anterior","Gentle resistance. Restore full motion."),
            ("Towel Scrunches","3 x 30s","Bodyweight","Foot intrinsics","Pick up towel with toes. Stability work."),
        ],
        "low":[
            ("Single Leg Balance","3 x 30s","Bodyweight","Ankle stability","Stand on affected leg. Use wall if needed."),
            ("Calf Raises (bilateral)","3 x 15","Bodyweight","Calves","Both feet. Progress to single leg later."),
            ("Low-Impact Walking","1 x 20 min","--","Full body, Heart","Flat surface only. Supportive footwear."),
        ]
    },
    "Hip":{
        "moderate":[
            ("Clamshells","3 x 20","Light band","Hip abductors, Glutes","Side-lying. Pain-free range only."),
            ("Hip Flexor Stretch","3 x 30s","Bodyweight","Hip flexors","Kneeling lunge position. Gentle hold."),
            ("Supine Hip Rotation","3 x 10","Bodyweight","Hip joint mobility","Lie on back. Slowly rotate knee in/out."),
            ("Standing Hip Abduction","3 x 15","Light band","Glute medius","Hold wall for balance. Controlled motion."),
        ],
        "low":[
            ("Bodyweight Squats","3 x 12","Bodyweight","Quads, Glutes, Hip","Pain-free depth only."),
            ("Side-Lying Leg Raises","3 x 15","Bodyweight","Hip abductors","Controlled. No momentum."),
            ("Step-Ups","3 x 10","Bodyweight","Glutes, Hip","Low step. Full control on descent."),
        ]
    },
    "Elbow":{
        "moderate":[
            ("Wrist Flexion/Extension","3 x 15","No weight","Forearm muscles","Gentle ROM restoration. No resistance."),
            ("Forearm Pronation/Supination","3x15","Light band","Forearm, Elbow","Rotate palm up/down. Controlled speed."),
            ("Elbow ROM Circles","3 x 10","Bodyweight","Elbow joint","Full pain-free range of motion only."),
        ],
        "low":[
            ("Hammer Curls (light)","3 x 12","2-4 kg","Biceps, Brachialis","Neutral grip reduces elbow stress."),
            ("Tricep Pushdowns (band)","3 x 15","Light band","Triceps","Very light resistance. Pain-free range."),
        ]
    },
    "Neck":{
        "moderate":[
            ("Neck Retraction (Chin Tuck)","3 x 10","Bodyweight","Deep neck flexors","Pull chin back gently. Hold 5 sec."),
            ("Neck Side Tilt Stretch","3 x 30s","Bodyweight","Neck lateral flexors","Ear to shoulder. Gentle. No forcing."),
            ("Shoulder Shrugs","3 x 15","Bodyweight","Upper traps","Slow controlled shrugs. No jerking."),
            ("Scapular Retractions","3 x 15","Bodyweight","Rhomboids","Relieves neck tension indirectly."),
        ],
        "low":[
            ("Isometric Neck Resistance","3 x 10","Bodyweight","Neck stabilisers","Press hand against head. Don't move neck."),
            ("Upper Trap Stretch","3 x 30s","Bodyweight","Upper trapezius","Tilt head, use hand for gentle overpressure."),
        ]
    },
}

DEFAULT_SAFE = {
    "moderate":[
        ("Walking (flat surface)","1 x 20 min","--","Heart, Full body","Low impact. Monitor affected area."),
        ("Seated Upper Body","3 x 12","Light","Arms, Shoulders","Avoid loading the injured area."),
        ("Breathing Exercises","3 x 5 min","--","Lungs, Relaxation","Diaphragmatic breathing for recovery."),
        ("Gentle Stretching","1 x 15 min","--","Full body flexibility","Pain-free range only. Never force."),
    ],
    "low":[
        ("Bodyweight Circuit","3 x 10","Bodyweight","Full body","Avoid movements that load injured area."),
        ("Resistance Band Work","3 x 15","Light band","Multiple groups","Light resistance. Full pain-free range."),
        ("Cardio (low impact)","1 x 25 min","--","Heart, Legs","Cycling or swimming preferred over running."),
    ]
}

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
TRAINING_TYPES = {
    "Hypertrophy Training":                   {"cat":"strength",  "intensity":3,"emphasis":"volume"},
    "Strength Training":                       {"cat":"strength",  "intensity":4,"emphasis":"maximal"},
    "Powerlifting Training":                   {"cat":"strength",  "intensity":5,"emphasis":"maximal"},
    "Olympic Weightlifting":                   {"cat":"strength",  "intensity":5,"emphasis":"power"},
    "Strongman Training":                      {"cat":"strength",  "intensity":5,"emphasis":"full_body"},
    "Resistance Training":                     {"cat":"strength",  "intensity":3,"emphasis":"balanced"},
    "Isometric Training":                      {"cat":"strength",  "intensity":2,"emphasis":"static"},
    "Bodybuilding Training":                   {"cat":"strength",  "intensity":3,"emphasis":"aesthetic"},
    "Plyometric Training":                     {"cat":"strength",  "intensity":4,"emphasis":"explosive"},
    "Power / Explosive Training":              {"cat":"strength",  "intensity":5,"emphasis":"explosive"},
    "Cardiovascular (Cardio) Training":        {"cat":"cardio",    "intensity":2,"emphasis":"aerobic"},
    "Aerobic Training":                        {"cat":"cardio",    "intensity":2,"emphasis":"aerobic"},
    "Anaerobic Training":                      {"cat":"cardio",    "intensity":4,"emphasis":"anaerobic"},
    "Muscular Endurance Training":             {"cat":"endurance", "intensity":3,"emphasis":"endurance"},
    "HIIT (High-Intensity Interval Training)": {"cat":"hiit",      "intensity":5,"emphasis":"interval"},
    "Interval Training":                       {"cat":"hiit",      "intensity":4,"emphasis":"interval"},
    "Sprint Training":                         {"cat":"hiit",      "intensity":5,"emphasis":"speed"},
    "Metabolic Conditioning (MetCon)":         {"cat":"hiit",      "intensity":4,"emphasis":"metabolic"},
    "Bootcamp Training":                       {"cat":"hiit",      "intensity":4,"emphasis":"full_body"},
    "Circuit Training":                        {"cat":"endurance", "intensity":3,"emphasis":"circuit"},
    "Functional Training":                     {"cat":"functional","intensity":3,"emphasis":"movement"},
    "Calisthenics":                            {"cat":"functional","intensity":3,"emphasis":"bodyweight"},
    "Athletic Performance Training":           {"cat":"functional","intensity":4,"emphasis":"performance"},
    "Sports-Specific Training":                {"cat":"functional","intensity":4,"emphasis":"sport"},
    "Kettlebell Training":                     {"cat":"functional","intensity":3,"emphasis":"ballistic"},
    "Suspension Training (TRX)":               {"cat":"functional","intensity":3,"emphasis":"stability"},
    "Bodyweight Training":                     {"cat":"functional","intensity":2,"emphasis":"bodyweight"},
    "Speed & Agility Training":                {"cat":"functional","intensity":4,"emphasis":"speed"},
    "Martial Arts Conditioning":               {"cat":"functional","intensity":4,"emphasis":"combat"},
    "Flexibility Training":                    {"cat":"mobility",  "intensity":1,"emphasis":"stretch"},
    "Mobility Training":                       {"cat":"mobility",  "intensity":1,"emphasis":"joint"},
    "Yoga Training":                           {"cat":"mobility",  "intensity":1,"emphasis":"mindful"},
    "Pilates Training":                        {"cat":"mobility",  "intensity":2,"emphasis":"core_flex"},
    "Stability & Balance Training":            {"cat":"mobility",  "intensity":2,"emphasis":"balance"},
    "Core Training":                           {"cat":"mobility",  "intensity":2,"emphasis":"core"},
    "Cross-Training / Hybrid Training":        {"cat":"hybrid",    "intensity":3,"emphasis":"variety"},
    "Functional Bodybuilding":                 {"cat":"hybrid",    "intensity":3,"emphasis":"aesthetics_function"},
    "Resistance Band Training":                {"cat":"hybrid",    "intensity":2,"emphasis":"resistance"},
    "Recovery / Active Recovery Training":     {"cat":"recovery",  "intensity":1,"emphasis":"rest"},
    "Rehabilitation / Corrective Exercise":    {"cat":"recovery",  "intensity":1,"emphasis":"corrective"},
}

ALL_TRAINING_TYPES = sorted(TRAINING_TYPES.keys())

# ============================================================
# EXERCISE LIBRARY — extended pool
# ============================================================
EXERCISE_LIBRARY = {
    "chest":[
        ("Push-Ups","3 x 12","Bodyweight","Chest, Triceps, Shoulders","Add 2 reps per week."),
        ("Dumbbell Press","3 x 10","8-12 kg","Chest, Triceps","Increase 2 kg when 12 reps feel easy."),
        ("Incline Push-Ups","3 x 15","Bodyweight","Upper Chest, Shoulders","Flatten incline progressively."),
        ("Chest Flyes","3 x 12","6-8 kg","Chest, Front Deltoid","Increase 1 kg every 2 weeks."),
        ("Decline Push-Ups","3 x 10","Bodyweight","Lower Chest, Triceps","Elevate feet for more difficulty."),
    ],
    "back":[
        ("Dumbbell Rows","3 x 10","8-12 kg","Lats, Rhomboids, Biceps","Increase 2 kg when 10 reps feel easy."),
        ("Superman Hold","3 x 12","Bodyweight","Lower Back, Glutes","Hold each rep 2 extra seconds weekly."),
        ("Resistance Band Row","3 x 15","Light band","Upper Back, Rear Deltoid","Progress to heavier band after 3 weeks."),
        ("Lat Pulldown","3 x 10","10-15 kg","Lats, Biceps","Add 2.5 kg every 2 weeks."),
        ("Pull-Ups","3 x max","Bodyweight","Lats, Biceps, Core","Add band for assistance if needed."),
    ],
    "legs":[
        ("Bodyweight Squats","3 x 15","Bodyweight","Quads, Glutes, Hamstrings","Add resistance band after week 2."),
        ("Lunges","3 x 12","Bodyweight","Quads, Glutes, Balance","Hold 5 kg dumbbells once form is solid."),
        ("Glute Bridges","3 x 15","Bodyweight","Glutes, Hamstrings","Add weight on hips after week 3."),
        ("Step-Ups","3 x 10","Bodyweight","Quads, Glutes, Calves","Add dumbbells or increase step height."),
        ("Wall Sit","3 x 30s","Bodyweight","Quads, Core","Add 10 seconds per week."),
        ("Romanian Deadlift","3 x 10","12-20 kg","Hamstrings, Glutes","Increase load 2.5 kg every 2 weeks."),
        ("Calf Raises","3 x 20","Bodyweight","Calves","Progress to single-leg variation."),
    ],
    "shoulders":[
        ("Shoulder Press","3 x 10","6-10 kg","Deltoids, Triceps","Increase 2 kg when 10 reps feel easy."),
        ("Lateral Raises","3 x 12","4-6 kg","Side Deltoids","Slow the lowering phase, then add weight."),
        ("Arnold Press","3 x 10","6-8 kg","All Deltoid Heads","Increase 1 kg every 2 weeks."),
        ("Front Raises","3 x 12","4-6 kg","Front Deltoids","Alternate arms for stability work."),
        ("Rear Delt Flyes","3 x 12","4-6 kg","Rear Deltoids","Bend forward 45 deg for best activation."),
    ],
    "arms":[
        ("Bicep Curls","3 x 12","6-10 kg","Biceps","Increase 2 kg when 12 reps feel easy."),
        ("Tricep Dips","3 x 10","Bodyweight","Triceps, Chest","Slow the descent for more challenge."),
        ("Hammer Curls","3 x 12","6-8 kg","Biceps, Forearms","Keep elbows fixed - no swinging."),
        ("Overhead Extension","3 x 12","6-8 kg","Triceps","Increase 1 kg every 2 weeks."),
        ("Close-Grip Push-Ups","3 x 10","Bodyweight","Triceps, Chest","Elbows stay close to body."),
    ],
    "core":[
        ("Plank","3 x 30s","Bodyweight","Full Core, Shoulders","Add 10 seconds per week until 90 seconds."),
        ("Crunches","3 x 20","Bodyweight","Abs","Add plate on chest after week 3."),
        ("Leg Raises","3 x 15","Bodyweight","Lower Abs, Hip Flexors","Slow the lowering phase."),
        ("Russian Twists","3 x 20","Bodyweight","Obliques, Core","Hold dumbbell when bodyweight is easy."),
        ("Mountain Climbers","3 x 30s","Bodyweight","Core, Shoulders, Cardio","Increase speed gradually."),
        ("Dead Bug","3 x 10","Bodyweight","Core stability","Lower back stays flat on floor always."),
        ("Side Plank","3 x 25s","Bodyweight","Obliques, Glute medius","Stack feet or stagger for stability."),
        ("Hollow Body Hold","3 x 20s","Bodyweight","Full core","Press lower back into floor throughout."),
    ],
    "cardio":[
        ("Brisk Walking","1 x 30 min","--","Heart, Legs, Full Body","Increase pace or add 5 min each week."),
        ("Cycling","1 x 25 min","--","Heart, Quads, Glutes","Increase resistance or duration weekly."),
        ("Jump Rope","3 x 3 min","--","Heart, Calves, Coord.","Add 1 min per round each week."),
        ("Jogging","1 x 20 min","--","Heart, Legs","Alternate walk/jog, build run time weekly."),
        ("HIIT Circuit","4 x 4 min","Bodyweight","Full Body, Heart","Reduce rest time between rounds."),
        ("Low-Impact Aerobics","1 x 30 min","--","Heart, Full Body","Great for joints. Increase duration."),
        ("Swimming","1 x 30 min","--","Full Body, Heart","Increase laps or reduce rest time."),
        ("Battle Ropes","5 x 30s","--","Shoulders, Core, Heart","Alternate with 30 sec rest."),
    ],
    "power":[
        ("Box Jumps","4 x 6","Bodyweight","Quads, Glutes, Calves","Land softly. Increase box height weekly."),
        ("Medicine Ball Slam","4 x 8","6-10 kg ball","Core, Shoulders, Lats","Full extension overhead before slam."),
        ("Kettlebell Swing","4 x 15","12-16 kg","Glutes, Hamstrings, Core","Hip hinge drives the swing. Not arms."),
        ("Jump Squat","4 x 8","Bodyweight","Quads, Glutes, Power","Land in squat position. Absorb force."),
        ("Broad Jumps","4 x 5","Bodyweight","Full lower body","Max distance each rep. Rest 90 sec."),
    ],
    "olympic":[
        ("Snatch (technique)","5 x 3","Light-mod","Full body, coordination","Start with PVC pipe. Perfect form first."),
        ("Clean and Jerk","5 x 3","Moderate","Full body, power","Drive from legs. Catch in squat."),
        ("Overhead Squat","4 x 5","Light","Full body stability","Flexibility prerequisite. Go slow."),
        ("Hang Clean","4 x 4","Moderate","Posterior chain, power","Start from mid-thigh. Explosive pull."),
        ("Front Squat","4 x 6","Moderate","Quads, Core, Rack position","Elbows high. Torso vertical."),
    ],
    "strongman":[
        ("Farmer's Carry","4 x 30m","Heavy","Grip, Traps, Core, Legs","Shoulders back. Short quick steps."),
        ("Tire Flip","4 x 5","Heavy","Full posterior chain","Drive with legs. Pull with arms late."),
        ("Log Press","4 x 5","Moderate","Shoulders, Triceps","Clean to chest before press."),
        ("Sled Push","4 x 20m","Moderate","Quads, Glutes, Heart","Low hips. Drive from glutes."),
        ("Yoke Carry","4 x 20m","Heavy","Core, Legs, Traps","Brace hard. Eyes forward. Short steps."),
    ],
    "kettlebell":[
        ("KB Swing","4 x 15","12-16 kg","Glutes, Hamstrings, Core","Hip hinge not squat. Explosive."),
        ("KB Turkish Get-Up","3 x 3ea","8-12 kg","Full body, stability","Slow and deliberate. Each step matters."),
        ("KB Goblet Squat","3 x 12","12-16 kg","Quads, Glutes, Core","Hold at chest. Elbows inside knees."),
        ("KB Clean and Press","3 x 8ea","10-14 kg","Shoulders, Full body","Clean first. Press from rack position."),
        ("KB Snatch","3 x 8ea","12-16 kg","Full body, power","Hike back then drive through hips."),
    ],
    "trx":[
        ("TRX Row","3 x 12","Bodyweight","Back, Biceps","Walk feet in for more difficulty."),
        ("TRX Push-Up","3 x 12","Bodyweight","Chest, Triceps, Core","Straps at mid-chest height."),
        ("TRX Squat","3 x 15","Bodyweight","Legs, Core","Use straps for balance assistance."),
        ("TRX Plank","3 x 30s","Bodyweight","Core, Shoulders","Feet in straps at mid-calf height."),
        ("TRX Single Leg Squat","3 x 8ea","Bodyweight","Balance, Quads, Glutes","Hold strap for stability."),
    ],
    "yoga":[
        ("Sun Salutation A","5 x flow","Bodyweight","Full body, breath","Move with the breath. 1 breath per pose."),
        ("Warrior I & II","3 x 30s","Bodyweight","Legs, Hip flexors","Stack front knee over ankle."),
        ("Downward Dog","3 x 30s","Bodyweight","Hamstrings, Calves, Back","Press heels toward floor."),
        ("Pigeon Pose","3 x 60s","Bodyweight","Hip flexors, Glutes","Stay relaxed. Breathe into tension."),
        ("Bridge Pose","3 x 30s","Bodyweight","Glutes, Spine, Chest","Press through feet. Avoid neck strain."),
    ],
    "pilates":[
        ("The Hundred","1 x 100","Bodyweight","Core, Breath control","5 counts in, 5 counts out. Legs at 45 deg."),
        ("Roll-Up","3 x 10","Bodyweight","Spine, Abs","Peel vertebra by vertebra. Slow descent."),
        ("Single Leg Circle","3 x 8ea","Bodyweight","Hip mobility, Core","Stabilise the pelvis throughout."),
        ("Swimming","3 x 30s","Bodyweight","Back extensors, Glutes","Alternate arm and leg lifts."),
        ("Side-Lying Leg Lift","3 x 15ea","Bodyweight","Hip abductors","Keep hips stacked. Control the motion."),
    ],
    "mobility":[
        ("Hip 90/90 Stretch","3 x 60s","Bodyweight","Hip mobility","Sit tall. Drive shin into floor."),
        ("Thoracic Rotation","3 x 10ea","Bodyweight","Spine, Shoulders","Support with hand. Full rotation."),
        ("World's Greatest Stretch","3 x 5ea","Bodyweight","Full body mobility","Lunge + thoracic rotation combo."),
        ("Couch Stretch","3 x 60s","Bodyweight","Hip flexors, Quads","Against wall. Drive hips forward."),
        ("Shoulder Dislocates","3 x 10","Stick/band","Shoulder ROM","Wide grip. Move slowly through range."),
    ],
    "plyometric":[
        ("Box Jumps","4 x 8","Bodyweight","Explosive leg power","Land softly in squat. Step down."),
        ("Lateral Bounds","4 x 8ea","Bodyweight","Glutes, Balance, Power","Stick the landing each side."),
        ("Tuck Jumps","4 x 6","Bodyweight","Full lower body, Core","Drive knees high. Land soft."),
        ("Plyo Push-Ups","3 x 8","Bodyweight","Chest, Triceps, Power","Explosive extension. Land with control."),
        ("Skater Jumps","4 x 10ea","Bodyweight","Glutes, Balance, Power","Single-leg landing. Absorb force."),
    ],
    "isometric":[
        ("Isometric Squat Hold","5 x 30s","Bodyweight","Quads, Glutes","90 deg. Breathe steadily."),
        ("Isometric Push-Up Hold","5 x 20s","Bodyweight","Chest, Triceps","Mid-rep position. Core braced."),
        ("Isometric Plank","5 x 45s","Bodyweight","Full core","Create full-body tension throughout."),
        ("Isometric Lunge Hold","5 x 25s","Bodyweight","Quads, Hip flexors","Back knee hovering. Upright torso."),
        ("Wall Push Isometric","5 x 20s","Bodyweight","Chest activation","Push into wall maximally. No movement."),
    ],
    "agility":[
        ("Cone Drills","4 x 30s","Bodyweight","Speed, Coordination","Sharp cuts. Stay low. Quick feet."),
        ("Ladder Drills","4 x length","Bodyweight","Footwork, Agility","Eyes up. High knees. Fast cadence."),
        ("T-Drill","4 x reps","Bodyweight","Multi-directional speed","Plant and cut hard. Low center of gravity."),
        ("Pro Agility Shuttle","4 x reps","Bodyweight","Acceleration, Change of direction","Touch the line. Explode back."),
        ("Reactive Bounds","4 x 8","Bodyweight","Reactive agility","Respond to visual cue. Immediate move."),
    ],
    "recovery":[
        ("Foam Rolling","1 x 15 min","Foam roller","Full body fascia","30 sec per muscle. Slow strokes."),
        ("Static Stretching","1 x 20 min","Bodyweight","Full body flexibility","30-60 sec holds. Breathe deeply."),
        ("Breathing Exercises","5 x 5 min","--","Nervous system","4-7-8 breathing. Parasympathetic activation."),
        ("Light Walking","1 x 20 min","--","Blood flow, Recovery","Easy pace. No intensity."),
        ("Contrast Therapy","3 x cycles","--","Circulation, Recovery","2 min hot, 1 min cold. Finish cold."),
    ],
    "rest":[
        ("Full Rest Day","--","--","Full Body Recovery","Hydrate well, sleep 7-9 hours."),
        ("Light Stretching","1 x 20 min","--","Flexibility, Recovery","Hold each stretch 30 sec."),
        ("Yoga / Mobility","1 x 30 min","--","Joints, Flexibility","Follow a beginner YouTube yoga session."),
    ]
}

# ============================================================
# EXERCISE COMPREHENSION LAYER (decoupled from the recommendation engine)
# Plain-language descriptor + form cues + common mistake per exercise.
# Anything not listed still gets a universal 'Watch demo' search link.
# ============================================================
EXERCISE_INFO = {
    "Push-Ups": {
        "desc": "A classic bodyweight press — lower your chest to the floor and push back up.",
        "cues": [
            "Keep your body in one straight line, head to heels.",
            "Lower until your elbows reach about 90°.",
            "Push the floor away; don't flare elbows out wide."
        ],
        "mistake": "Letting the hips sag or pike up instead of staying straight."
    },
    "Dumbbell Press": {
        "desc": "Lie on a bench and press two dumbbells up from chest level.",
        "cues": [
            "Plant your feet, slight natural arch in the back.",
            "Lower the weights to chest level under control.",
            "Press up and slightly together at the top."
        ],
        "mistake": "Bouncing the weights off your chest."
    },
    "Incline Push-Ups": {
        "desc": "A push-up with your hands on a raised surface — easier than the floor version.",
        "cues": [
            "Hands on a bench, box, or wall.",
            "Hold a straight line from head to heels.",
            "Lower your chest toward the surface, then press up."
        ],
        "mistake": "Letting the hips pike up or sag."
    },
    "Chest Flyes": {
        "desc": "Lying down, open and close your arms in a wide arc to work the chest.",
        "cues": [
            "Keep a slight, fixed bend in the elbows.",
            "Lower in a wide arc until you feel a chest stretch.",
            "Squeeze the chest to bring the weights back together."
        ],
        "mistake": "Bending the elbows so it turns into a press."
    },
    "Decline Push-Ups": {
        "desc": "A push-up with your feet raised — shifts the work to the upper chest.",
        "cues": [
            "Feet on a bench or step, hands on the floor.",
            "Keep your core tight and body straight.",
            "Lower your chest, then press up."
        ],
        "mistake": "Letting the lower back arch under the load."
    },
    "Dumbbell Rows": {
        "desc": "Bend at the hips and pull a dumbbell up toward your waist.",
        "cues": [
            "Flat back, soft knees, hinge forward.",
            "Drive your elbow up and back toward your waist.",
            "Lower slowly under control."
        ],
        "mistake": "Shrugging or rounding the back to lift heavier."
    },
    "Superman Hold": {
        "desc": "Lie face-down and lift your arms, chest and legs off the floor.",
        "cues": [
            "Reach your arms forward, legs straight back.",
            "Lift everything a few inches and hold.",
            "Keep your neck relaxed and eyes down."
        ],
        "mistake": "Cranking your head up and straining the neck."
    },
    "Resistance Band Row": {
        "desc": "Pull a band toward you, squeezing your shoulder blades together.",
        "cues": [
            "Anchor the band; start with arms straight ahead.",
            "Pull your elbows back past your ribs.",
            "Squeeze the shoulder blades, then return slowly."
        ],
        "mistake": "Pulling with the arms only and ignoring the back."
    },
    "Lat Pulldown": {
        "desc": "Pull a bar down toward your upper chest to build the lats.",
        "cues": [
            "Grip slightly wider than your shoulders.",
            "Pull the bar to your upper chest, elbows down.",
            "Control the bar back up — don't let it yank you."
        ],
        "mistake": "Leaning way back and using momentum."
    },
    "Pull-Ups": {
        "desc": "Hang from a bar and pull your chin above it.",
        "cues": [
            "Start from a full hang, shoulders engaged.",
            "Pull your elbows down toward your sides.",
            "Lower all the way down with control."
        ],
        "mistake": "Swinging or kipping instead of a controlled pull."
    },
    "Bodyweight Squats": {
        "desc": "Sit your hips back and down, then stand tall.",
        "cues": [
            "Feet shoulder-width, toes slightly out.",
            "Push your hips back as you bend the knees.",
            "Keep your chest up and heels planted."
        ],
        "mistake": "Letting the knees cave inward."
    },
    "Lunges": {
        "desc": "Step forward and lower until both knees are bent about 90°.",
        "cues": [
            "Step forward, drop the back knee toward the floor.",
            "Front knee tracks over the foot, not past the toes.",
            "Push through the front heel to stand."
        ],
        "mistake": "Letting the front knee collapse inward."
    },
    "Glute Bridges": {
        "desc": "Lie on your back and lift your hips by squeezing your glutes.",
        "cues": [
            "Feet flat, knees bent, arms by your sides.",
            "Drive through your heels to lift the hips.",
            "Squeeze the glutes hard at the top."
        ],
        "mistake": "Arching the lower back instead of using the glutes."
    },
    "Step-Ups": {
        "desc": "Step up onto a raised surface, driving through the front leg.",
        "cues": [
            "Place your whole foot on the step.",
            "Drive through the heel to stand tall.",
            "Lower slowly — don't just drop down."
        ],
        "mistake": "Pushing off the back foot instead of the top leg."
    },
    "Wall Sit": {
        "desc": "Hold a seated position against a wall with no chair.",
        "cues": [
            "Back flat on the wall, thighs parallel to the floor.",
            "Knees stacked over the ankles at about 90°.",
            "Breathe steadily and hold."
        ],
        "mistake": "Letting the hips creep up to make it easier."
    },
    "Romanian Deadlift": {
        "desc": "Hinge at the hips to lower the weight down the front of your legs.",
        "cues": [
            "Soft knees; push your hips back.",
            "Keep the weight close to your legs.",
            "Feel the hamstring stretch, then squeeze up."
        ],
        "mistake": "Rounding the back or turning it into a squat."
    },
    "Calf Raises": {
        "desc": "Rise up onto the balls of your feet to work the calves.",
        "cues": [
            "Stand tall, push through the balls of your feet.",
            "Rise as high as you can; pause at the top.",
            "Lower slowly for a full stretch."
        ],
        "mistake": "Bouncing quickly with a tiny range of motion."
    },
    "Shoulder Press": {
        "desc": "Press weights overhead from shoulder height.",
        "cues": [
            "Start at shoulder level, elbows under wrists.",
            "Press straight up while bracing your core.",
            "Lower under control to the start."
        ],
        "mistake": "Arching the lower back to push the weight up."
    },
    "Lateral Raises": {
        "desc": "Raise the dumbbells out to your sides to shoulder height.",
        "cues": [
            "Keep a slight bend in the elbows.",
            "Lead with the elbows up to shoulder height.",
            "Lower slowly — resist the drop."
        ],
        "mistake": "Swinging the weights up with momentum."
    },
    "Arnold Press": {
        "desc": "A shoulder press that rotates the palms as you press up.",
        "cues": [
            "Start with palms facing you near your chin.",
            "Rotate and press overhead in one smooth motion.",
            "Reverse the rotation on the way down."
        ],
        "mistake": "Rushing the rotation and losing control."
    },
    "Front Raises": {
        "desc": "Raise the weights straight in front of you to shoulder height.",
        "cues": [
            "Arms nearly straight, palms facing down.",
            "Raise to shoulder height — no higher.",
            "Lower slowly without swinging."
        ],
        "mistake": "Using the back to heave the weight up."
    },
    "Rear Delt Flyes": {
        "desc": "Bent forward, raise the weights out to the sides for the rear shoulders.",
        "cues": [
            "Hinge forward about 45°, slight elbow bend.",
            "Raise the weights out to the sides.",
            "Squeeze the rear shoulders, then lower slowly."
        ],
        "mistake": "Standing too upright and using the traps."
    },
    "Bicep Curls": {
        "desc": "Curl the weights up toward your shoulders.",
        "cues": [
            "Pin your elbows to your sides.",
            "Curl up and squeeze the biceps.",
            "Lower slowly all the way down."
        ],
        "mistake": "Swinging the body to lift the weight."
    },
    "Tricep Dips": {
        "desc": "Lower and press your body on a bench or bars to work the triceps.",
        "cues": [
            "Hands by your hips, elbows pointing back.",
            "Lower until your elbows reach about 90°.",
            "Press back up, staying controlled."
        ],
        "mistake": "Flaring the elbows wide or dropping too deep."
    },
    "Hammer Curls": {
        "desc": "Curl with a neutral, thumbs-up grip for biceps and forearms.",
        "cues": [
            "Palms facing each other throughout.",
            "Keep your elbows fixed at your sides.",
            "Curl up, then lower slowly."
        ],
        "mistake": "Letting the elbows swing forward."
    },
    "Overhead Extension": {
        "desc": "Extend a weight overhead to work the triceps.",
        "cues": [
            "Weight behind your head, elbows pointing up.",
            "Straighten the elbows to extend up.",
            "Keep the elbows from flaring outward."
        ],
        "mistake": "Letting the elbows flare and the back arch."
    },
    "Close-Grip Push-Ups": {
        "desc": "A push-up with the hands close together to target the triceps.",
        "cues": [
            "Hands under your chest, close together.",
            "Keep your elbows tucked close to the body.",
            "Lower and press in a straight line."
        ],
        "mistake": "Letting the elbows flare out to the sides."
    },
    "Plank": {
        "desc": "Hold a straight-body position on your forearms.",
        "cues": [
            "Elbows under shoulders, body in a straight line.",
            "Brace your abs and squeeze the glutes.",
            "Don't let the hips sag or pike up."
        ],
        "mistake": "Dropping the hips or holding your breath."
    },
    "Crunches": {
        "desc": "Curl your upper back off the floor to contract the abs.",
        "cues": [
            "Hands light by your head — don't pull the neck.",
            "Curl the shoulders up using your abs.",
            "Lower slowly under control."
        ],
        "mistake": "Yanking on the neck to come up."
    },
    "Leg Raises": {
        "desc": "Lift your straight legs up while lying on your back.",
        "cues": [
            "Press your lower back into the floor.",
            "Lift the legs toward vertical, then lower slowly.",
            "Stop before the lower back arches up."
        ],
        "mistake": "Letting the lower back lift off the floor."
    },
    "Russian Twists": {
        "desc": "Rotate your torso side to side in a seated lean-back.",
        "cues": [
            "Lean back slightly, feet up or down.",
            "Rotate from the torso, not just the arms.",
            "Tap each side under control."
        ],
        "mistake": "Only moving the arms while the torso stays still."
    },
    "Mountain Climbers": {
        "desc": "From a plank, drive your knees toward your chest one at a time.",
        "cues": [
            "Strong plank, shoulders over hands.",
            "Drive one knee in, then switch.",
            "Keep the hips low and steady."
        ],
        "mistake": "Bouncing the hips high with each rep."
    },
    "Dead Bug": {
        "desc": "On your back, lower the opposite arm and leg while keeping the core braced.",
        "cues": [
            "Press your lower back flat to the floor.",
            "Extend the opposite arm and leg slowly.",
            "Return, then switch sides."
        ],
        "mistake": "Letting the lower back pop off the floor."
    },
    "Side Plank": {
        "desc": "Hold your body in a straight line on one forearm, facing sideways.",
        "cues": [
            "Elbow under shoulder; stack or stagger the feet.",
            "Lift the hips into a straight line.",
            "Hold tall — don't let the hips drop."
        ],
        "mistake": "Letting the hips sink toward the floor."
    },
    "Hollow Body Hold": {
        "desc": "On your back, lift your shoulders and legs into a shallow 'banana' shape.",
        "cues": [
            "Press the lower back firmly into the floor.",
            "Lift the shoulders and legs a few inches.",
            "Reach long through the arms and toes."
        ],
        "mistake": "Arching the back so it lifts off the floor."
    }
}


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
_IMG_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
_EXERCISE_IMAGES = {
    "Arnold Press": ["Arnold_Dumbbell_Press/0.jpg", "Arnold_Dumbbell_Press/1.jpg"],
    "Bicep Curls": ["Dumbbell_Bicep_Curl/0.jpg", "Dumbbell_Bicep_Curl/1.jpg"],
    "Bodyweight Squats": ["Bodyweight_Squat/0.jpg", "Bodyweight_Squat/1.jpg"],
    "Calf Raises": ["Standing_Calf_Raises/0.jpg", "Standing_Calf_Raises/1.jpg"],
    "Chest Flyes": ["Dumbbell_Flyes/0.jpg", "Dumbbell_Flyes/1.jpg"],
    "Close-Grip Push-Ups": ["Push-Ups_-_Close_Triceps_Position/0.jpg", "Push-Ups_-_Close_Triceps_Position/1.jpg"],
    "Crunches": ["Crunches/0.jpg", "Crunches/1.jpg"],
    "Dead Bug": ["Dead_Bug/0.jpg", "Dead_Bug/1.jpg"],
    "Decline Push-Ups": ["Decline_Push-Up/0.jpg", "Decline_Push-Up/1.jpg"],
    "Dumbbell Press": ["Dumbbell_Bench_Press/0.jpg", "Dumbbell_Bench_Press/1.jpg"],
    "Dumbbell Rows": ["Bent_Over_Two-Dumbbell_Row/0.jpg", "Bent_Over_Two-Dumbbell_Row/1.jpg"],
    "Front Raises": ["Front_Dumbbell_Raise/0.jpg", "Front_Dumbbell_Raise/1.jpg"],
    "Glute Bridges": ["Butt_Lift_Bridge/0.jpg", "Butt_Lift_Bridge/1.jpg"],
    "Hammer Curls": ["Hammer_Curls/0.jpg", "Hammer_Curls/1.jpg"],
    "Incline Push-Ups": ["Incline_Push-Up/0.jpg", "Incline_Push-Up/1.jpg"],
    "Lat Pulldown": ["Wide-Grip_Lat_Pulldown/0.jpg", "Wide-Grip_Lat_Pulldown/1.jpg"],
    "Lateral Raises": ["Side_Lateral_Raise/0.jpg", "Side_Lateral_Raise/1.jpg"],
    "Leg Raises": ["Flat_Bench_Lying_Leg_Raise/0.jpg", "Flat_Bench_Lying_Leg_Raise/1.jpg"],
    "Lunges": ["Bodyweight_Walking_Lunge/0.jpg", "Bodyweight_Walking_Lunge/1.jpg"],
    "Mountain Climbers": ["Mountain_Climbers/0.jpg", "Mountain_Climbers/1.jpg"],
    "Overhead Extension": ["Standing_Dumbbell_Triceps_Extension/0.jpg", "Standing_Dumbbell_Triceps_Extension/1.jpg"],
    "Plank": ["Plank/0.jpg", "Plank/1.jpg"],
    "Pull-Ups": ["Pullups/0.jpg", "Pullups/1.jpg"],
    "Push-Ups": ["Pushups/0.jpg", "Pushups/1.jpg"],
    "Rear Delt Flyes": ["Reverse_Flyes/0.jpg", "Reverse_Flyes/1.jpg"],
    "Resistance Band Row": ["Seated_Cable_Rows/0.jpg", "Seated_Cable_Rows/1.jpg"],
    "Romanian Deadlift": ["Romanian_Deadlift/0.jpg", "Romanian_Deadlift/1.jpg"],
    "Russian Twists": ["Russian_Twist/0.jpg", "Russian_Twist/1.jpg"],
    "Shoulder Press": ["Dumbbell_Shoulder_Press/0.jpg", "Dumbbell_Shoulder_Press/1.jpg"],
    "Side Plank": ["Side_Bridge/0.jpg", "Side_Bridge/1.jpg"],
    "Step-Ups": ["Dumbbell_Step_Ups/0.jpg", "Dumbbell_Step_Ups/1.jpg"],
    "Superman Hold": ["Superman/0.jpg", "Superman/1.jpg"],
    "Tricep Dips": ["Dips_-_Triceps_Version/0.jpg", "Dips_-_Triceps_Version/1.jpg"],
}

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
REHAB_PROTOCOLS = {
    "ACL (Anterior Cruciate Ligament)":{
        "phase":"Early-Stage ACL Rehabilitation",
        "warning":"Never return to sport without physiotherapist clearance. Avoid deep squats, pivoting, jumping.",
        "program":[
            ("Day 1 - Swelling Control",[("Quad Sets","3 x 15","Bodyweight","Quadriceps","Tighten quad with knee straight. Hold 5 sec."),("Straight Leg Raise","3 x 15","Bodyweight","Quads, Hip flexors","No knee bend. Slow and controlled."),("Ankle Pumps","3 x 30","Bodyweight","Ankle, Circulation","Pump foot up and down. Prevents clots."),("Heel Slides","3 x 15","Bodyweight","Knee ROM","Slide heel toward glutes. Pain-free range.")]),
            ("Day 2 - Gentle Mobility",[("Seated Knee Flexion","3 x 15","Bodyweight","Knee ROM","Bend and straighten while seated. No force."),("Clamshells","3 x 20","Light band","Hip abductors","Stabilise hip to protect knee."),("Short Arc Quads","3 x 15","Bodyweight","Quads","Only final 30 deg of extension."),("Standing Hip Abduction","3 x 15","Bodyweight","Glute medius","Hold wall. Slowly raise leg to side.")]),
            ("Day 3 - Neuromuscular Control",[("Single Leg Balance","3 x 30s","Bodyweight","Knee stability","Use wall if needed. Build to 60 sec."),("Mini Squats 0-30 deg","3 x 15","Bodyweight","Quads, Glutes","Never past 30 deg depth. Slow descent."),("Step-Ups (very low)","3 x 10","Bodyweight","Quads, Glutes","2-inch step only. Full control."),("Glute Bridges","3 x 15","Bodyweight","Glutes, Hamstrings","Reduces anterior knee stress.")]),
            ("Day 4 - Active Rest",[("Gentle Walking","1 x 20 min","--","Full body","Flat surface. Stop if pain above 3/10."),("Ice and Elevation","3 x 15 min","--","Recovery","After any exercise session."),("Diaphragmatic Breathing","3 x 5 min","--","Nervous system","Activates parasympathetic recovery.")]),
            ("Day 5 - Strength Foundation",[("Wall Squats","3 x 30s","Bodyweight","Quads, Glutes","Back against wall. 45 deg only."),("Resistance Band Walk","3 x 10","Light band","Hip abductors","Side-step with band at ankles."),("Calf Raises","3 x 20","Bodyweight","Calves","Bilateral only at this stage."),("Core Plank","3 x 20s","Bodyweight","Core","Reduces compensatory movement patterns.")]),
            ("Day 6 - Cardio Without Load",[("Stationary Cycling","1 x 20 min","--","Heart, Quads","Seat high - reduces knee flexion load."),("Swimming (if available)","1 x 20 min","--","Full body","No kicking - arms only at early stage."),("Upper Body Strength","3 x 12","Light","Arms, Chest","Maintain general fitness safely.")]),
            ("Day 7 - Full Recovery",[("Complete Rest","--","--","Full recovery","Ice if swollen. Elevate. Sleep 8-9 hours."),("Light Stretching","1 x 15 min","--","Flexibility","Hip flexor, quad, calf - pain-free only.")]),
        ]
    },
    "Rotator Cuff Injury":{
        "phase":"Rotator Cuff Rehabilitation",
        "warning":"No overhead pressing. No throwing. No sleeping on the affected shoulder. Stop if sharp pain occurs.",
        "program":[
            ("Day 1 - Pain Relief & ROM",[("Pendulum Circles","3 x 60s","Bodyweight","Shoulder joint","Lean forward. Let arm hang and circle gently."),("Codman's Exercise","3 x 10","Bodyweight","Shoulder capsule","Gravity-assisted movement. Very gentle."),("Neck Retraction","3 x 10","Bodyweight","Deep neck flexors","Relieves referred shoulder tension."),("Diaphragmatic Breathing","3 x 5 min","--","Relaxation","Reduces muscle guarding around shoulder.")]),
            ("Day 2 - Rotator Cuff Activation",[("External Rotation (band)","3 x 15","Light band","Infraspinatus, Teres minor","Elbow at 90 deg. Tiny motion. Pain-free."),("Internal Rotation (band)","3 x 15","Light band","Subscapularis","Same position. Opposite direction."),("Scapular Retractions","3 x 15","Bodyweight","Rhomboids, Traps","Squeeze blades together. Hold 3 sec."),("Wall Slides","3 x 12","Bodyweight","Rotator cuff, Serratus","Slide arms up wall. No pain allowed.")]),
            ("Day 3 - Scapular Stability",[("Prone Y-T-W Raises","3 x 10","Bodyweight","Lower traps, Rotator cuff","Face down, raise arms to Y,T,W shape."),("Face Pulls (band)","3 x 15","Light band","Rear deltoid, External rotators","Keep elbows high. Pull to forehead."),("Doorway Stretch","3 x 30s","Bodyweight","Chest, Anterior shoulder","Gentle chest stretch. Relieves impingement.")]),
            ("Day 4 - Active Rest & Lower Body",[("Brisk Walking","1 x 25 min","--","Heart, Legs","Keep arm still or in sling if needed."),("Bodyweight Squats","3 x 15","Bodyweight","Legs","No arm loading. Safe lower body work."),("Core Plank (forearms)","3 x 20s","Bodyweight","Core","Forearm plank removes shoulder load.")]),
            ("Day 5 - Strengthening Phase",[("Side-Lying External Rotation","3x15","Light dumbbell","Rotator cuff","2 kg max. Elbow bent. Rotate up."),("Low Row (band)","3 x 15","Light band","Mid traps, Rhomboids","Pull band to hip. Elbow close to body."),("Serratus Wall Punch","3 x 12","Bodyweight","Serratus anterior","Arm forward at shoulder height. Protract scapula.")]),
            ("Day 6 - Functional Movement",[("Reaching with Control","3 x 10","Bodyweight","Shoulder complex","Reach forward, side, diagonal. Stop at pain."),("Light Cardio","1 x 25 min","--","Heart","Walking or cycling. No arm swing stress."),("Bicep Curl (light)","3 x 12","2-3 kg","Biceps","Light weight. No shoulder compensation.")]),
            ("Day 7 - Rest & Reflection",[("Complete Rest","--","--","Full recovery","Ice 15 min if aching. Avoid overhead."),("Postural Awareness","1 x 10 min","--","Posture","Sit tall. Retract shoulders. Chin tucked.")]),
        ]
    },
    "Lower Back Pain / Herniated Disc":{
        "phase":"Lumbar Spine Rehabilitation",
        "warning":"No heavy deadlifts. No forward bending under load. No sit-ups or crunches. Stop if leg pain or numbness occurs - see a doctor immediately.",
        "program":[
            ("Day 1 - Decompression & Mobility",[("Knee-to-Chest Stretch","3 x 30s","Bodyweight","Lumbar spine","Pull both knees gently to chest. Hold."),("Cat-Cow","3 x 12","Bodyweight","Spine mobility","Slow. 4 sec each direction."),("Pelvic Tilts","3 x 15","Bodyweight","Lower back, Core","Flatten lumbar to floor. Hold 5 sec."),("Child's Pose","3 x 30s","Bodyweight","Lower back","Arms forward. Deep hold. Very gentle.")]),
            ("Day 2 - Core Stability",[("Dead Bug","3 x 10","Bodyweight","Core, Lower back","Keep back flat to floor. Opposite arm/leg."),("Bird Dog","3 x 10","Bodyweight","Lower back, Glutes","Extend opposite arm/leg. Hold 3 sec."),("Glute Bridges","3 x 15","Bodyweight","Glutes, Lower back","Activates glutes to unload spine."),("Plank (short)","3 x 15s","Bodyweight","Core","Build duration gradually. No sagging hips.")]),
            ("Day 3 - Hip & Nerve Mobility",[("Hip Flexor Stretch","3 x 30s","Bodyweight","Hip flexors","Tight hip flexors worsen lower back pain."),("Piriformis Stretch","3 x 30s","Bodyweight","Piriformis","Figure-4 stretch. Relieves sciatic pressure."),("Sciatic Nerve Floss","3 x 10","Bodyweight","Sciatic nerve","Sit. Extend knee, flex ankle. Gentle pump."),("Walking","1 x 20 min","--","Full body","Flat surface. Upright posture. No hunching.")]),
            ("Day 4 - Active Rest",[("Diaphragmatic Breathing","5 x 5 min","--","Core, Relaxation","Breathing activates deep core stabilisers."),("Gentle Stretching","1 x 15 min","--","Full body","Hip flexors, piriformis, hamstrings.")]),
            ("Day 5 - Functional Strength",[("Squat to Chair","3 x 12","Bodyweight","Legs, Glutes","Sit-to-stand pattern. Spine neutral."),("Standing Hip Hinge","3 x 12","Bodyweight","Hamstrings, Glutes","Hinge at hips. Back flat. No rounding."),("Side Plank (modified)","3 x 15s","Bodyweight","Obliques","Knees bent version reduces spinal load.")]),
            ("Day 6 - Low-Impact Cardio",[("Swimming","1 x 20 min","--","Full body, Heart","Water unloads spine. Backstroke preferred."),("Stationary Cycling","1 x 20 min","--","Heart, Legs","Upright position. Not hunched forward."),("Walking","1 x 20 min","--","Full body","Build to 30 min gradually.")]),
            ("Day 7 - Full Recovery",[("Complete Rest","--","--","Full recovery","Heat therapy 15 min on lower back if stiff."),("Posture Check","1 x 10 min","--","Posture","Sit at edge of chair. Lumbar lordosis maintained.")]),
        ]
    },
    "Knee Pain (General / Patellofemoral)":{
        "phase":"Knee Pain & Patellofemoral Rehabilitation",
        "warning":"Avoid deep squats, lunges past 90 deg, stair running, and kneeling on hard surfaces.",
        "program":[
            ("Day 1 - Quad & Hip Activation",[("Quad Sets","3 x 15","Bodyweight","Quads","Tighten quad with knee straight. Hold 5 sec."),("Straight Leg Raise","3 x 15","Bodyweight","Quads, Hip flexors","No knee bend. Slow and controlled."),("Clamshells","3 x 20","Light band","Glute medius","Hip control reduces knee valgus stress."),("Glute Bridges","3 x 15","Bodyweight","Glutes, Hamstrings","Reduces anterior knee loading.")]),
            ("Day 2 - VMO Strengthening",[("Terminal Knee Extension","3 x 15","Light band","VMO, Quads","Band behind knee. Straighten against resistance."),("Short Arc Squats","3 x 15","Bodyweight","Quads","Only last 30 deg of extension. Very safe."),("Step-Ups (low)","3 x 10","Bodyweight","Quads, Glutes","4-inch step. Control descent slowly.")]),
            ("Day 3 - Balance & Proprioception",[("Single Leg Balance","3 x 30s","Bodyweight","Knee stability","Progress to unstable surface when ready."),("Lateral Band Walks","3 x 10","Light band","Hip abductors","Reduce knee cave during all movements."),("Low-Impact Cardio","1 x 20 min","--","Heart","Cycling preferred - lower patellofemoral load.")]),
            ("Day 4 - Active Rest",[("Swimming","1 x 20 min","--","Full body","Ideal cross-training for knee rehab."),("Upper Body Strength","3 x 12","Moderate","Upper body","Maintain fitness without knee load."),("Ice Application","2 x 15 min","--","Recovery","After any exercise. Reduces inflammation.")]),
            ("Day 5 - Progressive Loading",[("Wall Squat (45 deg)","3 x 30s","Bodyweight","Quads, Glutes","Back on wall. 45 deg only. Hold."),("Leg Press (light)","3 x 15","Light weight","Quads, Glutes","Foot position high on plate. Less knee stress."),("Calf Raises","3 x 20","Bodyweight","Calves","Bilateral. Full range. Controlled descent.")]),
            ("Day 6 - Functional Movement",[("Sit-to-Stand","3 x 12","Bodyweight","Quads, Glutes","Practice daily movement. Pain-free only."),("Stationary Cycling","1 x 20 min","--","Heart, Quads","Seat height high. Reduces knee flexion."),("Core Stability","3 x 20s","Bodyweight","Core","Plank, bird dog. Reduce compensatory patterns.")]),
            ("Day 7 - Full Recovery",[("Complete Rest","--","--","Recovery","Elevate leg if swollen. Ice as needed."),("Gentle Stretching","1 x 15 min","--","Flexibility","Quad, hip flexor, calf stretches.")]),
        ]
    },
    "Plantar Fasciitis":{
        "phase":"Plantar Fasciitis Rehabilitation",
        "warning":"Never walk barefoot on hard floors. Avoid running until pain-free for 2 weeks. Ice after activity.",
        "program":[
            ("Day 1 - Stretching & Massage",[("Plantar Fascia Stretch","3 x 30s","Bodyweight","Plantar fascia","Seated. Pull toes back. Hold firmly."),("Calf Stretch (straight)","3 x 30s","Bodyweight","Gastrocnemius","Against wall. Heel down. Knee straight."),("Calf Stretch (bent knee)","3 x 30s","Bodyweight","Soleus","Same position but bend knee slightly."),("Frozen Water Bottle Roll","3 x 2 min","--","Plantar fascia","Roll arch over frozen bottle.")]),
            ("Day 2 - Intrinsic Foot Strengthening",[("Towel Scrunches","3 x 30s","Bodyweight","Foot intrinsics","Scrunch towel with toes."),("Marble Pickups","3 x 10","Bodyweight","Foot arch","Pick up marbles with toes."),("Short Foot Exercise","3 x 10","Bodyweight","Intrinsic muscles","Shorten foot without curling toes."),("Seated Calf Raises","3 x 20","Bodyweight","Calf, Arch","Seated - avoids painful weight-bearing.")]),
            ("Day 3 - Load Progression",[("Standing Calf Raises","3 x 15","Bodyweight","Calves, Plantar fascia","Bilateral only. Slow descent."),("Single Leg Balance","3 x 30s","Bodyweight","Foot stability","Progress only when pain < 3/10."),("Low-Impact Walking","1 x 15 min","--","Full body","Good footwear. Flat surface only.")]),
            ("Day 4 - Upper Body & Core",[("Upper Body Strength","3 x 12","Moderate","Arms, Chest, Back","Full upper body - foot is unloaded."),("Core Work","3 x 15","Bodyweight","Core","Dead bug, bird dog - no standing load."),("Swimming","1 x 20 min","--","Full body","Zero plantar load. Excellent cross-training.")]),
            ("Day 5 - Eccentric Loading",[("Eccentric Calf Lowering","3 x 15","Bodyweight","Calf, Plantar fascia","Rise on both feet, lower on one."),("Stair Stretch","3 x 30s","Bodyweight","Calf, Arch","Heel off step. Slow stretch. Both sides."),("Ankle Mobility Circles","3 x 10","Bodyweight","Ankle joint","Restore full range after rest.")]),
            ("Day 6 - Cardio Without Impact",[("Stationary Cycling","1 x 25 min","--","Heart, Legs","Zero plantar fascia load."),("Aqua Jogging","1 x 20 min","--","Full body","Buoyancy removes ground-force impact.")]),
            ("Day 7 - Rest & Ice",[("Complete Rest","--","--","Recovery","Ice 15 min morning and evening."),("Plantar Fascia Stretch","3 x 30s","Bodyweight","Plantar fascia","First thing on waking - most important time.")]),
        ]
    },
    "Muscle Strain (General)":{
        "phase":"Muscle Strain Rehabilitation",
        "warning":"Never stretch into pain. Do not return to full training until pain-free through full ROM for 7 consecutive days.",
        "program":[
            ("Day 1-2 - PRICE Protocol",[("Complete Rest","--","--","Injured muscle","Protect. Rest. No loading of strained area."),("Ice Application","3 x 15 min","--","Inflammation control","Every 2 hours for first 48 hours."),("Compression","--","--","Swelling reduction","Compression bandage if accessible."),("Elevation","--","--","Circulation","Elevate limb above heart level when resting.")]),
            ("Day 3 - Gentle Activation",[("Isometric Holds","3 x 10","Bodyweight","Strained muscle","Gentle contraction. No movement. Hold 5 sec."),("Range of Motion (pain-free)","3x10","Bodyweight","Joint mobility","Move through pain-free range only."),("Unaffected Area Training","3 x 12","Moderate","Uninjured muscles","Train everything except the strained area.")]),
            ("Day 4-5 - Gentle Stretching",[("Static Stretch (gentle)","3 x 30s","Bodyweight","Strained muscle","Hold at first point of tension. No pain."),("Active ROM","3 x 15","Bodyweight","Joint mobility","Move through full pain-free range actively."),("Cross-Training","1 x 20 min","--","Cardio","Swimming or cycling to maintain fitness.")]),
            ("Day 6 - Progressive Loading",[("Eccentric Training","3 x 10","Light weight","Strained muscle","Slow lowering phase. Rebuilds muscle fibre."),("Resistance Band Work","3 x 15","Light band","Strained muscle","Light resistance through full range."),("Balance Work","3 x 30s","Bodyweight","Stability","Proprioception often impaired after strain.")]),
            ("Day 7 - Return to Function",[("Sport-Specific Movement","3 x 10","Bodyweight","Full function","Only when 100% pain-free. Gradual return."),("Full Stretch Routine","1 x 15 min","Bodyweight","Flexibility","Comprehensive stretching of entire body.")]),
        ]
    },
    "Tendonitis (General)":{
        "phase":"Tendonitis Rehabilitation",
        "warning":"Avoid high-impact and repetitive loading of the affected tendon. Warm up thoroughly before any exercise.",
        "program":[
            ("Day 1 - Load Reduction",[("Complete Rest from aggravating activity","--","--","Tendon","Remove the cause. Identify and stop the trigger."),("Ice Massage","3 x 5 min","--","Tendon","Ice cube directly on tendon. Circular motion."),("Gentle ROM","3 x 10","Bodyweight","Joint mobility","Move through pain-free range only.")]),
            ("Day 2-3 - Isometric Loading",[("Isometric Hold","5 x 45s","Moderate","Affected tendon","Isometrics reduce tendon pain immediately."),("Unloaded Mobility","3 x 10","Bodyweight","Joint","Move without resistance. Restore motion.")]),
            ("Day 4-5 - Isotonic Loading",[("Slow Eccentric Training","3 x 15","Light weight","Affected tendon","3 sec lowering phase. Tendon remodelling."),("Concentric Strengthening","3 x 15","Light weight","Tendon + muscle","Normal lifting speed. Build from light.")]),
            ("Day 6 - Energy Storage",[("Plyometric Progression","3 x 8","Bodyweight","Tendon resilience","Only begin when pain-free for 1 week."),("Sport-Specific Load","3 x 10","Moderate","Functional movement","Gradual return to normal training patterns.")]),
            ("Day 7 - Rest",[("Complete Rest","--","--","Tendon recovery","Mandatory rest day between tendon loading sessions."),("Contrast Therapy","2 x 10 min","--","Circulation","Alternate hot and cold. Promotes healing.")]),
        ]
    },
    "Frozen Shoulder (Adhesive Capsulitis)":{
        "phase":"Frozen Shoulder Rehabilitation",
        "warning":"Never force range of motion. Pain during stretching means you have gone too far. Progress is measured in weeks, not days.",
        "program":[
            ("Day 1 - Pendulum & Heat",[("Pendulum Swings","3 x 60s","Bodyweight","Shoulder capsule","Lean on table. Let arm hang and swing freely."),("Heat Application","2 x 15 min","--","Blood flow","Apply heat before exercise to increase mobility."),("Finger Wall Walk","3 x 10","Bodyweight","Shoulder ROM","Walk fingers up wall as high as comfortable.")]),
            ("Day 2 - Assisted ROM",[("Pulley Exercise","3 x 15","Rope/band","Shoulder flexion","Use good arm to lift affected arm via pulley."),("Cross-Body Stretch","3 x 30s","Bodyweight","Posterior capsule","Pull arm across chest. Gentle sustained hold."),("Sleeper Stretch","3 x 30s","Bodyweight","Posterior shoulder","Lie on affected side. Gentle internal rotation.")]),
            ("Day 3 - Strengthening",[("Isometric Flexion","3 x 10","Bodyweight","Anterior deltoid","Push arm forward against wall. No movement."),("Isometric Abduction","3 x 10","Bodyweight","Middle deltoid","Push arm out against wall. Isometric hold."),("Scapular Retractions","3 x 15","Bodyweight","Rhomboids","Improve postural support around shoulder.")]),
            ("Day 4 - Rest & Lower Body",[("Brisk Walking","1 x 25 min","--","Heart, Legs","Maintain cardio fitness during recovery."),("Bodyweight Squats","3 x 15","Bodyweight","Legs","Full lower body training safe with frozen shoulder."),("Core Work","3 x 20s","Bodyweight","Core","Plank on forearms. No shoulder loading.")]),
            ("Day 5 - Rotation Work",[("External Rotation (supine)","3x15","Light band","Rotator cuff","Lying down removes gravity load."),("Internal Rotation Stretch","3x30s","Bodyweight","Internal rotators","Behind-back reach. Very gentle."),("Shoulder Circles (small)","3 x 10","Bodyweight","Shoulder joint","Tiny circles. Increase size gradually.")]),
            ("Day 6 - Functional Reach",[("Overhead Reach (assisted)","3x10","Bodyweight","Shoulder flexion","Use other hand to assist. Stop at pain."),("Low-Impact Cardio","1 x 20 min","--","Heart","Walking or stationary bike.")]),
            ("Day 7 - Full Rest",[("Complete Rest","--","--","Recovery","Ice if inflamed. Heat if stiff."),("Gentle Pendulums only","2 x 30s","Bodyweight","Shoulder","Maintenance movement only.")]),
        ]
    },
}

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
        fig.update_layout(**ly("Daily Steps")); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    with c2:
        fig=go.Figure(); fig.add_trace(go.Bar(x=df["date"],y=df["active_minutes"],marker_color="#00B4FF",opacity=0.85,name="Active Min"))
        fig.update_layout(**ly("Active Minutes")); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    c3,c4=st.columns(2)
    with c3:
        fig=go.Figure(); fig.add_trace(go.Scatter(x=df["date"],y=df["bmi"],mode="lines+markers",
            line=dict(color="#FF6B35",width=2),marker=dict(size=5,color="#FF6B35"),name="BMI"))
        fig.add_hrect(y0=18.5,y1=24.9,fillcolor="rgba(0,230,118,0.05)",line_width=0,
            annotation_text="Normal",annotation_font=dict(size=10,color="#00E676"))
        fig.update_layout(**ly("BMI Trend")); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    with c4:
        fig=go.Figure(); fig.add_trace(go.Scatter(x=df["date"],y=df["calorie_score"],mode="lines+markers",
            line=dict(color="#FF4D00",width=2),marker=dict(size=5,color="#FF4D00"),
            fill="tozeroy",fillcolor="rgba(255,77,0,0.06)",name="GA Score"))
        fig.update_layout(**ly("GA Calorie Score")); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

# ============================================================
# PDF EXPORT — unicode safe
# ============================================================
def generate_pdf(user_profile,bmi,bmi_cat,norm_calories,calorie_intensity,
                 rl_rec,rl_tip,streak,total_sessions,badges,injury_profile=None):
    try: from fpdf import FPDF
    except ImportError: return None

    def clean(text):
        return (str(text).replace("\u2014","-").replace("\u2013","-").replace("\u00b7",".")
                .replace("\u2022","-").replace("\u2019","'").replace("\u2018","'")
                .replace("\u201c",'"').replace("\u201d",'"').replace("\u2026","..."))

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(8,10,14); self.rect(0,0,210,297,'F')
            self.set_font("Helvetica","B",28); self.set_text_color(232,255,0)
            self.cell(0,14,"FITGENIX",ln=True,align="C")
            self.set_font("Helvetica","",9); self.set_text_color(107,114,128)
            self.cell(0,6,"Adaptive Fitness Intelligence Report",ln=True,align="C"); self.ln(4)
        def section(self,title):
            self.set_font("Helvetica","B",11); self.set_text_color(232,255,0)
            self.cell(0,8,clean(title).upper(),ln=True)
            self.set_draw_color(232,255,0); self.set_line_width(0.3)
            self.line(10,self.get_y(),200,self.get_y()); self.ln(3)
        def row(self,label,value):
            self.set_font("Helvetica","",9); self.set_text_color(107,114,128)
            self.cell(55,7,clean(label),ln=False); self.set_text_color(240,242,245)
            self.cell(0,7,clean(value),ln=True)

    pdf=PDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True,margin=15)
    pdf.set_font("Helvetica","",8); pdf.set_text_color(107,114,128)
    pdf.cell(0,6,f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}",ln=True,align="R"); pdf.ln(2)
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
    pdf.set_y(-20); pdf.set_font("Helvetica","",7); pdf.set_text_color(55,65,81)
    pdf.cell(0,5,"FITGENIX - GA + RL + 39 Training Types + Injury-Aware AI Coach",align="C")
    return pdf.output()

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
            if st.button("Log in", use_container_width=True, key="btn_login"):
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
            if st.button("Create account", use_container_width=True, key="btn_signup"):
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
    generate = st.button("GENERATE MY REPORT", use_container_width=True)

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
if not generate:
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
    rl_rec,rl_color,rl_tip = get_rl_recommendation(fatigue_level)
    bmi,bmi_cat,bmi_color  = calculate_bmi(weight_kg,height_cm)

    save_entry({"steps":steps,"active_minutes":active_minutes,"bmi":bmi,
                "calorie_score":round(norm_calories,4),"calorie_intensity":calorie_intensity,
                "rl_rec":rl_rec,"goal":goal,"fatigue":fatigue_choice,"weight":weight_kg,"height":height_cm})
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
        st.dataframe(q_df,use_container_width=True)

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

    st.markdown("""<hr style="border:none;border-top:1px solid rgba(232,255,0,0.1);margin:1.5rem 0;">
    <div style="font-size:0.7rem;letter-spacing:0.2em;color:#E8FF00;text-transform:uppercase;
                margin-bottom:0.75rem;">-- Export Your Report</div>""",unsafe_allow_html=True)

    pdf_bytes=generate_pdf(user_profile,bmi,bmi_cat,norm_calories,calorie_intensity,
                           rl_rec,rl_tip,streak,total_sessions,badges,injury_profile)
    if pdf_bytes:
        st.download_button(label="Download PDF Report",data=pdf_bytes,
            file_name=f"FITGENIX_Report_{datetime.date.today().isoformat()}.pdf",
            mime="application/pdf",use_container_width=True)
    else:
        st.info("Run `pip install fpdf2` to enable PDF export.")

    st.markdown("""
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.05);margin:2rem 0 1rem;">
    <div style="text-align:center;font-size:0.75rem;color:#374151;">
      FITGENIX - Genetic Algorithm + Reinforcement Learning + 39 Training Modalities + Injury-Aware AI Coach<br>
      Research: Real-Time Adaptive Fitness Planning with Genetic Algorithms - Fitbit Dataset
    </div>""",unsafe_allow_html=True)
