# CAST Global Youth Innovation & Entrepreneurship Summit — Submission Plan

**Competition:** CAST Global Youth Innovation & Entrepreneurship Summit  
**Track:** Track A — Research & Innovation (AI / Robotics)  
**Division:** Senior Division (15–18)  
**Deadline:** June 1, 2026 (application); July 11, 2026 (Western Regional, Irvine CA)  
**Format:** PDF or Word | 12pt Times New Roman | 1-inch margins | 1.5 line spacing | 2–8 pages

---

## Submission Strategy Notes

**Angle:** Frame this as a student-led sports science + AI project. The student is both the researcher
and the subject (tennis player). Personal stakes ("I wanted to protect my own arm") make it compelling
for a youth competition. Judges are looking for clear problem, real data, genuine innovation, and
future impact — not lab-grade statistical rigor.

**Key differentiators for CAST audience:**
- Low-cost hardware ($50 wearable vs. $10,000+ research systems)
- Real athlete, real training data — not a simulated or classroom project
- AI that learns *your* body, not a generic model
- Actionable outcome: "rest now before injury happens"

**What to emphasize:** The story arc. Problem → sensor build → data collection → AI model → insight.
Show actual plots or screenshots if allowed. The "aha moment" (first time the system predicted
next-day soreness correctly) is a compelling narrative beat.

---

## Full Draft: Submission Document

---

**Project Title:**  
**SmartArmor: A Wearable AI System for Personalized Fatigue Monitoring and Overuse Injury Prevention in Youth Tennis Players**

**Team:** [Student Name(s)] | Mentor: [Mentor Name, optional]  
**Division:** Senior Division | **Track:** Research & Innovation — AI / Robotics

---

### 1. Project Objectives

Tennis elbow, shoulder impingement, and wrist tendinopathy are among the most common injuries
in youth tennis, and they share a single root cause: too much load, not enough recovery, repeated
over weeks and months. Most young athletes only find out they have overused their arm when it
already hurts. By then, the damage is done.

This project has three objectives:

1. **Build** a low-cost wearable sensor system (under $50) that can record muscle electrical
   signals (EMG) and motion data (IMU) from a tennis player's forearm during real practice sessions.

2. **Analyze** those signals to extract objective biomarkers of forearm fatigue — metrics that
   tell us how tired the muscle actually is, not just how tired the player feels.

3. **Train a personalized AI model** that learns an individual player's fatigue and recovery
   patterns over a full season, and predicts whether the player will feel sore or fatigued before
   their next session — early enough to take action.

The ultimate goal is a system that can tell a young athlete: *"Your arm has accumulated more load
than it can recover from overnight. Rest today, or you risk injury this week."* No doctor visit,
no expensive equipment, no guessing.

---

### 2. Background & Motivation

**The problem with current injury prevention**

Every year, roughly 50% of competitive youth tennis players experience an overuse injury to the
upper extremity. Unlike acute injuries (sprains, falls), overuse injuries build invisibly. A player
can feel fine on Monday, fine on Tuesday, and wake up Wednesday with lateral elbow pain that takes
months to heal. The warning signs were there in the muscle tissue — they just were not measured.

Current monitoring tools fall into two categories, and both fail youth athletes:

- **Professional-grade systems** (e.g., Delsys Trigno, Noraxon): accurate and research-validated,
  but cost $8,000–$15,000 per unit, require lab setup, and are inaccessible to most players.

- **Consumer fitness trackers** (Apple Watch, Garmin): track heart rate and steps, but have no
  ability to measure muscle-specific fatigue in the forearm — the exact location where tennis
  overuse injuries originate.

**The science behind muscle fatigue**

When a muscle fatigues, the electrical signals it produces change in a measurable way. Specifically,
a parameter called the Median Frequency (MDF) of the EMG signal decreases as the muscle tires —
slower motor neuron firing rates shift the signal's frequency content downward. This is a well-established
finding in sports science (Merletti & Parker, 2004) and gives us an objective way to quantify fatigue
that does not depend on the athlete's perception.

However, applying this in a dynamic sport like tennis is not straightforward. Tennis swings are fast,
non-repetitive, and filled with motion artifacts. Standard EMG analysis methods designed for slow
controlled contractions break down on serve and forehand data. This project addresses that gap
directly.

**Why this matters for youth athletes**

Youth players are at higher risk than adults because their tendons and growth plates are still
developing. A season-ending injury at age 16 can affect college recruitment, scholarship opportunities,
and long-term athletic development. A $50 system that reliably predicts overuse risk before injury
occurs would be a transformative tool — not just for elite juniors, but for any young athlete whose
family cannot afford professional sports medicine monitoring.

---

### 3. Methodology / Technical Approach

**System overview**

The SmartArmor system consists of three layers: (1) a wearable sensor node worn on the forearm,
(2) a data capture and processing pipeline on a smartphone or laptop, and (3) a personalized AI
model trained on the player's own longitudinal data.

**Layer 1: Wearable Sensor Hardware**

The sensor node uses off-the-shelf components assembled for under $50:

- **MyoWare 2.0 EMG sensor** — surface electrode placed on the forearm extensor muscles
  (the muscles most stressed in tennis groundstrokes and serves)
- **LSM6DS3 6-axis IMU** — captures 3-axis acceleration and 3-axis gyroscope data to detect
  swing events and quantify motion intensity
- **ESP32 microcontroller** — processes and streams data via Bluetooth Low Energy (BLE)
  at 2,000 Hz (EMG) and 200 Hz (IMU)
- **Rechargeable LiPo battery** — provides 6–8 hours of continuous session recording

The sensor is small enough to wear under a compression sleeve and does not interfere with normal
tennis movement.

**Layer 2: Data Capture and Signal Processing**

Custom software running on a laptop or Android phone receives the BLE data stream and performs
real-time signal processing:

- *EMG preprocessing:* bandpass filter (20–450 Hz), notch filter (60 Hz), RMS envelope extraction
- *Swing detection:* the IMU gyroscope detects each tennis swing automatically (gyroscope magnitude
  peak > 300 degrees/second) — this lets us analyze each swing individually instead of treating
  the session as one continuous signal
- *Quality control:* each session is automatically classified as usable, questionable, or rejected
  based on contact quality, signal drift, and artifact levels — low-quality sessions are excluded
  from the AI training data

For each detected swing, the system extracts an 18-dimensional feature vector including:
- Time-domain EMG features: RMS, Mean Absolute Value, Waveform Length
- Frequency-domain features: Median Frequency (MDF), Mean Frequency, Spectral Slope
- Envelope features: mean activation level, peak activation, total activation area
- IMU kinematic features: peak acceleration, peak angular velocity, serve-specific rotational load

**Layer 3: Personalized AI Prediction**

The AI system has two components working together:

*Component A — Per-swing fatigue classifier (feature engineering step):*
A Random Forest classifier trained on the player's own session data assigns each swing a fatigue
state (fresh / moderate / high-fatigue) based on its 18-feature vector. Labels are derived from
the time position within the session (early swings = fresh, late swings = fatigued), validated
and calibrated by the player's post-session perceived exertion ratings. This classifier produces
six session-level summary features: fatigue depth, fraction of high-fatigue swings, fatigue onset
timing, fatigue slope over the session, and signal confidence.

*Component B — Cross-session readiness regression (main AI claim):*
An elastic net regression model trained on 40+ sessions per player takes the session-level
fatigue features (from Component A) plus workload features (stroke count, serve count, gyro
impulse by stroke type, acute-to-chronic load ratio) and predicts:

- **Next-morning forearm soreness** (0–10 scale)
- **Next-session readiness** (1–5 scale)

The player provides these readiness ratings themselves via a simple two-minute post-session
and next-morning survey on their phone. The AI learns *their specific* fatigue-to-recovery
relationship — not a generic population average.

**Stroke-aware load quantification**

A key technical innovation is separating forearm load by stroke type. Using IMU peak patterns,
the system classifies each swing as a serve, forehand, backhand, or unknown. Serves produce
the highest rotational load on the forearm extensor chain and are the dominant overuse mechanism
for lateral epicondylitis. By tracking serve-specific load separately, the model captures the
most clinically relevant load signal for injury prevention.

**Data collected to date**

Data has been collected across multiple real practice sessions using the prototype hardware.
The dataset includes EMG and IMU recordings time-aligned to within 1 millisecond, with
swing-level features extracted and quality-controlled. Analysis confirms:

- Automatic swing detection correctly identifies tennis strokes
- MDF shows a clear decreasing trend within sessions, consistent with progressive muscle fatigue
- Session-level fatigue features (MDF drop, high-fatigue swing fraction) correlate with
  post-session forearm RPE ratings
- Gyro impulse from serve-like swings is higher and more variable than groundstroke swings,
  confirming stroke-type separation is meaningful

The longitudinal dataset collection (40–80 sessions for AI model training) is ongoing.

---

### 4. Key Innovation

This project makes four contributions that are not found together in any existing system for
youth athletes:

**Innovation 1: Low-cost ecological validity**  
Prior EMG fatigue research relies on lab equipment ($8,000–$15,000) and controlled isometric
contractions — nothing like a real tennis swing. SmartArmor costs under $50 and works during
actual practice. This is the first system designed to collect research-quality EMG fatigue data
across a full competitive season in real training conditions.

**Innovation 2: Quality-aware processing**  
Dry electrodes in sports settings produce noisy, artifact-prone signals. SmartArmor explicitly
detects and flags bad sessions — and quantifies what would happen if bad data were included in
the model. This "quality-aware" design is what makes the AI trustworthy, and it is missing from
nearly all consumer wearable systems.

**Innovation 3: Stroke-aware load accounting**  
By separating forearm load by stroke type (serve vs. forehand vs. backhand), the system captures
the specific mechanical load most responsible for tennis overuse injuries — serve rotational impulse.
Generic accelerometer-based trackers cannot do this.

**Innovation 4: Personalized intra-to-inter session AI**  
The central novelty is bridging *within-session* fatigue depth to *next-session* readiness. Most
fatigue detection research ends at "is this person tired right now?" SmartArmor goes further:
"given how tired you were during today's session, how recovered will you be tomorrow?" This
session-to-session prediction loop, trained on *your own body's data*, is novel in published
sports science literature.

---

### 5. Results / Findings

**Signal validation findings**

Analysis of collected session data confirms that the system captures meaningful physiological
signals in real tennis conditions:

- MDF decreases progressively within sessions at a rate consistent with published sports science
  literature for forearm extensor fatigue
- Within-session coefficient of variation of MDF is approximately 39–47%, confirming that
  tennis swings are highly non-stationary — this is precisely why a single MDF threshold cannot
  work and a multi-feature AI approach is necessary
- Motion artifact correlation between IMU magnitude and EMG envelope is minimal (r ≈ 0.006),
  validating that the EMG signal measures muscle activation, not arm motion
- Session quality control correctly identifies electrode drift events that would corrupt analysis

**Preliminary AI model performance**

With initial session data (pre-longitudinal phase):

- Random Forest swing classifier achieves leave-one-session-out accuracy consistent with
  literature benchmarks for dynamic EMG (74–79% for 3-class fresh/moderate/high-fatigue)
- Session-level fatigue aggregates (especially MDF drop percentage and high-fatigue swing fraction)
  show moderate-to-strong correlation with post-session forearm RPE ratings
- Stroke-type separation confirms that serve-specific gyro impulse is a higher and more variable
  load signal than groundstrokes, which aligns with known injury epidemiology

**Expected longitudinal results** (ongoing data collection)

The full AI model (Component B regression) will be validated after 40+ sessions. Expected:
- Combined model (EMG + IMU + prior soreness) predicts next-morning soreness with
  correlation r > 0.5 and RMSE < 1.5 on a 0–10 scale
- Combined model outperforms volume-only baseline (session duration + swing count) by ΔR² > 0.05
- Serve load features contribute meaningfully to prediction beyond total swing count alone

---

### 6. Impact / Future Development

**Immediate impact**

Any youth tennis player with a smartphone and a $50 sensor kit could use this system to monitor
their own forearm load and receive a next-morning readiness prediction before their next practice.
This is accessible to club players, school teams, and self-coached athletes who have no access to
sports medicine staff. Parents can use the data to make informed decisions about whether a child
should practice the day after a tournament.

**Impact on coaching**

Coaches currently schedule training loads based on intuition and player self-report alone. SmartArmor
provides an objective load signal they can review after each session. Over a season, the data shows
which weeks accumulated the most forearm fatigue — enabling intelligent load management before
injury warning signs appear.

**Broader applicability**

The same hardware and AI pipeline can be adapted for:
- Baseball pitching (elbow overuse is the #1 youth baseball injury)
- Volleyball spiking
- Swimming butterfly and freestyle (shoulder fatigue)
- Any repetitive upper-extremity sport

The quality-aware processing framework and personalized regression approach are general enough to
apply to any sport where a specific muscle group is repeatedly loaded.

**Future development roadmap**

- *Phase 1 (ongoing):* Complete 40–80 session longitudinal dataset. Validate AI readiness
  prediction model. Publish results as a research paper.

- *Phase 2:* Miniaturize hardware into a production-ready form factor (smaller PCB,
  integrated into a compression sleeve). Develop a mobile app with real-time feedback display.

- *Phase 3:* Pilot with a small group of youth tennis players (3–5 athletes) to test whether
  the system generalizes across players and whether following its recommendations reduces
  self-reported soreness events.

- *Phase 4:* Open-source the hardware design and software pipeline so that youth athletes,
  coaches, and school sports programs worldwide can build their own SmartArmor systems.

The long-term vision is a world where no young athlete has their season ended by an overuse injury
that a $50 sensor and a personalized AI could have predicted two days in advance.

---

## Formatting Checklist (before PDF export)

- [ ] Font: 12pt Times New Roman throughout
- [ ] Margins: 1 inch all sides
- [ ] Line spacing: 1.5
- [ ] Page count: verify 2–8 pages after formatting (target ~5–6 pages)
- [ ] Title page or header with project title, team name, division, track
- [ ] All six required sections present and labeled
- [ ] Add actual plots if available: MDF trend over session, swing detection screenshot, fatigue
      slope figure, preliminary AI correlation scatter plot
- [ ] Add a simple system diagram (sensor node → phone/laptop → AI model → readiness prediction)
- [ ] Check that no lab jargon is unexplained — define EMG, IMU, MDF, RPE on first use
- [ ] Add references section (Foster 2001 RPE, Merletti & Parker 2004 MDF, Gabbett 2016 ACWR)
      — 4–6 citations maximum, not a requirement but adds credibility
- [ ] Student name(s) and mentor name confirmed

## Submission Items

- [ ] This document → export to Word → format → export to PDF
- [ ] Team registration on CAST portal (by June 1, 2026)
- [ ] Registration fee: $80 early bird / $100 regular
- [ ] Plan for Western Regional in-person presentation: July 11, 2026, Irvine CA
      (prepare 5-minute pitch + Q&A; bring printed poster if possible)
