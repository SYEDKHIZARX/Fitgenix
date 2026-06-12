"""
FITGENIX - Static data module.
Pure data structures (exercise library, training types, injury maps,
rehab protocols, comprehension info, movement-image map). No Streamlit,
no logic - just data, imported by streamlit_app.py via `from data import *`.
"""

__all__ = ["INJURY_MUSCLE_MAP","INJURY_SAFE_EXERCISES","DEFAULT_SAFE","TRAINING_TYPES","EXERCISE_LIBRARY","EXERCISE_INFO","_IMG_BASE","_EXERCISE_IMAGES","_EMPHASIS_WHY","REHAB_PROTOCOLS","SPLIT_CHOICES","SPLIT_DAYS","SPECIALIZE_MUSCLES","days_for_split","specialization_recovery_warning"]

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

_EMPHASIS_WHY = {
    "volume": "high training volume to drive muscle growth",
    "maximal": "heavy, low-rep work to build maximal strength",
    "power": "explosive movement to develop power",
    "explosive": "explosive movement to develop power",
    "aesthetic": "targeted volume for muscle shape and definition",
    "balanced": "balanced strength across the body",
    "full_body": "full-body strength and coordination",
    "static": "static holds to build control and stability",
    "endurance": "higher reps to build muscular endurance",
    "variety": "varied stimulus to keep progress steady",
    "metabolic": "elevated heart rate to maximise calorie burn",
    "hypertrophy": "muscle-building volume",
}

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


# ============================================================
# PHASE 5: SPLIT-FIRST programme structure
# Ask the split the user wants, THEN offer day-counts that fit it.
# ============================================================

# The five split choices the user picks from (label, value)
SPLIT_CHOICES = [
    ("Single muscle focus",   "single"),
    ("Two muscles a day",     "two_a_day"),
    ("Push / Pull / Legs",    "ppl"),
    ("Upper & Lower body",    "upper_lower"),
    ("Full body",             "full_body"),
]

# Valid day-counts per split (recovery-aligned). Single-muscle handled separately.
SPLIT_DAYS = {
    "two_a_day":   [2, 3, 4],
    "ppl":         [3, 6],          # one or two full PPL rotations
    "upper_lower": [2, 4],          # each trained 1x or 2x per week
    "full_body":   [2, 3],
}

# Muscles selectable for single-muscle specialization
SPECIALIZE_MUSCLES = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"]

def days_for_split(split_value, single_mode=None):
    """Return the logical day-count options for a chosen split.
    single_mode: 'specialize' (train one muscle repeatedly, 1-6 days, warn >2)
                 'rotate'     (one muscle per day, cycle: 3-6 days)."""
    if split_value == "single":
        if single_mode == "specialize":
            return [1, 2, 3, 4, 5, 6]      # allowed, but warn beyond 2
        if single_mode == "rotate":
            return [3, 4, 5, 6]            # need enough days to rotate parts
        return [1, 2]
    return SPLIT_DAYS.get(split_value, [2, 3])

def specialization_recovery_warning(days):
    """Honest coach warning when specialization frequency risks under-recovery.
    A muscle needs ~48h to recover; training it >2x consecutively is suboptimal."""
    if days and days > 2:
        return ("Training one muscle " + str(days) + " days a week exceeds its "
                "~48h recovery window. You can proceed, but 1-2 focused sessions "
                "per week (with rest between) usually builds it faster and safer.")
    return None
