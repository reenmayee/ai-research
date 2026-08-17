import json
from pathlib import Path
from collections import Counter, defaultdict


# ============================================================
# FILES
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

INPUT_FILE = DATA_DIR / "final_results.json"
OUTPUT_FILE = DATA_DIR / "analysis_results.json"


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("ANALYZING FINAL RESEARCH DATASET")
print("=" * 70)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    records = data.get("results", [])
else:
    records = data

if len(records) != 100:
    raise ValueError(
        f"Expected 100 apps, found {len(records)}"
    )

print(f"Loaded {len(records)} records")


# ============================================================
# HELPERS
# ============================================================

def safe_list(value):
    return value if isinstance(value, list) else []


def safe_dict(value):
    return value if isinstance(value, dict) else {}


def pct(n, total):
    return round((n / total) * 100, 1) if total else 0


def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_coverage(record):
    return safe_dict(
        record.get("composio")
    ).get(
        "coverage",
        "unknown"
    )


def get_api(record):
    return safe_dict(
        record.get("api")
    )


def get_auth(record):
    return safe_list(
        record.get("auth")
    )


def get_access(record):
    return record.get(
        "self_serve",
        "unknown"
    )


def get_mcp(record):
    return record.get(
        "mcp",
        "unknown"
    )


# ============================================================
# COMPOSIO COVERAGE
# ============================================================

coverage_counts = Counter(
    get_coverage(r)
    for r in records
)

confirmed = coverage_counts["confirmed"]
semantic_only = coverage_counts["semantic_match_only"]
not_found = coverage_counts["not_found"]
composio_errors = coverage_counts["error"]


# ============================================================
# AUTHENTICATION
# ============================================================

auth_counts = Counter()

for record in records:

    auth_values = get_auth(record)

    if not auth_values:
        auth_counts["Unknown"] += 1
    else:
        for auth in auth_values:
            auth_counts[str(auth)] += 1


apps_with_auth = sum(
    1
    for r in records
    if get_auth(r)
)


# ============================================================
# ACCESS / SELF-SERVE
# ============================================================

access_counts = Counter(
    get_access(r)
    for r in records
)

self_serve = access_counts["self-serve"]
conditional = access_counts["conditional"]
gated = access_counts["gated"]
access_unknown = access_counts["unknown"]


# ============================================================
# API SURFACE
# ============================================================

api_available = Counter()
api_types = Counter()
api_breadth = Counter()

for record in records:

    api = get_api(record)

    api_available[
        api.get(
            "available",
            "unknown"
        )
    ] += 1

    for api_type in safe_list(
        api.get("types")
    ):
        api_types[str(api_type)] += 1

    breadth = api.get(
        "breadth",
        "unknown"
    )

    api_breadth[str(breadth)] += 1


api_yes = api_available["yes"]
api_no = api_available["no"]
api_unknown = api_available["unknown"]


# ============================================================
# MCP
# ============================================================

mcp_counts = Counter(
    get_mcp(r)
    for r in records
)

mcp_existing = mcp_counts["existing"]
mcp_not_found = mcp_counts["not_found"]
mcp_unknown = mcp_counts["unknown"]
mcp_possible = mcp_counts["possible"]


# ============================================================
# BUILDABILITY
# ============================================================

buildability_counts = Counter(
    r.get(
        "buildability",
        "UNCLEAR"
    )
    for r in records
)

build_now = buildability_counts["BUILD_NOW"]

build_with_constraints = buildability_counts[
    "BUILD_WITH_CONSTRAINTS"
]

composio_covered = buildability_counts[
    "Composio-covered"
]

research_required_count = buildability_counts[
    "RESEARCH_REQUIRED"
]

outreach_required = buildability_counts[
    "OUTREACH_OR_RESEARCH"
]

unclear = buildability_counts[
    "UNCLEAR"
]


# ============================================================
# HUMAN REVIEW / VERIFICATION
# ============================================================

review_required = sum(
    1
    for r in records
    if r.get(
        "needs_human_review",
        False
    )
)

verified_records = len(records) - review_required


# ============================================================
# CONFIDENCE
#
# Support both:
#   research_confidence
#   confidence
# ============================================================

confidence_values = []

for record in records:

    value = record.get(
        "research_confidence",
        record.get(
            "confidence",
            0
        )
    )

    confidence_values.append(
        safe_float(value)
    )


high_confidence = sum(
    1
    for value in confidence_values
    if value >= 0.75
)

medium_confidence = sum(
    1
    for value in confidence_values
    if 0.50 <= value < 0.75
)

low_confidence = sum(
    1
    for value in confidence_values
    if value < 0.50
)


average_confidence = (
    round(
        sum(confidence_values)
        / len(confidence_values),
        3
    )
    if confidence_values
    else 0
)


# ============================================================
# TOOL COUNTS
# ============================================================

direct_tool_counts = []

for record in records:

    composio = safe_dict(
        record.get("composio")
    )

    direct_tool_counts.append(
        safe_float(
            composio.get(
                "tool_count",
                0
            )
        )
    )


total_tools = int(
    sum(direct_tool_counts)
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
# VERIFIED BUILD-NOW CHECK
#
# BUILD_NOW is only considered a strong opportunity when
# critical integration fields are actually known.
# ============================================================

verified_build_now = []

for record in records:

    api = get_api(record)
    auth = get_auth(record)
    access = get_access(record)
    coverage = get_coverage(record)

    if (
        record.get("buildability") == "BUILD_NOW"
        and api.get("available") == "yes"
        and auth
        and access == "self-serve"
        and coverage != "confirmed"
        and not record.get(
            "needs_human_review",
            False
        )
    ):
        verified_build_now.append(record)


verified_build_now_count = len(
    verified_build_now
)


# ============================================================
# OPPORTUNITY ANALYSIS
# ============================================================

def opportunity_score(record):
    """
    Transparent prioritization heuristic.

    Higher score means:
    - API is documented
    - authentication is documented
    - access is self-serve
    - no direct Composio coverage exists
    - evidence does not require immediate review

    This is NOT a measure of business value.
    """

    score = 0
    reasons = []

    api = get_api(record)
    auth = get_auth(record)
    access = get_access(record)
    coverage = get_coverage(record)

    review = record.get(
        "needs_human_review",
        False
    )

    buildability = record.get(
        "buildability",
        "UNCLEAR"
    )

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    if api.get("available") == "yes":

        score += 3
        reasons.append(
            "public API detected"
        )

    elif api.get("available") == "unknown":

        reasons.append(
            "API availability unknown"
        )


    # --------------------------------------------------------
    # AUTH
    # --------------------------------------------------------

    if auth:

        score += 2
        reasons.append(
            "authentication documented"
        )

    else:

        reasons.append(
            "authentication unknown"
        )


    # --------------------------------------------------------
    # ACCESS
    # --------------------------------------------------------

    if access == "self-serve":

        score += 3
        reasons.append(
            "self-serve access"
        )

    elif access == "conditional":

        score += 1
        reasons.append(
            "conditional access"
        )

    elif access == "gated":

        reasons.append(
            "gated access"
        )

    else:

        reasons.append(
            "access unknown"
        )


    # --------------------------------------------------------
    # COMPOSIO GAP
    # --------------------------------------------------------

    if coverage != "confirmed":

        score += 2
        reasons.append(
            "no direct Composio toolkit"
        )


    # --------------------------------------------------------
    # BUILDABILITY BONUS
    # --------------------------------------------------------

    if buildability == "BUILD_NOW":

        score += 1
        reasons.append(
            "classified as build-now"
        )

    elif buildability == "BUILD_WITH_CONSTRAINTS":

        reasons.append(
            "buildable with constraints"
        )


    # --------------------------------------------------------
    # REVIEW PENALTY
    # --------------------------------------------------------

    if review:

        score -= 2
        reasons.append(
            "requires human verification"
        )


    score = max(
        0,
        min(score, 10)
    )

    return score, reasons


# ============================================================
# CREATE OPPORTUNITIES
# ============================================================

opportunities = []

for record in records:

    score, reasons = opportunity_score(
        record
    )

    opportunities.append({

        "app": record.get("app"),

        "category": record.get(
            "category"
        ),

        "score": score,

        "reasons": reasons,

        "buildability": record.get(
            "buildability",
            "UNCLEAR"
        ),

        "composio_coverage": get_coverage(
            record
        ),

        "api": get_api(record).get(
            "available",
            "unknown"
        ),

        "auth_documented": bool(
            get_auth(record)
        ),

        "self_serve": get_access(
            record
        ),

        "needs_human_review": record.get(
            "needs_human_review",
            False
        )
    })


opportunities.sort(
    key=lambda x: (
        x["score"],
        x["app"] or ""
    ),
    reverse=True
)


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

category_stats = defaultdict(
    lambda: {
        "total": 0,
        "direct_composio": 0,
        "semantic_only": 0,
        "not_found": 0,
        "api_available": 0,
        "auth_documented": 0,
        "self_serve": 0,
        "conditional": 0,
        "gated": 0,
        "mcp_existing": 0,
        "build_now": 0,
        "build_with_constraints": 0,
        "research_required": 0,
        "human_review": 0
    }
)


for record in records:

    category = record.get(
        "category",
        "Unknown"
    )

    stats = category_stats[
        category
    ]

    stats["total"] += 1

    coverage = get_coverage(
        record
    )

    if coverage == "confirmed":

        stats[
            "direct_composio"
        ] += 1

    elif coverage == "semantic_match_only":

        stats[
            "semantic_only"
        ] += 1

    elif coverage == "not_found":

        stats[
            "not_found"
        ] += 1


    api = get_api(record)

    if api.get(
        "available"
    ) == "yes":

        stats[
            "api_available"
        ] += 1


    if get_auth(record):

        stats[
            "auth_documented"
        ] += 1


    access = get_access(
        record
    )

    if access == "self-serve":

        stats[
            "self_serve"
        ] += 1

    elif access == "conditional":

        stats[
            "conditional"
        ] += 1

    elif access == "gated":

        stats[
            "gated"
        ] += 1


    if get_mcp(record) == "existing":

        stats[
            "mcp_existing"
        ] += 1


    buildability = record.get(
        "buildability",
        "UNCLEAR"
    )

    if buildability == "BUILD_NOW":

        stats[
            "build_now"
        ] += 1

    elif buildability == "BUILD_WITH_CONSTRAINTS":

        stats[
            "build_with_constraints"
        ] += 1

    elif buildability == "RESEARCH_REQUIRED":

        stats[
            "research_required"
        ] += 1


    if record.get(
        "needs_human_review",
        False
    ):

        stats[
            "human_review"
        ] += 1


# ============================================================
# CATEGORY PERCENTAGES
# ============================================================

for category, stats in category_stats.items():

    total = stats["total"]

    stats[
        "direct_composio_pct"
    ] = pct(
        stats["direct_composio"],
        total
    )

    stats[
        "api_available_pct"
    ] = pct(
        stats["api_available"],
        total
    )

    stats[
        "self_serve_pct"
    ] = pct(
        stats["self_serve"],
        total
    )

    stats[
        "build_now_pct"
    ] = pct(
        stats["build_now"],
        total
    )

    stats[
        "human_review_pct"
    ] = pct(
        stats["human_review"],
        total
    )


# ============================================================
# EASY WINS / OUTREACH / RESEARCH
# ============================================================

easy_wins = [
    r
    for r in records
    if r.get(
        "buildability"
    ) == "BUILD_NOW"
]


constraint_opportunities = [
    r
    for r in records
    if r.get(
        "buildability"
    ) == "BUILD_WITH_CONSTRAINTS"
]


outreach_apps = [
    r
    for r in records
    if (
        r.get("buildability") == "OUTREACH_OR_RESEARCH"
        or (
            r.get("buildability") == "BUILD_WITH_CONSTRAINTS"
            and r.get("self_serve") in ["gated", "conditional"]
        )
    )
]


research_required = [
    r
    for r in records
    if r.get(
        "buildability"
    ) in [
        "RESEARCH_REQUIRED",
        "UNCLEAR"
    ]
]


# ============================================================
# DATA QUALITY / VERIFICATION
# ============================================================

missing_evidence = []

for record in records:

    evidence = safe_list(
        record.get("evidence")
    )

    if not evidence:

        missing_evidence.append(
            record.get("app")
        )


unsupported_or_uncertain = [
    r.get("app")
    for r in records
    if r.get(
        "needs_human_review",
        False
    )
]


evidence_coverage = (
    len(records)
    - len(missing_evidence)
)


evidence_coverage_pct = pct(
    evidence_coverage,
    len(records)
)


# ============================================================
# CRITICAL FIELD COMPLETENESS
# ============================================================

critical_complete = 0

for record in records:

    api = get_api(record)

    if (
        api.get("available")
        not in [None, "", "unknown"]
        and get_auth(record)
        and get_access(record)
        not in [None, "", "unknown"]
    ):
        critical_complete += 1


critical_complete_pct = pct(
    critical_complete,
    len(records)
)


# ============================================================
# PATTERN HEADLINES
# ============================================================

auth_dominant = (
    auth_counts.most_common(1)[0]
    if auth_counts
    else ("Unknown", 0)
)


largest_category_gap = None

category_candidates = []

for category, stats in category_stats.items():

    category_candidates.append(
        (
            stats["total"]
            - stats["direct_composio"],

            category,

            stats
        )
    )


if category_candidates:

    largest_category_gap = max(
        category_candidates,
        key=lambda x: x[0]
    )


headline_patterns = {

    "auth_dominates": {

        "pattern":
            auth_dominant[0],

        "count":
            auth_dominant[1],

        "share_of_all_records":
            pct(
                auth_dominant[1],
                len(records)
            )
    },


    "direct_composio_coverage": {

        "count":
            confirmed,

        "percentage":
            pct(
                confirmed,
                len(records)
            )
    },


    "semantic_only_opportunities": {

        "count":
            semantic_only,

        "percentage":
            pct(
                semantic_only,
                len(records)
            )
    },


    "api_available": {

        "count":
            api_yes,

        "percentage":
            pct(
                api_yes,
                len(records)
            )
    },


    "self_serve": {

        "count":
            self_serve,

        "percentage":
            pct(
                self_serve,
                len(records)
            )
    },


    "gated": {

        "count":
            gated,

        "percentage":
            pct(
                gated,
                len(records)
            )
    },


    "mcp_existing": {

        "count":
            mcp_existing,

        "percentage":
            pct(
                mcp_existing,
                len(records)
            )
    },


    "build_now": {

        "count":
            build_now,

        "percentage":
            pct(
                build_now,
                len(records)
            )
    },


    "verified_build_now": {

        "count":
            verified_build_now_count,

        "percentage":
            pct(
                verified_build_now_count,
                len(records)
            )
    },


    "build_with_constraints": {

        "count":
            build_with_constraints,

        "percentage":
            pct(
                build_with_constraints,
                len(records)
            )
    },


    "human_review": {

        "count":
            review_required,

        "percentage":
            pct(
                review_required,
                len(records)
            )
    }
}


# ============================================================
# FINAL ANALYSIS OUTPUT
# ============================================================

analysis = {

    "metadata": {

        "total_apps":
            len(records),

        "methodology": (
            "Analysis is derived from the final merged dataset. "
            "Composio coverage, API availability, authentication, "
            "access, MCP, buildability and verification status are "
            "treated as separate dimensions."
        ),

        "accuracy_note": (
            "These statistics describe the research pipeline output "
            "and evidence coverage. They should not be presented as "
            "100-app factual accuracy without human verification."
        ),

        "scoring_note": (
            "Opportunity scores are prioritization heuristics, "
            "not measures of objective business value."
        )
    },


    # ========================================================
    # HEADLINES
    # ========================================================

    "headline_patterns":
        headline_patterns,


    # ========================================================
    # COMPOSIO
    # ========================================================

    "composio_coverage": {

        "confirmed":
            confirmed,

        "semantic_match_only":
            semantic_only,

        "not_found":
            not_found,

        "errors":
            composio_errors,

        "confirmed_percentage":
            pct(
                confirmed,
                len(records)
            ),

        "semantic_percentage":
            pct(
                semantic_only,
                len(records)
            ),

        "not_found_percentage":
            pct(
                not_found,
                len(records)
            ),

        "actual_tools":
            total_tools,

        "average_tools_per_confirmed_app":
            average_tools
    },


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    "authentication": {

        "counts":
            dict(auth_counts),

        "apps_with_documented_auth":
            apps_with_auth,

        "unknown":
            len(records)
            - apps_with_auth,

        "documented_percentage":
            pct(
                apps_with_auth,
                len(records)
            )
    },


    # ========================================================
    # ACCESS
    # ========================================================

    "access": {

        "self_serve":
            self_serve,

        "conditional":
            conditional,

        "gated":
            gated,

        "unknown":
            access_unknown,

        "self_serve_percentage":
            pct(
                self_serve,
                len(records)
            ),

        "gated_percentage":
            pct(
                gated,
                len(records)
            )
    },


    # ========================================================
    # API
    # ========================================================

    "api": {

        "availability":
            dict(api_available),

        "types":
            dict(api_types),

        "breadth":
            dict(api_breadth),

        "available_percentage":
            pct(
                api_yes,
                len(records)
            )
    },


    # ========================================================
    # MCP
    # ========================================================

    "mcp": {

        "existing":
            mcp_existing,

        "possible":
            mcp_possible,

        "not_found":
            mcp_not_found,

        "unknown":
            mcp_unknown
    },


    # ========================================================
    # BUILDABILITY
    # ========================================================

    "buildability": {

        "counts":
            dict(buildability_counts),

        "easy_wins_count":
            len(easy_wins),

        "verified_build_now_count":
            verified_build_now_count,

        "build_with_constraints_count":
            len(constraint_opportunities),

        "outreach_count":
            len(outreach_apps),

        "research_required_count":
            len(research_required)
    },


    # ========================================================
    # CONFIDENCE
    # ========================================================

    "confidence": {

        "high":
            high_confidence,

        "medium":
            medium_confidence,

        "low":
            low_confidence,

        "average":
            average_confidence
    },


    # ========================================================
    # VERIFICATION
    # ========================================================

    "verification": {

        "human_review_required":
            review_required,

        "human_review_percentage":
            pct(
                review_required,
                len(records)
            ),

        "records_without_human_review":
            verified_records,

        "records_with_evidence":
            evidence_coverage,

        "evidence_coverage_percentage":
            evidence_coverage_pct,

        "critical_fields_complete":
            critical_complete,

        "critical_fields_complete_percentage":
            critical_complete_pct,

        "missing_evidence_apps":
            missing_evidence,

        "apps_requiring_review":
            unsupported_or_uncertain
    },


    # ========================================================
    # CATEGORY STATS
    # ========================================================

    "category_stats":
        dict(category_stats),


    # ========================================================
    # TOP OPPORTUNITIES
    # ========================================================

    "top_opportunities":
        opportunities[:15],


    # ========================================================
    # EASY WINS
    # ========================================================

    "easy_wins": [

        {

            "app":
                r.get("app"),

            "category":
                r.get("category"),

            "buildability":
                r.get("buildability"),

            "coverage":
                get_coverage(r),

            "api":
                get_api(r).get(
                    "available",
                    "unknown"
                ),

            "auth":
                get_auth(r),

            "self_serve":
                get_access(r),

            "needs_human_review":
                r.get(
                    "needs_human_review",
                    False
                )
        }

        for r in easy_wins
    ],


    # ========================================================
    # CONSTRAINT OPPORTUNITIES
    # ========================================================

    "build_with_constraints": [

        {

            "app":
                r.get("app"),

            "category":
                r.get("category"),

            "blocker":
                r.get(
                    "blocker",
                    ""
                ),

            "coverage":
                get_coverage(r),

            "api":
                get_api(r).get(
                    "available",
                    "unknown"
                ),

            "self_serve":
                get_access(r)
        }

        for r in constraint_opportunities
    ],


    # ========================================================
    # OUTREACH
    # ========================================================

    "outreach_required": [

        {

            "app":
                r.get("app"),

            "category":
                r.get("category"),

            "blocker":
                r.get(
                    "blocker",
                    ""
                )
        }

        for r in outreach_apps
    ],


    # ========================================================
    # RESEARCH REQUIRED
    # ========================================================

    "research_required": [

        {

            "app":
                r.get("app"),

            "category":
                r.get("category"),

            "blocker":
                r.get(
                    "blocker",
                    ""
                ),

            "missing_fields":
                safe_dict(
                    r.get("data_quality")
                ).get(
                    "missing_fields",
                    []
                ),

            "needs_human_review":
                r.get(
                    "needs_human_review",
                    False
                )
        }

        for r in research_required
    ],


    # ========================================================
    # LARGEST CATEGORY GAP
    # ========================================================

    "largest_category_gap": (

        {

            "category":
                largest_category_gap[1],

            "gap":
                largest_category_gap[0],

            "stats":
                largest_category_gap[2]
        }

        if largest_category_gap
        else None
    )
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
        analysis,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# TERMINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print(
    f"Total apps:              "
    f"{len(records)}"
)

print(
    f"Direct Composio:         "
    f"{confirmed} "
    f"({pct(confirmed, len(records))}%)"
)

print(
    f"Semantic-only:           "
    f"{semantic_only} "
    f"({pct(semantic_only, len(records))}%)"
)

print(
    f"API detected:            "
    f"{api_yes} "
    f"({pct(api_yes, len(records))}%)"
)

print(
    f"Self-serve:              "
    f"{self_serve} "
    f"({pct(self_serve, len(records))}%)"
)

print(
    f"Gated:                   "
    f"{gated} "
    f"({pct(gated, len(records))}%)"
)

print(
    f"Existing MCP:            "
    f"{mcp_existing} "
    f"({pct(mcp_existing, len(records))}%)"
)

print(
    f"Build now:               "
    f"{build_now}"
)

print(
    f"Build with constraints:  "
    f"{build_with_constraints}"
)

print(
    f"Research required:       "
    f"{research_required_count}"
)

print(
    f"Verified build-now:      "
    f"{verified_build_now_count}"
)

print(
    f"Human review required:   "
    f"{review_required} "
    f"({pct(review_required, len(records))}%)"
)

print(
    f"Evidence coverage:       "
    f"{evidence_coverage} "
    f"({evidence_coverage_pct}%)"
)

print(
    f"Critical fields complete:"
    f" {critical_complete} "
    f"({critical_complete_pct}%)"
)

print(
    f"Average confidence:      "
    f"{average_confidence}"
)

print()

print("Top 10 opportunities:")

for opportunity in opportunities[:10]:

    print(
        f"  {opportunity['app']}: "
        f"{opportunity['score']}/10"
    )

print()

print(
    f"Saved to: {OUTPUT_FILE}"
)

print("=" * 70)