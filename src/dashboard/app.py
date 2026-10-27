"""Static local report renderer; no server, trading, credentials or extra dependencies."""
import argparse
import html
from pathlib import Path

from src.common import read_json


def render(report_path, output):
    report = read_json(report_path)
    rows = ''.join('<tr><td>'+html.escape(name)+f'</td><td>{v["brier"]:.4f}</td><td>{v["log_loss"]:.4f}</td></tr>'
                   for name,v in report['scores_on_common_cohort'].items())
    contrasts = ''.join('<li>'+html.escape(f'{r["question"]}: difference={r["mean_brier_difference"]:.4f}; 95% CI={r["ci95"]}')+'</li>'
                        for r in report['contrasts'])
    text = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>HX2605 research report</title><style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px;background:#f5f7fa;color:#172233}}h1{{font-size:32px}}.status{{padding:16px;background:#ffe7b3;border-radius:8px}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}li{{margin:12px 0}}img{{max-width:100%}}</style>
<h1>HX2605 forecasting experiment</h1><p class="status">{html.escape(report['status'])}</p>
<p>{report['event_groups']} event groups; {report['common_rows']} paired forecast rows; {report['unresolved_rows']} unresolved rows.</p>
<p>Lower Brier score and log loss are better. Synthetic results demonstrate software only.</p>
<table><tr><th>System</th><th>Brier</th><th>Log loss</th></tr>{rows}</table><h2>Paired comparisons</h2><ul>{contrasts}</ul>
<p>Negative score differences favor the first system. Inspect the protocol and coverage before interpreting improvements.</p></html>'''
    Path(output).write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report')
    parser.add_argument('--output', default='artifacts/report.html')
    args = parser.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    render(args.report, args.output)
