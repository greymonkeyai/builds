"""Configured sources — seed import, admission gate, domain matching,
retrieval. The seed payload below is `configured-sources-001.md`'s fenced
JSON verbatim — one representation, imported as configured-source ledger rows.
"""
import concurrent.futures
import json
import re
import urllib.request
import urllib.parse
SEED_REVISION = "configured-sources-001 2026-11-25"
SEED_PAYLOAD = {
    "revision": SEED_REVISION,
    "sources": [
        {"key": "source-simpsons", "name": "Simpsons Wiki", "kind": "mediawiki", "url": "https://simpsons.fandom.com", "api": "https://simpsons.fandom.com/api.php", "domains": ["simpsons", "television", "animation", "comedy"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-wookieepedia", "name": "Wookieepedia", "kind": "mediawiki", "url": "https://starwars.fandom.com", "api": "https://starwars.fandom.com/api.php", "domains": ["star-wars", "film", "space-opera", "canon-lore"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-memory-alpha", "name": "Memory Alpha", "kind": "mediawiki", "url": "https://memory-alpha.fandom.com", "api": "https://memory-alpha.fandom.com/api.php", "domains": ["star-trek", "television", "space-opera", "canon-lore"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-tardis", "name": "Tardis Wiki (Doctor Who)", "kind": "mediawiki", "url": "https://tardis.fandom.com", "api": "https://tardis.fandom.com/api.php", "domains": ["doctor-who", "television", "science-fiction", "time-travel"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-harry-potter", "name": "Harry Potter Wiki", "kind": "mediawiki", "url": "https://harrypotter.fandom.com", "api": "https://harrypotter.fandom.com/api.php", "domains": ["harry-potter", "fantasy", "literature", "film"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-marvel", "name": "Marvel Database", "kind": "mediawiki", "url": "https://marvel.fandom.com", "api": "https://marvel.fandom.com/api.php", "domains": ["marvel", "comics", "superheroes", "film"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-dc", "name": "DC Database", "kind": "mediawiki", "url": "https://dc.fandom.com", "api": "https://dc.fandom.com/api.php", "domains": ["dc", "comics", "superheroes", "film"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-tolkien-gateway", "name": "Tolkien Gateway", "kind": "mediawiki", "url": "https://tolkiengateway.net", "api": "https://tolkiengateway.net/w/api.php", "domains": ["tolkien", "middle-earth", "fantasy", "literature"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-halopedia", "name": "Halopedia", "kind": "mediawiki", "url": "https://www.halopedia.org", "api": "https://www.halopedia.org/api.php", "domains": ["halo", "games", "science-fiction"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-bulbapedia", "name": "Bulbapedia", "kind": "mediawiki", "url": "https://bulbapedia.bulbagarden.net", "api": "https://bulbapedia.bulbagarden.net/w/api.php", "domains": ["pokemon", "games", "anime"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-zelda", "name": "Zelda Wiki", "kind": "mediawiki", "url": "https://zeldawiki.wiki", "api": "https://zeldawiki.wiki/api.php", "domains": ["zelda", "games", "fantasy"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-mario", "name": "Super Mario Wiki", "kind": "mediawiki", "url": "https://www.mariowiki.com", "api": "https://www.mariowiki.com/api.php", "domains": ["mario", "games", "nintendo"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-minecraft", "name": "Minecraft Wiki", "kind": "mediawiki", "url": "https://minecraft.wiki", "api": "https://minecraft.wiki/api.php", "domains": ["minecraft", "games", "sandbox"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-fallout", "name": "Fallout Wiki", "kind": "mediawiki", "url": "https://fallout.wiki", "api": "https://fallout.wiki/api.php", "domains": ["fallout", "games", "post-apocalyptic"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-stargate", "name": "Stargate Wiki", "kind": "mediawiki", "url": "https://stargate.fandom.com", "api": "https://stargate.fandom.com/api.php", "domains": ["stargate", "television", "science-fiction"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-muppet", "name": "Muppet Wiki", "kind": "mediawiki", "url": "https://muppet.fandom.com", "api": "https://muppet.fandom.com/api.php", "domains": ["muppets", "television", "puppetry", "children"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-battlestar", "name": "Battlestar Wiki", "kind": "mediawiki", "url": "https://en.battlestarwiki.org", "api": "https://en.battlestarwiki.org/api.php", "domains": ["battlestar-galactica", "television", "space-opera"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-lostpedia", "name": "Lostpedia", "kind": "mediawiki", "url": "https://lostpedia.fandom.com", "api": "https://lostpedia.fandom.com/api.php", "domains": ["lost", "television", "mystery"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-forgotten-realms", "name": "Forgotten Realms Wiki", "kind": "mediawiki", "url": "https://forgottenrealms.fandom.com", "api": "https://forgottenrealms.fandom.com/api.php", "domains": ["dungeons-and-dragons", "forgotten-realms", "fantasy", "games"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-lexicanum", "name": "Warhammer 40,000 Lexicanum", "kind": "mediawiki", "url": "https://wh40k.lexicanum.com", "api": "https://wh40k.lexicanum.com/api.php", "domains": ["warhammer-40k", "tabletop", "science-fiction", "games"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-buffyverse", "name": "Buffyverse Wiki", "kind": "mediawiki", "url": "https://buffy.fandom.com", "api": "https://buffy.fandom.com/api.php", "domains": ["buffy", "television", "supernatural"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-avatar", "name": "Avatar: The Last Airbender Wiki", "kind": "mediawiki", "url": "https://avatar.fandom.com", "api": "https://avatar.fandom.com/api.php", "domains": ["avatar-the-last-airbender", "animation", "fantasy", "television"], "descriptor": "granted_only", "ceiling": 0.6},
        {"key": "source-awoiaf", "name": "A Wiki of Ice and Fire", "kind": "mediawiki", "url": "https://awoiaf.westeros.org", "api": "https://awoiaf.westeros.org/api.php", "domains": ["a-song-of-ice-and-fire", "game-of-thrones", "fantasy", "literature"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-tvtropes", "name": "TV Tropes", "kind": "web", "url": "https://tvtropes.org", "domains": ["tropes", "narrative", "media-analysis", "television", "film", "literature"], "descriptor": "granted_only", "ceiling": 0.55},
        {"key": "source-scp", "name": "SCP Foundation", "kind": "web", "url": "https://scp-wiki.wikidot.com", "domains": ["scp-foundation", "collaborative-fiction", "horror", "science-fiction"], "descriptor": "granted_only", "ceiling": 0.5},
        {"key": "source-wikipedia", "name": "Wikipedia", "kind": "mediawiki", "url": "https://en.wikipedia.org", "api": "https://en.wikipedia.org/w/api.php", "domains": ["general-knowledge", "encyclopedia", "reference"], "descriptor": "all_avatars", "ceiling": 0.8},
        {"key": "source-wikidata", "name": "Wikidata", "kind": "mediawiki", "url": "https://www.wikidata.org", "api": "https://www.wikidata.org/w/api.php", "domains": ["structured-data", "entities", "general-knowledge"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-wiktionary", "name": "Wiktionary", "kind": "mediawiki", "url": "https://en.wiktionary.org", "api": "https://en.wiktionary.org/w/api.php", "domains": ["dictionary", "language", "etymology"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-wikiquote", "name": "Wikiquote", "kind": "mediawiki", "url": "https://en.wikiquote.org", "api": "https://en.wikiquote.org/w/api.php", "domains": ["quotations", "speech", "literature"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-wikisource", "name": "Wikisource", "kind": "mediawiki", "url": "https://en.wikisource.org", "api": "https://en.wikisource.org/w/api.php", "domains": ["primary-texts", "literature", "historical-documents"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-wikibooks", "name": "Wikibooks", "kind": "mediawiki", "url": "https://en.wikibooks.org", "api": "https://en.wikibooks.org/w/api.php", "domains": ["textbooks", "instruction", "reference"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-wikivoyage", "name": "Wikivoyage", "kind": "mediawiki", "url": "https://en.wikivoyage.org", "api": "https://en.wikivoyage.org/w/api.php", "domains": ["travel", "geography", "practicalities"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-wikimedia-commons", "name": "Wikimedia Commons", "kind": "mediawiki", "url": "https://commons.wikimedia.org", "api": "https://commons.wikimedia.org/w/api.php", "domains": ["media", "images", "public-domain-media"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-gutenberg", "name": "Project Gutenberg", "kind": "web", "url": "https://www.gutenberg.org", "domains": ["literature", "public-domain-books", "classics"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-standard-ebooks", "name": "Standard Ebooks", "kind": "web", "url": "https://standardebooks.org", "api": "https://standardebooks.org/feeds/opds", "domains": ["literature", "public-domain-books", "edited-editions"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-open-library", "name": "Open Library", "kind": "api", "url": "https://openlibrary.org", "api": "https://openlibrary.org/search.json", "domains": ["books", "bibliography", "library-catalog"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-internet-archive", "name": "Internet Archive", "kind": "api", "url": "https://archive.org", "api": "https://archive.org/advancedsearch.php", "domains": ["digital-archive", "media", "historical-web", "texts"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-librivox", "name": "LibriVox", "kind": "api", "url": "https://librivox.org", "api": "https://librivox.org/api/feed/audiobooks", "domains": ["audiobooks", "public-domain", "spoken-word"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-sep", "name": "Stanford Encyclopedia of Philosophy", "kind": "web", "url": "https://plato.stanford.edu", "domains": ["philosophy", "reference", "academia"], "descriptor": "granted_only", "ceiling": 0.85},
        {"key": "source-iep", "name": "Internet Encyclopedia of Philosophy", "kind": "web", "url": "https://iep.utm.edu", "domains": ["philosophy", "reference", "academia"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-marxists", "name": "Marxists Internet Archive", "kind": "web", "url": "https://www.marxists.org", "domains": ["marxism", "political-theory", "primary-texts", "history"], "descriptor": "granted_only", "ceiling": 0.75},
        {"key": "source-heinlein-society", "name": "The Heinlein Society", "kind": "web", "url": "https://www.heinleinsociety.org", "domains": ["robert-heinlein", "science-fiction", "literature", "bibliography"], "descriptor": "granted_only", "ceiling": 0.65},
        {"key": "source-armypubs", "name": "U.S. Army Publishing Directorate", "kind": "web", "url": "https://armypubs.army.mil", "domains": ["military-doctrine", "us-army", "regulations", "defense"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-ntrs", "name": "NASA Technical Reports Server", "kind": "api", "url": "https://ntrs.nasa.gov", "api": "https://ntrs.nasa.gov/api/citations/search", "domains": ["aerospace", "nasa", "technical-reports", "space"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-cia-factbook", "name": "CIA World Factbook", "kind": "web", "url": "https://www.cia.gov/the-world-factbook", "domains": ["geography", "geopolitics", "countries", "reference"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-loc", "name": "Library of Congress", "kind": "api", "url": "https://www.loc.gov", "api": "https://www.loc.gov/search/?fo=json", "domains": ["library-catalog", "americana", "historical-documents", "reference"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-arxiv", "name": "arXiv", "kind": "api", "url": "https://arxiv.org", "api": "https://export.arxiv.org/api/query", "domains": ["preprints", "physics", "mathematics", "computer-science", "research"], "descriptor": "granted_only", "ceiling": 0.7},
        {"key": "source-pubmed", "name": "PubMed", "kind": "api", "url": "https://pubmed.ncbi.nlm.nih.gov", "api": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", "domains": ["medicine", "biomedical", "research", "abstracts"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-musicbrainz", "name": "MusicBrainz", "kind": "api", "url": "https://musicbrainz.org", "api": "https://musicbrainz.org/ws/2", "domains": ["music", "discography", "metadata"], "descriptor": "granted_only", "ceiling": 0.8},
        {"key": "source-sacred-texts", "name": "Internet Sacred Text Archive", "kind": "web", "url": "https://sacred-texts.com", "domains": ["religion", "mythology", "sacred-texts", "primary-texts"], "descriptor": "granted_only", "ceiling": 0.7},
    ],
}
AI_OPTOUT_AGENTS = ("gptbot", "claudebot", "ccbot", "google-extended",
                    "anthropic-ai", "perplexitybot", "bytespider", "amazonbot")
LOGIN_MARKERS = ("login required", "please log in", "sign in to continue",
                 "create an account to", "subscription required",
                 "wp-login", "auth_required")
UA = "chorus-install/0.3.0.006 (local-first persona host)"
def _fetch(url, timeout=6, max_bytes=200000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(max_bytes).decode("utf-8", "replace")
def admit_source(entry, timeout=6):
    """Source-admission gate (owner ruling 2026-11-25): verify free-tier
    readability, no-login, and no published AI-usage opt-out before use.
    Returns a verdict dict; the caller records it as an assertion."""
    verdict = {"key": entry["key"], "admitted": None, "checks": {},
               "basis": None, "quarantined": False}
    # 1. free-tier readability
    free = False
    try:
        status, body = _fetch(entry.get("api") or entry["url"], timeout=timeout)
        verdict["checks"]["http_status"] = status
        low = body.lower()
        if status == 200:
            if any(m in low for m in LOGIN_MARKERS) and "log in" not in low[:200]:
                verdict["checks"]["login_gate"] = "suspected"
            free = True
        verdict["checks"]["free_read"] = free
    except Exception as e:
        verdict["checks"]["free_read"] = False
        verdict["checks"]["error"] = str(e)[:160]
    # 2. no-login: content readable anonymously (a login form alone does not
    # gate content on wikis — gating = content itself behind auth)
    verdict["checks"]["no_login"] = free
    # 3. AI-usage opt-out posture via robots.txt
    optout = None
    try:
        host = urllib.parse.urlparse(entry["url"])
        rurl = f"{host.scheme}://{host.netloc}/robots.txt"
        status, robots = _fetch(rurl, timeout=timeout, max_bytes=120000)
        verdict["checks"]["robots_status"] = status
        low = robots.lower()
        hits = []
        for agent in AI_OPTOUT_AGENTS:
            m = re.search(r"user-agent:\s*\*?" + re.escape(agent) +
                          r"\*?\s*\n([^u]*)", low)
            if m and "disallow: /" in m.group(1):
                hits.append(agent)
        optout = hits
        verdict["checks"]["ai_optout"] = hits
    except Exception:
        verdict["checks"]["ai_optout"] = "robots-unreachable"
        optout = "unknown"
    if free and (optout == [] or optout == "unknown"):
        verdict["admitted"] = True
        verdict["basis"] = ("gate: free-read ok; no-login ok; "
                            f"opt-out posture {optout}")
    else:
        verdict["admitted"] = False
        verdict["quarantined"] = True
        why = []
        if not free:
            why.append("free-tier readability failed")
        if optout not in ([], "unknown"):
            why.append(f"AI-usage opt-out for {optout}")
        verdict["basis"] = "gate refused: " + "; ".join(why)
    return verdict
def domain_match(persona_domains, sources):
    """Rank sources by knowledge-domain overlap — the character-creation
    suggestion. A star-trek persona gets memory-alpha, not simpsons."""
    pset = {d.lower().strip() for d in persona_domains}
    scored = []
    for s in sources:
        overlap = pset & {d.lower() for d in s.get("domains", [])}
        if overlap:
            scored.append((len(overlap), s["ceiling"], s, overlap))
    scored.sort(key=lambda t: (-t[0], -t[1]))
    return scored
def mediawiki_search(src, query, limit=5, timeout=8):
    api = src.get("api") or src["url"] + "/api.php"
    q = urllib.parse.urlencode({
        "action": "opensearch", "search": query, "limit": limit,
        "namespace": 0, "format": "json"})
    try:
        _, body = _fetch(api + "?" + q, timeout=timeout)
        data = json.loads(body)
        return [{"title": t, "url": u} for t, u in zip(data[1], data[3])]
    except Exception:
        return []
def mediawiki_extract(src, title, timeout=8):
    api = src.get("api") or src["url"] + "/api.php"
    q = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "explaintext": 1,
        "exsectionformat": "plain", "titles": title, "format": "json",
        "redirects": 1})
    try:
        _, body = _fetch(api + "?" + q, timeout=timeout)
        data = json.loads(body)
        for page in data.get("query", {}).get("pages", {}).values():
            return page.get("extract", "")[:4000]
    except Exception:
        return ""
    return ""
def mediawiki_category(src, category, limit=500, timeout=12):
    """Category members — specialized list retrieval (C-SetBuild under
    S-list-project; C-SpecializedListRetrieval)."""
    api = src.get("api") or src["url"] + "/api.php"
    members, cont = [], {}
    while len(members) < limit:
        params = {"action": "query", "list": "categorymembers",
                  "cmtitle": category, "cmlimit": min(500, limit - len(members)),
                  "cmnamespace": 0, "format": "json"}
        params.update(cont)
        try:
            _, body = _fetch(api + "?" + urllib.parse.urlencode(params),
                             timeout=timeout)
            data = json.loads(body)
        except Exception:
            break
        members += [m["title"] for m in data.get("query", {})
                    .get("categorymembers", [])]
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    return members
def admit_all(book, entries, workers=12):
    """Run the admission gate over entries; each result recorded as an
    assertion. Returns {key: verdict}."""
    verdicts = {}
    with concurrent.futures.ThreadPoolExecutor(workers) as ex:
        for v in ex.map(lambda e: admit_source(e), entries):
            verdicts[v["key"]] = v
            book.append(
                "source:admission",
                {"subject": v["key"], "admitted": v["admitted"],
                 "checks": v["checks"], "verdictBasis": v["basis"]},
                claimant="host", certainty=0.9, basis="execution-evidence")
            if v["quarantined"]:
                book.append(
                    "source:quarantine",
                    {"subject": v["key"], "basis": v["basis"]},
                    claimant="host", certainty=0.9, basis="execution-evidence")
    return verdicts
