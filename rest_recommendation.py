# Real-time decision logic (use proba_knn or proba_lr over time)
threshold_on  = 0.6
threshold_off = 0.4
need_on_consec  = 4   # ~0.8 s if 50% overlap
need_off_consec = 6

fatigued = False
on_count = off_count = 0

recommendations = []
for p in proba_knn:  # iterate in time order
    if not fatigued:
        if p >= threshold_on:
            on_count += 1
            if on_count >= need_on_consec:
                fatigued = True
                on_count = 0
                recommendations.append("REST for 45s")
        else:
            on_count = 0
            recommendations.append("KEEP GOING")
    else:
        if p <= threshold_off:
            off_count += 1
            if off_count >= need_off_consec:
                fatigued = False
                off_count = 0
                recommendations.append("RESUME")
        else:
            off_count = 0
            recommendations.append("CONTINUE REST")