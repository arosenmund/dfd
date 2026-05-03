from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


def is_valid_number(value: Any) -> bool:
    try:
        return value is not None and float(value) == float(value)
    except (TypeError, ValueError):
        return False


@dataclass
class Rule:
    field: str
    operator: str
    description: str
    threshold: Optional[float] = None
    value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None or key in {"field", "operator", "description"}}


def infer_rules(real_stats: Dict[str, Dict[str, Any]], fake_stats: Dict[str, Dict[str, Any]]) -> List[Rule]:
    rules: List[Rule] = []
    for field, real_data in real_stats.items():
        if field not in fake_stats:
            continue
        fake_data = fake_stats[field]
        if real_data.get("type") != "numeric" or fake_data.get("type") != "numeric":
            continue

        real_mean = real_data.get("mean")
        fake_mean = fake_data.get("mean")
        if not (is_valid_number(real_mean) and is_valid_number(fake_mean)):
            continue
        midpoint = (float(real_mean) + float(fake_mean)) / 2
        if float(fake_mean) > float(real_mean):
            rules.append(
                Rule(
                    field=field,
                    operator=">=",
                    threshold=midpoint,
                    description=f"{field} is typically higher in fake videos",
                )
            )
        elif float(fake_mean) < float(real_mean):
            rules.append(
                Rule(
                    field=field,
                    operator="<=",
                    threshold=midpoint,
                    description=f"{field} is typically lower in fake videos",
                )
            )

    # Additional categorical heuristics
    fake_rc_mode = fake_stats.get("rc_mode")
    if fake_rc_mode and fake_rc_mode.get("type") == "categorical":
        frequencies = fake_rc_mode.get("frequencies", {})
        if "crf" in frequencies:
            rules.append(
                Rule(
                    field="rc_mode",
                    operator="==",
                    value="crf",
                    description="Fake videos frequently use crf instead of cbr",
                )
            )

    if "ref_frames" in real_stats and "ref_frames" in fake_stats:
        real_mean = real_stats["ref_frames"].get("mean")
        fake_mean = fake_stats["ref_frames"].get("mean")
        if is_valid_number(real_mean) and is_valid_number(fake_mean) and float(fake_mean) > float(real_mean):
            rules.append(
                Rule(
                    field="ref_frames",
                    operator=">=",
                    threshold=(float(real_mean) + float(fake_mean)) / 2,
                    description="Fake videos use more reference frames",
                )
            )

    return rules


def apply_rules(rules: List[Rule], file_metadata: Dict[str, Any]) -> List[str]:
    triggered: List[str] = []
    for rule in rules:
        field = rule.field
        if field not in file_metadata:
            continue
        value = file_metadata[field]
        if value == "missing" or value is None:
            continue

        if rule.operator == ">=" and is_valid_number(value) and rule.threshold is not None:
            if float(value) >= float(rule.threshold):
                triggered.append(
                    f"{field} ({value}) ≥ threshold ({rule.threshold:.2f}) → {rule.description}"
                )
        elif rule.operator == "<=" and is_valid_number(value) and rule.threshold is not None:
            if float(value) <= float(rule.threshold):
                triggered.append(
                    f"{field} ({value}) ≤ threshold ({rule.threshold:.2f}) → {rule.description}"
                )
        elif rule.operator == "==" and rule.value is not None and value == rule.value:
            triggered.append(f"{field} = {value} → {rule.description}")

    return triggered


def evaluate_detection(
    real_stats: Dict[str, Dict[str, Any]],
    fake_stats: Dict[str, Dict[str, Any]],
    file_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    rules = infer_rules(real_stats, fake_stats)
    findings = apply_rules(rules, file_metadata)
    total_rules = len(rules)
    triggered_count = len(findings)
    confidence = (triggered_count / total_rules) * 100 if total_rules > 0 else 0.0
    verdict = "FAKE" if triggered_count > 0 else "REAL"
    return {
        "rules": rules,
        "findings": findings,
        "total_rules": total_rules,
        "triggered_rules": triggered_count,
        "confidence": confidence,
        "verdict": verdict,
    }
