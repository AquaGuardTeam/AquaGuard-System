from app.domain.condition_classifier import ConditionClassifier, Condition


def test_normal_condition():
    result = ConditionClassifier().classify([25, 27, 26], [2.0, 2.1, 2.0])
    assert result.condition == Condition.NORMAL


def test_critical_tds_condition():
    result = ConditionClassifier().classify([100, 120, 150], [2.0, 2.1, 2.0])
    assert result.condition == Condition.CRITICAL


def test_critical_turbidity_condition():
    result = ConditionClassifier().classify([100, 102, 103], [3.0, 8.0, 12.0])
    assert result.condition == Condition.CRITICAL


def test_insufficient_data_is_noncritical():
    result = ConditionClassifier().classify([], [])
    assert result.condition == Condition.NORMAL
