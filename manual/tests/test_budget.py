# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for manual/budget.py. Run: python -m pytest manual/tests -q"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import budget  # noqa: E402


def _report(tmp_path, rows):
    p = tmp_path / 'report.json'
    p.write_text(json.dumps({'rows': rows}))
    return budget.load_coeffs(str(p))


def test_placeholder_gpu_profile_uses_published_seed_and_no_dollars_without_rate():
    r = budget.estimate(audio_hours=1000, stages='speech-full', profile='gpu-4090')
    g = budget.EMILIA_GPU_HOURS_PER_AUDIO_HOUR_4090 * 1000
    assert r['gpu_hours'] == pytest.approx((g, g))
    assert 'PLACEHOLDER' in r['gpu_hours_basis'] and 'Emilia' in r['gpu_hours_basis']
    assert r['usd'] is None
    assert r['profile_measured'] is False
    assert any('UNMEASURED' in w for w in r['warnings'])
    r = budget.estimate(audio_hours=1000, stages='speech-full', profile='gpu-4090', rate='1-2')
    assert r['usd'] == pytest.approx((g, 2 * g))


def test_a100_placeholder_has_no_seed_and_computes_nothing():
    r = budget.estimate(audio_hours=500, stages='speech-full', profile='gpu-a100', rate='1-2')
    assert r['gpu_hours'] is None
    assert r['usd'] is None
    assert any('UNMEASURED' in w for w in r['warnings'])


def test_emilia_seed_reproduces_paper_gpu_hours():
    # Emilia: 666.94 h in 240.5 min on 8x RTX 4090 = 32.07 GPU-hours.
    r = budget.estimate(audio_hours=666.94, stages='speech-full', profile='gpu-4090')
    assert r['gpu_hours'][0] == pytest.approx(240.5 / 60 * 8, rel=1e-3)
    assert budget.EMILIA_GPU_HOURS_PER_AUDIO_HOUR_4090 * 1000 == pytest.approx(48.1, abs=0.05)


def test_subset_on_placeholder_profile_is_flagged_upper_bound():
    r = budget.estimate(audio_hours=1000, stages='asr_primary', profile='gpu-4090')
    assert any('upper bound' in w for w in r['warnings'])


def test_laptop_linear_in_hours_and_workers(tmp_path):
    co = _report(tmp_path, [
        {'stage': 'speech_vad_silero', 'hardware_profile': 'laptop-m3pro', 'rtf': 0.003},
        {'stage': 'speech_asr_whisper_large_v3_cpu_int8', 'hardware_profile': 'laptop-m3pro', 'rtf': 1.0},
    ])
    r = budget.estimate(audio_hours=10, stages='vad,asr_primary', profile='laptop-m3pro', coeffs=co)
    assert r['wall_hours'] == pytest.approx(10 * 1.003)
    assert r['gpu_hours'] == (0.0, 0.0)
    r2 = budget.estimate(audio_hours=10, stages='vad,asr_primary', profile='laptop-m3pro', coeffs=co, cpu_workers=3)
    assert r2['wall_hours'] == pytest.approx(10 * (0.003 / 3 + 1.0))
    r3 = budget.estimate(audio_hours=20, stages='vad,asr_primary', profile='laptop-m3pro', coeffs=co)
    assert r3['wall_hours'] == pytest.approx(2 * r['wall_hours'])


def test_text_stage_hours(tmp_path):
    co = _report(tmp_path, [{'stage': 'text_norm_bayanat_norm_v1_ref', 'hardware_profile': 'laptop-m3pro', 'docs_per_second': 100.0}])
    r = budget.estimate(docs=1_000_000, stages='norm', profile='laptop-m3pro', coeffs=co)
    assert r['wall_hours'] == pytest.approx(1_000_000 / 100 / 3600)
    r = budget.estimate(docs=1_000_000, stages='norm', profile='laptop-m3pro', coeffs=co, cpu_workers=4)
    assert r['wall_hours'] == pytest.approx(1_000_000 / 100 / 3600 / 4)


def test_measured_gpu_profile_replaces_placeholder(tmp_path):
    co = _report(tmp_path, [{'stage': 'speech_asr_whisper_large_v3_cuda_fp16', 'hardware_profile': 'gpu-a100', 'rtf': 0.05,
                             'gpu_type': 'NVIDIA A100', 'gpu_count': 1}])
    r = budget.estimate(audio_hours=1000, stages='asr_primary', profile='gpu-a100', rate='1-2', gpus=2, coeffs=co)
    assert r['gpu_hours'] == pytest.approx((50.0, 50.0))
    assert r['wall_hours'] == pytest.approx(25.0)
    assert r['usd'] == pytest.approx((50.0, 100.0))
    assert r['basis'] == 'per-stage measured coefficients'


def test_load_coeffs_keeps_fastest_and_skips_probe(tmp_path):
    co = _report(tmp_path, [
        {'stage': 'speech_align_wav2vec2_cpu', 'hardware_profile': 'laptop-m3pro', 'rtf': 0.2},
        {'stage': 'speech_align_wav2vec2_mps', 'hardware_profile': 'laptop-m3pro', 'rtf': 0.05},
        {'stage': 'text_parse_arwiki_probe_smallest_part', 'hardware_profile': 'laptop-m3pro', 'docs_per_second': 1.0},
        {'stage': 'text_parse_arwiki', 'hardware_profile': 'laptop-m3pro', 'docs_per_second': 3000.0},
    ])
    assert co['laptop-m3pro']['speech']['alignment']['rtf'] == 0.05
    assert co['laptop-m3pro']['text']['parse']['docs_per_second'] == 3000.0


def test_text_on_gpu_profile_borrows_laptop_cpu_figures(tmp_path):
    co = _report(tmp_path, [{'stage': 'text_lid_fasttext_lid176', 'hardware_profile': 'laptop-m3pro', 'docs_per_second': 1000.0}])
    r = budget.estimate(docs=3_600_000, stages='lid', profile='gpu-4090', coeffs=co)
    assert r['wall_hours'] == pytest.approx(1.0)
    assert r['rows'][0]['borrowed_from'] == 'laptop-m3pro'


def test_yield_and_qa():
    r = budget.estimate(audio_hours=1000, stages='speech-full', profile='gpu-4090', qa_items=1000, qa_minutes_per_item=1.5)
    assert 'clean_hours_expected' not in r
    assert any('--yield' in w for w in r['warnings'])
    assert r['human_qa_hours'] == pytest.approx(25.0)
    r = budget.estimate(audio_hours=100, stages='speech-full', profile='gpu-4090', yield_range='0.5-0.6', qa_items=10)
    assert r['clean_hours_expected'] == pytest.approx((50.0, 60.0))
    assert 'human_qa_hours' not in r


def test_bad_inputs():
    with pytest.raises(ValueError):
        budget.estimate(audio_hours=1, stages='nonsense')
    with pytest.raises(ValueError):
        budget.estimate(audio_hours=1, profile='gpu-h100')
    with pytest.raises(ValueError):
        budget.estimate(audio_hours=-1)
    with pytest.raises(ValueError):
        budget.parse_range('2-1')


def test_cli_runs(capsys):
    assert budget.main(['--audio-hours', '1000', '--stages', 'speech-full', '--profile', 'gpu-4090', '--rate', '1-2']) == 0
    out = capsys.readouterr().out
    assert 'PLACEHOLDER' in out and 'Emilia' in out and 'USD: $' in out


def test_generic_gpu_profile_from_coeffs(tmp_path):
    co = _report(tmp_path, [{'stage': 'speech_asr_whisper_large_v3_cuda_fp16', 'hardware_profile': 'gpu-h100', 'rtf': 0.02}])
    r = budget.estimate(audio_hours=1000, stages='asr_primary', profile='gpu-h100', rate='2-3', coeffs=co)
    assert r['profile_measured'] is True
    assert r['gpu_hours'] == pytest.approx((20.0, 20.0))
    assert r['usd'] == pytest.approx((40.0, 60.0))
    with pytest.raises(ValueError):
        budget.estimate(audio_hours=1, stages='asr_primary', profile='gpu-h100')


def test_text_scaling_by_characters(tmp_path):
    co = _report(tmp_path, [{'stage': 'text_norm_bayanat_norm_v1_ref', 'hardware_profile': 'laptop-m3pro',
                             'docs_per_second': 10000.0, 'chars_per_second': 3_600_000.0}])
    r = budget.estimate(docs=1_000_000, stages='norm', profile='laptop-m3pro', coeffs=co, mean_chars_per_doc=3600)
    assert r['wall_hours'] == pytest.approx(1_000_000 * 3600 / 3_600_000 / 3600)


def test_no_measured_coefficients_embedded_in_public_estimator():
    # Measured laptop figures stay in the calibration report and are loaded with --coeffs: budget.py embeds none.
    assert not hasattr(budget, 'LAPTOP_MEASURED')
    r = budget.estimate(audio_hours=10, docs=1000, stages='vad,norm', profile='laptop-m3pro')
    assert r['unmeasured_stages'] == ['vad', 'norm']
    assert r['profile_measured'] is False
    assert any('--coeffs' in w for w in r['warnings'])


def test_no_dollar_or_yield_defaults_embedded():
    # budget.py carries no price, rate or yield of its own: only the published Emilia-Pipe seed.
    assert not [n for n in dir(budget) if n.isupper() and ('USD' in n or 'YIELD' in n or 'RATE' in n)]
    r = budget.estimate(audio_hours=1000, stages='speech-full', profile='gpu-4090')
    assert r['usd'] is None and 'clean_hours_expected' not in r
