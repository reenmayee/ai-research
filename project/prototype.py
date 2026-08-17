import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT = ROOT / "index.html"
FINAL = DATA_DIR / "final_results.json"
ANALYSIS = DATA_DIR / "analysis_results.json"

# This prototype intentionally keeps the current index.html design and
# replaces its runtime fetch with embedded JSON so GitHub Pages can serve
# one self-contained HTML file.

HTML_TEMPLATE = r"""<!doctype html>

\<html lang="en">\<head>\<meta charset="utf-8">\<meta name="viewport" content="width=device-width,initial-scale=1">

\<title>Composio · AI Product Ops Research\</title>

\<style>

:root{--bg:#07090d;--p:#0d1118;--p2:#111722;--l:#202938;--t:#f5f7fb;--m:#9ca7b7;--a:#7dd3fc;--g:#4ade80;--y:#fbbf24;--r:#fb7185;--v:#a78bfa}\*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% -10%,#172033,transparent 35%),var(--bg);color:var(--t);font:14px/1.5 Inter,system-ui,sans-serif}.wrap{max-width:1450px;margin:auto;padding:0 28px}.hero{padding:70px 0 42px;border-bottom:1px solid var(--l)}.ey{color:var(--a);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}h1{font-size:clamp(38px,6vw,70px);line-height:.98;letter-spacing:-.05em;max-width:1000px;margin:14px 0}h2{font-size:27px;margin:0 0 7px}.lead{color:var(--m);max-width:850px}.section{padding:40px 0;border-bottom:1px solid var(--l)}.grid{display:grid;gap:14px}.kpis{grid-template-columns:repeat(6,1fr)}.cards{grid-template-columns:repeat(3,1fr)}.card{background:linear-gradient(145deg,var(--p),var(--p2));border:1px solid var(--l);border-radius:17px;padding:18px}.num{font-size:30px;font-weight:900}.muted{color:var(--m);font-size:12px}.flow{grid-template-columns:repeat(5,1fr)}.flow b{color:var(--a);font-size:11px}.pill{display:inline-block;padding:4px 7px;border-radius:7px;border:1px solid var(--l);font-size:10px;font-weight:800;white-space:nowrap}.g{color:var(--g)}.y{color:var(--y)}.r{color:var(--r)}.b{color:var(--a)}.v{color:var(--v)}input,select{background:#0a0f16;color:var(--t);border:1px solid var(--l);border-radius:10px;padding:11px;width:100%}.filters{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:10px;margin:18px 0}.table{overflow:auto;border:1px solid var(--l);border-radius:15px}table{border-collapse:collapse;width:100%;min-width:1200px}th,td{padding:11px;border-bottom:1px solid var(--l);text-align:left;vertical-align:top}th{position:sticky;top:0;background:#111722;font-size:10px;text-transform:uppercase;color:#cbd5e1}td{font-size:12px}.app{font-weight:800}.ev a{display:block;max-width:290px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--a)}.score{font-size:27px;font-weight:900;color:var(--a)}.bar{height:6px;background:#161d28;border-radius:9px;margin:8px 0}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--a),var(--v));border-radius:9px}.note{border:1px solid #304057;background:#0b121d;border-radius:15px;padding:16px;color:#cbd5e1}.footer{padding:35px 0 70px;color:#718096;font-size:12px}@media(max-width:1050px){.kpis{grid-template-columns:repeat(3,1fr)}.cards{grid-template-columns:1fr 1fr}.flow{grid-template-columns:1fr 1fr}}@media(max-width:650px){.wrap{padding:0 15px}.kpis,.cards,.flow,.filters{grid-template-columns:1fr}}

\</style>\</head>\<body>\<div class="wrap">

\<header class="hero">\<div class="ey">AI Product Ops Intern · Take-home\</div>\<h1>100-app research for agent buildability — with an agent.\</h1>\<p class="lead">A reproducible pipeline combining Composio coverage with documentation evidence to assess authentication, API surface, access model, MCP and buildability.\</p>\</header>

\<section class="section">\<h2>The headline\</h2>\<p class="lead">The strongest operational insight is not just the toolkit gap. It is knowing where automated research is strong and where human verification is still required.\</p>\<div id="kpis" class="grid kpis">\</div>\</section>

\<section class="section">\<h2>Patterns\</h2>\<div id="patterns" class="grid cards">\</div>\</section>

\<section class="section">\<h2>Agent workflow\</h2>\<div class="grid flow">\<div class="card">\<b>01 · DISCOVER\</b>\<h3>Official docs\</h3>\<p class="muted">Start from the 100-app research set and locate developer documentation.\</p>\</div>\<div class="card">\<b>02 · RESEARCH\</b>\<h3>Evidence\</h3>\<p class="muted">Capture auth, API, access and MCP signals with source URLs.\</p>\</div>\<div class="card">\<b>03 · MERGE\</b>\<h3>Composio + research\</h3>\<p class="muted">Keep toolkit coverage separate from external research.\</p>\</div>\<div class="card">\<b>04 · ANALYZE\</b>\<h3>Prioritize\</h3>\<p class="muted">Classify buildability and rank candidate opportunities.\</p>\</div>\<div class="card">\<b>05 · VERIFY\</b>\<h3>Human review\</h3>\<p class="muted">Flag uncertain critical fields instead of inventing certainty.\</p>\</div>\</div>\</section>

\<section class="section">\<div class="note">\<b>Verification:\</b> automated output is not presented as 100-app factual ground truth. Critical-field gaps and human-review flags remain visible so a reviewer can sample, cross-check official docs and measure accuracy.\</div>\</section>

\<section class="section">\<h2>Toolkit opportunities\</h2>\<p class="lead">Heuristic ranking: API + auth + access + Composio gap, penalized when human review is required.\</p>\<div id="opps" class="grid cards">\</div>\</section>

\<section class="section">\<h2>100-app research matrix\</h2>\<div class="filters">\<input id="q" placeholder="Search app, category, auth, blocker…">\<select id="cat">\<option value="">All categories\</option>\</select>\<select id="build">\<option value="">All buildability\</option>\</select>\<select id="rev">\<option value="">All review status\</option>\<option value="yes">Needs review\</option>\<option value="no">No review\</option>\</select>\</div>\<div class="table">\<table>\<thead>\<tr>\<th>App\</th>\<th>Category\</th>\<th>Auth\</th>\<th>Access\</th>\<th>API\</th>\<th>MCP\</th>\<th>Composio\</th>\<th>Tools\</th>\<th>Buildability\</th>\<th>Confidence\</th>\<th>Review\</th>\<th>Evidence\</th>\</tr>\</thead>\<tbody id="rows">\</tbody>\</table>\</div>\</section>

\<section class="section">\<h2>Verification status\</h2>\<div id="verify" class="grid cards">\</div>\</section>\<div class="footer">Composio AI Product Ops case study · opportunity scores are prioritization heuristics, not objective business-value estimates.\</div>

\</div>\<script>

async function load(){

const r=await fetch('project/data/final_results.json');const a=await fetch('project/data/analysis_results.json');

const fd=await r.json(),A=await a.json();const R=fd.results||fd;window.R=R;window.A=A;render();

}

const $=x=>document.getElementById(x),arr=x=>Array.isArray(x)?x:[],D=x=>x&&typeof x==='object'&&!Array.isArray(x)?x:{};

const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

function pill(x,c){return \`\<span class="pill ${c||''}">${esc(x)}\</span>\`}function access(x){return pill(x||'Unknown',x==='self-serve'?'g':x==='gated'?'r':x==='conditional'?'y':'')}function build(x){return pill(x||'UNKNOWN',x==='BUILD_NOW'?'g':x==='BUILD_WITH_CONSTRAINTS'?'y':x==='RESEARCH_REQUIRED'?'r':x==='Composio-covered'?'b':'')}function api(x){return pill(x==='yes'?'Yes':x==='no'?'No':'Unknown',x==='yes'?'g':x==='no'?'r':'')}function cov(x){return pill(x==='confirmed'?'Confirmed':x==='semantic_match_only'?'Semantic-only':x||'Unknown',x==='confirmed'?'b':x==='semantic_match_only'?'v':'')}function mcp(x){return pill(x==='existing'?'Existing':x==='possible'?'Possible':x==='not_found'?'Not found':'Unknown',x==='existing'?'b':x==='possible'?'y':'')}

function render(){const A=window.A,R=window.R,C=A.composio_coverage||{},AP=A.api||{},B=A.buildability||{},V=A.verification||{},AC=A.access||{};

$('kpis').innerHTML=[[R.length,'Apps researched','10 categories'],[C.confirmed||0,'Confirmed Composio','direct coverage'],[C.semantic_match_only||0,'Semantic-only','candidate gaps'],[AP.availability?.yes||0,'Documented APIs','research output'],[B.verified_build_now_count||0,'Verified build-now','strict subset'],[V.human_review_required||0,'Human review','uncertain records']].map(x=>\`\<div class="card">\<div class="num">${x[0]}\</div>\<div>${x[1]}\</div>\<div class="muted">${x[2]}\</div>\</div>\`).join('');

$('patterns').innerHTML=[['Coverage',\`Direct Composio coverage: ${C.confirmed||0}/100. Semantic-only matches: ${C.semantic_match_only||0}.\`],['Evidence bottleneck',\`API unknown: ${AP.availability?.unknown||0}/100. Access unknown: ${AC.unknown||0}/100.\`],['Buildability',\`Verified BUILD_NOW: ${B.verified_build_now_count||0}; constraints: ${B.build_with_constraints_count||0}; research required: ${B.research_required_count||0}.\`]].map(x=>\`\<div class="card">\<b>${x[0]}\</b>\<p class="muted">${x[1]}\</p>\</div>\`).join('');

const opp=(A.top_opportunities||[]).filter(x=>x.composio_coverage!=='confirmed').slice(0,9);$('opps').innerHTML=opp.map(x=>\`\<div class="card">\<div class="score">${x.score}/10\</div>\<h3>${esc(x.app)}\</h3>\<div class="muted">${esc(x.category||'')} · ${esc(x.buildability||'')}\</div>\<div class="bar">\<i style="width:${Math.min(100,(x.score||0)\*10)}%">\</i>\</div>\<p class="muted">${arr(x.reasons).map(esc).join(' · ')}\</p>\</div>\`).join('');

 [...new Set(R.map(x=>x.category).filter(Boolean))].sort().forEach(x=>$('cat').insertAdjacentHTML('beforeend',\`\<option>${esc(x)}\</option>\`));[...new Set(R.map(x=>x.buildability).filter(Boolean))].sort().forEach(x=>$('build').insertAdjacentHTML('beforeend',\`\<option>${esc(x)}\</option>\`));['q','cat','build','rev'].forEach(x=>$(x).addEventListener('input',rows));rows();

$('verify').innerHTML=[[V.critical_fields_complete||0,\`/100 critical fields complete\`],[V.records_with_evidence||0,\`/100 records with evidence\`],[V.human_review_required||0,\`/100 need human review\`]].map(x=>\`\<div class="card">\<div class="num">${x[0]}\</div>\<div>${x[1]}\</div>\</div>\`).join('');}

function rows(){const q=$('q').value.toLowerCase(),cat=$('cat').value,b=$('build').value,rv=$('rev').value;const out=window.R.filter(r=>{if(q&&!JSON.stringify(r).toLowerCase().includes(q))return false;if(cat&&r.category!==cat)return false;if(b&&r.buildability!==b)return false;if(rv==='yes'&&!r.needs_human_review)return false;if(rv==='no'&&r.needs_human_review)return false;return true});$('rows').innerHTML=out.map(r=>{const a=D(r.api),c=D(r.composio),ev=arr(r.evidence).map(e=>typeof e==='string'?e:(e.source||e.url)).filter(Boolean).slice(0,4);return \`\<tr>\<td>\<div class="app">${esc(r.app)}\</div>\<div class="muted">${esc(r.description||'')}\</div>\</td>\<td>${esc(r.category||'')}\</td>\<td>${esc(arr(r.auth).join(', ')||'Unknown')}\</td>\<td>${access(r.self_serve)}\</td>\<td>${api(a.available)}\<div class="muted">${esc(arr(a.types).join(', '))}\</div>\</td>\<td>${mcp(r.mcp)}\</td>\<td>${cov(c.coverage)}\</td>\<td>${c.tool_count??0}\</td>\<td>${build(r.buildability)}\</td>\<td>${esc(r.research_confidence??r.confidence??'—')}\</td>\<td>${r.needs_human_review?pill('Review','y'):pill('OK','g')}\</td>\<td class="ev">${ev.length?ev.map(u=>\`\<a target="_blank" rel="noopener" href="${esc(u)}">${esc(u)}\</a>\`).join(''):'\<span class="muted">No URL\</span>'}\</td>\</tr>\`}).join('')||'\<tr>\<td colspan="12">No matching apps.\</td>\</tr>'}

load().catch(e=>{$('rows').innerHTML=\`\<tr>\<td colspan="12">Could not load project/data JSON. Run prototype.py to generate a self-contained index.html.\</td>\</tr>\`;console.error(e)});

\</script>\</body>\</html>"""

def main():
    if not FINAL.exists():
        raise FileNotFoundError(f"Missing: {FINAL}")
    if not ANALYSIS.exists():
        raise FileNotFoundError(f"Missing: {ANALYSIS}")

    final_data = json.loads(FINAL.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))

    records = (
        final_data.get("results", final_data)
        if isinstance(final_data, dict)
        else final_data
    )

    if not isinstance(records, list):
        raise ValueError("final_results.json must contain a results list")
    if len(records) != 100:
        raise ValueError(f"Expected 100 apps, found {len(records)}")

    payload = json.dumps(
        {"records": records, "analysis": analysis},
        ensure_ascii=False,
        separators=(",", ":")
    ).replace("</script>", "<\\/script>")

    loader = """async function load(){
 const DATA=__DATA__;
 window.R=DATA.records;
 window.A=DATA.analysis;
 render();
}""".replace("__DATA__", payload)

    # Replace the original fetch loader if present.
    marker_start = "async function load(){"
    marker_end = "}\n"
    pos = HTML_TEMPLATE.find(marker_start)

    if pos == -1:
        raise ValueError("Could not find load() function in index template")

    end = HTML_TEMPLATE.find(marker_end, pos)
    if end == -1:
        raise ValueError("Could not find end of load() function")

    html = HTML_TEMPLATE[:pos] + loader + HTML_TEMPLATE[end + len(marker_end):]

    OUT.write_text(html, encoding="utf-8")

    print(f"Generated: {OUT}")
    print(f"Apps embedded: {len(records)}")
    print("Mode: self-contained GitHub Pages HTML")

if __name__ == "__main__":
    main()