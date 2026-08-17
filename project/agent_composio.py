import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from composio import Composio


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

API_KEY = os.getenv("COMPOSIO_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "COMPOSIO_API_KEY not found in .env"
    )

INPUT_FILE = "data/apps.csv"
OUTPUT_FILE = "data/composio_results.json"

client = Composio(api_key=API_KEY)


# ============================================================
# SESSION
# ============================================================

def create_session():

    print("=" * 70)
    print("CREATING COMPOSIO SESSION")
    print("=" * 70)

    session = client.sessions.create(
        user_id="api-scout-research",
        mcp=True
    )

    print("Session created successfully.")
    print("Session ID:", session.session_id)
    print("MCP URL:", session.mcp.url)

    return session


# ============================================================
# NAME NORMALIZATION
# ============================================================

def normalize_name(value):

    if not value:
        return ""

    value = str(value).lower()

    for char in [
        " ",
        "-",
        "_",
        ".",
        "(",
        ")",
        "/",
        ":"
    ]:
        value = value.replace(char, "")

    return value


# ============================================================
# KNOWN TOOLKIT ALIASES
# ============================================================

ALIASES = {

    "salesforce": [
        "salesforce"
    ],

    "hubspot": [
        "hubspot",
        "hubspotcrm"
    ],

    "pipedrive": [
        "pipedrive"
    ],

    "attio": [
        "attio"
    ],

    "twenty": [
        "twenty"
    ],

    "podio": [
        "podio"
    ],

    "zoho crm": [
        "zoho",
        "zohocrm"
    ],

    "close": [
        "close"
    ],

    "copper": [
        "copper"
    ],

    "dealcloud": [
        "dealcloud"
    ],

    "zendesk": [
        "zendesk"
    ],

    "intercom": [
        "intercom"
    ],

    "freshdesk": [
        "freshdesk"
    ],

    "front": [
        "front"
    ],

    "pylon": [
        "pylon"
    ],

    "liveagent": [
        "liveagent"
    ],

    "plain": [
        "plain"
    ],

    "help scout": [
        "helpscout"
    ],

    "gorgias": [
        "gorgias"
    ],

    "gladly": [
        "gladly"
    ],

    "slack": [
        "slack"
    ],

    "twilio": [
        "twilio"
    ],

    "zoho cliq": [
        "zoho",
        "zohocliq"
    ],

    "lark": [
        "lark",
        "larksuite"
    ],

    "pumble": [
        "pumble"
    ],

    "discord": [
        "discord"
    ],

    "telegram": [
        "telegram"
    ],

    "whatsapp business": [
        "whatsapp"
    ],

    "aircall": [
        "aircall"
    ],

    "vonage": [
        "vonage"
    ],

    "google ads": [
        "googleads"
    ],

    "meta ads": [
        "metaads",
        "facebookads"
    ],

    "linkedin ads": [
        "linkedinads",
        "linkedin"
    ],

    "gohighlevel": [
        "gohighlevel"
    ],

    "mailchimp": [
        "mailchimp"
    ],

    "klaviyo": [
        "klaviyo"
    ],

    "systeme.io": [
        "systeme"
    ],

    "pinterest": [
        "pinterest"
    ],

    "threads": [
        "threads"
    ],

    "sendgrid": [
        "sendgrid"
    ],

    "shopify": [
        "shopify"
    ],

    "woocommerce": [
        "woocommerce"
    ],

    "bigcommerce": [
        "bigcommerce"
    ],

    "salesforce commerce cloud": [
        "salesforcecommercecloud",
        "commercecloud"
    ],

    "magento adobe commerce": [
        "magento",
        "adobecommerce"
    ],

    "squarespace": [
        "squarespace"
    ],

    "ecwid": [
        "ecwid"
    ],

    "gumroad": [
        "gumroad"
    ],

    "amazon selling partner": [
        "amazonspapi",
        "amazonsellingpartner",
        "amazon"
    ],

    "fanbasis": [
        "fanbasis"
    ],

    "dataforseo": [
        "dataforseo"
    ],

    "se ranking": [
        "seranking"
    ],

    "ahrefs": [
        "ahrefs"
    ],

    "mrscraper": [
        "mrscraper"
    ],

    "apify": [
        "apify"
    ],

    "firecrawl": [
        "firecrawl"
    ],

    "bright data": [
        "brightdata"
    ],

    "sherlock": [
        "sherlock"
    ],

    "waterfall.io": [
        "waterfall"
    ],

    "clay": [
        "clay"
    ],

    "github": [
        "github"
    ],

    "vercel": [
        "vercel"
    ],

    "netlify": [
        "netlify"
    ],

    "cloudflare": [
        "cloudflare"
    ],

    "supabase": [
        "supabase"
    ],

    "neo4j": [
        "neo4j"
    ],

    "snowflake": [
        "snowflake"
    ],

    "mongodb atlas": [
        "mongodb",
        "mongodbatlas"
    ],

    "datadog": [
        "datadog"
    ],

    "sentry": [
        "sentry"
    ],

    "notion": [
        "notion"
    ],

    "airtable": [
        "airtable"
    ],

    "linear": [
        "linear"
    ],

    "jira": [
        "jira"
    ],

    "asana": [
        "asana"
    ],

    "monday.com": [
        "monday",
        "mondaycom"
    ],

    "clickup": [
        "clickup"
    ],

    "coda": [
        "coda"
    ],

    "smartsheet": [
        "smartsheet"
    ],

    "harvest": [
        "harvest"
    ],

    "stripe": [
        "stripe"
    ],

    "plaid": [
        "plaid"
    ],

    "binance": [
        "binance"
    ],

    "paygent connect": [
        "paygent",
        "nmi"
    ],

    "ipayx": [
        "ipayx"
    ],

    "quickbooks": [
        "quickbooks",
        "quickbooks_online"
    ],

    "xero": [
        "xero"
    ],

    "brex": [
        "brex"
    ],

    "ramp": [
        "ramp"
    ],

    "pitchbook": [
        "pitchbook"
    ],

    "notebooklm": [
        "notebooklm"
    ],

    "otter ai": [
        "otter"
    ],

    "fathom": [
        "fathom"
    ],

    "consensus": [
        "consensus"
    ],

    "reducto": [
        "reducto"
    ],

    "devin": [
        "devin"
    ],

    "higgsfield": [
        "higgsfield"
    ],

    "mermaid cli": [
        "mermaid"
    ],

    "youtube transcript": [
        "youtubetranscript"
    ],

    "grain": [
        "grain"
    ]
}


# ============================================================
# TOOLKIT MATCHING
# ============================================================

def toolkit_matches_app(app, toolkit):

    app_key = normalize_name(app)
    toolkit_key = normalize_name(toolkit)

    aliases = ALIASES.get(
        app.lower(),
        []
    )

    normalized_aliases = [
        normalize_name(x)
        for x in aliases
    ]

    # Direct exact match
    if app_key == toolkit_key:
        return True

    # Alias match
    if toolkit_key in normalized_aliases:
        return True

    return False


# ============================================================
# TOOL BELONGS TO TOOLKIT
# ============================================================

def tool_belongs_to_toolkit(tool, toolkit):

    if not tool or not toolkit:
        return False

    tool_norm = normalize_name(tool)
    toolkit_norm = normalize_name(toolkit)

    aliases = [
        toolkit
    ]

    aliases.extend(
        ALIASES.get(
            toolkit.lower(),
            []
        )
    )

    aliases = [
        normalize_name(x)
        for x in aliases
    ]

    for alias in aliases:

        if not alias:
            continue

        # Most Composio tools look like:
        #
        # SALESFORCE_CREATE_CONTACT
        # CLOSE_CREATE_LEAD
        # STRIPE_CREATE_CUSTOMER
        #
        if (
            tool_norm.startswith(alias)
            or tool_norm.startswith(alias + "tool")
        ):
            return True

    return False


# ============================================================
# SEARCH
# ============================================================

def search_composio(
    session,
    app,
    category
):

    query = (
        f"{app} {category} "
        "API integration tools"
    )

    try:

        return session.search(
            query=query
        )

    except Exception as e:

        print(
            f"    Search error: {e}"
        )

        return None


# ============================================================
# EXTRACT RESULTS
# ============================================================

def extract_results(
    result,
    app
):

    output = {

        "coverage": "not_found",

        "matched_toolkits": [],

        "related_toolkits": [],

        "tools": [],

        "tool_count": 0,

        "connection_required": False
    }

    if result is None:
        return output

    all_toolkits = []
    all_tools = []

    try:

        for item in result.results:

            toolkits = getattr(
                item,
                "toolkits",
                None
            )

            if toolkits:

                for toolkit in toolkits:

                    if toolkit not in all_toolkits:

                        all_toolkits.append(
                            toolkit
                        )

            primary_tools = getattr(
                item,
                "primary_tool_slugs",
                None
            )

            if primary_tools:

                for tool in primary_tools:

                    if tool not in all_tools:

                        all_tools.append(
                            tool
                        )

            related_tools = getattr(
                item,
                "related_tool_slugs",
                None
            )

            if related_tools:

                for tool in related_tools:

                    if tool not in all_tools:

                        all_tools.append(
                            tool
                        )

    except Exception as e:

        print(
            f"    Parsing warning: {e}"
        )

    # ========================================================
    # CLASSIFY TOOLKITS
    # ========================================================

    matched = []
    related = []

    for toolkit in all_toolkits:

        if toolkit_matches_app(
            app,
            toolkit
        ):

            matched.append(
                toolkit
            )

        else:

            related.append(
                toolkit
            )

    # ========================================================
    # COVERAGE
    # ========================================================

    if matched:

        coverage = "confirmed"

        connection_required = True

    elif all_toolkits:

        coverage = "semantic_match_only"

        connection_required = False

    else:

        coverage = "not_found"

        connection_required = False

    # ========================================================
    # CRITICAL FIX:
    #
    # ONLY RETAIN TOOLS THAT BELONG TO THE ACTUAL
    # MATCHED TOOLKIT.
    # ========================================================

    app_tools = []

    for tool in all_tools:

        belongs = False

        for toolkit in matched:

            if tool_belongs_to_toolkit(
                tool,
                toolkit
            ):

                belongs = True
                break

        if belongs and tool not in app_tools:

            app_tools.append(
                tool
            )

    # ========================================================
    # IF WE HAVE A CONFIRMED TOOLKIT BUT NO PREFIX-MATCHED
    # TOOLS, KEEP ZERO RATHER THAN INCLUDING UNRELATED TOOLS.
    # THIS IS DELIBERATELY CONSERVATIVE.
    # ========================================================

    return {

        "coverage":
            coverage,

        "matched_toolkits":
            matched,

        "related_toolkits":
            related,

        "tools":
            app_tools,

        "tool_count":
            len(app_tools),

        "connection_required":
            connection_required
    }


# ============================================================
# RESEARCH ONE APP
# ============================================================

def research_app(
    session,
    row
):

    app = row["app"]

    category = row["category"]

    website = row["website"]

    print(
        f"\n[{row['id']}/100] {app}"
    )

    result = search_composio(
        session,
        app,
        category
    )

    composio_data = extract_results(
        result,
        app
    )

    print(
        f"    Coverage: "
        f"{composio_data['coverage']}"
    )

    print(
        f"    Matched toolkit(s): "
        f"{composio_data['matched_toolkits'] or 'none'}"
    )

    print(
        f"    Related toolkit(s): "
        f"{composio_data['related_toolkits'] or 'none'}"
    )

    print(
        f"    ACTUAL app tools: "
        f"{composio_data['tool_count']}"
    )

    return {

        "id":
            int(row["id"]),

        "app":
            app,

        "category":
            category,

        "website":
            website,

        "composio":
            composio_data
    }


# ============================================================
# MAIN
# ============================================================

def main():

    apps = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Loaded {len(apps)} apps."
    )

    if len(apps) != 100:

        raise ValueError(
            f"Expected 100 apps, "
            f"but found {len(apps)}"
        )

    session = create_session()

    results = []

    for _, row in apps.iterrows():

        try:

            result = research_app(
                session,
                row
            )

            results.append(
                result
            )

        except Exception as e:

            print(
                f"    FAILED: {e}"
            )

            results.append({

                "id":
                    int(row["id"]),

                "app":
                    row["app"],

                "category":
                    row["category"],

                "website":
                    row["website"],

                "composio": {

                    "coverage":
                        "error",

                    "matched_toolkits":
                        [],

                    "related_toolkits":
                        [],

                    "tools":
                        [],

                    "tool_count":
                        0,

                    "connection_required":
                        False
                },

                "error":
                    str(e)
            })

        time.sleep(0.5)

    # ========================================================
    # SAVE
    # ========================================================

    os.makedirs(
        "data",
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

    confirmed = sum(
        1
        for r in results
        if r["composio"]["coverage"]
        == "confirmed"
    )

    semantic = sum(
        1
        for r in results
        if r["composio"]["coverage"]
        == "semantic_match_only"
    )

    not_found = sum(
        1
        for r in results
        if r["composio"]["coverage"]
        == "not_found"
    )

    errors = sum(
        1
        for r in results
        if r["composio"]["coverage"]
        == "error"
    )

    total_tools = sum(
        r["composio"]["tool_count"]
        for r in results
    )

    print()
    print("=" * 70)
    print("COMPOSIO RESEARCH COMPLETE")
    print("=" * 70)

    print(
        f"Total apps: {len(results)}"
    )

    print(
        f"Confirmed direct coverage: {confirmed}"
    )

    print(
        f"Semantic matches only: {semantic}"
    )

    print(
        f"Not found: {not_found}"
    )

    print(
        f"Errors: {errors}"
    )

    print(
        f"Actual matched-app tools: {total_tools}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()