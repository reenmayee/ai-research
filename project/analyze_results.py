import json
from pathlib import Path
from collections import Counter, defaultdict


# ============================================================
# FILES
# ============================================================

COMPOSIO_FILE = Path(
    "data/composio_results.json"
)

OUTPUT_FILE = Path(
    "data/final_results.json"
)


# ============================================================
# LOAD
# ============================================================

with open(
    COMPOSIO_FILE,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)


if isinstance(data, dict):

    records = data.get(
        "results",
        []
    )

else:

    records = data


print("=" * 70)
print("CLEANING COMPOSIO RESULTS")
print("=" * 70)

print(
    f"Records loaded: {len(records)}"
)


# ============================================================
# SAFETY
# ============================================================

if len(records) != 100:

    raise ValueError(
        f"Expected 100 apps, "
        f"found {len(records)}"
    )


# ============================================================
# CLEAN
# ============================================================

cleaned = []


for item in records:

    composio = item.get(
        "composio",
        {}
    )

    if not isinstance(
        composio,
        dict
    ):
        composio = {}

    coverage = composio.get(
        "coverage",
        "not_found"
    )

    matched_toolkits = composio.get(
        "matched_toolkits",
        []
    )

    related_toolkits = composio.get(
        "related_toolkits",
        []
    )

    tools = composio.get(
        "tools",
        []
    )

    # --------------------------------------------------------
    # Deduplicate tools
    # --------------------------------------------------------

    tools = list(
        dict.fromkeys(
            t for t in tools
            if isinstance(t, str)
            and t.strip()
        )
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # If there is no confirmed toolkit, there should be ZERO
    # actual app tools.
    # --------------------------------------------------------

    if coverage != "confirmed":

        tools = []

    # --------------------------------------------------------
    # Buildability
    # --------------------------------------------------------

    if coverage == "confirmed":

        if tools:

            buildability = "READY"

        else:

            buildability = "READY_WITH_REVIEW"

    elif coverage == "semantic_match_only":

        buildability = "OUTREACH_OR_BUILD"

    elif coverage == "not_found":

        buildability = "OUTREACH_OR_BUILD"

    else:

        buildability = "RESEARCH_ERROR"

    # --------------------------------------------------------
    # Blocker
    # --------------------------------------------------------

    if coverage == "confirmed":

        if tools:

            blocker = (
                "Direct Composio toolkit coverage exists. "
                "Credential connection and required API "
                "permissions still need validation."
            )

        else:

            blocker = (
                "Toolkit matched, but no app-specific "
                "tools were confidently identified."
            )

    elif coverage == "semantic_match_only":

        blocker = (
            "Related Composio integrations were found, "
            "but no direct toolkit was confidently matched."
        )

    elif coverage == "not_found":

        blocker = (
            "No Composio toolkit was discovered."
        )

    else:

        blocker = (
            "Composio research returned an error."
        )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if coverage == "confirmed" and tools:

        confidence = 0.90

    elif coverage == "confirmed":

        confidence = 0.70

    elif coverage == "semantic_match_only":

        confidence = 0.45

    elif coverage == "not_found":

        confidence = 0.35

    else:

        confidence = 0.0

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    website = item.get(
        "website",
        ""
    )

    evidence = []

    if website:

        evidence.append({

            "url":
                website,

            "source":
                "provided official website",

            "type":
                "official"
        })

    # --------------------------------------------------------
    # Final record
    # --------------------------------------------------------

    cleaned.append({

        "id":
            item.get("id"),

        "app":
            item.get(
                "app",
                "Unknown"
            ),

        "category":
            item.get(
                "category",
                "Unknown"
            ),

        "website":
            website,

        "description":
            "",

        "auth":
            [],

        "self_serve":
            "unknown",

        "self_serve_signals":
            [],

        "api": {

            "available":
                "unknown",

            "types":
                [],

            "breadth":
                "unknown"
        },

        "mcp":
            "unknown",

        "composio": {

            "coverage":
                coverage,

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
                    composio.get(
                        "connection_required",
                        False
                    )
                )
        },

        "buildability":
            buildability,

        "blocker":
            blocker,

        "evidence":
            evidence,

        "confidence":
            confidence,

        "needs_human_review":
            True
    })


# ============================================================
# SORT
# ============================================================

cleaned.sort(
    key=lambda x: (
        x["id"]
        if isinstance(
            x["id"],
            int
        )
        else 9999
    )
)


# ============================================================
# STATISTICS
# ============================================================

coverage_counts = Counter(
    x["composio"]["coverage"]
    for x in cleaned
)


category_stats = defaultdict(
    lambda: {

        "total": 0,

        "confirmed": 0,

        "semantic_match_only": 0,

        "not_found": 0,

        "errors": 0,

        "actual_tools": 0
    }
)


for record in cleaned:

    category = record["category"]

    stats = category_stats[
        category
    ]

    stats["total"] += 1

    coverage = (
        record["composio"]["coverage"]
    )

    if coverage == "confirmed":

        stats["confirmed"] += 1

    elif coverage == "semantic_match_only":

        stats["semantic_match_only"] += 1

    elif coverage == "not_found":

        stats["not_found"] += 1

    elif coverage == "error":

        stats["errors"] += 1

    stats["actual_tools"] += (
        record["composio"]["tool_count"]
    )


# ============================================================
# TOTALS
# ============================================================

confirmed = (
    coverage_counts["confirmed"]
)

semantic = (
    coverage_counts[
        "semantic_match_only"
    ]
)

not_found = (
    coverage_counts["not_found"]
)

errors = (
    coverage_counts["error"]
)

total_tools = sum(
    x["composio"]["tool_count"]
    for x in cleaned
)


average_tools = (
    round(
        total_tools / confirmed,
        2
    )
    if confirmed
    else 0
)


# ============================================================
# TOP APPS
# ============================================================

top_apps = sorted(
    cleaned,
    key=lambda x:
        x["composio"]["tool_count"],
    reverse=True
)[:10]


# ============================================================
# FINAL DATASET
# ============================================================

output = {

    "metadata": {

        "pipeline_version":
            "2.0",

        "total_apps":
            len(cleaned),

        "confirmed_apps":
            confirmed,

        "semantic_match_only":
            semantic,

        "not_found":
            not_found,

        "errors":
            errors,

        "total_actual_app_tools":
            total_tools,

        "average_tools_per_confirmed_app":
            average_tools,

        "important_note":
            "Tool counts include only tools belonging "
            "to a directly matched Composio toolkit. "
            "Semantic or related toolkit tools are excluded."
    },

    "results":
        cleaned,

    "patterns": {

        "coverage":
            dict(
                coverage_counts
            ),

        "category_stats":
            dict(
                category_stats
            ),

        "top_apps_by_tool_count":
            [
                {

                    "app":
                        x["app"],

                    "category":
                        x["category"],

                    "tool_count":
                        x["composio"][
                            "tool_count"
                        ]
                }

                for x in top_apps
            ]
    }
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
# PRINT
# ============================================================

print()
print("=" * 70)
print("FINAL DATASET CREATED")
print("=" * 70)

print(
    f"Total apps:             {len(cleaned)}"
)

print(
    f"Confirmed:              {confirmed}"
)

print(
    f"Semantic-only:          {semantic}"
)

print(
    f"Not found:              {not_found}"
)

print(
    f"Errors:                 {errors}"
)

print(
    f"Actual app tools:       {total_tools}"
)

print(
    f"Average tools/confirmed:{average_tools}"
)

print()
print("Coverage:")

for key, value in coverage_counts.items():

    print(
        f"  {key}: {value}"
    )

print()
print("Top apps by ACTUAL app tools:")

for app in top_apps:

    print(
        f"  {app['app']}: "
        f"{app['composio']['tool_count']}"
    )

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)

print("=" * 70)