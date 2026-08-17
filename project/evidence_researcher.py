import json
import re
import time
import requests

from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = Path(
    "data/composio_results.json"
)

OUTPUT_FILE = Path(
    "data/research_results.json"
)

REQUEST_DELAY = 0.35
REQUEST_TIMEOUT = 15

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151 Safari/537.36"
}


# ============================================================
# RULES
# ============================================================

AUTH_RULES = {

    "OAuth2": [
        r"\boauth 2\.0\b",
        r"\boauth2\b",
        r"\boauth\b",
        r"authorization code",
        r"oauth authorization"
    ],

    "API key": [
        r"\bapi key\b",
        r"\bapikey\b",
        r"x-api-key"
    ],

    "Bearer token": [
        r"bearer token",
        r"authorization:\s*bearer",
        r"\bbearer\b"
    ],

    "Basic": [
        r"basic authentication",
        r"basic auth"
    ],

    "JWT": [
        r"\bjwt\b",
        r"json web token"
    ]
}


API_RULES = {

    "REST": [
        r"\brest api\b",
        r"\brestful api\b",
        r"\brest api reference\b",
        r"\bhttp api\b",
        r"\brest endpoints?\b"
    ],

    "GraphQL": [
        r"\bgraphql\b",
        r"graphql api",
        r"graphql endpoint"
    ],

    "Webhooks": [
        r"\bwebhooks?\b"
    ],

    "SDK": [
        r"\bsdk\b",
        r"software development kit",
        r"client library"
    ]
}


SELF_SERVE_RULES = [

    r"free plan",
    r"free trial",
    r"developer account",
    r"create an account",
    r"\bsign up\b",
    r"get an api key",
    r"generate an api key",
    r"developer portal",
    r"self.?serve",
    r"developer signup",
    r"register an application",
    r"create an application"
]


GATED_RULES = [

    r"contact sales",
    r"contact our sales team",
    r"enterprise only",
    r"enterprise plan",
    r"request access",
    r"approval required",
    r"admin approval",
    r"\bpartner\b",
    r"partnership",
    r"waitlist",
    r"invite only"
]


MCP_RULES = [

    r"\bmcp server\b",
    r"model context protocol server",
    r"model-context-protocol",
    r"\bmcp integration\b",
    r"\bmcp tool\b",
    r"\bmcp endpoint\b"
]


# ============================================================
# DESCRIPTION MAP
# ============================================================

DESCRIPTIONS = {

    "Salesforce":
        "Enterprise CRM for sales, service, marketing and customer data.",

    "HubSpot":
        "CRM platform combining sales, marketing, customer service and content tools.",

    "Pipedrive":
        "Sales CRM focused on pipeline, deals, activities and sales workflows.",

    "Attio":
        "Modern CRM for managing contacts, companies, deals and relationship data.",

    "Twenty":
        "Open-source CRM for managing people, companies, opportunities and workflows.",

    "Slack":
        "Team communication platform for channels, messaging, apps and automation.",

    "Twilio":
        "Communications platform providing programmable messaging, voice and other APIs.",

    "GitHub":
        "Developer platform for source control, collaboration, issues and CI/CD.",

    "Shopify":
        "Commerce platform providing storefront, product, order and customer management.",

    "Stripe":
        "Payments platform providing APIs for payments, billing, subscriptions and financial workflows.",

    "Notion":
        "Workspace platform for documents, databases, knowledge and team collaboration.",

    "Airtable":
        "Collaborative database platform for structured data, workflows and applications."
}


# ============================================================
# HTTP
# ============================================================

def fetch(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        return {

            "status":
                response.status_code,

            "url":
                response.url,

            "html":
                response.text
        }

    except Exception as e:

        return {

            "status":
                0,

            "url":
                url,

            "html":
                "",

            "error":
                str(e)
        }


# ============================================================
# TEXT
# ============================================================

def extract_text(html):

    if not html:
        return ""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg"
        ]
    ):

        tag.decompose()

    return " ".join(
        soup.stripped_strings
    )


# ============================================================
# PATTERN MATCHING
# ============================================================

def matched_patterns(
    text,
    patterns
):

    if not text:
        return []

    results = []

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.I
        ):

            results.append(
                pattern
            )

    return results


# ============================================================
# FIELD DETECTION WITH SOURCE
# ============================================================

def detect_field(
    pages,
    rules
):

    matches = []

    for page in pages:

        found = matched_patterns(
            page["text"],
            rules
        )

        if found:

            matches.append({

                "url":
                    page["url"],

                "patterns":
                    found
            })

    return matches


# ============================================================
# AUTH
# ============================================================

def detect_auth(pages):

    detected = []

    evidence = []

    for auth_type, rules in AUTH_RULES.items():

        matches = detect_field(
            pages,
            rules
        )

        if matches:

            detected.append(
                auth_type
            )

            evidence.append({

                "field":
                    "auth",

                "value":
                    auth_type,

                "source":
                    matches[0]["url"],

                "signals":
                    matches[0]["patterns"]
            })

    return detected, evidence


# ============================================================
# API
# ============================================================

def detect_api(pages):

    detected = []

    evidence = []

    total_endpoint_signals = 0

    for page in pages:

        total_endpoint_signals += len(
            re.findall(
                r"\b(GET|POST|PUT|PATCH|DELETE)\b",
                page["text"],
                flags=re.I
            )
        )

    for api_type, rules in API_RULES.items():

        matches = detect_field(
            pages,
            rules
        )

        if matches:

            detected.append(
                api_type
            )

            evidence.append({

                "field":
                    "api",

                "value":
                    api_type,

                "source":
                    matches[0]["url"],

                "signals":
                    matches[0]["patterns"]
            })

    if not detected:

        return {

            "available":
                "unknown",

            "types":
                [],

            "breadth":
                "unknown"
        }, evidence

    if (
        len(detected) >= 3
        or total_endpoint_signals >= 10
    ):

        breadth = "broad"

    elif (
        len(detected) >= 2
        or total_endpoint_signals >= 3
    ):

        breadth = "medium"

    else:

        breadth = "narrow"

    return {

        "available":
            "yes",

        "types":
            detected,

        "breadth":
            breadth

    }, evidence


# ============================================================
# SELF SERVE
# ============================================================

def detect_access(pages):

    self_matches = detect_field(
        pages,
        SELF_SERVE_RULES
    )

    gated_matches = detect_field(
        pages,
        GATED_RULES
    )

    if (
        self_matches
        and gated_matches
    ):

        status = "conditional"

    elif gated_matches:

        status = "gated"

    elif self_matches:

        status = "self-serve"

    else:

        status = "unknown"

    evidence = []

    for item in self_matches[:3]:

        evidence.append({

            "field":
                "self_serve",

            "value":
                "self-serve",

            "source":
                item["url"],

            "signals":
                item["patterns"]
        })

    for item in gated_matches[:3]:

        evidence.append({

            "field":
                "self_serve",

            "value":
                "gated",

            "source":
                item["url"],

            "signals":
                item["patterns"]
        })

    return {

        "status":
            status,

        "signals":
            [
                x
                for item in (
                    self_matches
                    + gated_matches
                )
                for x in item["patterns"]
            ][:10]

    }, evidence


# ============================================================
# MCP
# ============================================================

def detect_mcp(pages):

    evidence = []

    for page in pages:

        matches = matched_patterns(
            page["text"],
            MCP_RULES
        )

        if matches:

            evidence.append({

                "field":
                    "mcp",

                "value":
                    "possible",

                "source":
                    page["url"],

                "signals":
                    matches
            })

    if evidence:

        return "possible", evidence

    return "not_found", []


# ============================================================
# CANDIDATE DOC URLS
# ============================================================

def candidate_urls(website):

    base = website.rstrip("/")

    return [

        base + "/developers",

        base + "/developer",

        base + "/docs",

        base + "/api",

        base + "/developer/docs",

        base + "/developers/docs",

        base + "/docs/api",

        base + "/api/docs"
    ]


# ============================================================
# DESCRIPTION
# ============================================================

def description_for(
    app,
    category
):

    if app in DESCRIPTIONS:

        return DESCRIPTIONS[app]

    category_descriptions = {

        "CRM and Sales":
            "CRM and sales platform for managing customer relationships and sales workflows.",

        "Support and Helpdesk":
            "Customer support platform for managing conversations, tickets and service workflows.",

        "Communications and Messaging":
            "Communication platform for messaging, calls, notifications or collaboration.",

        "Marketing, Ads, Email and Social":
            "Marketing, advertising, email or social platform for audience engagement.",

        "Ecommerce":
            "Commerce platform for products, orders, customers or online sales.",

        "Data, SEO and Scraping":
            "Data, SEO, web-scraping or enrichment platform.",

        "Developer, Infra and Data platforms":
            "Developer, infrastructure or data platform with programmable services.",

        "Productivity and Project Management":
            "Productivity and project-management platform for organizing work and collaboration.",

        "Finance and Fintech":
            "Financial platform for payments, financial data or business finance workflows.",

        "AI, Research and Media-native":
            "AI, research, meeting, media or content platform with programmable capabilities."
    }

    return category_descriptions.get(
        category,
        f"{app} software platform."
    )


# ============================================================
# RESEARCH ONE APP
# ============================================================

def research_app(record):

    app = record["app"]

    website = record["website"]

    print(
        f"    Researching official sources..."
    )

    pages = []

    # --------------------------------------------------------
    # Homepage
    # --------------------------------------------------------

    home = fetch(
        website
    )

    if home["status"]:

        home_text = extract_text(
            home["html"]
        )

        if home_text:

            pages.append({

                "url":
                    home["url"],

                "text":
                    home_text,

                "status":
                    home["status"]
            })

    # --------------------------------------------------------
    # Candidate developer/docs pages
    # --------------------------------------------------------

    seen_urls = {
        p["url"]
        for p in pages
    }

    successful_docs = 0

    for url in candidate_urls(
        website
    ):

        if url in seen_urls:
            continue

        response = fetch(
            url
        )

        final_url = response["url"]

        seen_urls.add(
            final_url
        )

        if response["status"] != 200:
            continue

        text = extract_text(
            response["html"]
        )

        if len(text) < 150:
            continue

        pages.append({

            "url":
                final_url,

            "text":
                text,

            "status":
                response["status"]
        })

        successful_docs += 1

        # We don't need to crawl dozens of pages.
        if successful_docs >= 4:
            break

        time.sleep(
            0.15
        )

    # --------------------------------------------------------
    # Detection
    # --------------------------------------------------------

    auth, auth_evidence = detect_auth(
        pages
    )

    api, api_evidence = detect_api(
        pages
    )

    access, access_evidence = detect_access(
        pages
    )

    mcp, mcp_evidence = detect_mcp(
        pages
    )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = 0.25

    if home["status"] == 200:

        confidence += 0.20

    if successful_docs >= 1:

        confidence += 0.15

    if successful_docs >= 2:

        confidence += 0.10

    if auth:

        confidence += 0.05

    if api["available"] == "yes":

        confidence += 0.05

    if access["status"] != "unknown":

        confidence += 0.05

    confidence = min(
        confidence,
        0.85
    )

    # --------------------------------------------------------
    # Human review
    #
    # Keyword research is NOT treated as final proof.
    # --------------------------------------------------------

    needs_review = (

        confidence < 0.75

        or not auth

        or access["status"] == "unknown"

        or api["available"] == "unknown"

        or mcp == "possible"
    )

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    evidence = (
        auth_evidence
        + api_evidence
        + access_evidence
        + mcp_evidence
    )

    # Deduplicate evidence

    unique_evidence = []

    seen = set()

    for item in evidence:

        key = (
            item["field"],
            item["value"],
            item["source"]
        )

        if key not in seen:

            seen.add(key)

            unique_evidence.append(
                item
            )

    return {

        "id":
            record["id"],

        "app":
            app,

        "category":
            record["category"],

        "website":
            website,

        "description":
            description_for(
                app,
                record["category"]
            ),

        "auth":
            auth,

        "self_serve":
            access["status"],

        "self_serve_signals":
            access["signals"],

        "api":
            api,

        "mcp":
            mcp,

        "evidence":
            unique_evidence,

        "confidence":
            round(
                confidence,
                2
            ),

        "needs_human_review":
            needs_review,

        # Keep Composio untouched.
        "composio":
            record.get(
                "composio",
                {}
            )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("STARTING EVIDENCE RESEARCH")
    print("=" * 70)

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        records = json.load(f)

    if isinstance(
        records,
        dict
    ):

        records = records.get(
            "results",
            []
        )

    if len(records) != 100:

        raise ValueError(
            f"Expected 100 apps, "
            f"found {len(records)}"
        )

    results = []

    errors = 0

    for index, record in enumerate(
        records,
        start=1
    ):

        print()
        print(
            f"[{index}/100] "
            f"{record['app']}"
        )

        try:

            result = research_app(
                record
            )

            results.append(
                result
            )

            print(
                f"    Auth: "
                f"{result['auth'] or 'unknown'}"
            )

            print(
                f"    API: "
                f"{result['api']['available']} "
                f"{result['api']['types']}"
            )

            print(
                f"    Access: "
                f"{result['self_serve']}"
            )

            print(
                f"    MCP: "
                f"{result['mcp']}"
            )

            print(
                f"    Confidence: "
                f"{result['confidence']}"
            )

        except Exception as e:

            errors += 1

            print(
                f"    ERROR: {e}"
            )

            results.append({

                "id":
                    record.get("id"),

                "app":
                    record.get("app"),

                "category":
                    record.get("category"),

                "website":
                    record.get("website"),

                "description":
                    description_for(
                        record.get("app", ""),
                        record.get("category", "")
                    ),

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

                "evidence":
                    [],

                "confidence":
                    0.0,

                "needs_human_review":
                    True,

                "error":
                    str(e),

                "composio":
                    record.get(
                        "composio",
                        {}
                    )
            })

        time.sleep(
            REQUEST_DELAY
        )

    # ========================================================
    # SAVE
    # ========================================================

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
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("EVIDENCE RESEARCH COMPLETE")
    print("=" * 70)

    print(
        f"Records researched: "
        f"{len(results)}"
    )

    print(
        f"Errors: "
        f"{errors}"
    )

    print(
        f"Saved: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()