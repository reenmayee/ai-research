import json
from pathlib import Path
from collections import Counter, defaultdict


# ============================================================
# FILES
# ============================================================

RESEARCH_FILE = Path("data/research_results.json")
COMPOSIO_FILE = Path("data/composio_results.json")
OUTPUT_FILE = Path("data/final_results.json")


# ============================================================
# HELPERS
# ============================================================

def load_json(path):
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
    # Start from RESEARCH record
    #
    # This preserves:
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

        c = composio_item.get("composio", {})

        if not isinstance(c, dict):
            c = {}

        coverage = c.get(
            "coverage",
            "not_found"
        )

        matched_toolkits = c.get(
            "matched_toolkits",
            []
        )

        related_toolkits = c.get(
            "related_toolkits",
            []
        )

        tools = c.get(
            "tools",
            []
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Only tools from matched toolkit count.
        #
        # If coverage is semantic-only, tools MUST be zero.
        # ----------------------------------------------------

        if coverage != "confirmed":
            tools = []

        # Deduplicate
        tools = list(
            dict.fromkeys(tools)
        )

        merged["composio"] = {

            "coverage": coverage,

            "matched_toolkits":
                matched_toolkits,

            "related_toolkits":
                related_toolkits,

            "tools":
                tools,

            "tool_count":
                len(tools),

            "connection_required":
                bool(
                    c.get(
                        "connection_required",
                        False
                    )
                )
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
    # NORMALIZED BUILDABILITY
    # --------------------------------------------------------

    composio_info = merged["composio"]

    coverage = composio_info["coverage"]

    api = merged.get("api", {})
    api_available = (
        api.get("available")
        if isinstance(api, dict)
        else "unknown"
    )

    auth = merged.get("auth", [])

    self_serve = merged.get(
        "self_serve",
        "unknown"
    )

    mcp = merged.get(
        "mcp",
        "unknown"
    )

    # --------------------------------------------------------
    # Buildability
    #
    # Conservative:
    # do NOT claim READY merely because Composio has coverage.
    # --------------------------------------------------------

    if (
        coverage == "confirmed"
        and
        composio_info["tool_count"] > 0
    ):

        buildability = "Composio-covered"

        blocker = (
            "No direct Composio coverage blocker; "
            "credential connection, permissions and "
            "production validation remain."
        )

    elif coverage == "semantic_match_only":

        buildability = "Needs toolkit work"

        blocker = (
            "No direct Composio toolkit confirmed; "
            "requires integration/API/MCP validation "
            "or new toolkit work."
        )

    else:

        buildability = "Needs investigation"

        blocker = (
            "No confirmed Composio toolkit coverage."
        )

    merged["buildability"] = buildability

    # Only replace blocker if the research didn't already
    # provide a stronger blocker.
    if not merged.get("blocker"):
        merged["blocker"] = blocker

    # --------------------------------------------------------
    # DATA QUALITY FLAG
    # --------------------------------------------------------

    missing = []

    if not auth:
        missing.append("auth")

    if self_serve == "unknown":
        missing.append("self_serve")

    if api_available in (None, "", "unknown"):
        missing.append("api")

    if mcp in (None, "", "unknown"):
        missing.append("mcp")

    if not merged.get("evidence"):
        missing.append("evidence")

    merged["data_quality"] = {

        "missing_fields":
            missing,

        "complete":
            len(missing) == 0
    }

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
category_counter = Counter()

category_stats = defaultdict(
    lambda: {
        "total": 0,
        "confirmed": 0,
        "semantic_only": 0,
        "tools": 0
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

        category_stats[category][
            "confirmed"
        ] += 1

    elif coverage == "semantic_match_only":

        category_stats[category][
            "semantic_only"
        ] += 1

    category_stats[category][
        "tools"
    ] += item["composio"]["tool_count"]

    # --------------------------------------------------------
    # Auth
    # --------------------------------------------------------

    auth = item.get("auth", [])

    if not auth:
        auth_counter["unknown"] += 1

    else:

        for method in auth:

            auth_counter[
                str(method)
            ] += 1

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

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    api = item.get(
        "api",
        {}
    )

    if not isinstance(api, dict):
        api = {}

    available = api.get(
        "available",
        "unknown"
    )

    api_counter[
        str(available)
    ] += 1

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


# ============================================================
# TOOL STATISTICS
# ============================================================

confirmed_apps = [
    x for x in final_results
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
    key=lambda x:
        x["composio"]["tool_count"],
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

        "merge_errors":
            len(merge_errors)
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
        ]
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
    f"Merge errors:               "
    f"{len(merge_errors)}"
)

print()
print("Coverage:")

for key, value in coverage_counter.items():

    print(
        f"  {key}: {value}"
    )

print()
print("Top apps by actual Composio tools:")

for item in top_apps:

    print(
        f"  {item['app']}: "
        f"{item['composio']['tool_count']}"
    )

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)

print("=" * 70)