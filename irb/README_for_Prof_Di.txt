README — IRB Application Packet, Draft v0.5
=============================================
Date: 2026-05-23
For: Dr. YanMing Di (Faculty PI)
From: Xiaodong Wang (Technical Assistant)

WHAT'S IN THIS FOLDER
---------------------
IRB_Packet_OSU_sEMG_IMU_Athletic_Practice_v0.5.docx
    The full IRB application packet for OSU HRPP submission. Contains
    Cover Letter, Doc 1 (IRB Protocol), Doc 2A/2B (Parental Permission),
    Doc 3A/3B (Minor Assent), Doc 4 (Risk Assessment), Doc 5 (Sensor
    & Device Description), Doc 6 (COI Management Plan), Doc 7 (Data
    Security Plan), Doc 8 (IAA Designation + Script), and Appendices
    A-E (Manuscript Ethics Statement, Recruitment Plan, Adverse Event
    Procedure, CITI Tracker, IEEE Compliance Checklist).

IRB_requirements_v0.5.docx
    A reference document capturing the OSU HRPP and IEEE publication
    requirements that govern the packet. Includes a 14-row TBD table
    plus a grouped pre-submission action-item checklist (Part 4) for
    items that need real values before Cayuse submission.

STUDY AT A GLANCE
-----------------
Title:    Passive Forearm sEMG/IMU Monitoring During Tennis Practice
          and Running: A Minimal-Risk Two-Participant Pilot Case
          Series in Minor Student-Athletes
PI:       Dr. YanMing Di (Department of Statistics, OSU)
Cohort:   N=2 minor student-athletes / student co-authors
            * Ryan Wang (17, Westview HS) — tennis at residential
              court in California
            * Theodore (Teddy) Di (15, Crescent Valley HS) —
              running at neighborhood fitness center in Corvallis
Review:   Anticipated expedited review under 45 CFR 46.110
          (OSU determines the applicable category); non-exempt
          minimal-risk under 45 CFR 46.404
Target:   Future IEEE biomedical submissions (EMBC / JBHI / JTEHM /
          TBME / Sensors)

KEY DESIGN ELEMENTS WORTH FLAGGING
----------------------------------
* Closed-family study team. Both minor participants are children of
  team members (Theodore = PI's son; Ryan = technical assistant's
  son) and both are intended student co-authors. The packet treats
  this as a serious COI/undue-influence concern and applies symmetric
  mitigations:
    - Independent Assent Administrator (IAA) — an OSU faculty/staff
      person who is NOT a parent, NOT a co-author, and has no
      publication interest. The IAA conducts each minor's assent
      privately. (Doc 8)
    - Participation-authorship separation: withdrawal from data
      collection does not affect family, school, athletic
      opportunities, or scholarly credit. (Doc 1 §10, Doc 6)
    - Two-parent permission sought when feasible (although §46.404
      permits one-parent permission per §46.408(b)).
    - Closed-cohort recruitment, no compensation, no school
      involvement.

* Two activities, two sites:
    Site A: residential tennis court (Ryan, tennis, California)
    Site B: neighborhood fitness center (Theodore, running, Corvallis)
  Site B is treated as a semi-public space; explicit language states
  no data are collected from any third party (staff, members,
  patrons, coaches).

* Personally-owned hardware. No OSU lab facilities, equipment, or
  budget. OSU's role is institutional review and PI oversight only.

* Publication scope. The packet is decoupled from any current
  in-flight engineering write-up (paper_cnib.md). It supports future
  IEEE-targeted manuscripts only. Pre-IRB engineering test data is
  explicitly excluded (Doc 1 §21).

WORKFLOW FOR REVIEW
-------------------
The .md files in this repository are the source of truth. The .docx
files are generated from the .md via pandoc for ease of Word-based
review.

To suggest changes:
    Option 1 (preferred): leave Word comments / track changes in the
    .docx file and return it. The technical assistant will read the
    comments and apply the corresponding edits to the .md.

    Option 2: send a plain-text feedback list (numbered points
    referencing section numbers, e.g., "Doc 1 §10, second paragraph:
    suggest ..."). This is faster to apply.

After updates, the technical assistant regenerates the .docx and
ships v0.5 for the next round.

The final .docx is what gets attached to OSU Cayuse HE.

PRE-SUBMISSION ACTION ITEMS (REQUIRES PI INPUT)
-----------------------------------------------
The following items remain as TBD values and need PI / family input
before Cayuse submission. Full grouped checklist is in Part 4 of
IRB_requirements_v0.5.docx.

Highest-impact items:
    1. Identify the Independent Assent Administrator (OSU
       faculty/staff; not a parent, co-author, or technical
       assistant; no publication interest).
    2. Confirm whether the Corvallis neighborhood fitness center
       requires written facility permission / letter of
       cooperation. If yes, obtain it before Cayuse submission.
    3. Confirm Theodore's exact date of birth (day in September) so
       the adult re-consent timeline language is exact.
    4. Capture both residential addresses (Ryan, CA; Theodore,
       Corvallis OR) for Cayuse or a confidential IRB-only
       site appendix.
    5. Decide concrete data retention period (recommended:
       5 years after publication or study closure).
    6. Decide cloud-licensed vs. encrypted-local storage for the
       Level 2 data security plan.
    7. CITI Group 1 or Group 2 (Human Subjects Protection)
       completion for all listed study personnel including the IAA
       designee. Renewed every 3 years.
    8. File COI disclosure via OSU Beaver Research Hub for the
       familial-participant relationship with Theodore.
    9. Decide IEEE target venue (affects which biomedical-publication
       norms become mandatory).
   10. Obtain ORCID for each author (Dr. Di, Ryan, Theodore).

CAYUSE-FILLED ITEMS (POST-APPROVAL):
   - OSU IRB protocol number
   - Approval date
   - Continuing review due date

REVISION HISTORY
----------------
v0.1   Initial draft (Cover Letter + Doc 1 + Docs 2-8 + Appendices)
v0.2   Audit pass 3 — softened "not a medical device" language;
       OSU-determines expedited category; minor emails removed;
       Cayuse study-team listing; no-coach pressure;
       BLE encryption softer; retention recommendation surfaced
v0.3   Audit pass 4 — Theodore activity changed to running at
       Corvallis fitness center; site language broadened to
       facility/equipment/treadmill; Theodore 18th-birthday year
       corrected; engineering paper -> research paper /
       future IEEE-targeted manuscript(s)
v0.4   Audit pass 5 — minor consistency polish (athletic-practice
       framing, sports/athletic opportunities, technical-assistant
       scope clarified to California sessions, file renamed)
v0.5   Audit pass 6 — final wording cleanup: §4 reframed to
       "future IEEE-targeted manuscript(s)" and "two distinct
       off-site settings"; §16 broadened to weather/court/facility/
       treadmill/equipment conditions; requirements §7.1 and §7.5
       broadened from tennis-only to athletic-scope language;
       Appx A.5 Xiaodong's sensor-setup-assistance scope tightened
       to California tennis sessions, matching frontmatter and
       Appx A.7. Drafting work complete; only factual TBDs remain.

CONTACT
-------
Technical Assistant:  Xiaodong Wang
Source-of-truth files: in this folder, *.md
Companion repo / tooling questions: contact the technical assistant
