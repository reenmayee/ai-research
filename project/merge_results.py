import json
from pathlib import Path
from collections import Counter, defaultdict


# ============================================================
# FILES
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

COMPOSIO_FILE = DATA_DIR / "composio_results.json"
RESEARCH_FILE = DATA_DIR / "research_results.json"
OUTPUT_FILE = DATA_DIR / "final_results.json"


# ============================================================
# HELPERS
# ============================================================

def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support:
    # [...]
    # {"results": [...]}
    if isinstance(data, dict):
        return data.get("results", [])

    return data


def normalize_name(name):
    if not name:
        return ""

    return (
        str(name)
        .lower()
        .strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )


def safe_list(value):
    return value if isinstance(value, list) else []


def safe_dict(value):
    return value if isinstance(value, dict) else {}


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("BUILDING FINAL DATASET")
print("=" * 70)

research = load_json(RESEARCH_FILE)
composio = load_json(COMPOSIO_FILE)

print(f"Research records:  {len(research)}")
print(f"Composio records:  {len(composio)}")

if len(research) != 100:
    raise ValueError(
        f"Research file should contain 100 apps, found {len(research)}"
    )

if len(composio) != 100:
    raise ValueError(
        f"Composio file should contain 100 apps, found {len(composio)}"
    )


# ============================================================
# INDEX COMPOSIO RESULTS
# ============================================================

composio_by_id = {}
composio_by_name = {}

for item in composio:
    app_id = item.get("id")
    app_name = item.get("app")

    if app_id is not None:
        composio_by_id[app_id] = item

    if app_name:
        composio_by_name[
            normalize_name(app_name)
        ] = item


# ============================================================
# MERGE
# ============================================================

final_results = []
merge_errors = []

for research_item in research:

    app_id = research_item.get("id")
    app_name = research_item.get("app")

    # --------------------------------------------------------
    # Find corresponding Composio record
    # --------------------------------------------------------

    composio_item = None

    if app_id in composio_by_id:
        composio_item = composio_by_id[app_id]

    elif normalize_name(app_name) in composio_by_name:
        composio_item = composio_by_name[
            normalize_name(app_name)
        ]

    # --------------------------------------------------------
    # Start from RESEARCH record.
    #
    # This preserves the actual evidence research:
    # description
    # auth
    # self-serve
    # API
    # MCP
    # evidence
    # confidence
    # etc.
    # --------------------------------------------------------

    merged = dict(research_item)

    # --------------------------------------------------------
    # COMPOSIO DATA
    # --------------------------------------------------------

    if composio_item:

        c = safe_dict(
            composio_item.get("composio", {})
        )

        coverage = c.get(
            "coverage",
            "not_found"
        )

        matched_toolkits = safe_list(
            c.get("matched_toolkits", [])
        )

        related_toolkits = safe_list(
            c.get("related_toolkits", [])
        )

        tools = safe_list(
            c.get("tools", [])
        )

        # Only tools belonging to a confirmed toolkit count.
        # Semantic matches are NOT counted as actual tools.
        if coverage != "confirmed":
            tools = []

        # Deduplicate tool names safely.
        cleaned_tools = []
        seen_tools = set()

        for tool in tools:
            if not isinstance(tool, str):
                continue

            tool = tool.strip()

            if not tool or tool in seen_tools:
                continue

            seen_tools.add(tool)
            cleaned_tools.append(tool)

        merged["composio"] = {
            "coverage": coverage,
            "matched_toolkits": matched_toolkits,
            "related_toolkits": related_toolkits,
            "tools": cleaned_tools,
            "tool_count": len(cleaned_tools),
            "connection_required": bool(
                c.get(
                    "connection_required",
                    False
                )
            ),
        }

    else:

        merge_errors.append({
            "id": app_id,
            "app": app_name,
            "error": "No Composio record found"
        })

        merged["composio"] = {
            "coverage": "not_found",
            "matched_toolkits": [],
            "related_toolkits": [],
            "tools": [],
            "tool_count": 0,
            "connection_required": False
        }

    # --------------------------------------------------------
    # NORMALIZED RESEARCH FIELDS
    # --------------------------------------------------------

    composio_info = merged["composio"]
    coverage = composio_info["coverage"]

    api = safe_dict(
        merged.get("api", {})
    )

    api_available = api.get(
        "available",
        "unknown"
    )

    auth = safe_list(
        merged.get("auth", [])
    )

    self_serve = merged.get(
        "self_serve",
        "unknown"
    )

    mcp = merged.get(
        "mcp",
        "unknown"
    )

    evidence = safe_list(
        merged.get("evidence", [])
    )

    # --------------------------------------------------------
    # BUILDABILITY
    #
    # Conservative interpretation of the assignment:
    # - BUILD_NOW only when API + auth + self-serve are known.
    # - BUILD_WITH_CONSTRAINTS when API/auth are known but access
    #   is conditional or gated.
    # - RESEARCH_REQUIRED when critical fields remain unknown.
    # - Composio coverage is reported separately and never used
    #   as proof that the underlying app is buildable.
    # --------------------------------------------------------

    has_auth = bool(auth)

    if (
        api_available == "yes"
        and has_auth
        and self_serve == "self-serve"
    ):
        buildability = "BUILD_NOW"
        blocker = (
            "No major access blocker detected. "
            "Requires toolkit implementation plus "
            "credential, permissions and action validation."
        )

    elif (
        api_available == "yes"
        and has_auth
        and self_serve in ("conditional", "gated")
    ):
        buildability = "BUILD_WITH_CONSTRAINTS"
        blocker = (
            "API and authentication are documented, but "
            "credential/account access has a constraint."
        )

    elif (
        api_available == "yes"
        and not has_auth
    ):
        buildability = "RESEARCH_REQUIRED"
        blocker = (
            "API was detected, but the authentication method "
            "could not be established confidently."
        )

    elif (
        api_available == "yes"
        and self_serve == "unknown"
    ):
        buildability = "RESEARCH_REQUIRED"
        blocker = (
            "API appears available, but credential/access "
            "requirements could not be established confidently."
        )

    elif api_available == "unknown":
        buildability = "RESEARCH_REQUIRED"
        blocker = (
            "API availability could not be established "
            "confidently from the researched documentation."
        )

    else:
        buildability = "RESEARCH_REQUIRED"
        blocker = (
            "The available research does not establish a clear "
            "public API and credential path."
        )

    merged["buildability"] = buildability

    existing_blocker = merged.get("blocker")
    if (
        not existing_blocker
        or str(existing_blocker).strip().lower()
        in {"unknown", "none", "n/a"}
    ):
        merged["blocker"] = blocker

    # --------------------------------------------------------
    # DATA QUALITY
    #
    # Unknown means insufficient evidence.
    # Not-found is a legitimate MCP/API research result.
    # --------------------------------------------------------

    missing = []

    if not auth:
        missing.append("auth")

    if self_serve in (None, "", "unknown"):
        missing.append("self_serve")

    if api_available in (None, "", "unknown"):
        missing.append("api")

    if mcp in (None, "", "unknown"):
        missing.append("mcp")

    if not evidence:
        missing.append("evidence")

    merged["data_quality"] = {
        "missing_fields": missing,
        "complete": len(missing) == 0,
        "verification_status": (
            "needs_human_review"
            if missing
            else "agent_complete"
        )
    }

    # --------------------------------------------------------
    # HUMAN REVIEW
    # --------------------------------------------------------

    needs_review = bool(
        merged.get(
            "needs_human_review",
            False
        )
    )

    if missing:
        needs_review = True

    if buildability == "RESEARCH_REQUIRED":
        needs_review = True

    # Existing MCP claims are important enough to verify manually.
    if mcp == "existing":
        needs_review = True

    merged["needs_human_review"] = needs_review

    final_results.append(merged)


# ============================================================
# SORT BY ID
# ============================================================

final_results.sort(
    key=lambda x: (
        x.get("id")
        if isinstance(x.get("id"), int)
        else 9999
    )
)


# ============================================================
# PATTERN ANALYSIS
# ============================================================

coverage_counter = Counter()
auth_counter = Counter()
self_serve_counter = Counter()
api_counter = Counter()
mcp_counter = Counter()
buildability_counter = Counter()
category_counter = Counter()

category_stats = defaultdict(
    lambda: {
        "total": 0,
        "confirmed": 0,
        "semantic_only": 0,
        "not_found": 0,
        "tools": 0,
        "api_available": 0,
        "auth_documented": 0,
        "self_serve": 0,
        "gated": 0,
        "mcp_existing": 0,
        "build_now": 0,
        "build_with_constraints": 0,
        "research_required": 0,
        "human_review": 0,
    }
)


for item in final_results:

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    coverage = item["composio"]["coverage"]
    coverage_counter[coverage] += 1

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    category = item.get(
        "category",
        "Unknown"
    )

    category_counter[category] += 1
    category_stats[category]["total"] += 1

    if coverage == "confirmed":
        category_stats[category]["confirmed"] += 1

    elif coverage == "semantic_match_only":
        category_stats[category]["semantic_only"] += 1

    elif coverage == "not_found":
        category_stats[category]["not_found"] += 1

    category_stats[category]["tools"] += (
        item["composio"]["tool_count"]
    )

    # --------------------------------------------------------
    # Auth
    # --------------------------------------------------------

    auth = safe_list(
        item.get("auth", [])
    )

    if not auth:
        auth_counter["unknown"] += 1

    else:
        for method in auth:
            auth_counter[str(method)] += 1

        category_stats[category]["auth_documented"] += 1

    # --------------------------------------------------------
    # Self serve
    # --------------------------------------------------------

    self_serve = item.get(
        "self_serve",
        "unknown"
    )

    self_serve_counter[
        str(self_serve)
    ] += 1

    if self_serve == "self-serve":
        category_stats[category]["self_serve"] += 1

    elif self_serve == "gated":
        category_stats[category]["gated"] += 1

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    api = safe_dict(
        item.get("api", {})
    )

    available = api.get(
        "available",
        "unknown"
    )

    api_counter[
        str(available)
    ] += 1

    if available == "yes":
        category_stats[category]["api_available"] += 1

    # --------------------------------------------------------
    # MCP
    # --------------------------------------------------------

    mcp = item.get(
        "mcp",
        "unknown"
    )

    mcp_counter[
        str(mcp)
    ] += 1

    if mcp == "existing":
        category_stats[category]["mcp_existing"] += 1

    # --------------------------------------------------------
    # Buildability
    # --------------------------------------------------------

    buildability = item.get(
        "buildability",
        "UNCLEAR"
    )

    buildability_counter[
        buildability
    ] += 1

    if buildability == "BUILD_NOW":
        category_stats[category]["build_now"] += 1

    elif buildability == "BUILD_WITH_CONSTRAINTS":
        category_stats[category]["build_with_constraints"] += 1

    elif buildability == "RESEARCH_REQUIRED":
        category_stats[category]["research_required"] += 1

    if item.get("needs_human_review", False):
        category_stats[category]["human_review"] += 1


# ============================================================
# TOOL STATISTICS
# ============================================================

confirmed_apps = [
    x
    for x in final_results
    if x["composio"]["coverage"] == "confirmed"
]

total_tools = sum(
    x["composio"]["tool_count"]
    for x in final_results
)

average_tools = (
    total_tools / len(confirmed_apps)
    if confirmed_apps
    else 0
)


top_apps = sorted(
    final_results,
    key=lambda x: x["composio"]["tool_count"],
    reverse=True
)[:10]


# ============================================================
# QUALITY STATISTICS
# ============================================================

complete_records = sum(
    1
    for x in final_results
    if x["data_quality"]["complete"]
)

human_review_records = sum(
    1
    for x in final_results
    if x.get("needs_human_review", False)
)

verified_records = len(final_results) - human_review_records

critical_fields_complete = sum(
    1
    for x in final_results
    if (
        safe_list(x.get("auth"))
        and safe_dict(x.get("api", {})).get("available")
            not in (None, "", "unknown")
        and x.get("self_serve", "unknown")
            not in (None, "", "unknown")
    )
)


# ============================================================
# OPPORTUNITY / PRIORITIZATION
# ============================================================

def opportunity_score(item):
    """
    Transparent prioritization heuristic.

    Higher score means:
      - public API detected
      - authentication documented
      - self-serve access
      - no confirmed Composio toolkit

    Human-review records receive a penalty.
    This is a prioritization heuristic, not business value.
    """

    score = 0
    reasons = []

    api = safe_dict(item.get("api", {}))
    auth = safe_list(item.get("auth", []))
    self_serve = item.get("self_serve", "unknown")
    coverage = item["composio"]["coverage"]
    buildability = item.get("buildability", "RESEARCH_REQUIRED")
    review = item.get("needs_human_review", False)

    if api.get("available") == "yes":
        score += 3
        reasons.append("public API detected")
    else:
        reasons.append("API not confirmed")

    if auth:
        score += 2
        reasons.append("authentication documented")
    else:
        reasons.append("authentication unknown")

    if self_serve == "self-serve":
        score += 3
        reasons.append("self-serve access")
    elif self_serve == "conditional":
        score += 1
        reasons.append("conditional access")
    elif self_serve == "gated":
        reasons.append("gated access")
    else:
        reasons.append("access unknown")

    if coverage != "confirmed":
        score += 2
        reasons.append("no confirmed Composio toolkit")

    if buildability == "BUILD_NOW":
        score += 1
        reasons.append("build-now classification")

    if review:
        score -= 2
        reasons.append("human verification required")

    score = max(0, min(score, 10))

    return score, reasons


opportunities = []

for item in final_results:

    score, reasons = opportunity_score(item)

    opportunities.append({
        "app": item.get("app"),
        "category": item.get("category"),
        "score": score,
        "reasons": reasons,
        "buildability": item.get(
            "buildability",
            "UNCLEAR"
        ),
        "composio_coverage": item[
            "composio"
        ]["coverage"],
    })


opportunities.sort(
    key=lambda x: x["score"],
    reverse=True
)


# ============================================================
# FINAL OBJECT
# ============================================================

output = {
    "metadata": {

        "total_apps":
            len(final_results),

        "research_records":
            len(research),

        "composio_records":
            len(composio),

        "confirmed_composio":
            coverage_counter["confirmed"],

        "semantic_match_only":
            coverage_counter[
                "semantic_match_only"
            ],

        "not_found":
            coverage_counter[
                "not_found"
            ],

        "total_actual_composio_tools":
            total_tools,

        "average_tools_per_confirmed_app":
            round(
                average_tools,
                2
            ),

        "complete_records":
            complete_records,

        "records_needing_human_review":
            human_review_records,

        "records_without_human_review":
            verified_records,

        "critical_fields_complete":
            critical_fields_complete,

        "critical_fields_complete_percentage":
            round(
                critical_fields_complete / len(final_results) * 100,
                1
            ) if final_results else 0,

        "merge_errors":
            len(merge_errors),

        "methodology": (
            "The 100 supplied URLs are treated as research "
            "starting points. App research and Composio toolkit "
            "coverage are kept as separate dimensions. "
            "Buildability is determined conservatively from API "
            "availability, authentication and access requirements. "
            "Composio coverage is reported separately and is not "
            "treated as proof that the underlying app is buildable."
        ),

        "accuracy_note": (
            "Dataset statistics describe agent research output. "
            "They are not claims of 100-app factual accuracy. "
            "Accuracy should be reported from the separately "
            "human-verified sample."
        ),
    },

    "results":
        final_results,

    "patterns": {

        "coverage":
            dict(coverage_counter),

        "auth":
            dict(auth_counter),

        "self_serve":
            dict(self_serve_counter),

        "api":
            dict(api_counter),

        "mcp":
            dict(mcp_counter),

        "buildability":
            dict(buildability_counter),

        "categories":
            dict(category_counter),

        "category_stats":
            dict(category_stats),

        "top_apps_by_tool_count": [

            {
                "app":
                    x["app"],

                "category":
                    x.get("category"),

                "tool_count":
                    x["composio"]["tool_count"]
            }

            for x in top_apps
        ],

        "top_opportunities":
            opportunities[:15],
    },

    "merge_errors":
        merge_errors
}


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# TERMINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("FINAL DATASET CREATED")
print("=" * 70)

print(
    f"Total apps:                 "
    f"{len(final_results)}"
)

print(
    f"Confirmed Composio:         "
    f"{coverage_counter['confirmed']}"
)

print(
    f"Semantic-only:              "
    f"{coverage_counter['semantic_match_only']}"
)

print(
    f"Not found:                  "
    f"{coverage_counter['not_found']}"
)

print(
    f"Actual Composio tools:      "
    f"{total_tools}"
)

print(
    f"Average tools/confirmed:    "
    f"{average_tools:.2f}"
)

print(
    f"Complete records:           "
    f"{complete_records}/100"
)

print(
    f"Needs human review:         "
    f"{human_review_records}/100"
)

print(
    f"Critical fields complete:   "
    f"{critical_fields_complete}/100"
)

print()
print("Buildability:")

for key, value in buildability_counter.items():
    print(f"  {key}: {value}")

print()
print("Coverage:")

for key, value in coverage_counter.items():
    print(f"  {key}: {value}")

print()
print("Top apps by actual Composio tools:")

for item in top_apps:
    print(
        f"  {item['app']}: "
        f"{item['composio']['tool_count']}"
    )

print()
print("Top toolkit opportunities:")

for item in opportunities[:10]:
    print(
        f"  {item['app']}: "
        f"{item['score']}/10 - "
        f"{', '.join(item['reasons'])}"
    )

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)

print("=" * 70)