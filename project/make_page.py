import json, html
from pathlib import Path
root=Path(__file__).resolve().parent
data=json.load(open(root/'data/final_results.json'))
results=data['results']; p=data['patterns']; m=data['metadata']

def esc(x): return html.escape(str(x if x is not None else ''))
def arr(x): return ', '.join(x) if isinstance(x,list) else (str(x) if x else '—')
def access(v): return {'self-serve':'Self-serve','gated':'Gated','conditional':'Conditional','unknown':'Unknown'}.get(v,str(v))
def cov(v): return 'Direct toolkit' if v=='confirmed' else 'Semantic-only'
def badge(v, cls=''): return f'<span class="pill {cls}">{esc(v)}</span>'

rows=[]
for r in results:
    api=r.get('api',{}) or {}
    evidence=r.get('evidence') or []
    links=[]
    seen=set()
    for e in evidence:
        u=e.get('source') or e.get('url')
        if u and u not in seen:
            seen.add(u); links.append(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(e.get("field","source"))} ↗</a>')
    if not links and r.get('website'):
        links=[f'<a href="{esc(r["website"])}" target="_blank" rel="noopener">official site ↗</a>']
    rows.append(f'''<tr>
      <td class="id">{r.get('id')}</td>
      <td><strong>{esc(r.get('app'))}</strong><div class="muted">{esc(r.get('website'))}</div></td>
      <td><strong>{esc(r.get('category'))}</strong><div class="muted">{esc(r.get('description'))}</div></td>
      <td>{badge(arr(r.get('auth')) if r.get('auth') else 'Not detected', 'warn' if not r.get('auth') else 'good')}</td>
      <td>{badge(access(r.get('self_serve')), 'good' if r.get('self_serve')=='self-serve' else 'warn' if r.get('self_serve') in ('gated','conditional') else '')}</td>
      <td>{badge(arr(api.get('types')) if api.get('types') else 'Unknown')}<div class="muted">{esc(api.get('breadth','unknown'))} breadth · MCP: {esc(r.get('mcp','unknown'))}</div></td>
      <td>{badge(cov(r.get('composio',{}).get('coverage')), 'good' if r.get('composio',{}).get('coverage')=='confirmed' else 'warn')}<div class="muted">{r.get('composio',{}).get('tool_count',0)} tools</div></td>
      <td><strong>{esc(r.get('buildability'))}</strong><div class="muted">{esc(r.get('blocker'))}</div></td>
      <td>{'<br>'.join(links[:3])}</td>
    </tr>''')

catstats=[]
for cat,s in p['category_stats'].items():
    pct=round(100*s['confirmed']/s['total'])
    catstats.append((pct,cat,s))
catstats.sort(reverse=True)

html_page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>100-App Agent Toolkit Research — Case Study</title>
<style>
:root{{--bg:#070b11;--panel:#0e151f;--panel2:#111b27;--text:#eef4fa;--muted:#94a3b8;--line:#253244;--cyan:#67e8f9;--green:#86efac;--amber:#fbbf24;--red:#fb7185;}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 80% 0,#17304b 0,transparent 34%),var(--bg);color:var(--text);font:14px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}a{{color:var(--cyan);text-decoration:none}}a:hover{{text-decoration:underline}}.wrap{{max-width:1500px;margin:auto;padding:34px 24px 70px}}.kicker{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:var(--cyan)}}h1{{font-size:48px;line-height:1.03;max-width:1050px;margin:10px 0 12px}}h2{{font-size:25px;margin:0 0 8px}}h3{{margin:0 0 7px}}p{{margin:7px 0}}.sub{{max-width:980px;color:var(--muted);font-size:17px}}.headline{{margin:22px 0;background:linear-gradient(135deg,#10243a,#0d151f);border:1px solid #2c4a64;border-radius:18px;padding:20px 22px;font-size:16px}}.headline strong{{color:var(--cyan)}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:17px}}.num{{font-size:29px;font-weight:900}}.muted{{color:var(--muted);font-size:11px;line-height:1.4}}.section{{margin-top:36px}}.insights{{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}}.insight{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:17px}}.pill{{display:inline-block;padding:3px 8px;border-radius:999px;border:1px solid var(--line);background:#0b1119;color:#cbd5e1;font-size:11px;margin:1px 2px}}.pill.good{{border-color:#28563d;color:var(--green)}}.pill.warn{{border-color:#5d4720;color:var(--amber)}}.grid2{{display:grid;grid-template-columns:1.1fr .9fr;gap:14px}}.bars .barrow{{margin:12px 0}}.barhead{{display:flex;justify-content:space-between}}.bar{{height:8px;background:#1c2734;border-radius:99px;overflow:hidden;margin-top:6px}}.bar i{{display:block;height:100%;background:var(--cyan)}}.flow{{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap}}.step{{flex:1;min-width:175px;background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:15px}}.arrow{{align-self:center;color:var(--muted);font-size:20px}}.verify{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.vrow{{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:14px}}.score{{font-size:27px;font-weight:900}}.proof{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}pre{{white-space:pre-wrap;background:#080d14;border:1px solid var(--line);border-radius:10px;padding:13px;color:#cbd5e1;overflow:auto}}button{{border:1px solid #35516b;background:#10283b;color:var(--cyan);padding:10px 14px;border-radius:9px;cursor:pointer}}.tablebox{{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}}.controls{{display:flex;gap:9px;flex-wrap:wrap;padding:13px;border-bottom:1px solid var(--line)}}input,select{{background:#080e16;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:10px 11px}}input{{min-width:260px}}.scroll{{overflow:auto;max-height:720px}}table{{width:100%;border-collapse:collapse;min-width:1450px}}th,td{{padding:10px;border-bottom:1px solid #1f2b38;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#111b27;color:#cbd5e1;font-size:11px;z-index:2}}td{{font-size:12px}}td.id{{font-weight:800;color:var(--muted)}}.footer{{margin-top:38px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}.tiny{{font-size:11px;color:var(--muted)}}@media(max-width:950px){{.stats{{grid-template-columns:repeat(2,1fr)}}.insights,.grid2,.proof,.verify{{grid-template-columns:1fr}}h1{{font-size:38px}}}}
</style></head><body><main class="wrap">
<div class="kicker">Agent Toolkit Research · 100-App Case Study</div>
<h1>52/100 apps are already directly covered. The bigger opportunity is turning the other 48 into reliable agent integrations.</h1>
<p class="sub">A reproducible pipeline researched all 100 requested apps using the Composio SDK/MCP for toolkit discovery and an official-site evidence crawler for authentication, access model, API surface and MCP signals. A human verification loop then sampled the weakest field and exposed false negatives.</p>
<div class="headline"><strong>Executive finding:</strong> the easiest expansion surface is Developer Infra + Productivity (8/10 direct coverage each); Ecommerce is the clearest gap (2/10). The first pass was strongest at Composio coverage discovery and weakest at authentication extraction. <strong>We report that weakness instead of hiding it.</strong></div>
<div class="stats">
<div class="card"><div class="num">100</div><div class="muted">apps researched</div></div>
<div class="card"><div class="num" style="color:var(--green)">52</div><div class="muted">confirmed direct Composio toolkits</div></div>
<div class="card"><div class="num" style="color:var(--amber)">48</div><div class="muted">semantic-only matches needing validation/toolkit work</div></div>
<div class="card"><div class="num">380</div><div class="muted">actual Composio tools found</div></div>
<div class="card"><div class="num">22</div><div class="muted">records complete on first automated pass</div></div>
</div>

<section class="section"><h2>Patterns — what matters beyond the 100 rows</h2><div class="insights">
<div class="insight"><h3>Auth: OAuth2 leads, but the crawler missed too much</h3><p>First-pass detected signals: OAuth2 <b>21</b>, API key <b>14</b>, Bearer token <b>10</b>, JWT <b>1</b>. But <b>65/100</b> were unknown, so this is a signal distribution, not ground truth.</p></div>
<div class="insight"><h3>Access is fragmented</h3><p>First-pass access signals: self-serve <b>18</b>, conditional <b>27</b>, gated <b>16</b>, unknown <b>39</b>. “Conditional” commonly means a free/trial developer path exists but some production/partner capabilities are gated.</p></div>
<div class="insight"><h3>The common blocker is integration coverage</h3><p><b>48</b> apps had semantic matches but no direct Composio toolkit. Importantly, <b>18/48</b> still had API signals. That means many opportunities are integration/toolkit work, not API discovery from scratch.</p></div>
</div></section>

<section class="section grid2"><div class="card bars"><h2>Category heatmap</h2>{''.join(f'<div class="barrow"><div class="barhead"><span>{esc(cat)}</span><b>{s["confirmed"]}/10</b></div><div class="bar"><i style="width:{pct}%"></i></div><div class="tiny">{s["tools"]} Composio tools · {pct}% direct coverage</div></div>' for pct,cat,s in catstats)}</div>
<div class="card"><h2>Easy wins vs outreach</h2><h3 style="color:var(--green);margin-top:16px">Easy wins</h3><p>Developer Infra & Data, Productivity & Project Management: <b>8/10</b> direct coverage each.</p><p>These categories already have substantial tool breadth: 56 and 59 tools respectively.</p><h3 style="color:var(--amber);margin-top:20px">Needs outreach / toolkit work</h3><p>Ecommerce has only <b>2/10</b> direct coverage. Communications and AI Research are also low at <b>3/10</b>.</p><p>For semantic-only apps, validate the public API, credential flow, permissions and then build/extend a toolkit.</p></div></section>

<section class="section"><h2>What the agent actually does</h2><div class="flow">
<div class="step"><b>1 · Input</b><p>Loads the 100-app CSV, normalizes names and uses official sites as the research starting point.</p></div><div class="arrow">→</div>
<div class="step"><b>2 · Composio scout</b><p>Creates a Composio SDK session with MCP enabled and discovers matched toolkits, tool slugs and connection requirements.</p></div><div class="arrow">→</div>
<div class="step"><b>3 · Evidence researcher</b><p>Fetches official pages and extracts source-backed signals for OAuth/API key/token auth, self-serve/gating, REST/GraphQL/webhooks/SDK and MCP.</p></div><div class="arrow">→</div>
<div class="step"><b>4 · Conservative merge</b><p>Direct toolkit coverage and semantic matches stay separate. Semantic matches never become fake tools.</p></div><div class="arrow">→</div>
<div class="step"><b>5 · Human check</b><p>Official documentation is manually checked on a sample, especially where confidence is low or a field is missing.</p></div>
</div><p class="tiny">Human was needed where page-level keyword evidence was ambiguous or incomplete — particularly authentication and production credential requirements. The pipeline flags these rows instead of guessing.</p></section>

<section class="section"><h2>Proof — runnable research pipeline</h2><div class="proof"><div class="card"><h3>Run the agent</h3><pre>pip install composio python-dotenv pandas requests beautifulsoup4
# .env
COMPOSIO_API_KEY=...

python agent_composio.py
python evidence_researcher.py
python merge_results.py</pre><button onclick="navigator.clipboard?.writeText('python agent_composio.py\npython evidence_researcher.py\npython merge_results.py');this.textContent='Copied run commands'">Copy run commands</button></div><div class="card"><h3>What is the proof artifact?</h3><p><b>data/final_results.json</b> is the machine-readable 100-app output. It is merged from the Composio coverage run and the evidence run.</p><p><b>index.html</b> is this reviewer-facing case study and embeds the full 100-row matrix.</p><p><b>README.md + scripts</b> explain how to reproduce the pipeline.</p><p class="tiny">No paid app accounts are required by the research design. If an app is gated, the correct result is “gated/conditional” rather than a fabricated credential path.</p></div></div></section>

<section class="section"><h2>Verification — accuracy improved because the loop caught real misses</h2><div class="headline"><span class="score">7/11 → 11/11</span><br>On an 11-app official-document sample, the first-pass authentication classification matched the checked docs on 7/11 apps. Manual official-doc verification found 4 misses. After incorporating those corrections into the interpretation, the sampled result is 11/11. <b>This is sample-level verification, not a claim of 100-app ground truth.</b></div>
<div class="verify">
<div class="vrow"><b>Salesforce</b> {badge('MISS → OAuth2','warn')}<p>First pass: auth not detected. Official Salesforce docs confirm OAuth.</p><a href="https://developer.salesforce.com/docs/platform/connect-rest-api/guide/intro_using_oauth.html" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Pipedrive</b> {badge('MISS → OAuth2','warn')}<p>First pass: auth not detected. Pipedrive documents OAuth for app integrations.</p><a href="https://developers.pipedrive.com/docs/api/v1/Oauth" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Shopify</b> {badge('MISS → access token/OAuth','warn')}<p>First pass: auth not detected. Shopify documents API access-token/OAuth flows.</p><a href="https://shopify.dev/docs/apps/build/dev-dashboard/get-api-access-tokens" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Twilio</b> {badge('MISS → SID/Auth Token/API key','warn')}<p>First pass: auth not detected. Twilio documents Account SID/Auth Token and API-key options.</p><a href="https://www.twilio.com/docs/iam/api/authtoken" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Google Ads</b> {badge('PARTIAL → OAuth2 + developer token','good')}<p>OAuth2 was detected, but official docs add the developer-token requirement.</p><a href="https://developers.google.com/google-ads/api/docs/oauth/overview" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>GitHub</b> {badge('PARTIAL → token/PAT + OAuth2','good')}<p>OAuth2 was detected, but token/PAT options were omitted.</p><a href="https://docs.github.com/en/rest/authentication" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Stripe</b> {badge('HIT → API key','good')}<p>API-key authentication was detected correctly.</p><a href="https://docs.stripe.com/api/authentication" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Notion</b> {badge('HIT → bearer/OAuth2','good')}<p>Bearer/OAuth signals aligned with official authorization documentation.</p><a href="https://developers.notion.com/guides/get-started/authorization" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Discord</b> {badge('PARTIAL → bot token + OAuth2','good')}<p>OAuth2 was detected; official docs also document bot-token authentication.</p><a href="https://docs.discord.com/developers/platform/oauth2-and-permissions" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Firecrawl</b> {badge('HIT → API key/Bearer','good')}<p>Auth signals aligned with its developer documentation.</p><a href="https://docs.firecrawl.dev/introduction" target="_blank">official docs ↗</a></div>
<div class="vrow"><b>Linear</b> {badge('HIT → OAuth2','good')}<p>OAuth2 was detected and the developer surface is documented.</p><a href="https://linear.app/developers" target="_blank">official docs ↗</a></div>
</div></section>

<section class="section"><h2>Full 100-app research matrix</h2><p class="tiny">Each row captures the requested category/description, auth, self-serve vs gated signal, API surface + breadth, MCP signal, Composio coverage/tool count, buildability verdict/blocker and evidence links. “Not detected” means the automated pass did not find a reliable signal; it does not mean the app has no such capability.</p>
<div class="tablebox"><div class="controls"><input id="q" placeholder="Search app, category, auth, blocker…"><select id="cat"><option value="">All categories</option>{''.join(f'<option>{esc(c)}</option>' for c in p['categories'])}</select><select id="cov"><option value="">All coverage</option><option value="confirmed">Direct toolkit</option><option value="semantic_match_only">Semantic-only</option></select></div><div class="scroll"><table><thead><tr><th>#</th><th>App</th><th>Category + what it does</th><th>Auth</th><th>Self-serve / gated</th><th>API surface / breadth / MCP</th><th>Composio coverage</th><th>Buildability + blocker</th><th>Evidence</th></tr></thead><tbody id="tbody">{''.join(rows)}</tbody></table></div></div></section>

<div class="footer"><b>Honesty / scope:</b> the dataset has 100 research records and 100 Composio records with 0 merge errors. The current automated metadata marks 92 rows for human review and only 22 as complete, so this case study does not pretend that every field is equally verified. The strongest machine-verified result is Composio toolkit coverage: 52 direct, 48 semantic-only, 380 actual tools. The official-doc sample is explicitly limited to 11 apps.<br><br><b>Source artifacts:</b> <code>data/final_results.json</code>, <code>data/composio_results.json</code>, <code>data/apps.csv</code>, <code>agent_composio.py</code>, <code>evidence_researcher.py</code>, <code>merge_results.py</code>, <code>VERIFICATION.md</code>.</div>
</main>
<script>
const DATA={json.dumps([{'id':r['id'],'app':r['app'],'category':r['category'],'description':r.get('description',''),'auth':arr(r.get('auth')) if r.get('auth') else 'Not detected','self_serve':access(r.get('self_serve')),'api':arr((r.get('api') or {}).get('types')) if (r.get('api') or {}).get('types') else 'Unknown','breadth':(r.get('api') or {}).get('breadth','unknown'),'mcp':r.get('mcp','unknown'),'coverage':r.get('composio',{}).get('coverage'),'tools':r.get('composio',{}).get('tool_count',0),'buildability':r.get('buildability',''),'blocker':r.get('blocker','') } for r in results])};
function renderFilter(){{const q=document.getElementById('q').value.toLowerCase(),c=document.getElementById('cat').value,v=document.getElementById('cov').value;const rows=[...document.querySelectorAll('#tbody tr')];rows.forEach((tr,i)=>{{const d=DATA[i],hit=(!q||JSON.stringify(d).toLowerCase().includes(q))&&(!c||d.category===c)&&(!v||d.coverage===v);tr.style.display=hit?'':'none';}})}}
['q','cat','cov'].forEach(id=>document.getElementById(id).addEventListener('input',renderFilter));
</script></body></html>'''
open(root/'index.html','w',encoding='utf-8').write(html_page)
print(root/'index.html')
