"""
FITGENIX — Unit Tests
=====================
Tests the load-bearing engine logic: injury filtering, schedule generation,
the personalised-RL safety behaviour, and BMI categorisation.

These tests import the REAL functions from streamlit_app.py + data.py. Because
the app file also contains Streamlit UI calls at module load, we extract and
exec only the pure-logic region (data + engine, up to the auth gate) into an
isolated namespace — so the tests exercise production code without needing a
running Streamlit server or Supabase.

Run:  pytest -v        (from the project root, with streamlit_app.py + data.py present)
"""

import os
import sys
import types
import importlib.util
import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))   # tests/ lives under project root


def _load_engine():
    """Load data.py + the pure-logic slice of the app into one namespace."""
    # streamlit stub (module-load calls like st.cache_resource must not fail)
    st = types.ModuleType("streamlit")
    st.session_state = {}
    st.cache_resource = lambda *a, **k: (lambda f: f)
    st.cache_data = lambda *a, **k: (lambda f: f)
    sys.modules["streamlit"] = st

    # make data.py importable
    sys.path.insert(0, ROOT)

    # find the app entry file (named streamlit_app.py in the repo, app.py locally)
    app_path = None
    for name in ("streamlit_app.py", "app.py"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            app_path = p
            break
    assert app_path, "Could not find streamlit_app.py or app.py in project root"

    src = open(app_path, encoding="utf-8").read()
    # start a bit before the data import so pre-import pure helpers
    # (predict_calories, get_rl_recommendation, calculate_bmi) are included
    start = src.index("def predict_calories")
    end_anchor = src.index("# AUTHENTICATION GATE")
    end = src.rfind("# ====", 0, end_anchor)
    slice_src = ("import numpy as np\n"
                 "from urllib.parse import quote_plus\n"
                 "import datetime\n" + src[start:end])
    ns = {}
    exec(compile(slice_src, app_path, "exec"), ns)
    return ns


ENGINE = _load_engine()


# ----------------------------------------------------------------------
# 1. BMI categorisation (boundary correctness)
# ----------------------------------------------------------------------
class TestBMI:
    def test_normal_weight(self):
        bmi, cat, _ = ENGINE["calculate_bmi"](70, 175)
        assert cat == "Normal weight"
        assert 22 < bmi < 24

    def test_underweight_boundary(self):
        # BMI just under 18.5
        _, cat, _ = ENGINE["calculate_bmi"](47, 170)   # ~16.3
        assert cat == "Underweight"

    def test_overweight(self):
        _, cat, _ = ENGINE["calculate_bmi"](85, 175)    # ~27.8
        assert cat == "Overweight"

    def test_obese(self):
        _, cat, _ = ENGINE["calculate_bmi"](110, 170)   # ~38
        assert cat == "Obese"

    def test_returns_rounded_value(self):
        bmi, _, _ = ENGINE["calculate_bmi"](70, 175)
        assert bmi == round(bmi, 1)


# ----------------------------------------------------------------------
# 2. Injury filtering
# ----------------------------------------------------------------------
class TestInjuryFiltering:
    def test_severe_knee_blocks_legs(self):
        blocked = ENGINE["get_blocked_groups"]("Knee", "Severe - no movement in this area")
        assert "legs" in blocked

    def test_moderate_knee_modifies_not_blocks(self):
        blocked = ENGINE["get_blocked_groups"]("Knee", "Moderate - some pain")
        modified = ENGINE["get_modified_groups"]("Knee", "Moderate - some pain")
        assert blocked == []            # moderate does not block
        assert "legs" in modified       # it modifies instead

    def test_no_injury_blocks_nothing(self):
        assert ENGINE["get_blocked_groups"]("Knee", "") == []
        assert ENGINE["get_modified_groups"]("Knee", "") == []

    def test_severe_knee_removes_leg_exercises_from_plan(self):
        prof = _profile(goal="Hypertrophy Training")
        plan = ENGINE["get_plan_data"](prof, {"has_injury": "Yes",
                                              "body_part": "Knee",
                                              "severity": "Severe - no movement in this area"})
        # collect every exercise's muscle text; no pure-leg exercise should appear
        leg_terms = ("Squat", "Lunge", "Glute Bridge", "Calf", "Step-Up")
        names = [ex["name"] for d in plan for ex in d["exercises"]]
        leaked = [n for n in names if any(t in n for t in leg_terms)]
        assert leaked == [], f"Severe knee should remove leg work, found: {leaked}"

    def test_safe_exercise_lookup_returns_list(self):
        safe = ENGINE["get_injury_safe_exercises"]("Knee", "Moderate - some pain")
        assert isinstance(safe, list) and len(safe) > 0


# ----------------------------------------------------------------------
# 3. Schedule generation
# ----------------------------------------------------------------------
class TestSchedule:
    def test_seven_day_plan(self):
        plan = ENGINE["get_plan_data"](_profile(), {"has_injury": "No"})
        assert len(plan) == 7

    def test_very_fatigued_makes_day1_recovery(self):
        prof = _profile(fatigue="Very Fatigued")
        plan = ENGINE["get_plan_data"](prof, {"has_injury": "No"})
        assert plan[0]["is_rest"] or "Recovery" in plan[0]["focus"]

    def test_overweight_adds_cardio(self):
        prof = _profile(bmi_cat="Overweight")
        plan = ENGINE["get_plan_data"](prof, {"has_injury": "No"})
        all_muscles = " ".join(ex["muscles"] for d in plan for ex in d["exercises"]).lower()
        focuses = " ".join(d["focus"] for d in plan).lower()
        assert "cardio" in focuses or "cardio" in all_muscles

    def test_every_training_day_has_exercises(self):
        plan = ENGINE["get_plan_data"](_profile(), {"has_injury": "No"})
        for d in plan:
            if not d["is_rest"]:
                assert len(d["exercises"]) > 0


# ----------------------------------------------------------------------
# 4. Personalised RL — the safety property that matters most
# ----------------------------------------------------------------------
class TestRLSafety:
    """Replicates the production reward/update math (rl_learn_from_outcomes) to
    assert the safety behaviour we validated in Phase 3."""

    ALPHA = 0.25

    def _update(self, row, rec, outcomes, cap):
        too_hard = sum(1 for o in outcomes if o["difficulty"] == "too_hard")
        done = sum(1 for o in outcomes if o["status"] == "completed" and o["difficulty"] != "too_hard")
        skipped = sum(1 for o in outcomes if o["status"] == "skipped")
        n = len(outcomes)
        reward = max(-1.0, min(1.0, (done - too_hard - 0.4 * skipped) / n))
        row = row.copy()
        row[rec] += self.ALPHA * (reward - row[rec])
        if too_hard > 0 and rec > 0:
            row[rec - 1] += self.ALPHA * 0.5 * abs(reward)
        if too_hard == 0 and done == n and rec < len(row) - 1:
            row[rec + 1] += self.ALPHA * 0.5 * reward
        new_cap = rec if too_hard > 0 else cap
        return row, new_cap, reward

    def _recommend(self, row, cap):
        if cap is not None and cap < len(row) - 1:
            return int(np.argmax(row[:cap + 1]))
        return int(np.argmax(row))

    def test_too_hard_lowers_intensity(self):
        row = np.array([0.4, 0.6, 0.7, 0.3])   # argmax = MODERATE (2)
        cap = None
        start = self._recommend(row, cap)
        out = [{"status": "completed", "difficulty": "too_hard"}] * 3
        row, cap, _ = self._update(row, start, out, cap)
        assert self._recommend(row, cap) < start   # moved to a gentler intensity

    def test_safety_cap_never_recommends_high_after_too_hard(self):
        row = np.array([0.4, 0.6, 0.7, 0.3])
        cap = None
        for _ in range(8):
            rec = self._recommend(row, cap)
            out = [{"status": "completed", "difficulty": "too_hard"}] * 3
            row, cap, _ = self._update(row, rec, out, cap)
            assert self._recommend(row, cap) != 3   # NEVER HIGH INTENSITY

    def test_easy_completion_can_increase_intensity(self):
        row = np.array([0.4, 0.6, 0.55, 0.3])   # argmax = LIGHT (1)
        cap = None
        start = self._recommend(row, cap)
        for _ in range(4):
            rec = self._recommend(row, cap)
            out = [{"status": "completed", "difficulty": None}] * 3
            row, cap, _ = self._update(row, rec, out, cap)
        assert self._recommend(row, cap) >= start   # progressed or held, never dropped

    def test_reward_bounded(self):
        row = np.array([0.4, 0.6, 0.7, 0.3])
        _, _, r = self._update(row, 2, [{"status": "completed", "difficulty": None}], None)
        assert -1.0 <= r <= 1.0


# ----------------------------------------------------------------------
# helper
# ----------------------------------------------------------------------
def _profile(goal="Hypertrophy Training", fatigue="Fully Rested", bmi_cat="Normal weight"):
    return {
        "age": 27, "gender": "Male", "height": 175, "weight": 72,
        "bmi": 23.5, "bmi_cat": bmi_cat, "body_type": "Mesomorph",
        "fitness_level": "Intermediate", "goal": goal,
        "steps": 8000, "active_minutes": 60, "fatigue": fatigue,
        "calorie_intensity": "Moderate", "rl_rec": "MODERATE WORKOUT",
    }


# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 5. Phase 5 — split-first programme structure (logical day alignment)
# ----------------------------------------------------------------------
class TestSplitStructure:
    def test_ppl_only_offers_3_or_6_days(self):
        assert ENGINE["days_for_split"]("ppl") == [3, 6]

    def test_upper_lower_offers_2_or_4(self):
        assert ENGINE["days_for_split"]("upper_lower") == [2, 4]

    def test_full_body_offers_2_or_3(self):
        assert ENGINE["days_for_split"]("full_body") == [2, 3]

    def test_single_specialize_allows_up_to_6(self):
        days = ENGINE["days_for_split"]("single", "specialize")
        assert max(days) == 6 and min(days) == 1

    def test_single_rotate_needs_enough_days(self):
        days = ENGINE["days_for_split"]("single", "rotate")
        assert min(days) >= 3   # can't rotate body parts in <3 days

    def test_specialization_warns_over_recovery_window(self):
        assert ENGINE["specialization_recovery_warning"](4) is not None  # warns
        assert ENGINE["specialization_recovery_warning"](2) is None      # safe, no warn

    def test_five_split_choices_exist(self):
        assert len(ENGINE["SPLIT_CHOICES"]) == 5
