"""Standalone HTML and SVG rendering from a StrataLens result."""

from __future__ import annotations

import html
import json


def render_html(result: dict[str, object], *, title: str = "StrataLens audit") -> str:
    aggregate = result["aggregate"]
    standardized = result["standardized"]
    classification = result["classification"]
    diagnostics = result["diagnostics"]
    rows = "".join(_stratum_row(item) for item in result["strata"])
    payload = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--ink:#12253f;--muted:#58708c;--paper:#f6f8fb;--card:#fff;--line:#dbe3ec;--navy:#183b66;--blue:#2f78c4;--coral:#ef765f;--mint:#2e9a86}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1120px;margin:auto;padding:40px 24px 64px}} .eyebrow{{color:var(--blue);font-weight:800;letter-spacing:.1em;text-transform:uppercase;font-size:.78rem}}
h1{{font-size:clamp(2.2rem,7vw,4.8rem);line-height:.95;margin:.25rem 0 1rem;letter-spacing:-.05em}} h2{{margin-top:2.2rem}}
.lede{{max-width:760px;color:var(--muted);font-size:1.1rem}} .banner{{margin:28px 0;padding:22px;border-left:6px solid var(--coral);background:#fff1ed;border-radius:12px}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}} .card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 10px 28px rgba(21,52,86,.06)}}
.metric{{font-size:2.15rem;font-weight:850;letter-spacing:-.04em}} .label{{color:var(--muted);font-size:.88rem}} .positive{{color:var(--mint)}} .negative{{color:var(--coral)}}
.track{{height:14px;background:#e8edf3;border-radius:99px;overflow:hidden;margin-top:12px}} .bar{{height:100%;border-radius:99px;background:var(--blue)}}
.table-wrap{{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:16px}} table{{border-collapse:collapse;width:100%;min-width:760px}} th,td{{padding:13px 16px;text-align:right;border-bottom:1px solid var(--line)}} th:first-child,td:first-child{{text-align:left}} th{{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em}} tr:last-child td{{border-bottom:0}}
.note{{color:var(--muted);font-size:.92rem}} code{{background:#edf2f7;padding:.12rem .35rem;border-radius:5px}} footer{{margin-top:38px;color:var(--muted);border-top:1px solid var(--line);padding-top:20px}}
@media(max-width:720px){{main{{padding:28px 16px 48px}}.grid{{grid-template-columns:1fr}}.metric{{font-size:1.9rem}}}}
</style>
</head>
<body><main>
<div class="eyebrow">Composition-aware comparison</div><h1>{html.escape(title)}</h1>
<p class="lede">The same binary comparison, viewed once as a raw aggregate and once after standardizing both groups to the pooled distribution of comparable strata.</p>
<section class="banner"><strong>{html.escape(_label(str(classification['label'])))}</strong><br>{html.escape(str(classification['message']))}</section>
<section class="grid" aria-label="headline metrics">
{_metric_card('Aggregate effect', float(aggregate['effect']))}
{_metric_card('Standardized effect', float(standardized['effect']))}
{_metric_card('Composition gap', float(result['composition_gap']))}
</section>
<h2>Why the aggregate can move</h2>
<div class="grid">
<article class="card"><div class="label">Comparable strata</div><div class="metric">{diagnostics['strata_comparable']} / {diagnostics['strata_total']}</div><div class="track"><div class="bar" style="width:{100*float(diagnostics['comparable_weight_share']):.2f}%"></div></div><p class="note">{_pct(float(diagnostics['comparable_weight_share']))} of pooled weight is represented in the standardized comparison.</p></article>
<article class="card"><div class="label">Largest group-share gap</div><div class="metric">{_pct(float(diagnostics['maximum_group_share_gap']))}</div><p class="note">The largest absolute difference between treated and control composition shares across comparable strata.</p></article>
<article class="card"><div class="label">Bootstrap replicates</div><div class="metric">{result['bootstrap']['valid']}</div><p class="note">Seed <code>{result['seed']}</code>; {result['bootstrap']['skipped']} replicates skipped because a valid overlap comparison could not be formed.</p></article>
</div>
<h2>Stratum evidence</h2><div class="table-wrap"><table><thead><tr><th>Stratum</th><th>Control rate</th><th>Treated rate</th><th>Difference</th><th>Control share</th><th>Treated share</th><th>Target share</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Target shares use the pooled weight distribution over strata containing both groups. Group shares describe the composition within each treatment group.</p>
<h2>Interpretation boundary</h2><article class="card"><p>{html.escape(str(result['interpretation']['statement']))}</p><p class="note">Binary treatment and outcome only. The row bootstrap treats rows as sampling units. Supplied weights are analysis weights, not an inferred survey design.</p></article>
<footer>Generated by StrataLens schema {result['schema_version']} from {result['row_count']} rows.</footer>
<script type="application/json" id="stratalens-data">{payload}</script>
</main></body></html>"""


def render_svg(result: dict[str, object], *, title: str = "A reversal hidden by composition") -> str:
    aggregate = float(result["aggregate"]["effect"])
    standardized = float(result["standardized"]["effect"])
    gap = float(result["composition_gap"])
    max_abs = max(abs(aggregate), abs(standardized), 0.01)
    center = 600
    scale = 430 / max_abs
    def endpoint(value: float) -> float:
        return center + value * scale
    a_end, s_end = endpoint(aggregate), endpoint(standardized)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)}</title><desc id="desc">Aggregate effect {_pct(aggregate)} and pooled-stratum standardized effect {_pct(standardized)} point in opposite directions.</desc>
<rect width="1200" height="630" rx="32" fill="#f6f8fb"/><text x="72" y="92" fill="#2f78c4" font-family="system-ui,sans-serif" font-size="22" font-weight="700" letter-spacing="2">STRATALENS AUDIT</text>
<text x="72" y="160" fill="#12253f" font-family="system-ui,sans-serif" font-size="48" font-weight="800">{html.escape(title)}</text>
<text x="72" y="210" fill="#58708c" font-family="system-ui,sans-serif" font-size="24">The raw aggregate and the composition-standardized comparison disagree.</text>
<line x1="170" y1="348" x2="1030" y2="348" stroke="#bfcbd8" stroke-width="4"/><line x1="600" y1="315" x2="600" y2="465" stroke="#12253f" stroke-width="3"/>
<text x="600" y="300" fill="#58708c" text-anchor="middle" font-family="system-ui,sans-serif" font-size="18">zero</text>
<line x1="600" y1="370" x2="{a_end:.1f}" y2="370" stroke="#ef765f" stroke-width="28" stroke-linecap="round"/><circle cx="{a_end:.1f}" cy="370" r="15" fill="#ef765f"/>
<text x="72" y="380" fill="#12253f" font-family="system-ui,sans-serif" font-size="22" font-weight="700">Aggregate</text><text x="1060" y="380" fill="#ef765f" font-family="system-ui,sans-serif" font-size="24" font-weight="800">{_pct(aggregate)}</text>
<line x1="600" y1="438" x2="{s_end:.1f}" y2="438" stroke="#2e9a86" stroke-width="28" stroke-linecap="round"/><circle cx="{s_end:.1f}" cy="438" r="15" fill="#2e9a86"/>
<text x="72" y="448" fill="#12253f" font-family="system-ui,sans-serif" font-size="22" font-weight="700">Standardized</text><text x="1060" y="448" fill="#2e9a86" font-family="system-ui,sans-serif" font-size="24" font-weight="800">{_pct(standardized)}</text>
<rect x="72" y="505" width="1056" height="72" rx="16" fill="#ffffff" stroke="#dbe3ec"/><text x="98" y="550" fill="#12253f" font-family="system-ui,sans-serif" font-size="22">Composition gap: <tspan font-weight="800">{_pct(gap)}</tspan> · {result['diagnostics']['strata_comparable']} comparable strata · seed {result['seed']}</text>
</svg>"""


def _metric_card(label: str, value: float) -> str:
    tone = "positive" if value > 0 else "negative" if value < 0 else ""
    return f'<article class="card"><div class="label">{html.escape(label)}</div><div class="metric {tone}">{_pct(value)}</div></article>'


def _stratum_row(item: dict[str, object]) -> str:
    if not item["comparable"]:
        return f'<tr><td>{html.escape(str(item["name"]))}</td><td colspan="6">Not comparable: one group is absent</td></tr>'
    return "<tr>" + "".join(
        [
            f'<td>{html.escape(str(item["name"]))}</td>',
            f'<td>{_pct(float(item["control"]["rate"]))}</td>',
            f'<td>{_pct(float(item["treated"]["rate"]))}</td>',
            f'<td>{_pct(float(item["difference"]))}</td>',
            f'<td>{_pct(float(item["control"]["group_share"]))}</td>',
            f'<td>{_pct(float(item["treated"]["group_share"]))}</td>',
            f'<td>{_pct(float(item["standardization_share"]))}</td>',
        ]
    ) + "</tr>"


def _pct(value: float) -> str:
    return f"{value * 100:+.2f}%" if value else "0.00%"


def _label(value: str) -> str:
    return value.replace("_", " ").title()
