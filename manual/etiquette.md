# How the Bayanat Labs crawler behaves

*Operating manual v1.0.1 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0 · Documentation, not legal advice.*

This page describes how Bayanat Labs fetches public material for its open Arabic datasets, and how site owners can limit or stop it. The Bayanat Labs crawler page (https://www.bayanatlabs.com/open/crawler) says the same. The rules our crawler follows are also checked at stage 2 of `manual/stages.yaml`.

## Who we are

| Item | Value |
|---|---|
| User-Agent | `BayanatLabs-OpenData/1.0 (+https://bayanatlabs.com/open; hello@bayanatlabs.com)` |
| robots.txt token | `BayanatLabs-OpenData` |
| Contact | `hello@bayanatlabs.com` |
| IP addresses | One stable, Bayanat Labs-owned address per worker. The list will be published here before the first crawl. |

We never spoof a browser User-Agent.

## How fast we fetch

- At most one request every 3 seconds to any host, one connection at a time.
- At most one request every 5 seconds to government portals, small sites and any host whose responses slow down.
- If your robots.txt sets a longer `Crawl-delay`, we use the longer delay.
- Documented APIs and dumps: we stay inside the published quota and never go faster than the limits above unless the founder has approved a documented exception in writing.
- Before any bulk run we probe 10 to 100 representative records, or the smallest file you offer.
- Downloads are resumable and checksummed, so we never fetch the same object twice by accident.

## Signals we read and obey

| Signal | What we do |
|---|---|
| robots.txt | We fetch and hash it at the start of every session and at least daily, and obey the rules for our token and for `*`. Robots.txt semantics follow RFC 9309 (https://www.rfc-editor.org/rfc/rfc9309.html). |
| Blocks on other AI crawlers | If your robots.txt blocks GPTBot, CCBot or Google-Extended, we read that as a statement of intent even though our token is not named. We then record only identifiers, URLs and metadata from your site, never the content. |
| TDMRep | We check `/.well-known/tdmrep.json`, the `tdm-reservation` HTTP header and the HTML meta tag (W3C TDMRep community report, https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240510/). If rights are reserved (`tdm-reservation: 1`) and we hold no licence, we record identifiers only. |
| Content-Signal | We read `Content-Signal:` lines in robots.txt (https://contentsignals.org/). If `ai-train=no`, your content stays out of every training-text and media release; we record identifiers only. |
| HTTP 429 and `Retry-After` | We stop requesting from your host, honour `Retry-After` and back off exponentially. After three 429 responses in a row we pause your host for 24 hours. We never retry from another IP. |
| 401, 403, login walls, CAPTCHAs, WAF challenges | We stop and log the denial. We do not retry with another IP, account, cookie or mirror. The source is marked as needing permission. |

## What we never do

- Solve a CAPTCHA, or bypass a login, paywall, bot check or web application firewall.
- Rotate proxies, IP addresses or accounts, or use residential proxies or VPN hopping.
- Use personal cookies or personal accounts.
- Route around a denial through a mirror, a cached copy or another account.
- Fetch from a source before its licence and terms have been read and filed.
- Republish whole terms pages; we quote only the short clause that shows a licence, with its URL and a hash.

## Special cases

- **Sites that block requests from outside Saudi Arabia.** We fetch them only from one in-Kingdom host that Bayanat Labs operates, with the same User-Agent and rate limits. We never use proxies, VPNs or unofficial mirrors. If that host is blocked too, we stop and ask the site owner for access.
- **Bulk downloads.** Where a site offers official dumps, we use them, one connection at a time, rather than its live API.
- **Data stored from an API.** We refresh or delete stored API data as each API's terms require, for example every 30 days where the terms say so, and we remove items that were deleted, made private or re-licensed.
- **Creative Commons uploads.** We screen content offered under a Creative Commons licence for licence laundering: a provenance review per uploader, fingerprint matches against known rights-holder material, and exclusion of uploaders who re-post mixed-licence material. We never use automatic captions as transcripts.

## What we log

Every fetched item gets a provenance record: source URL, retrieval time, HTTP status, robots.txt hash, TDMRep and Content-Signal values, licence evidence and a SHA-256 hash of the raw bytes. That lets us answer "where did this record come from?" in one query, and remove an item quickly when asked.

## How to opt out or ask for removal

| You want to | Do this | What happens |
|---|---|---|
| Stop us crawling your site | Add `User-agent: BayanatLabs-OpenData` with `Disallow: /` to robots.txt, or a TDMRep reservation, or `Content-Signal: ai-train=no` | We obey it from our next robots.txt check (at least daily) and record your site as IDs-only or excluded |
| Remove content already released | Email `hello@bayanatlabs.com` with the URL or item ID | We acknowledge within 2 business days, exclude the item from the next build at once and publish a corrected version within 30 days |
| Report personal data, child-safety or abuse material | Email `hello@bayanatlabs.com` | We stop serving the affected files within 24 hours |
| Platform request | Email `hello@bayanatlabs.com` | Affected rows or IDs are removed within 24 hours |

Opt-outs also go into a blocklist for future crawls and are passed to mirrors and partners bound by our terms.
