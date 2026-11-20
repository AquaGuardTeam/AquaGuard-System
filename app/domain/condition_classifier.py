from dataclasses import dataclass
from enum import Enum


class Condition(str, Enum):
    NORMAL = 'Normal'
    WARNING = 'Warning'
    CRITICAL = 'Critical'


@dataclass(frozen=True)
class Classification:
    condition: Condition
    trend_summary: str
    rule_version: str = 'AG-RULE-1.0'


class ConditionClassifier:
    """Rule-based trend classifier for TDS and turbidity; pH is display-only."""

    def __init__(self, tds_warning=50.0, tds_critical=100.0,
                 turbidity_warning=5.0, turbidity_critical=10.0,
                 tds_rate_warning=5.0, turbidity_rate_warning=1.0):
        self.tds_warning = tds_warning
        self.tds_critical = tds_critical
        self.turbidity_warning = turbidity_warning
        self.turbidity_critical = turbidity_critical
        self.tds_rate_warning = tds_rate_warning
        self.turbidity_rate_warning = turbidity_rate_warning

    @staticmethod
    def moving_average(values):
        valid = [value for value in values if value is not None]
        return sum(valid) / len(valid) if valid else None

    def classify(self, tds_values, turbidity_values):
        tds = self.moving_average(tds_values)
        turbidity = self.moving_average(turbidity_values)
        if tds is None or turbidity is None:
            return Classification(Condition.NORMAL, 'Insufficient trend data')

        tds_rate = self._rate_of_change(tds_values)
        turbidity_rate = self._rate_of_change(turbidity_values)

        critical = tds >= self.tds_critical or turbidity >= self.turbidity_critical
        warning = (
            tds >= self.tds_warning or turbidity >= self.turbidity_warning
            or (tds_rate is not None and tds_rate >= self.tds_rate_warning)
            or (turbidity_rate is not None and turbidity_rate >= self.turbidity_rate_warning)
        )

        if critical:
            condition = Condition.CRITICAL
        elif warning:
            condition = Condition.WARNING
        else:
            condition = Condition.NORMAL

        tds_rate_text = f'{tds_rate:.1f}' if tds_rate is not None else 'insufficient data'
        turbidity_rate_text = f'{turbidity_rate:.2f}' if turbidity_rate is not None else 'insufficient data'
        summary = (f'TDS MA {tds:.1f} ppm (rate {tds_rate_text}) | '
                   f'turbidity MA {turbidity:.2f} NTU (rate {turbidity_rate_text})')
        return Classification(condition, summary)

    @staticmethod
    def _rate_of_change(values):
        valid = [value for value in values if value is not None]
        if len(valid) < 2:
            return None
        return valid[-1] - valid[0]
