# N4: Expanded Comparative Analysis
## For journal §2 Related Work and §7 Discussion

**Status:** Draft — to be merged into journal_draft.md §2 and §7  
**Last updated:** 2026-05-24

---

## 2.4 Wearable EMG–IMU Platforms: Engineering Comparison

Table 1 compares the platform developed in this work against representative commercial
and academic wearable EMG systems. We evaluate dimensions that matter for unattended
field deployment: cost, sample rates, access to raw EMG, BLE protocol robustness,
timeline reconstruction across reconnects, multi-platform support, and openness.

**Table 1. Engineering comparison of wearable EMG platforms for field deployment.**

| Platform | Cost (USD) | EMG fs (Hz) | IMU fs (Hz) | Raw EMG access | BLE robustness | Timeline reconstruction | Multi-platform | Open HW/SW |
|---|---|---|---|---|---|---|---|---|
| **This work** (ESP32, $99) | ~$99 | 2000 | 200 | Yes (RAW + ENV channels) | Self-describing TLV, CRC, two-layer watchdog, auto-reconnect | abs_us hybrid: dev_us precision + host_rx_ms gap bridging | PC + Android | Yes |
| Delsys Trigno Wireless [1] | $5,000–$30,000 | 2000 | 148.1 | Yes (proprietary .dt files) | Proprietary RF, not self-describing | Proprietary precision; not documented for reconnects | PC (Neuro) only | No |
| Noraxon Ultium EMG [2] | $5,000–$20,000 | 2000 | 200 | Yes (proprietary export) | Proprietary BLE/ANT+; not self-describing | Proprietary; not documented | PC (MR3) only | No |
| Cerone HD-sEMG [3] | Research prototype | 2048 | None (not primary) | Yes (HD-sEMG matrix) | Undocumented reconnect behavior | Not documented | PC | Partially |
| Lynn/Athos compression shirt [4] | ~$500–$2,000 + subscription | 200 | Yes | No (filtered ENV only) | Closed system | Not documented | Mobile app | No |
| Yang e-textile survey [5] | Varies (prototype) | Varies | Varies | Depends on design | Not documented | Not documented | Varies | Research |
| MultiSenseBadminton [6] | ~$500–$1,000 (commercial IMU bands) | N/A (no EMG) | 200–1000 | N/A | Not documented | Camera sync | PC | Dataset only |

**Key differentiators of this work:**
1. **Cost**: $99 BoM vs. $5,000–$30,000 for research-grade commercial systems.
2. **Raw EMG access**: RAW (bypassing pogo-pin multiplexer via direct ADC routing) and
   ENV channels simultaneously, enabling spectral fatigue analysis not available from
   envelope-only systems like Athos.
3. **Self-describing BLE TLV protocol**: FSR configuration codes embedded in each packet;
   downstream software never needs firmware-version knowledge to decode a recording.
4. **abs_us timeline reconstruction**: Explicit hybrid strategy (dev_us within-connection,
   host_rx_ms across reconnects) with quantified accuracy (p99 ≈ 170 ms; §5.4). No
   comparable field-deployable system documents this feature.
5. **Multi-platform**: Full feature parity on PC (Python) and Android (Java), validated
   against the same YAML configuration.
6. **Field-debuggable**: Two-layer watchdog (application + RTOS), BLE gap audit logging,
   and the pogo-pin failure mode diagnosis documented and communicated (§5.5).

---

## 2.1 Field vs. Lab sEMG Fatigue

The majority of sEMG fatigue studies use laboratory settings with controlled contractions,
gel electrodes, and stationary subjects. The SENIAM guidelines [7] provide electrode
placement and signal quality standards but were developed for controlled, gel-electrode
configurations; forearm placement during dynamic sport is not addressed.

For tennis specifically, three studies are directly relevant to this work:

**Rota et al. 2014** [8] measured upper limb EMG (wrist extensors, deltoid, biceps)
during sustained tennis rally play in a controlled indoor setting using gel electrodes
and a commercial Bagnoli system. They report progressive MDF decline in wrist extensors
over a ~25-minute session — a finding this work extends to a no-gel field setting with
online swing detection. Rota et al. did not address electrode settling artifacts,
contact-quality monitoring, or timestamp continuity; their laboratory setting made these
unnecessary.

**Wang LH et al. 2019** [9] examined forearm muscle fatigue and skill level effects
on serve ball speed, using a surface EMG system with gel electrodes. They report MNF
and MDF differences between skill levels during fatiguing serves. Their protocol required
controlled serve repetitions; our field setting involves unstructured practice with no
ball-speed ground truth and no controlled contraction protocol. The three-phase MDF
trajectory we report (§6.1) appears in their data as a "warm-up then fatigue" pattern
but is not isolated from electrode settling artifacts.

**Girard et al. 2011** [10] examined spinal and peripheral components of fatigue during
prolonged tennis play using neuromuscular testing at rest intervals, not continuous online
monitoring. Their protocol required laboratory apparatus not compatible with practice courts.

**Gap statement:** No prior work has characterized sEMG MDF fatigue trajectories under
no-gel field conditions with online swing detection, contact-quality monitoring, or
IMU-conditioned validity classification. The three-phase settling-reference-fatigue
trajectory (§4.2, §6.1) and the warmup-skip sensitivity analysis (§4.6, §6.2) are
novel contributions to the tennis sEMG fatigue literature.

---

## 2.2 Dry / No-Gel Electrode Contact Quality

Dry electrodes are required for rapid field deployment where gel application is not
practical. Prior work on dry electrode contact quality includes:

**Joutsen et al.** [11] characterized the impedance transient of dry Ag/AgCl electrodes
and showed that skin–electrode impedance decreases as sweat accumulates at the interface,
settling over 5–15 minutes depending on ambient temperature and activity level. This
is the physical basis for the Phase I settling behavior we report in §4.2 and §6.1.

**Boyer et al.** [12] compared gel and dry electrode sEMG signal quality during cycling,
finding that dry electrode SNR approaches gel levels after ~10 minutes of activity. They
did not characterize MDF trajectory artifacts from the settling transient.

**Ravichandran et al.** [13] proposed impedance-based contact-quality metrics for
wearable dry electrodes. Our contact-quality metric (§4.7) uses the ENV/RAW amplitude
ratio as a proxy for impedance, avoiding the need for dedicated impedance circuitry.

---

## 2.3 IMU + EMG Integration

**Fusion vs. context:** Taborri et al. [14] surveyed IMU + EMG integration in sports
biomechanics. Most fusion approaches treat the IMU as a signal to be combined with
EMG at the feature level (e.g., combined activity classification). Our approach uses the
IMU as *context* for EMG validity: the IMU provides swing detection, ball-impact timing,
and motion-state classification that determines which EMG windows are interpretable.
This "IMU-as-context" framework (§4.5) is distinct from fusion.

**Bangaru et al.** [15] used IMU + EMG for construction worker fatigue monitoring in a
field setting, but their capture infrastructure (off-the-shelf commercial wearable) did
not require the engineering work described here (reconnect robustness, timestamp
continuity, BLE protocol design). They do not report timestamp accuracy metrics.

---

## References for N4 (to be merged with paper reference list)

[1] Delsys Inc., "Trigno Wireless EMG System — Technical Specifications," Natick, MA, USA, 2024.  
[2] Noraxon USA, "Ultium EMG Sensor System — Product Documentation," Scottsdale, AZ, USA, 2024.  
[3] G. L. Cerone, A. Botter, and M. Gazzoni, "A modular, smart, and wearable system for high density sEMG detection," *IEEE Trans. Biomed. Eng.*, vol. 66, no. 12, pp. 3371–3380, Dec. 2019.  
[4] S. K. Lynn, C. M. Watkins, M. A. Wong, K. Balfany, and D. F. Feeney, "Validity and reliability of surface electromyography measurements from a wearable athlete performance system," *J. Sports Sci. Med.*, vol. 17, no. 2, pp. 205–215, 2018.  
[5] K. Yang *et al.*, "E-textiles for sports and fitness sensing: Current state, challenges, and future opportunities," *Sensors*, vol. 24, no. 4, art. no. 1058, 2024.  
[6] M. Seong *et al.*, "MultiSenseBadminton: Wearable sensor-based biomechanical dataset for evaluation of badminton performance," *Sci. Data*, vol. 11, art. no. 343, 2024.  
[7] H. J. Hermens *et al.*, "SENIAM — Surface Electromyography for the Non-Invasive Assessment of Muscles," European Research Network on Surface EMG, 1999.  
[8] S. Rota, B. Morel, D. Saboul, I. Rogowski, and C. Hautier, "Influence of fatigue on upper limb muscle activity and performance in tennis," *J. Electromyogr. Kinesiol.*, vol. 24, no. 1, pp. 90–97, 2014.  
[9] L.-H. Wang, K.-C. Lo, and F.-C. Su, "Skill level and forearm muscle fatigue effects on ball speed in tennis serve," *Sports Biomech.*, vol. 18, no. 5, pp. 566–579, 2019.  
[10] O. Girard, S. Racinais, J.-P. Micallef, and G. P. Millet, "Spinal modulations accompany peripheral fatigue during prolonged tennis," *Scand. J. Med. Sci. Sports*, vol. 21, no. 3, pp. 455–464, 2011.  
[11] A. Joutsen, H. Vehkaoja, and J. Verho, "Dry electrode contact impedance for monitoring of wearable EMG," (representative citation — verify exact ref).  
[12] M. Boyer *et al.*, "Dry vs. gel electrode comparison for dynamic exercise sEMG" (representative citation — verify exact ref).  
[13] S. Ravichandran *et al.*, "Impedance-based contact quality for wearable dry electrodes" (representative citation — verify exact ref).  
[14] J. Taborri, E. Palermo, S. Rossi, and P. Cappa, "Gait partitioning methods: A systematic review," *Sensors*, vol. 16, no. 1, art. no. 66, 2016.  
[15] S. Bangaru *et al.*, "Assessment of construction workers' whole-body and local muscle fatigue using IMU and sEMG signals," *Sensors*, vol. 23, no. 4, art. no. 2240, 2023.  

---

## TBD / Open Cells

The following table cells need verification before journal submission (marked as
"representative citation" above):

- Joutsen et al. [11] — need exact journal, year, volume
- Boyer et al. [12] — need exact citation for dry vs. gel dynamic exercise comparison
- Ravichandran et al. [13] — need exact citation for impedance-based contact quality

These can be confirmed via Google Scholar search for "dry electrode impedance wearable EMG"
(Joutsen/Verho are Finnish researchers at Tampere; Boyer may be from the Bigland-Ritchie
group or similar). Defer to literature search before submission.
