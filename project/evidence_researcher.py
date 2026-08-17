import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

INPUT_FILE = DATA_DIR / "composio_results.json"
OUTPUT_FILE = DATA_DIR / "research_results.json"

REQUEST_DELAY = 0.35
REQUEST_TIMEOUT = 15
MAX_PAGES = 10
MAX_LINKS_FROM_PAGE = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151 Safari/537.36"
    )
}

# ------------------------------------------------------------
# Stronger, more conservative research rules
# ------------------------------------------------------------

AUTH_RULES = {
    "OAuth2": [
        r"\boauth\s*2\.0\b",
        r"\boauth2\b",
        r"authorization code grant",
        r"client credentials grant",
        r"oauth authorization",
    ],
    "API key": [
        r"\bapi key\b",
        r"\bapikey\b",
        r"x-api-key",
        r"api-key",
    ],
    "API token": [
        r"\bapi token\b",
        r"\bapitoken\b",
        r"api-token",
    ],
    "Bearer token": [
        r"bearer token",
        r"authorization:\s*bearer",
        r"\bbearer\s+authentication\b",
    ],
    "Basic": [
        r"basic authentication",
        r"basic auth",
    ],
    "JWT": [
        r"\bjwt\b",
        r"json web token",
    ],
    "Access token": [
        r"\baccess token\b",
        r"\baccess_token\b",
    ],
    "Personal access token": [
        r"personal access token",
        r"\bPAT\b",
    ],
    "Private app token": [
        r"private app token",
        r"private integration token",
    ],
    "Client credentials": [
        r"client credentials",
        r"client_id",
        r"client secret",
    ],
    "Auth token": [
        r"\bauth token\b",
        r"authentication token",
    ],
}

API_RULES = {
    "REST": [
        r"\bREST API\b",
        r"\bRESTful API\b",
        r"\bREST API reference\b",
        r"\bHTTP API\b",
        r"\bREST endpoints?\b",
    ],
    "GraphQL": [
        r"\bGraphQL\b",
        r"GraphQL API",
        r"GraphQL endpoint",
    ],
}

SUPPORTING_API_RULES = {
    "Webhooks": [r"\bwebhooks?\b"],
    "SDK": [r"\bSDK\b", r"software development kit", r"client library"],
}

SELF_SERVE_RULES = [
    r"get an api key",
    r"generate an api key",
    r"create an application",
    r"register an application",
    r"developer portal",
    r"developer signup",
    r"generate an access token",
    r"create an api token",
    r"create a private app",
    r"self[- ]serve api access",
]

GATED_RULES = [
    r"contact sales",
    r"contact our sales team",
    r"enterprise only",
    r"enterprise plan.*api",
    r"request api access",
    r"request access.*api",
    r"approval required",
    r"admin approval",
    r"partner approval required",
    r"become a partner",
    r"partnership required",
    r"partner access required",
    r"waitlist",
    r"invite only",
]

MCP_RULES = [
    r"\bmcp server\b",
    r"model context protocol server",
    r"model-context-protocol",
    r"\bofficial mcp\b",
]

DOC_KEYWORDS = (
    "developer",
    "developers",
    "docs",
    "documentation",
    "api",
    "reference",
    "authentication",
    "auth",
    "oauth",
    "token",
    "mcp",
    "graphql",
)

AUTH_PAGE_KEYWORDS = (
    "auth",
    "oauth",
    "token",
    "authorization",
    "api-key",
    "apikey",
    "authentication",
)

API_PAGE_KEYWORDS = (
    "api",
    "reference",
    "rest",
    "graphql",
    "endpoint",
)

MCP_PAGE_KEYWORDS = ("mcp", "model-context-protocol")


# ------------------------------------------------------------
# HTTP / parsing
# ------------------------------------------------------------

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url):
    try:
        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        return {
            "status": response.status_code,
            "url": response.url,
            "html": response.text,
        }
    except Exception as exc:
        return {
            "status": 0,
            "url": url,
            "html": "",
            "error": str(exc),
        }


def extract_page(html, url):
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title:
        title = soup.title.get_text(" ", strip=True)

    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        description = meta.get("content", "") or ""

    for tag in soup(
        ["script", "style", "noscript", "svg", "template"]
    ):
        tag.decompose()

    text = " ".join(soup.stripped_strings)

    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        absolute = urljoin(url, href)
        links.append(absolute)

    return {
        "url": url,
        "title": title,
        "description": description,
        "text": text,
        "links": links,
    }


def host(url):
    return urlparse(url).netloc.lower().split(":")[0]


def same_host(url_a, url_b):
    a = host(url_a)
    b = host(url_b)
    return bool(a and b and (a == b or a.endswith("." + b) or b.endswith("." + a)))


def url_is_doc_like(url):
    path = urlparse(url).path.lower()
    return any(k in path for k in DOC_KEYWORDS)


def score_url(url, keywords):
    path = urlparse(url).path.lower()
    return sum(1 for k in keywords if k in path)


def unique_urls(urls):
    result = []
    seen = set()

    for url in urls:
        normalized = url.split("#")[0].rstrip("/")
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result


# ------------------------------------------------------------
# Candidate documentation discovery
# ------------------------------------------------------------

def candidate_urls(website):
    base = website.rstrip("/")

    candidates = [
        base + "/developers",
        base + "/developer",
        base + "/docs",
        base + "/api",
        base + "/developer/docs",
        base + "/developers/docs",
        base + "/docs/api",
        base + "/api/docs",
        base + "/docs/auth",
        base + "/docs/authentication",
        base + "/docs/oauth",
        base + "/docs/api-reference",
        base + "/developer/api",
        base + "/developers/api",
        base + "/developers/docs/api",
    ]

    return unique_urls(candidates)


def discover_links(page):
    links = []

    for link in page.get("links", []):
        if not same_host(link, page["url"]):
            continue

        if url_is_doc_like(link):
            links.append(link)

    return unique_urls(links)


def collect_pages(website):
    pages = []
    queue = candidate_urls(website) + [website]
    seen = set()

    # Homepage is intentionally fetched first.
    ordered = [website] + candidate_urls(website)

    while ordered and len(pages) < MAX_PAGES:
        url = ordered.pop(0)
        url = url.split("#")[0].rstrip("/")

        if url in seen:
            continue
        seen.add(url)

        response = fetch(url)

        if response["status"] != 200:
            continue

        page = extract_page(response["html"], response["url"])

        if not page or len(page["text"]) < 100:
            continue

        pages.append(page)

        # Follow relevant same-site documentation links.
        links = discover_links(page)

        links.sort(
            key=lambda x: score_url(
                x,
                DOC_KEYWORDS
            ),
            reverse=True,
        )

        for link in links[:MAX_LINKS_FROM_PAGE]:
            if link not in seen:
                queue.append(link)

        # Keep the queue focused on the most useful pages.
        queue = unique_urls(queue)
        queue.sort(
            key=lambda x: score_url(
                x,
                DOC_KEYWORDS
            ),
            reverse=True,
        )

        ordered.extend(queue[:MAX_LINKS_FROM_PAGE])
        queue = []

        time.sleep(0.1)

    return pages


# ------------------------------------------------------------
# Evidence helpers
# ------------------------------------------------------------

def matched_patterns(text, patterns):
    if not text:
        return []

    found = []

    for pattern in patterns:
        if re.search(pattern, text, flags=re.I):
            found.append(pattern)

    return found


def page_score(page, keywords):
    path_score = score_url(page["url"], keywords)
    text = page["text"].lower()

    keyword_score = sum(
        1 for k in keywords if k.lower() in text
    )

    return path_score * 3 + min(keyword_score, 10)


def best_matches(pages, rules, url_keywords):
    results = []

    for page in pages:
        found = []

        for rule_name, patterns in rules.items():
            matches = matched_patterns(
                page["text"],
                patterns,
            )
            if matches:
                found.append(
                    {
                        "name": rule_name,
                        "patterns": matches,
                    }
                )

        if found:
            results.append(
                {
                    "page": page,
                    "matches": found,
                    "score": page_score(page, url_keywords),
                }
            )

    results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return results


def make_evidence(field, value, page, matches):
    return {
        "field": field,
        "value": value,
        "source": page["url"],
        "evidence_quality": "official",
        "signals": matches,
    }


# ------------------------------------------------------------
# Field detection
# ------------------------------------------------------------

def detect_auth(pages):
    detected = []
    evidence = []

    results = best_matches(
        pages,
        AUTH_RULES,
        AUTH_PAGE_KEYWORDS,
    )

    for result in results[:4]:
        page = result["page"]

        for match in result["matches"]:
            if match["name"] not in detected:
                detected.append(match["name"])
                evidence.append(
                    make_evidence(
                        "auth",
                        match["name"],
                        page,
                        match["patterns"],
                    )
                )

    return detected, evidence


def detect_api(pages):
    detected = []
    evidence = []
    supporting = []

    results = best_matches(
        pages,
        API_RULES,
        API_PAGE_KEYWORDS,
    )

    for result in results[:4]:
        page = result["page"]

        for match in result["matches"]:
            if match["name"] not in detected:
                detected.append(match["name"])
                evidence.append(
                    make_evidence(
                        "api",
                        match["name"],
                        page,
                        match["patterns"],
                    )
                )

    support_results = best_matches(
        pages,
        SUPPORTING_API_RULES,
        API_PAGE_KEYWORDS,
    )

    for result in support_results[:2]:
        page = result["page"]

        for match in result["matches"]:
            if match["name"] not in supporting:
                supporting.append(match["name"])
                evidence.append(
                    make_evidence(
                        "api_supporting",
                        match["name"],
                        page,
                        match["patterns"],
                    )
                )

    if not detected:
        available = "unknown"
        breadth = "unknown"
    else:
        available = "yes"

        # Conservative: don't call something "broad"
        # merely because GET/POST words appear repeatedly.
        if len(detected) >= 2:
            breadth = "documented"
        else:
            breadth = "documented"

    return {
        "available": available,
        "types": detected,
        "breadth": breadth,
        "additional_capabilities": supporting,
    }, evidence


def detect_access(pages):
    self_matches = []
    gated_matches = []

    for page in pages:
        self_found = matched_patterns(
            page["text"],
            SELF_SERVE_RULES,
        )
        gated_found = matched_patterns(
            page["text"],
            GATED_RULES,
        )

        if self_found:
            self_matches.append(
                {
                    "page": page,
                    "patterns": self_found,
                }
            )

        if gated_found:
            gated_matches.append(
                {
                    "page": page,
                    "patterns": gated_found,
                }
            )

    if self_matches and gated_matches:
        status = "conditional"
    elif gated_matches:
        status = "gated"
    elif self_matches:
        status = "self-serve"
    else:
        status = "unknown"

    evidence = []

    for item in self_matches[:3]:
        evidence.append(
            make_evidence(
                "self_serve",
                "self-serve",
                item["page"],
                item["patterns"],
            )
        )

    for item in gated_matches[:3]:
        evidence.append(
            make_evidence(
                "self_serve",
                "gated",
                item["page"],
                item["patterns"],
            )
        )

    signals = [
        pattern
        for item in self_matches + gated_matches
        for pattern in item["patterns"]
    ][:10]

    return {
        "status": status,
        "signals": signals,
    }, evidence


def detect_mcp(pages):
    evidence = []

    for page in pages:
        matches = matched_patterns(
            page["text"],
            MCP_RULES,
        )

        if matches:
            evidence.append(
                make_evidence(
                    "mcp",
                    "existing",
                    page,
                    matches,
                )
            )

    if evidence:
        return "existing", evidence

    return "not_found", []


# ------------------------------------------------------------
# Description
# ------------------------------------------------------------

def description_for(app, category, pages):
    # Prefer the supplied site's metadata/title over a generic
    # category sentence.
    for page in pages:
        description = page.get("description", "").strip()

        if 30 <= len(description) <= 300:
            return description

    for page in pages:
        title = page.get("title", "").strip()

        if title and len(title) <= 150:
            return f"{app}: {title}"

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
            "AI, research, meeting, media or content platform with programmable capabilities.",
    }

    return category_descriptions.get(
        category,
        f"{app} software platform.",
    )


# ------------------------------------------------------------
# Confidence
# ------------------------------------------------------------

def confidence_for(auth, api, access, mcp, evidence):
    score = 0.0

    fields = {
        "auth": auth,
        "api": api.get("available") == "yes",
        "access": access != "unknown",
        "mcp": mcp != "not_found",
    }

    if fields["auth"]:
        score += 0.25

    if fields["api"]:
        score += 0.25

    if fields["access"]:
        score += 0.20

    if fields["mcp"]:
        score += 0.15

    official_evidence_count = sum(
        1
        for item in evidence
        if item.get("evidence_quality") == "official"
    )

    score += min(official_evidence_count * 0.05, 0.15)

    return round(min(score, 1.0), 2)


# ------------------------------------------------------------
# Research one app
# ------------------------------------------------------------

def research_app(record):
    app = record["app"]
    website = record["website"]

    print("    Discovering official documentation...")

    pages = collect_pages(website)

    auth, auth_evidence = detect_auth(pages)
    api, api_evidence = detect_api(pages)
    access, access_evidence = detect_access(pages)
    mcp, mcp_evidence = detect_mcp(pages)

    evidence = (
        auth_evidence
        + api_evidence
        + access_evidence
        + mcp_evidence
    )

    # Deduplicate evidence.
    unique_evidence = []
    seen = set()

    for item in evidence:
        key = (
            item["field"],
            item["value"],
            item["source"],
        )

        if key not in seen:
            seen.add(key)
            unique_evidence.append(item)

    confidence = confidence_for(
        auth,
        api,
        access["status"],
        mcp,
        unique_evidence,
    )

    needs_review = (
        confidence < 0.75
        or not auth
        or access["status"] == "unknown"
        or api["available"] == "unknown"
        or not unique_evidence
    )

    return {
        "id": record["id"],
        "app": app,
        "category": record["category"],
        "website": website,
        "description": description_for(
            app,
            record["category"],
            pages,
        ),
        "auth": auth,
        "self_serve": access["status"],
        "self_serve_signals": access["signals"],
        "api": api,
        "mcp": mcp,
        "evidence": unique_evidence,
        "confidence": confidence,
        "needs_human_review": needs_review,
        "pages_researched": len(pages),
    }


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    print("=" * 70)
    print("STARTING EVIDENCE RESEARCH")
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

    results = []
    errors = 0

    for index, record in enumerate(records, start=1):
        print()
        print(f"[{index}/100] {record['app']}")

        try:
            result = research_app(record)
            results.append(result)

            print(f"    Auth: {result['auth'] or 'unknown'}")
            print(
                f"    API: {result['api']['available']} "
                f"{result['api']['types']}"
            )
            print(f"    Access: {result['self_serve']}")
            print(f"    MCP: {result['mcp']}")
            print(f"    Confidence: {result['confidence']}")
            print(
                f"    Review: "
                f"{result['needs_human_review']}"
            )

        except Exception as exc:
            errors += 1

            print(f"    ERROR: {exc}")

            results.append({
                "id": record.get("id"),
                "app": record.get("app"),
                "category": record.get("category"),
                "website": record.get("website"),
                "description": (
                    f"{record.get('app', 'Unknown')} software platform."
                ),
                "auth": [],
                "self_serve": "unknown",
                "self_serve_signals": [],
                "api": {
                    "available": "unknown",
                    "types": [],
                    "breadth": "unknown",
                    "additional_capabilities": [],
                },
                "mcp": "unknown",
                "evidence": [],
                "confidence": 0.0,
                "needs_human_review": True,
                "error": str(exc),
                "pages_researched": 0,
            })

        time.sleep(REQUEST_DELAY)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 70)
    print("EVIDENCE RESEARCH COMPLETE")
    print("=" * 70)
    print(f"Records researched: {len(results)}")
    print(f"Errors: {errors}")
    print(f"Saved: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()