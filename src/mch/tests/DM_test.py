import numpy as np
import pandas as pd
import pytest

from mch.models.differentialMethylationClassifier import DifferentialMethylation


def test_dm_skips_if_single_class(monkeypatch):
    """
    若 y 只有一个类别，DM 应该跳过并把 result 置为空列表，
    transform 直接原样返回 X。
    """
    X = pd.DataFrame(
        np.random.randn(5, 3),
        columns=["p1", "p2", "p3"]
    )
    y = pd.Series(["A"] * 5)

    dm = DifferentialMethylation()

    # 如果 DM 逻辑不小心触发 runDifferentialMethylation，就直接 fail
    monkeypatch.setattr(
        dm,
        "runDifferentialMethylation",
        lambda X, cond: pytest.fail("runDifferentialMethylation should not run for single class")
    )

    dm.fit(X, y)
    assert dm.result == []

    X2 = dm.transform(X)
    pd.testing.assert_frame_equal(X2, X)


def test_dm_transform_selects_probes(monkeypatch):
    """
    mock 掉 runDifferentialMethylation（避免 rpy2/R 依赖），
    检查 transform 是否能正确按 probes 选列。
    """
    X = pd.DataFrame(
        np.random.randn(6, 4),
        columns=["p1", "p2", "p3", "p4"]
    )
    y = pd.Series(["A", "A", "A", "B", "B", "B"])

    dm = DifferentialMethylation()

    # mock DM 的输出 probes
    monkeypatch.setattr(
        dm,
        "runDifferentialMethylation",
        lambda X, cond: ["p2", "p4"]
    )

    dm.fit(X, y)
    assert set(dm.result) == {"p2", "p4"}

    X_sel = dm.transform(X)
    assert list(X_sel.columns) == ["p2", "p4"]
    assert X_sel.shape == (6, 2)
