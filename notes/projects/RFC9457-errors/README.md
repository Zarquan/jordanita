# DAL error-handling thread, reconstructed

Reconstruction of the IVOA `dal` mailing-list conversation about error
messages, starting from Markus Demleitner's 2026-09-30 message
[Text error messages](http://mail.ivoa.net/pipermail/dal/2026-September/008922.html).

## Result

* **12 messages**, dated **2026-06-18** to **2026-10-01**.
* Thread root: [008883](http://mail.ivoa.net/pipermail/dal/2026-June/008883.html)
  `SCS2: Non-VOTable errors?` (Markus Demleitner). It has no
  `In-Reply-To` and no `References`, so this is the start of the
  conversation. Its body points to the earlier
  [SCS2 working draft](http://mail.ivoa.net/pipermail/dal/2026-June/008878.html)
  and to Stelios' GitHub issue, but those are not mail-header parents.
* Anchor: [008922](http://mail.ivoa.net/pipermail/dal/2026-September/008922.html)
  `Text error messages` (Markus Demleitner).
* Stop conditions: the start of the thread was reached; 12 is below
  the 100-message limit; the earliest message is from 2026, so the
  "earlier than 2024" limit did not apply.
* Every `References`/`In-Reply-To` identifier in the thread resolves
  inside the downloaded 2024-2026 archives. There are no dangling
  references to fetch.

## Thread structure

```
[01] 2026-06-18  Markus Demleitner   SCS2: Non-VOTable errors?
  [02] 2026-06-18  Patrick Dowler    SCS2: Non-VOTable errors?
  [03] 2026-06-18  Stelios Voutsinas SCS2: Non-VOTable errors?
    [04] 2026-06-19  Markus Demleitner   SCS2: Non-VOTable errors?
      [05] 2026-06-21  James Tocknell    SCS2: Non-VOTable errors?
        [06] 2026-06-30  Markus Demleitner   SCS2: Text error messages; New: VERB
          [07] 2026-06-30  Dave Morris        Text error messages
            [08] 2026-07-01  Markus Demleitner   Text error messages
              [10] 2026-07-09  Mark Taylor        Text error messages
                [11] 2026-09-30  Markus Demleitner   Text error messages
          [09] 2026-07-08  Mark Taylor        SCS2: Text error messages; New: VERB
            [12] 2026-10-01  Gregory Mantelet   SCS2: Text error messages; New: VERB
```

Message 11 is the anchor; messages 09 and 12 are the VERB side-thread.

Following the back references strictly from the anchor gives the
9-message ancestor chain 11 -> 10 -> 08 -> 07 -> 06 -> 05 -> 04 -> 03
-> 01. Messages 02 (Patrick), 09 (Mark on VERB) and 12 (Gregory's reply
to 09) belong to the same thread but are not ancestors of the anchor;
they are included so that the transcript covers the whole conversation.

## Timeline

| # | Date | From | Contribution |
|---|------|------|--------------|
| 01 | 2026-06-18 | Markus Demleitner | Raises Stelios' feedback that mandatory VOTable errors fight modern frameworks. Wants one reliable way for clients to get a display string; notes client error paths are under-tested and validators need something checkable. Open to Datalink-style text. |
| 02 | 2026-06-18 | Patrick Dowler | "Errors in VOTable" were a bad idea. Proposes `text/plain` with `{vocab term}: {human-readable explanation}` (as used in VOSpace); offers to draft a DALI change. |
| 03 | 2026-06-18 | Stelios Voutsinas | Distinguishes what the spec *specifies* from what it *tolerates*. Status code is the authoritative machine-readable signal; body is advisory. A FastAPI 422 with JSON should not count as broken. Cites ~200 lines of SIA error-handling code. |
| 04 | 2026-06-19 | Markus Demleitner | Restricts the problem to errors a working service can control. Insists on specific, readable diagnostics and validatable machine-readable prefixes. Converges on Pat's text/plain model plus free text; suggests QUERY_STATUS `ERROR` becomes legacy. |
| 05 | 2026-06-21 | James Tocknell | Proposes RFC 9457 (`application/problem+json`) and points to `fastapi-problem`. |
| 06 | 2026-06-30 | Markus Demleitner | Skeptical of RFC 9457: it offers choices rather than one form, adds a dependency, and is overkill for "give clients a string". Prefers Pat's DALI text. Moves on to the VERB item and suggests leaving VERB alone. |
| 07 | 2026-06-30 | Dave Morris | "Challenge accepted": champions RFC 9457, citing Spring, Quarkus, Swagger/OpenAPI, and Cloudflare implementations. |
| 08 | 2026-07-01 | Markus Demleitner | Asks what RFC 9457 enables that SODA/Datalink errors do not; notes DALI already has two mechanisms (VOTable `QUERY_STATUS`, SODA text). Skeptical of "growing ecosystem" arguments for a 20-year standard. |
| 09 | 2026-07-08 | Mark Taylor | +1 on leaving VERB as a non-binding hint. |
| 10 | 2026-07-09 | Mark Taylor | Agrees VOTable errors are burdensome. As a client writer he wants human-readable text; RFC 9457's `type`-driven client actions have no obvious VO use (IANA registry types are not useful, VO types would have to be invented). Asks what client behaviour RFC 9457 is meant to trigger. |
| 11 | 2026-09-30 | Markus Demleitner | **Anchor.** Reports a draft of the text-error change in SCS2 commit `8e366ae` (part of [PR #11](https://github.com/ivoa-std/SCS2/pull/11)) and asks for review. |
| 12 | 2026-10-01 | Gregory Mantelet | +1 on keeping VERB, citing Simbad/VizieR/Gaia experience; VERB=2 default limits columns and protects databases. |

## Where the argument landed

**On VOTable error documents.** Patrick and Mark agree that requiring
VOTable-formatted error bodies should go; Markus moves from agreement to
drafting the change. Stelios supplies the implementation-cost argument
and the framing that the HTTP status code, not the body, is the
machine-readable signal.

**On the replacement.** The emerging consensus is Patrick's
`text/plain` model: a controlled-vocabulary term, a colon, and a
human-readable explanation, plus optional free text. Markus wants the
prefix to be specific enough for validators; Stelios and Mark want the
body to stay advisory for clients. No one argues that plain text is
unworkable; Dave's objection is that RFC 9457 should be evaluated
first.

**On RFC 9457.** James proposes it and Dave champions it, citing
existing framework support. Markus and Mark push back: RFC 9457 allows
JSON and XML forms and extension members rather than prescribing one
shape, adds a dependency, and its `type`-based client actions have no
demonstrated VO use case. The thread does not resolve this; Markus
proceeds with the plain-text approach in SCS2 and asks for review
instead.

**On VERB.** The side-thread agrees to keep VERB as a non-binding
hint rather than impose hard per-level column requirements.

## RFC 9457: arguments recorded in the thread

| For | Against |
|-----|---------|
| Existing RFC with implementations in Spring, Quarkus, Swagger/OpenAPI and Cloudflare (Dave). | RFC 9457 allows JSON and XML forms and extension members rather than prescribing one shape ("you can do it like this or like this") (Markus). |
| Libraries exist, e.g. `fastapi-problem` (James). | Adds a library/dependency to every implementation; XML and JSON variants add complexity (Markus). |
| Structured and flexible enough for the range of VO errors (Dave). | DALI already has two mechanisms (VOTable `QUERY_STATUS`, SODA/Datalink text); a third needs a demonstrated benefit (Markus). |
| Grows the ecosystem around producing/consuming problem details (Dave). | No client behaviour in the thread actually keys off `type`; the IANA problem-type registry has nothing useful for VO (Mark). |
| Could be evaluated before inventing another wheel (Dave). | "Growing" is a poor argument for technology expected to last 20 years (Markus). |

## Related discussions in the same archive

These are about the same subject area but are **not** connected to the
2026 thread by `References`/`In-Reply-To`, so they are not part of the
12-message reconstruction:

* [Thoughts on standardizing TAP timeout/error handling](http://mail.ivoa.net/pipermail/dal/2025-July/008816.html)
  (2025-07-16 to 2025-07-24, 6 messages; Stelios Voutsinas, Markus
  Demleitner, Gregory Mantelet, Mark Taylor, Tamara Civera, Theresa
  Dower).
* [TAP 1.0/1.1 inconsistency: error document format](http://mail.ivoa.net/pipermail/dal/2025-September/008830.html)
  (2025-09-15 to 2025-10-10, 11 messages; Mark Taylor, Patrick Dowler,
  Gregory Mantelet, Gregory Dubois-Felsmann). This is the earlier
  VOTable-versus-plain-text argument for TAP/UWS error documents.

## Files

| Path | Contents |
|------|----------|
| [dal-error-thread.txt](dal-error-thread.txt) | Chronological transcript of the 12 messages, with headers, archive URLs and full bodies. |
| [dal-error-thread.json](dal-error-thread.json) | Machine-readable index: sequence, date, from, subject, Message-ID, parent, children, references, URL, local file. |
| `mail/thread/01.txt` … `12.txt` | One file per message, as extracted from the archives. |
| [mail/gz/](mail/gz/) | The 25 monthly gzipped pipermail archives for 2024-2026. |
| [mail/txt/](mail/txt/) | Decompressed mbox files. |
| [mail/pipermail-urls.tsv](mail/pipermail-urls.tsv) | Message-ID to pipermail URL map for the thread. |
| [mail/SOURCES.txt](mail/SOURCES.txt) | Download URLs, sizes and SHA-256 checksums. |
| [reconstruct.py](reconstruct.py) | Script that rebuilds the transcript and index from `mail/txt/`. |
| [20261024-01-RFC9457-errors.txt](20261024-01-RFC9457-errors.txt) | Session note. |

## Method

1. Downloaded every monthly `*.txt.gz` for 2024, 2025 and 2026 that
   exists in the archive (25 months; months with no messages return
   404 and are not present). See `mail/SOURCES.txt`.
2. Parsed the decompressed mboxes with Python's `mailbox` module and
   de-duplicated by `Message-ID` (some months contain duplicate copies).
3. Built an undirected graph from `In-Reply-To` and `References`
   headers, and walked the connected component containing the anchor
   `008922`.
4. Stopped at the thread root (no references), at 100 messages, or at
   2024-01-01, whichever came first.
5. Emitted the chronological transcript and JSON index.

To rebuild:

```bash
cd notes/projects/RFC9457-errors
./reconstruct.py
```

## Caveats

* The pipermail archive replaces non-ASCII bytes with `?` in some
  messages (for example "Gr?gory"), and obfuscates addresses as
  `user at host`. The transcript preserves what the archive contains.
* Message bodies include the quoted text from earlier messages, so the
  transcript repeats material. This is intentional: it keeps each
  message self-contained and lets inline replies be read in context.
* Thread membership is inferred only from the mail headers. A reply
  that dropped `In-Reply-To`/`References` or changed subject would not
  be found this way.
* The archive snapshot was downloaded on 2026-10-24; the pipermail
  index was last modified 2026-10-15.
* Message text remains copyright of the original authors and is
  included here for archival and analysis.
