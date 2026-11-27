# Configured Sources 001 — 2026-11-25
<!-- harness-doc kind=seed status=in-force since=2026-11-25 applies-to=cycle-6 -->

Owner-directed 2026-11-25: add the missing configured-source component — a seed
of external sources carrying personality-domain information, importable as
ledger objects. Corpus anchors: E-ConfiguredSources, D-SourceRelevanceDomains,
D-SourceConfidenceCeilings, C-MultiSourceAccess, C-CredentialDescriptor;
GreyAvatar precedent: `sourceKey` → `{kind, descriptor}` (D64, D76, D86).

**The fenced JSON block below IS the import payload** — one representation, no
parallel table to drift. Reviewers read the same block the build imports.

## Object schema

| Field | Meaning |
|---|---|
| `key` | Stable source identifier (`source-*`) |
| `name` | Display name |
| `kind` | `mediawiki` (MediaWiki API path), `api` (structured REST/feed), `web` (fetch/search only) |
| `url` | Base endpoint |
| `api` | API endpoint where distinct from `url` (omitted otherwise) |
| `domains` | Knowledge-domain tags — the match key for persona source suggestion |
| `descriptor` | Access policy: `all_avatars` (open) or `granted_only` (persona assignment = grant row, GreyAvatar D64 pattern) |
| `ceiling` | Suggested confidence ceiling, per D-SourceConfidenceCeilings |

## Screening rules (owner-stated 2026-11-25)

- **Free and no login required** — every entry readable anonymously.
- **No AI-usage opt-out** — excluded by rule: paywalled or login-gated corpora,
  known AI-training opt-outs and licensing-gated APIs (e.g. Reddit, X/Twitter,
  Quora, NYT-class news publishers, Britannica premium).
- **Composition:** exactly 50 entries; **≤25 fanwikis**; required entries
  `source-simpsons`, `source-wookieepedia`, `source-memory-alpha` present.
- Independent wikis preferred where communities moved off Fandom
  (minecraft.wiki, fallout.wiki, zeldawiki.wiki); Fandom-hosted wikis included —
  Fandom publishes no AI-usage opt-out and content is CC-licensed.
- **Domain-LLM analogs** the owner cited resolve to free public endpoints:
  Heinlein library → `source-heinlein-society`; Pentagon → `source-armypubs`
  (public doctrine); Marxist → `source-marxists` (Marxists Internet Archive).
- **The rules are the app's admission contract, not just this list's basis**
  (owner ruling 2026-11-25): the screening above is authoring-time judgment;
  the app's **source-admission gate** (S-source-admission-gate) re-verifies
  free-tier readability, no-login, and no-AI-opt-out per source at
  import/configure time, records the result as an assertion, and quarantines
  failures with basis. Authoring-time screening means the 50 rows *should*
  pass — the gate means they *must*.

## Payload

```json
{
  "revision": "configured-sources-001 2026-11-25",
  "sources": [
    { "key": "source-simpsons", "name": "Simpsons Wiki", "kind": "mediawiki", "url": "https://simpsons.fandom.com", "api": "https://simpsons.fandom.com/api.php", "domains": ["simpsons", "television", "animation", "comedy"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-wookieepedia", "name": "Wookieepedia", "kind": "mediawiki", "url": "https://starwars.fandom.com", "api": "https://starwars.fandom.com/api.php", "domains": ["star-wars", "film", "space-opera", "canon-lore"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-memory-alpha", "name": "Memory Alpha", "kind": "mediawiki", "url": "https://memory-alpha.fandom.com", "api": "https://memory-alpha.fandom.com/api.php", "domains": ["star-trek", "television", "space-opera", "canon-lore"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-tardis", "name": "Tardis Wiki (Doctor Who)", "kind": "mediawiki", "url": "https://tardis.fandom.com", "api": "https://tardis.fandom.com/api.php", "domains": ["doctor-who", "television", "science-fiction", "time-travel"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-harry-potter", "name": "Harry Potter Wiki", "kind": "mediawiki", "url": "https://harrypotter.fandom.com", "api": "https://harrypotter.fandom.com/api.php", "domains": ["harry-potter", "fantasy", "literature", "film"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-marvel", "name": "Marvel Database", "kind": "mediawiki", "url": "https://marvel.fandom.com", "api": "https://marvel.fandom.com/api.php", "domains": ["marvel", "comics", "superheroes", "film"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-dc", "name": "DC Database", "kind": "mediawiki", "url": "https://dc.fandom.com", "api": "https://dc.fandom.com/api.php", "domains": ["dc", "comics", "superheroes", "film"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-tolkien-gateway", "name": "Tolkien Gateway", "kind": "mediawiki", "url": "https://tolkiengateway.net", "api": "https://tolkiengateway.net/w/api.php", "domains": ["tolkien", "middle-earth", "fantasy", "literature"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-halopedia", "name": "Halopedia", "kind": "mediawiki", "url": "https://www.halopedia.org", "api": "https://www.halopedia.org/api.php", "domains": ["halo", "games", "science-fiction"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-bulbapedia", "name": "Bulbapedia", "kind": "mediawiki", "url": "https://bulbapedia.bulbagarden.net", "api": "https://bulbapedia.bulbagarden.net/w/api.php", "domains": ["pokemon", "games", "anime"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-zelda", "name": "Zelda Wiki", "kind": "mediawiki", "url": "https://zeldawiki.wiki", "api": "https://zeldawiki.wiki/api.php", "domains": ["zelda", "games", "fantasy"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-mario", "name": "Super Mario Wiki", "kind": "mediawiki", "url": "https://www.mariowiki.com", "api": "https://www.mariowiki.com/api.php", "domains": ["mario", "games", "nintendo"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-minecraft", "name": "Minecraft Wiki", "kind": "mediawiki", "url": "https://minecraft.wiki", "api": "https://minecraft.wiki/api.php", "domains": ["minecraft", "games", "sandbox"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-fallout", "name": "Fallout Wiki", "kind": "mediawiki", "url": "https://fallout.wiki", "api": "https://fallout.wiki/api.php", "domains": ["fallout", "games", "post-apocalyptic"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-stargate", "name": "Stargate Wiki", "kind": "mediawiki", "url": "https://stargate.fandom.com", "api": "https://stargate.fandom.com/api.php", "domains": ["stargate", "television", "science-fiction"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-muppet", "name": "Muppet Wiki", "kind": "mediawiki", "url": "https://muppet.fandom.com", "api": "https://muppet.fandom.com/api.php", "domains": ["muppets", "television", "puppetry", "children"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-battlestar", "name": "Battlestar Wiki", "kind": "mediawiki", "url": "https://en.battlestarwiki.org", "api": "https://en.battlestarwiki.org/api.php", "domains": ["battlestar-galactica", "television", "space-opera"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-lostpedia", "name": "Lostpedia", "kind": "mediawiki", "url": "https://lostpedia.fandom.com", "api": "https://lostpedia.fandom.com/api.php", "domains": ["lost", "television", "mystery"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-forgotten-realms", "name": "Forgotten Realms Wiki", "kind": "mediawiki", "url": "https://forgottenrealms.fandom.com", "api": "https://forgottenrealms.fandom.com/api.php", "domains": ["dungeons-and-dragons", "forgotten-realms", "fantasy", "games"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-lexicanum", "name": "Warhammer 40,000 Lexicanum", "kind": "mediawiki", "url": "https://wh40k.lexicanum.com", "api": "https://wh40k.lexicanum.com/api.php", "domains": ["warhammer-40k", "tabletop", "science-fiction", "games"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-buffyverse", "name": "Buffyverse Wiki", "kind": "mediawiki", "url": "https://buffy.fandom.com", "api": "https://buffy.fandom.com/api.php", "domains": ["buffy", "television", "supernatural"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-avatar", "name": "Avatar: The Last Airbender Wiki", "kind": "mediawiki", "url": "https://avatar.fandom.com", "api": "https://avatar.fandom.com/api.php", "domains": ["avatar-the-last-airbender", "animation", "fantasy", "television"], "descriptor": "granted_only", "ceiling": 0.6 },
    { "key": "source-awoiaf", "name": "A Wiki of Ice and Fire", "kind": "mediawiki", "url": "https://awoiaf.westeros.org", "api": "https://awoiaf.westeros.org/api.php", "domains": ["a-song-of-ice-and-fire", "game-of-thrones", "fantasy", "literature"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-tvtropes", "name": "TV Tropes", "kind": "web", "url": "https://tvtropes.org", "domains": ["tropes", "narrative", "media-analysis", "television", "film", "literature"], "descriptor": "granted_only", "ceiling": 0.55 },
    { "key": "source-scp", "name": "SCP Foundation", "kind": "web", "url": "https://scp-wiki.wikidot.com", "domains": ["scp-foundation", "collaborative-fiction", "horror", "science-fiction"], "descriptor": "granted_only", "ceiling": 0.5 },

    { "key": "source-wikipedia", "name": "Wikipedia", "kind": "mediawiki", "url": "https://en.wikipedia.org", "api": "https://en.wikipedia.org/w/api.php", "domains": ["general-knowledge", "encyclopedia", "reference"], "descriptor": "all_avatars", "ceiling": 0.8 },
    { "key": "source-wikidata", "name": "Wikidata", "kind": "mediawiki", "url": "https://www.wikidata.org", "api": "https://www.wikidata.org/w/api.php", "domains": ["structured-data", "entities", "general-knowledge"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-wiktionary", "name": "Wiktionary", "kind": "mediawiki", "url": "https://en.wiktionary.org", "api": "https://en.wiktionary.org/w/api.php", "domains": ["dictionary", "language", "etymology"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-wikiquote", "name": "Wikiquote", "kind": "mediawiki", "url": "https://en.wikiquote.org", "api": "https://en.wikiquote.org/w/api.php", "domains": ["quotations", "speech", "literature"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-wikisource", "name": "Wikisource", "kind": "mediawiki", "url": "https://en.wikisource.org", "api": "https://en.wikisource.org/w/api.php", "domains": ["primary-texts", "literature", "historical-documents"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-wikibooks", "name": "Wikibooks", "kind": "mediawiki", "url": "https://en.wikibooks.org", "api": "https://en.wikibooks.org/w/api.php", "domains": ["textbooks", "instruction", "reference"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-wikivoyage", "name": "Wikivoyage", "kind": "mediawiki", "url": "https://en.wikivoyage.org", "api": "https://en.wikivoyage.org/w/api.php", "domains": ["travel", "geography", "practicalities"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-wikimedia-commons", "name": "Wikimedia Commons", "kind": "mediawiki", "url": "https://commons.wikimedia.org", "api": "https://commons.wikimedia.org/w/api.php", "domains": ["media", "images", "public-domain-media"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-gutenberg", "name": "Project Gutenberg", "kind": "web", "url": "https://www.gutenberg.org", "domains": ["literature", "public-domain-books", "classics"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-standard-ebooks", "name": "Standard Ebooks", "kind": "web", "url": "https://standardebooks.org", "api": "https://standardebooks.org/feeds/opds", "domains": ["literature", "public-domain-books", "edited-editions"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-open-library", "name": "Open Library", "kind": "api", "url": "https://openlibrary.org", "api": "https://openlibrary.org/search.json", "domains": ["books", "bibliography", "library-catalog"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-internet-archive", "name": "Internet Archive", "kind": "api", "url": "https://archive.org", "api": "https://archive.org/advancedsearch.php", "domains": ["digital-archive", "media", "historical-web", "texts"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-librivox", "name": "LibriVox", "kind": "api", "url": "https://librivox.org", "api": "https://librivox.org/api/feed/audiobooks", "domains": ["audiobooks", "public-domain", "spoken-word"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-sep", "name": "Stanford Encyclopedia of Philosophy", "kind": "web", "url": "https://plato.stanford.edu", "domains": ["philosophy", "reference", "academia"], "descriptor": "granted_only", "ceiling": 0.85 },
    { "key": "source-iep", "name": "Internet Encyclopedia of Philosophy", "kind": "web", "url": "https://iep.utm.edu", "domains": ["philosophy", "reference", "academia"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-marxists", "name": "Marxists Internet Archive", "kind": "web", "url": "https://www.marxists.org", "domains": ["marxism", "political-theory", "primary-texts", "history"], "descriptor": "granted_only", "ceiling": 0.75 },
    { "key": "source-heinlein-society", "name": "The Heinlein Society", "kind": "web", "url": "https://www.heinleinsociety.org", "domains": ["robert-heinlein", "science-fiction", "literature", "bibliography"], "descriptor": "granted_only", "ceiling": 0.65 },
    { "key": "source-armypubs", "name": "U.S. Army Publishing Directorate", "kind": "web", "url": "https://armypubs.army.mil", "domains": ["military-doctrine", "us-army", "regulations", "defense"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-ntrs", "name": "NASA Technical Reports Server", "kind": "api", "url": "https://ntrs.nasa.gov", "api": "https://ntrs.nasa.gov/api/citations/search", "domains": ["aerospace", "nasa", "technical-reports", "space"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-cia-factbook", "name": "CIA World Factbook", "kind": "web", "url": "https://www.cia.gov/the-world-factbook", "domains": ["geography", "geopolitics", "countries", "reference"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-loc", "name": "Library of Congress", "kind": "api", "url": "https://www.loc.gov", "api": "https://www.loc.gov/search/?fo=json", "domains": ["library-catalog", "americana", "historical-documents", "reference"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-arxiv", "name": "arXiv", "kind": "api", "url": "https://arxiv.org", "api": "https://export.arxiv.org/api/query", "domains": ["preprints", "physics", "mathematics", "computer-science", "research"], "descriptor": "granted_only", "ceiling": 0.7 },
    { "key": "source-pubmed", "name": "PubMed", "kind": "api", "url": "https://pubmed.ncbi.nlm.nih.gov", "api": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", "domains": ["medicine", "biomedical", "research", "abstracts"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-musicbrainz", "name": "MusicBrainz", "kind": "api", "url": "https://musicbrainz.org", "api": "https://musicbrainz.org/ws/2", "domains": ["music", "discography", "metadata"], "descriptor": "granted_only", "ceiling": 0.8 },
    { "key": "source-sacred-texts", "name": "Internet Sacred Text Archive", "kind": "web", "url": "https://sacred-texts.com", "domains": ["religion", "mythology", "sacred-texts", "primary-texts"], "descriptor": "granted_only", "ceiling": 0.7 }
  ]
}
```

## Composition audit

- **Fanwikis (25):** simpsons, wookieepedia, memory-alpha, tardis,
  harry-potter, marvel, dc, tolkien-gateway, halopedia, bulbapedia, zelda,
  mario, minecraft, fallout, stargate, muppet, battlestar, lostpedia,
  forgotten-realms, lexicanum, buffyverse, avatar, awoiaf, tvtropes, scp.
  (tvtropes + scp counted as fanwikis — community fiction/media wikis.)
- **General reference (25):** wikipedia, wikidata, wiktionary, wikiquote,
  wikisource, wikibooks, wikivoyage, wikimedia-commons, gutenberg,
  standard-ebooks, open-library, internet-archive, librivox, sep, iep,
  marxists, heinlein-society, armypubs, ntrs, cia-factbook, loc, arxiv,
  pubmed, musicbrainz, sacred-texts.
- **Kinds exercised:** `mediawiki` ×31, `api` ×8, `web` ×11.
- **Descriptors:** `all_avatars` ×1 (wikipedia, D86 precedent); `granted_only`
  ×49 — persona assignment at character creation is the grant row.
- **Not included, by rule:** paywall/login (Britannica premium, Quora, Medium
  partner content); AI-usage opt-outs / licensing-gated APIs (Reddit,
  X/Twitter, NYT-class); IMDb (API license), Discogs (token), Stack Overflow
  (licensing posture unsettled).
