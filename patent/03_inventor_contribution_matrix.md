# Inventor / Contributor Matrix
## Patent: Reliability-Gated Wearable EMG Monitoring Using RAW/ENV/IMU Consistency

> **Legal note:** Inventorship is a legal determination made by a registered patent attorney, not by this document. This matrix records who did what for counsel's review. Incorrect inventorship can invalidate a US patent. Review with counsel before filing.

> **Minor participant:** Ryan Wang is a high school student and may be a minor at filing time. A parent or guardian must sign the USPTO oath/declaration on his behalf.

---

## 1. Sole Inventor

**Ryan Wang** — Westview High School, San Diego, CA

Ryan conceived all of the claimed inventive ideas: the RAW/ENV/IMU signal-quality validity-gating framework, the trustworthiness classification and downstream action logic, the contact-quality metric, the settling-aware baseline gating, the session-gap continuity audit, and the ghost-channel diagnostic.

---

## 2. Other Contributors (Not Inventors)

| Contributor | Affiliation | Role | Why Not an Inventor |
|-------------|-------------|------|---------------------|
| Larry Wang | — | Hardware assembly, git setup, firmware implementation support | Implementation / support role; did not conceive the claimed inventive ideas |
| Theodore (Teddy) Di | Crescent Valley High School | Co-author (CNIB paper) | Did not contribute to conception of the inventive concepts |
| Dr. YanMing Di | Dept. of Statistics, Oregon State University | Faculty advisor; statistical review; co-author (ICPICS, CNIB) | Advisory and statistical guidance only; did not conceive the claimed inventive ideas |

---

## 3. Conception Evidence by Claim Family

| Family | Core Inventive Concept | Inventor |
|--------|------------------------|----------|
| A — RAW/ENV/IMU validity gate | Use hardware ENV as quality channel; RAW/ENV consistency check; IMU as independent validity context; trustworthiness classification gating downstream fatigue metrics | Ryan Wang |
| B — Quality-gated baseline selection | Reject settling-contaminated baseline windows; multi-condition quality gate; warmup-skip sensitivity as required robustness audit | Ryan Wang |
| C — Session continuity / BLE gap audit | Detect BLE reconnect gap as fatigue-analysis confound; segment-aware analysis; hybrid abs_us timeline | Ryan Wang |
| D — Pogo-pin / ghost-channel diagnostic | Identify ghost-channel signature (r≈1, variance≈0, post-filter flatline); three-condition detection gate | Ryan Wang |

---

## 4. Ownership

| Question | Status |
|----------|--------|
| School IP policy (Westview High School) | Confirm — student personal research projects are typically not claimed by high schools, but verify |
| OSU IP policy (Dr. YanMing Di) | Confirm — advisory-only involvement by a faculty member typically does not trigger OSU ownership, but verify |
| Employer IP policy (Larry Wang) | Confirm — implementation support as a family member, not under employment for this project |
| Joint ownership with any party | None expected given roles above |

---

## 5. Action Items Before Filing

- [ ] Confirm Ryan Wang's age at expected filing date; arrange guardian (Larry Wang) to sign USPTO oath/declaration
- [ ] Confirm Westview High School has no IP claim on student personal research
- [ ] Confirm OSU has no IP claim based on Dr. YanMing Di's advisory role
- [ ] Provide this matrix to counsel for formal inventorship determination

---

*Last updated: 2026-06-01*
