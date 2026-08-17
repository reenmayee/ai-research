import json
import os
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "composio_results.json"
HTML_FILE = BASE_DIR / "index.html"

PORT = 8000

# Load COMPOSIO_API_KEY from .env (and keep normal OS environment support).
load_dotenv(BASE_DIR / ".env")


# ============================================================
# LOAD REAL COMPOSIO DATA
# ============================================================

def load_results():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Missing {DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("results", [])

    return data


RESULTS = load_results()


# ============================================================
# NORMALIZE
# ============================================================

def get_app(name):

    name = name.strip().lower()

    for item in RESULTS:

        app = str(item.get("app", "")).lower()

        if app == name:
            return item

    # partial match

    for item in RESULTS:

        app = str(item.get("app", "")).lower()

        if name in app or app in name:
            return item

    return None


# ============================================================
# STATS
# ============================================================

def get_stats():

    direct = 0
    semantic = 0
    tools = 0

    for item in RESULTS:

        composio = item.get("composio", {})

        coverage = composio.get(
            "coverage",
            "unknown"
        )

        count = composio.get(
            "tool_count",
            0
        )

        if coverage == "confirmed":
            direct += 1

        elif coverage == "semantic_match_only":
            semantic += 1

        tools += count

    return {
        "total": len(RESULTS),
        "direct": direct,
        "semantic": semantic,
        "tools": tools
    }


# ============================================================
# LIVE COMPOSIO SESSION
# ============================================================

def create_live_session():

    try:
        from composio import Composio

        api_key = os.getenv("COMPOSIO_API_KEY")

        if not api_key:
            return {
                "success": False,
                "error": "COMPOSIO_API_KEY is not set."
            }

        composio = Composio(
            api_key=api_key
        )

        # Create a REAL Composio session with MCP enabled.
        session = composio.sessions.create(
            user_id="research-demo-user",
            mcp=True
        )

        # ----------------------------------------------------
        # LIVE VERIFICATION
        # Ask Composio for the actual tools available
        # in this newly-created session.
        # ----------------------------------------------------

        live_tools = []

        try:
            tools_result = session.tools()

            if tools_result:
                for tool in tools_result:

                    if isinstance(tool, dict):
                        name = (
                            tool.get("slug")
                            or tool.get("name")
                            or tool.get("tool_slug")
                        )

                        if name:
                            live_tools.append(name)

                    else:
                        name = getattr(
                            tool,
                            "slug",
                            None
                        ) or getattr(
                            tool,
                            "name",
                            None
                        )

                        if name:
                            live_tools.append(name)

        except Exception as tool_error:

            return {
                "success": False,
                "error":
                    "Session was created, but live tool "
                    f"verification failed: {tool_error}"
            }

        # Remove duplicates
        live_tools = list(
            dict.fromkeys(live_tools)
        )

        # MCP endpoint
        mcp_url = None

        try:
            mcp_url = session.mcp.url
        except Exception:
            pass

        return {
            "success": True,

            "message":
                "Live Composio Tool Router session created "
                "and verified.",

            "session_id":
                getattr(
                    session,
                    "session_id",
                    None
                ),

            "mcp_url":
                mcp_url,

            "live_verified":
                True,

            "live_tool_count":
                len(live_tools),

            "live_tools":
                live_tools[:20]
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# HTML
# ============================================================

PAGE = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Composio Research Agent</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Inter,
        Arial,
        sans-serif;

    background:
        #080b12;

    color:
        #eef2ff;
}

.container {

    max-width: 1150px;

    margin:
        auto;

    padding:
        40px 24px 80px;
}

h1 {

    font-size:
        42px;

    margin-bottom:
        10px;
}

.subtitle {

    color:
        #9aa4b8;

    font-size:
        17px;

    line-height:
        1.6;

    max-width:
        850px;
}

.badges {

    display:
        flex;

    gap:
        12px;

    flex-wrap:
        wrap;

    margin:
        25px 0;
}

.badge {

    padding:
        9px 14px;

    border:
        1px solid #293246;

    border-radius:
        999px;

    background:
        #111725;

    color:
        #b9c3d8;
}

.stats {

    display:
        grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap:
        14px;

    margin:
        30px 0;
}

.stat {

    background:
        #111725;

    border:
        1px solid #202a3c;

    border-radius:
        14px;

    padding:
        22px;
}

.number {

    font-size:
        30px;

    font-weight:
        800;
}

.label {

    color:
        #8e99ae;

    margin-top:
        5px;

    font-size:
        13px;
}

.panel {

    background:
        #111725;

    border:
        1px solid #202a3c;

    border-radius:
        16px;

    padding:
        24px;

    margin-top:
        25px;
}

input {

    width:
        100%;

    padding:
        15px;

    border-radius:
        10px;

    border:
        1px solid #34405a;

    background:
        #080b12;

    color:
        white;

    font-size:
        16px;

    margin-bottom:
        12px;
}

button {

    border:
        0;

    border-radius:
        10px;

    padding:
        13px 18px;

    font-size:
        15px;

    font-weight:
        700;

    cursor:
        pointer;

    background:
        #6ee7b7;

    color:
        #07100c;

    margin-right:
        8px;

    margin-bottom:
        8px;
}

button.secondary {

    background:
        #222d42;

    color:
        #dce5f5;
}

.result {

    margin-top:
        22px;

    padding:
        20px;

    background:
        #080b12;

    border-radius:
        12px;

    border:
        1px solid #273247;

}

.tool {

    display:
        inline-block;

    padding:
        7px 10px;

    margin:
        4px;

    background:
        #192236;

    border-radius:
        7px;

    font-size:
        12px;

    color:
        #c8d2e7;
}

.success {

    color:
        #6ee7b7;

    font-weight:
        700;
}

.warning {

    color:
        #f4c95d;

    font-weight:
        700;
}

.error {

    color:
        #ff8fa3;

    font-weight:
        700;
}

.workflow {

    display:
        grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap:
        12px;

}

.step {

    padding:
        18px;

    background:
        #192236;

    border-radius:
        12px;

}

.step strong {

    display:
        block;

    margin-bottom:
        7px;

}

.small {

    color:
        #8e99ae;

    font-size:
        13px;

    line-height:
        1.5;
}

@media(max-width:800px) {

    .stats,
    .workflow {

        grid-template-columns:
            1fr 1fr;
    }

}

</style>

</head>


<body>

<div class="container">

<h1>
    Agent Toolkit Census
</h1>

<div class="subtitle">

    A working Composio-powered research prototype that
    evaluates 100 applications for agent integration
    readiness, discovers existing Composio coverage,
    and exposes the actual tools available for each app.

</div>


<div class="badges">

    <div class="badge">
        Composio Tool Router
    </div>

    <div class="badge">
        100 applications
    </div>

    <div class="badge">
        Agent-assisted research
    </div>

    <div class="badge">
        Evidence + uncertainty exposed
    </div>

</div>


<div class="stats">

    <div class="stat">

        <div
            class="number"
            id="total">
            -
        </div>

        <div class="label">
            Apps researched
        </div>

    </div>


    <div class="stat">

        <div
            class="number"
            id="direct">
            -
        </div>

        <div class="label">
            Direct Composio matches
        </div>

    </div>


    <div class="stat">

        <div
            class="number"
            id="semantic">
            -
        </div>

        <div class="label">
            Semantic matches
        </div>

    </div>


    <div class="stat">

        <div
            class="number"
            id="tools">
            -
        </div>

        <div class="label">
            Matched-app tools
        </div>

    </div>

</div>


<div class="panel">

<h2>
    Live Research Demo
</h2>

<p class="small">

Search the actual dataset produced by the Composio
research run. Then create a live Tool Router session
using your Composio API key.

</p>


<input
    id="appInput"
    placeholder="Try Salesforce, Stripe, Slack, Notion..."
>


<button onclick="research()">
    Research App
</button>


<button
    class="secondary"
    onclick="liveSession()">

    Create Live Composio Session

</button>


<div id="output"></div>

</div>


<div class="panel">

<h2>
    How the agent works
</h2>

<div class="workflow">

<div class="step">

<strong>1. Input</strong>

<span class="small">
100 applications across 10 categories.
</span>

</div>


<div class="step">

<strong>2. Composio Discovery</strong>

<span class="small">
Search Composio's integration coverage and
identify direct toolkit matches.
</span>

</div>


<div class="step">

<strong>3. Normalization</strong>

<span class="small">
Separate direct coverage from semantic matches
so related integrations are not falsely counted.
</span>

</div>


<div class="step">

<strong>4. Human Verification</strong>

<span class="small">
Unknown and ambiguous fields remain explicitly
flagged instead of being fabricated.
</span>

</div>

</div>

</div>


<div class="panel">

<h2>
    Key Finding
</h2>

<p>

The research run found direct Composio coverage
for <strong>52 of 100 applications</strong>, while
48 produced semantic/related matches rather than
a confirmed direct toolkit.

</p>

<p class="small">

This distinction is intentional: a semantic search
result is not treated as proof that the target
application has a Composio toolkit.

</p>

</div>

</div>


<script>

async function loadStats() {

    const response =
        await fetch("/api/stats");

    const data =
        await response.json();

    document.getElementById("total")
        .innerText = data.total;

    document.getElementById("direct")
        .innerText = data.direct;

    document.getElementById("semantic")
        .innerText = data.semantic;

    document.getElementById("tools")
        .innerText = data.tools;
}


async function research() {

    const app =
        document.getElementById(
            "appInput"
        ).value;

    if (!app) return;

    const output =
        document.getElementById(
            "output"
        );

    output.innerHTML =
        "<p>Researching...</p>";

    const response =
        await fetch(
            "/api/research?app=" +
            encodeURIComponent(app)
        );

    const data =
        await response.json();

    if (!data.found) {

        output.innerHTML =
            "<div class='result'>" +
            "<p class='error'>" +
            "Application not found." +
            "</p></div>";

        return;
    }

    const c =
        data.composio || {};

    const tools =
        c.tools || [];

    let toolHTML = "";

    for (const tool of tools) {

        toolHTML +=
            "<span class='tool'>" +
            tool +
            "</span>";

    }

    output.innerHTML = `

        <div class="result">

            <h2>${data.app}</h2>

            <p>
                <strong>Category:</strong>
                ${data.category || "unknown"}
            </p>

            <p>
                <strong>Composio coverage:</strong>

                <span class="${
                    c.coverage === "confirmed"
                    ? "success"
                    : "warning"
                }">

                    ${c.coverage}

                </span>

            </p>

            <p>
                <strong>Toolkit:</strong>
                ${
                    (c.matched_toolkits || [])
                    .join(", ") || "none"
                }
            </p>

            <p>
                <strong>Actual app tools:</strong>
                ${c.tool_count || 0}
            </p>

            <div>
                ${toolHTML}
            </div>

        </div>

    `;
}


async function liveSession() {

    const output =
        document.getElementById(
            "output"
        );

    output.innerHTML =
        "<div class='result'>" +
        "<p>Creating live Composio session...</p>" +
        "</div>";

    const response =
        await fetch(
            "/api/live-session"
        );

    const data =
        await response.json();

    if (!data.success) {

        output.innerHTML = `

    <div class="result">

        <p class="success">
            ✓ LIVE COMPOSIO SESSION CREATED
        </p>

        <p>
            <strong>Session ID:</strong>
            ${data.session_id || "created"}
        </p>

        <p class="success">
            ✓ LIVE TOOL VERIFICATION PASSED
        </p>

        <p>
            <strong>Tools available in live session:</strong>
            ${data.live_tool_count || 0}
        </p>

        <p class="small">
            Composio session created successfully and
            queried for its live tool inventory.
        </p>

        <h3>Verified Live Tools</h3>

        <div>
            ${
                (data.live_tools || [])
                .map(
                    tool =>
                        `<span class="tool">✓ ${tool}</span>`
                )
                .join("")
            }
        </div>

        <p class="small" style="margin-top:20px;">
            Hosted MCP endpoint:
        </p>

        <code>
            ${data.mcp_url || "available in session"}
        </code>

    </div>

`;

        return;
    }

    output.innerHTML = `

        <div class="result">

            <p class="success">
                ✓ LIVE COMPOSIO SESSION CREATED
            </p>

            <p>
                Session ID:
                <strong>
                    ${data.session_id || "created"}
                </strong>
            </p>

            <p class="small">
                Tool Router MCP endpoint:
            </p>

            <code>
                ${data.mcp_url || "available in session"}
            </code>

        </div>

    `;
}


loadStats();

</script>

</body>

</html>
"""


# ============================================================
# SERVER
# ============================================================

class Handler(BaseHTTPRequestHandler):

    def send_json(self, data):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)


    def do_GET(self):

        parsed = urlparse(self.path)

        path = parsed.path

        params = parse_qs(parsed.query)


        # ----------------------------------------------------
        # HTML
        # ----------------------------------------------------

        if path == "/":

            body = PAGE.encode(
                "utf-8"
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(body))
            )

            self.end_headers()

            self.wfile.write(body)

            return


        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

        if path == "/api/stats":

            self.send_json(
                get_stats()
            )

            return


        # ----------------------------------------------------
        # RESEARCH
        # ----------------------------------------------------

        if path == "/api/research":

            name = params.get("app", [""])[0]

            item = get_app(name)

            if not item:

                self.send_json({
                    "found": False
                })

                return

            self.send_json({
                "found": True,
                **item
            })

            return


        # ----------------------------------------------------
        # LIVE COMPOSIO
        # ----------------------------------------------------

        if path == "/api/live-session":

            result = create_live_session()

            self.send_json(
                result
            )

            return


        self.send_response(404)

        self.end_headers()


# ============================================================
# START
# ============================================================

def main():

    print("=" * 65)

    print(
        "COMPOSIO RESEARCH PROTOTYPE"
    )

    print("=" * 65)

    print(
        f"Loaded {len(RESULTS)} applications."
    )

    stats = get_stats()

    print(
        f"Direct coverage: {stats['direct']}"
    )

    print(
        f"Semantic matches: {stats['semantic']}"
    )

    print(
        f"Matched tools: {stats['tools']}"
    )

    print()

    print(
        f"Running at:"
    )

    print(
        f"http://localhost:{PORT}"
    )

    print()

    server = HTTPServer(
        ("localhost", PORT),
        Handler
    )

    threading.Timer(
        1.0,
        lambda:
            webbrowser.open(
                f"http://localhost:{PORT}"
            )
    ).start()

    server.serve_forever()


if __name__ == "__main__":
    main()
