from typing import Any


def classify_threat(score: int) -> str:
    if score <= 20:
        return "low"
    if score <= 40:
        return "medium"
    if score <= 60:
        return "high"
    if score <= 80:
        return "critical"
    return "extreme"


def calculate_threat_score(
    reputation_score: int,
    source_count: int,
    has_malware: bool,
    has_cisa_kev: bool,
    historical_score: int = 0,
    asset_criticality: int = 50,
) -> dict[str, Any]:
    """Transparent, explainable threat scoring algorithm.

    Inputs:
        reputation_score: 0-100 raw provider reputation score.
        source_count: number of confirming intelligence sources.
        has_malware: whether the IOC is tied to known malware.
        has_cisa_kev: whether the CVE is in CISA KEV.
        historical_score: 0-100 score based on prior internal sightings.
        asset_criticality: 0-100 criticality of affected assets.

    Output:
        A dictionary containing the final score (0-100), classification,
        contributing factors, and component breakdown.
    """
    components: dict[str, Any] = {}

    # 1. Reputation component (max 35)
    rep_component = min(reputation_score * 0.35, 35)
    components["reputation"] = round(rep_component, 2)

    # 2. Multi-source confirmation (max 20)
    source_component = min(source_count * 6, 20)
    components["source_confirmation"] = source_component

    # 3. Malware presence (max 20)
    malware_component = 20 if has_malware else 0
    components["malware_presence"] = malware_component

    # 4. Exploit/KEV impact (max 15)
    kev_component = 15 if has_cisa_kev else 0
    components["cisa_kev"] = kev_component

    # 5. Historical activity (max 5)
    historical_component = min(historical_score * 0.05, 5)
    components["historical_activity"] = round(historical_component, 2)

    # 6. Asset criticality amplification (max 5)
    criticality_component = min(asset_criticality * 0.05, 5)
    components["asset_criticality"] = round(criticality_component, 2)

    total = sum(components.values())
    score = min(round(total), 100)
    classification = classify_threat(score)

    factors = []
    if reputation_score >= 70:
        factors.append("high reputation score across providers")
    if source_count >= 3:
        factors.append("multiple independent sources confirm the threat")
    if has_malware:
        factors.append("linked to known malware")
    if has_cisa_kev:
        factors.append("listed in CISA Known Exploited Vulnerabilities")
    if historical_score >= 50:
        factors.append("significant historical internal activity")
    if asset_criticality >= 70:
        factors.append("affects high-criticality assets")

    explanation = " ".join(factors) if factors else "No high-severity indicators detected."

    return {
        "score": score,
        "classification": classification,
        "components": components,
        "explanation": explanation,
    }
