#!/usr/bin/env python3
# Copyright 2026 Bayanat Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Bayanat Labs pipeline budget estimator (operating manual, manual/budget.py).

Estimates wall-clock hours, GPU-hours, dollar ranges, expected clean hours and human QA hours for a
dataset job from: hours of audio, number of text documents, the stages selected, a hardware profile
and the coefficients, rate and yield you supply.

This file embeds no Bayanat Labs measurement, price, rate or yield. Dollars are computed only from a
rate passed with --rate, and clean hours only from a yield passed with --yield.

Profiles
  laptop-m3pro  An Apple M3 Pro laptop (CPU, plus Metal for the aligner). Its coefficients are loaded
                with --coeffs from a calibration report; none is embedded here. Laptop numbers are not
                GPU numbers.
  gpu-4090      PLACEHOLDER (unmeasured). GPU-hours are seeded from the published Emilia-Pipe run
                (arXiv:2501.15907: 666.94 h of source audio in 240.5 min on 8x RTX 4090, RTF 0.006),
                which is about 48.1 GPU-hours per 1,000 h for Emilia's own stage set (Whisper medium).
                Replace with measured coefficients before quoting.
  gpu-a100      PLACEHOLDER (unmeasured). No published seed: pass --coeffs.

Measured coefficients are loaded from a calibration report (rows with `hardware_profile`, `stage`,
`rtf` or `docs_per_second`) with --coeffs; a GPU calibration run writes the same format, so it turns
a placeholder profile into a measured one. Without --coeffs every stage of the laptop profile is
reported as unmeasured.

Usage
  python budget.py --audio-hours 1000 --stages speech-full --profile gpu-4090 --rate LO-HI
  python budget.py --audio-hours 2 --docs 1000000 --stages vad,asr_primary,alignment,norm,lid,dedup_minhash,pii_regex \
                   --profile laptop-m3pro --cpu-workers 4 --coeffs <calibration report.json>
"""
import argparse
import json
import os
import sys

SPEECH_STAGES = ['vad', 'separation', 'diarisation', 'asr_primary', 'asr_second', 'alignment',
                 'quality_dnsmos', 'quality_squim', 'dialect_id', 'fingerprint']
TEXT_STAGES = ['parse', 'norm', 'lid', 'dedup_minhash', 'pii_regex', 'pii_presidio']
GROUPS = {
    'speech-full': list(SPEECH_STAGES),
    'speech-laptop-measured': ['vad', 'asr_primary', 'alignment', 'quality_dnsmos', 'quality_squim'],
    'text-full': list(TEXT_STAGES),
}
# Stages whose laptop coefficient was measured single-threaded; --cpu-workers divides their wall-clock
# (assumes linear scaling across independent worker processes: an assumption, not a measurement).
SINGLE_THREAD_STAGES = {'vad', 'parse', 'norm', 'lid', 'dedup_minhash', 'pii_regex', 'pii_presidio', 'quality_dnsmos'}

# Map calibration-report stage names to estimator stage keys.
STAGE_MAP = [
    ('speech_vad', 'vad'), ('speech_source_separation', 'separation'), ('speech_diarisation', 'diarisation'),
    ('speech_asr_second', 'asr_second'), ('speech_asr', 'asr_primary'), ('speech_align', 'alignment'),
    ('speech_quality_dnsmos', 'quality_dnsmos'), ('speech_quality_squim', 'quality_squim'),
    ('speech_dialect', 'dialect_id'), ('speech_fingerprint', 'fingerprint'),
    ('text_parse_arwiki_probe', None), ('text_parse', 'parse'), ('text_norm', 'norm'), ('text_lid', 'lid'),
    ('text_dedup', 'dedup_minhash'), ('text_pii_regex', 'pii_regex'), ('text_pii_presidio', 'pii_presidio'),
]

# Published seed: Emilia paper (arXiv:2501.15907), 666.94 h of source audio in 240.5 min on 8x RTX 4090.
EMILIA_GPU_HOURS_PER_AUDIO_HOUR_4090 = round(240.5 / 60 * 8 / 666.94, 4)

PROFILES = {
    'laptop-m3pro': {'kind': 'laptop', 'measured': True, 'gpu_type': None,
                     'note': 'MEASURED on an Apple M3 Pro laptop (coefficients from --coeffs); laptop numbers are not GPU numbers'},
    'gpu-4090': {'kind': 'gpu', 'measured': False, 'gpu_type': 'NVIDIA RTX 4090',
                 'end_to_end_gpu_hours_per_audio_hour': EMILIA_GPU_HOURS_PER_AUDIO_HOUR_4090,
                 'end_to_end_gpu_hours_source': 'Emilia-Pipe (separation, diarisation, VAD, Whisper-medium ASR, DNSMOS) on 8x RTX 4090: 666.94 h in 240.5 min',
                 'note': 'PLACEHOLDER (unmeasured): GPU-hours seeded from the published Emilia-Pipe run, not a Bayanat Labs measurement'},
    'gpu-a100': {'kind': 'gpu', 'measured': False, 'gpu_type': 'NVIDIA A100',
                 'end_to_end_gpu_hours_per_audio_hour': None,
                 'end_to_end_gpu_hours_source': None,
                 'note': 'PLACEHOLDER (unmeasured): no published seed; pass --coeffs'},
}


def parse_range(s):
    """'1-2' -> (1.0, 2.0); '0.5' -> (0.5, 0.5); None -> None."""
    if s is None:
        return None
    if isinstance(s, (tuple, list)):
        return (float(s[0]), float(s[1]))
    s = str(s)
    if '-' in s:
        a, b = s.split('-', 1)
        lo, hi = float(a), float(b)
    else:
        lo = hi = float(s)
    if lo < 0 or hi < lo:
        raise ValueError('bad range: ' + s)
    return (lo, hi)


def expand_stages(spec):
    out = []
    for tok in ([spec] if isinstance(spec, str) else spec):
        for t in str(tok).split(','):
            t = t.strip()
            if not t:
                continue
            if t in GROUPS:
                out.extend(GROUPS[t])
            elif t in SPEECH_STAGES or t in TEXT_STAGES:
                out.append(t)
            else:
                raise ValueError(f'unknown stage {t!r}; known: {SPEECH_STAGES + TEXT_STAGES + list(GROUPS)}')
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            uniq.append(t); seen.add(t)
    return uniq


def _map_stage(name):
    for prefix, key in STAGE_MAP:
        if name.startswith(prefix):
            return key, True
    return None, False


def load_coeffs(path):
    """Read a calibration report and return {profile: {'speech': {stage: rtf}, 'text': {stage: docs/s}}}.
    Where several rows map to one stage (e.g. CPU and Metal), the fastest is kept."""
    rep = json.load(open(path, encoding='utf-8'))
    out = {}
    for r in rep.get('rows', []):
        key, ok = _map_stage(r.get('stage', ''))
        if not ok or key is None:
            continue
        prof = r.get('hardware_profile') or 'laptop-m3pro'
        d = out.setdefault(prof, {'speech': {}, 'text': {}})
        if key in SPEECH_STAGES and r.get('rtf') is not None:
            cur = d['speech'].get(key)
            if cur is None or r['rtf'] < cur['rtf']:
                d['speech'][key] = {'rtf': float(r['rtf']), 'device': r.get('device'), 'gpu_type': r.get('gpu_type'),
                                    'gpu_count': r.get('gpu_count')}
        elif key in TEXT_STAGES and r.get('docs_per_second'):
            cur = d['text'].get(key)
            if cur is None or r['docs_per_second'] > cur['docs_per_second']:
                d['text'][key] = {'docs_per_second': float(r['docs_per_second']), 'device': r.get('device')}
                if r.get('chars_per_second'):
                    d['text'][key]['chars_per_second'] = float(r['chars_per_second'])
    return out


def estimate(audio_hours=0.0, docs=0, stages='speech-full', profile='laptop-m3pro', rate=None, gpus=1,
             cpu_workers=1, yield_range=None, qa_items=0, qa_minutes_per_item=None, coeffs=None, mean_chars_per_doc=None):
    """Return a dict with per-stage rows and totals. `rate` is USD per GPU-hour (or per laptop-hour for the
    laptop profile) as a (low, high) tuple or 'lo-hi' string; without it no dollar figure is computed.
    `yield_range` is the clean share of raw audio hours as a (low, high) tuple or 'lo-hi' string; without
    it no clean-hours figure is computed. `coeffs` is the output of load_coeffs(). `mean_chars_per_doc`
    rescales text stages by characters instead of documents where a chars/s coefficient exists (useful
    when the calibration documents were much shorter or longer than the job's)."""
    if profile in PROFILES:
        P = PROFILES[profile]
    elif profile.startswith('gpu-') and coeffs and profile in coeffs:
        P = {'kind': 'gpu', 'measured': True, 'gpu_type': None, 'end_to_end_gpu_hours_per_audio_hour': None,
             'end_to_end_gpu_hours_source': None, 'note': 'MEASURED on a GPU box (coefficients from --coeffs)'}
    else:
        raise ValueError(f'unknown profile {profile!r}; known: {list(PROFILES)} or a gpu-* profile present in --coeffs')
    if audio_hours < 0 or docs < 0 or gpus < 1 or cpu_workers < 1:
        raise ValueError('audio_hours and docs must be >= 0; gpus and cpu_workers >= 1')
    st = expand_stages(stages)
    rate = parse_range(rate)
    yr = parse_range(yield_range) if yield_range is not None else None
    measured = {'speech': {}, 'text': {}}
    if coeffs and profile in coeffs:
        measured['speech'].update(coeffs[profile]['speech'])
        measured['text'].update(coeffs[profile]['text'])
    # Text stages are CPU-bound everywhere: on GPU profiles fall back to the laptop per-process figures.
    text_src = dict(measured['text'])
    if P['kind'] == 'gpu':
        lap = dict(coeffs['laptop-m3pro']['text']) if coeffs and 'laptop-m3pro' in coeffs else {}
        for k, v in lap.items():
            text_src.setdefault(k, dict(v, borrowed_from='laptop-m3pro'))

    rows = []
    res_warn = []
    audio_s = audio_hours * 3600.0
    wall_h = 0.0
    gpu_h = 0.0
    unmeasured_speech = []
    for s in st:
        if s in SPEECH_STAGES:
            c = measured['speech'].get(s)
            if c is None:
                unmeasured_speech.append(s)
                rows.append({'stage': s, 'kind': 'speech', 'measured': False, 'coefficient': None,
                             'wall_hours': None, 'gpu_hours': None, 'note': 'no measured coefficient for this profile'})
                continue
            h = c['rtf'] * audio_s / 3600.0
            if P['kind'] == 'gpu':
                g = h  # rtf on one GPU = GPU-seconds per audio second
                w = g / gpus
            else:
                g = 0.0
                w = h / (cpu_workers if s in SINGLE_THREAD_STAGES else 1)
            wall_h += w
            gpu_h += g
            rows.append({'stage': s, 'kind': 'speech', 'measured': True, 'coefficient': {'rtf': c['rtf']},
                         'device': c.get('device'), 'wall_hours': w, 'gpu_hours': g})
        else:
            c = text_src.get(s)
            if c is None:
                rows.append({'stage': s, 'kind': 'text', 'measured': False, 'coefficient': None,
                             'wall_hours': None, 'gpu_hours': 0.0, 'note': 'no measured coefficient'})
                continue
            if mean_chars_per_doc and c.get('chars_per_second'):
                w = docs * float(mean_chars_per_doc) / c['chars_per_second'] / 3600.0 / cpu_workers
            else:
                w = docs / c['docs_per_second'] / 3600.0 / cpu_workers
                if mean_chars_per_doc:
                    res_warn.append(f'{s}: no chars/s coefficient, scaled by documents only')
            wall_h += w
            rows.append({'stage': s, 'kind': 'text', 'measured': True, 'coefficient': {'docs_per_second': c['docs_per_second']},
                         'device': c.get('device'), 'borrowed_from': c.get('borrowed_from'), 'wall_hours': w, 'gpu_hours': 0.0,
                         'note': 'CPU stage; linear scaling over cpu_workers assumed'})

    if profile == 'laptop-m3pro' and not (coeffs and profile in coeffs):
        res_warn.append('laptop-m3pro has no embedded coefficients: pass measured ones with --coeffs')
    res = {'profile': profile, 'profile_note': P['note'], 'profile_measured': P['measured'], 'gpu_type': P['gpu_type'],
           'audio_hours': audio_hours, 'docs': docs, 'stages': st, 'gpus': gpus, 'cpu_workers': cpu_workers,
           'rows': rows, 'wall_hours': wall_h, 'gpu_hours': (gpu_h, gpu_h), 'usd': None, 'basis': 'per-stage measured coefficients',
           'unmeasured_stages': [r['stage'] for r in rows if not r['measured']], 'warnings': list(res_warn)}

    if profile == 'laptop-m3pro' and not (coeffs and profile in coeffs):
        res['profile_measured'] = False
    speech_sel = [s for s in st if s in SPEECH_STAGES]
    if coeffs and profile in coeffs and speech_sel and not unmeasured_speech:
        res['profile_measured'] = True
        res['profile_note'] = res['profile_note'].replace('PLACEHOLDER (unmeasured)', 'MEASURED via --coeffs (placeholder seed superseded)')
    if P['kind'] == 'gpu' and speech_sel and unmeasured_speech:
        # Placeholder mode: only a published end-to-end GPU-hour seed is available, if any.
        seed = P.get('end_to_end_gpu_hours_per_audio_hour')
        if seed:
            g = seed * audio_hours
            res['gpu_hours'] = (g, g)
            res['gpu_hours_basis'] = 'PLACEHOLDER: Emilia-Pipe seed (' + P['end_to_end_gpu_hours_source'] + '); not the full Bayanat Labs stack, unmeasured'
            res['basis'] = 'PLACEHOLDER: GPU-hours from the published Emilia-Pipe seed times the given rate'
            if set(speech_sel) != set(SPEECH_STAGES):
                res['warnings'].append('stage subset selected but the placeholder seed covers a whole pipeline: treat it as an upper bound')
            if rate:
                res['usd'] = (g * rate[0], g * rate[1])
            else:
                res['basis'] = 'no --rate given: dollars not computed'
            res['wall_hours'] = wall_h + g / gpus
        else:
            res['gpu_hours'] = None
            res['gpu_hours_basis'] = 'no published GPU-hour seed for this profile; pass --coeffs with measured coefficients'
            res['basis'] = 'no seed and no measured coefficients: dollars not computed'
        res['warnings'].append('UNMEASURED profile: replace with measured coefficients (--coeffs) before quoting')
    else:
        if rate:
            billable = gpu_h if P['kind'] == 'gpu' else wall_h
            res['usd'] = (billable * rate[0], billable * rate[1])
        elif P['kind'] == 'laptop':
            res['usd'] = (0.0, 0.0)
            res['warnings'].append('laptop profile: owned hardware, no rate given, dollars shown as 0')
        if unmeasured_speech:
            res['warnings'].append('speech stages without a coefficient were left out of the totals: ' + ', '.join(unmeasured_speech))

    if audio_hours and yr is not None:
        res['clean_hours_expected'] = (audio_hours * yr[0], audio_hours * yr[1])
        res['yield_basis'] = 'given'
    elif audio_hours:
        res['warnings'].append('no --yield given: expected clean hours not computed')
    if qa_items:
        if qa_minutes_per_item is None:
            res['warnings'].append('qa_items given without qa_minutes_per_item: human QA hours not computed')
        else:
            res['human_qa_hours'] = qa_items * float(qa_minutes_per_item) / 60.0
    return res


def _fmt_range(r, nd=1, prefix=''):
    if r is None:
        return 'n/a'
    if isinstance(r, (int, float)):
        return f'{prefix}{r:,.{nd}f}'
    lo, hi = r
    return f'{prefix}{lo:,.{nd}f}' if abs(hi - lo) < 1e-12 else f'{prefix}{lo:,.{nd}f}-{prefix}{hi:,.{nd}f}'


def render(res):
    L = [f"Profile: {res['profile']} ({res['profile_note']})",
         f"Inputs: {res['audio_hours']:,} h audio, {res['docs']:,} docs, stages {', '.join(res['stages'])}, gpus {res['gpus']}, cpu workers {res['cpu_workers']}",
         '', f"{'stage':<16}{'measured':<10}{'coefficient':<28}{'wall h':>12}{'GPU h':>12}"]
    for r in res['rows']:
        c = r['coefficient']
        cs = '' if c is None else (f"RTF {c['rtf']:.5f}" if 'rtf' in c else f"{c['docs_per_second']:,.1f} docs/s")
        if r.get('borrowed_from'):
            cs += ' (laptop)'
        L.append(f"{r['stage']:<16}{('yes' if r['measured'] else 'NO'):<10}{cs:<28}"
                 f"{('' if r['wall_hours'] is None else format(r['wall_hours'], ',.2f')):>12}"
                 f"{('' if r['gpu_hours'] is None else format(r['gpu_hours'], ',.2f')):>12}")
    L += ['', f"Wall-clock hours: {_fmt_range(res['wall_hours'], 2)}",
          f"GPU-hours: {_fmt_range(res['gpu_hours'], 1)}" + (f"  [{res.get('gpu_hours_basis')}]" if res.get('gpu_hours_basis') else ''),
          f"USD: {_fmt_range(res['usd'], 0, '$')}  [{res['basis']}]"]
    if 'clean_hours_expected' in res:
        L.append(f"Expected clean hours: {_fmt_range(res['clean_hours_expected'], 0)}  [{res['yield_basis']}]")
    if 'human_qa_hours' in res:
        L.append(f"Human QA hours: {res['human_qa_hours']:,.1f}")
    for w in res['warnings']:
        L.append('WARNING: ' + w)
    return '\n'.join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Bayanat Labs pipeline budget estimator')
    ap.add_argument('--audio-hours', type=float, default=0.0)
    ap.add_argument('--docs', type=int, default=0)
    ap.add_argument('--stages', default='speech-full', help='comma list of stages or groups: ' + ', '.join(list(GROUPS) + SPEECH_STAGES + TEXT_STAGES))
    ap.add_argument('--profile', default='laptop-m3pro', help='laptop-m3pro (measured), gpu-4090 or gpu-a100 (placeholders), or any gpu-* profile present in --coeffs')
    ap.add_argument('--rate', default=None, help='USD per GPU-hour (or per laptop-hour) as LO-HI; no dollars without it')
    ap.add_argument('--gpus', type=int, default=1)
    ap.add_argument('--cpu-workers', type=int, default=1)
    ap.add_argument('--yield', dest='yield_range', default=None, help='clean share of raw audio hours as LO-HI; no clean hours without it')
    ap.add_argument('--qa-items', type=int, default=0)
    ap.add_argument('--qa-minutes', type=float, default=None)
    ap.add_argument('--mean-chars', type=float, default=None, help='mean characters per document; rescales text stages by chars/s')
    ap.add_argument('--coeffs', default=None, help='calibration report JSON with measured rows')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    coeffs = load_coeffs(a.coeffs) if a.coeffs else None
    res = estimate(a.audio_hours, a.docs, a.stages, a.profile, a.rate, a.gpus, a.cpu_workers, a.yield_range,
                   a.qa_items, a.qa_minutes, coeffs, a.mean_chars)
    print(json.dumps(res, indent=1) if a.json else render(res))
    return 0


if __name__ == '__main__':
    sys.exit(main())
