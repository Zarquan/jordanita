#!/usr/bin/env python3
#
# <meta:header>
#   <meta:licence>
#     Copyright (c) 2026, University of Manchester (http://www.manchester.ac.uk/)
#
#     This information is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This information is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this software. If not, see <http://www.gnu.org/licenses/>.
#   </meta:licence>
# </meta:header>
#
"""Reconstruct a mailing-list conversation from downloaded pipermail mboxes.

The conversation is found by following the Message-ID / In-Reply-To /
References headers.  Traversal stops when there are no further connected
messages, when ``--max`` messages have been collected, or when the next
message is older than ``--min-date``.

Usage:
    ./reconstruct.py --anchor '<message-id>'

Inputs:
    mail/txt/*.txt          decompressed pipermail month archives (mbox)
    mail/pipermail-urls.tsv optional Message-ID <TAB> URL map

Outputs:
    dal-error-thread.json   machine-readable index of the thread
    dal-error-thread.txt    chronological transcript
"""

import argparse
import datetime as dt
import glob
import html
import json
import mailbox
import os
import re
import sys
from collections import defaultdict, deque
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

DEFAULT_ANCHOR = "<ertxjvatbqn3vmk2o36ayf4qa3yvasuvofsre65popkhdrhuni@qzamffkomv7m>"
DEFAULT_MIN_DATE = "2024-01-01"
DEFAULT_MAX = 100


def decode_header_value(value):
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)


def message_body(message):
    """Return the text/plain body, decoded as UTF-8 with replacement."""
    if message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload is not None:
                    parts.append(payload.decode("utf-8", "replace"))
        return "\n".join(parts)
    payload = message.get_payload(decode=True)
    if payload is None:
        return str(message.get_payload())
    return payload.decode("utf-8", "replace")


def parse_messages(maildir):
    messages = {}
    sources = {}
    for path in sorted(glob.glob(os.path.join(maildir, "*.txt"))):
        for message in mailbox.mbox(path):
            mid = (message.get("Message-ID") or "").strip()
            if not mid:
                continue
            # Month archives can contain the same message more than once.
            if mid in messages:
                continue
            messages[mid] = message
            sources[mid] = os.path.basename(path)
    return messages, sources


def header_ids(message, name):
    value = message.get(name)
    if not value:
        return []
    return re.findall(r"<[^>]+>", str(value))


def collect_thread(messages, anchor, min_date, limit):
    """Breadth-first walk of the reference graph around *anchor*."""
    graph = defaultdict(set)
    for mid, message in messages.items():
        refs = set(header_ids(message, "In-Reply-To"))
        refs.update(header_ids(message, "References"))
        for ref in refs:
            if ref in messages:
                graph[mid].add(ref)
                graph[ref].add(mid)

    cutoff = dt.datetime.fromisoformat(min_date).replace(tzinfo=dt.timezone.utc)

    def date_of(mid):
        value = messages[mid].get("Date")
        try:
            return parsedate_to_datetime(value).astimezone(dt.timezone.utc)
        except Exception:
            return dt.datetime.max.replace(tzinfo=dt.timezone.utc)

    selected = []
    seen = set()
    queue = deque([anchor])
    seen.add(anchor)
    while queue and len(selected) < limit:
        mid = queue.popleft()
        if date_of(mid) < cutoff:
            continue
        selected.append(mid)
        for neighbour in sorted(graph[mid], key=date_of):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)

    selected.sort(key=lambda mid: (date_of(mid), mid))
    return selected, graph, cutoff


def load_urls(path):
    urls = {}
    if not os.path.exists(path):
        return urls
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) >= 2:
                urls[fields[0]] = fields[1]
    return urls


def short(mid):
    return mid.strip("<>").split("@")[0][:12]


def build_index(selected, messages, graph, urls, sources):
    index = []
    seq = {mid: i + 1 for i, mid in enumerate(selected)}
    for mid in selected:
        message = messages[mid]
        parents = [p for p in header_ids(message, "In-Reply-To") if p in seq]
        children = sorted(
            (seq[c] for c in seq if mid in header_ids(messages[c], "In-Reply-To")),
        )
        refs = [r for r in header_ids(message, "References") if r in seq]
        index.append(
            {
                "seq": seq[mid],
                "date": decode_header_value(str(message.get("Date") or "")),
                "from": decode_header_value(str(message.get("From") or "")),
                "subject": decode_header_value(str(message.get("Subject") or "")),
                "message_id": mid,
                "in_reply_to": (message.get("In-Reply-To") or "").strip() or None,
                "parent_seq": seq[parents[0]] if parents else None,
                "children_seq": children,
                "references_seq": sorted({seq[r] for r in refs}),
                "url": urls.get(mid),
                "source_file": sources[mid],
                "text_file": f"mail/thread/{seq[mid]:02d}.txt",
            }
        )
    return index


def build_tree(index):
    by_seq = {entry["seq"]: entry for entry in index}
    lines = []
    roots = [entry for entry in index if entry["parent_seq"] is None]

    def walk(entry, depth):
        lines.append(
            "  " * depth
            + f"[{entry['seq']:02d}] {entry['date']}  {entry['from']}"
            + f"  -- {entry['subject']}"
        )
        for child in entry["children_seq"]:
            walk(by_seq[child], depth + 1)

    for root in roots:
        walk(root, 0)
    return "\n".join(lines)


def write_transcript(path, index, messages, tree, anchor):
    total = len(index)
    with open(path, "w", encoding="utf-8") as out:
        out.write("DAL mailing list -- reconstructed conversation\n")
        out.write("=============================================\n\n")
        out.write("Anchor (the message this reconstruction started from):\n")
        out.write(f"  {anchor}\n")
        anchor_entry = next((e for e in index if e["message_id"] == anchor), None)
        if anchor_entry and anchor_entry["url"]:
            out.write(f"  {anchor_entry['url']}\n")
        out.write(f"\nMessages collected: {total}\n")
        out.write(f"Oldest message:     {index[0]['date']}\n")
        out.write(f"Newest message:     {index[-1]['date']}\n")
        if index[0]["parent_seq"] is None:
            out.write(
                "Stopped at:         start of thread "
                f"(message {index[0]['seq']:02d} has no parent)\n"
            )
        out.write("Limits:             100 messages, nothing earlier than 2024-01-01.\n\n")
        out.write("Thread structure:\n\n")
        out.write(tree + "\n\n")
        out.write("Note: message bodies are reproduced as archived, including\n")
        out.write("quoted text from earlier messages.  Raw messages are in\n")
        out.write("mail/thread/ and the original archives in mail/gz/.\n")

        for entry in index:
            message = messages[entry["message_id"]]
            out.write("\n" + "=" * 78 + "\n")
            out.write(f"Message {entry['seq']:02d} of {total}\n")
            out.write("=" * 78 + "\n")
            out.write(f"Date:       {entry['date']}\n")
            out.write(f"From:       {entry['from']}\n")
            out.write(f"Subject:    {entry['subject']}\n")
            out.write(f"Message-ID: {entry['message_id']}\n")
            if entry["in_reply_to"]:
                parent = entry["parent_seq"]
                suffix = f" (message {parent:02d})" if parent else " (outside thread)"
                out.write(f"In-Reply-To: {entry['in_reply_to']}{suffix}\n")
            else:
                out.write("In-Reply-To: (none -- start of thread)\n")
            if entry["references_seq"]:
                out.write(
                    "References: "
                    + ", ".join(f"{n:02d}" for n in entry["references_seq"])
                    + "\n"
                )
            else:
                out.write("References: (none)\n")
            if entry["url"]:
                out.write(f"Archive:    {entry['url']}\n")
            out.write(f"Local:      {entry['text_file']}\n")
            out.write("-" * 78 + "\n\n")
            out.write(message_body(message).strip() + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", default=DEFAULT_ANCHOR)
    parser.add_argument("--maildir", default="mail/txt")
    parser.add_argument("--min-date", default=DEFAULT_MIN_DATE)
    parser.add_argument("--max", type=int, default=DEFAULT_MAX)
    parser.add_argument("--index", default="dal-error-thread.json")
    parser.add_argument("--transcript", default="dal-error-thread.txt")
    parser.add_argument("--urls", default="mail/pipermail-urls.tsv")
    args = parser.parse_args()

    messages, sources = parse_messages(args.maildir)
    if args.anchor not in messages:
        sys.exit(f"anchor not found in archives: {args.anchor}")

    selected, graph, cutoff = collect_thread(
        messages, args.anchor, args.min_date, args.max
    )
    urls = load_urls(args.urls)
    index = build_index(selected, messages, graph, urls, sources)
    tree = build_tree(index)

    with open(args.index, "w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    write_transcript(args.transcript, index, messages, tree, args.anchor)

    print(f"collected {len(index)} messages")
    print(f"oldest: {index[0]['date']}  newest: {index[-1]['date']}")
    print(tree)
    print(f"wrote {args.index} and {args.transcript}")

    # Report references that point outside the downloaded archives.
    known = set(messages)
    dangling = set()
    for entry in index:
        for ref in header_ids(messages[entry["message_id"]], "References"):
            if ref not in known:
                dangling.add(ref)
    if dangling:
        print("\nReferences outside the downloaded archives:")
        for ref in sorted(dangling):
            print(f"  {ref}")


if __name__ == "__main__":
    main()
