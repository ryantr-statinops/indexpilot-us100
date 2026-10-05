from dataclasses import replace
import os
import subprocess
import sys
import pytest
from final_helpers import source_fixture
from indexpilot_us100.evaluation.final.protocol import prepare_protocol
from indexpilot_us100.evaluation.final.workflow import run_evaluation
from indexpilot_us100.evaluation.chart import load_chart_series


def test_final_chart_reads_saved_matrix(tmp_path):
    data,source,config=source_fixture(tmp_path);root=tmp_path/'final'
    prepare_protocol(data,source,replace(config,seeds=(42,7),costs_bps=(10.,)),root)
    run_evaluation(root)
    assert len(load_chart_series(root))==8
    assert len(load_chart_series(root,risk_lambda=2.,seeds=True))==2
    with pytest.raises(ValueError,match='Cost'): load_chart_series(root,cost_bps=20)


def test_offscreen_png_smoke(tmp_path):
    pytest.importorskip('finplot')
    destination=tmp_path/'chart.png'
    script="""import numpy as np
from pathlib import Path
from PyQt6.QtCore import QTimer
from indexpilot_us100.evaluation.chart import create_chart
series=[dict(name='cash',status='completed',times=np.array([1700000000.,1700086400.]),equity=np.array([100000.,100000.]),drawdown=np.array([0.,0.]))]
fplt,axes=create_chart(series)
def save():
    assert axes[0].vb.win.grab().save(DESTINATION)
    fplt.close()
QTimer.singleShot(200,save)
fplt.show()
"""
    subprocess.run([sys.executable,'-c',script.replace('DESTINATION',repr(str(destination)))],env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},check=True,timeout=30,capture_output=True)
    assert destination.read_bytes().startswith(b'\x89PNG')
