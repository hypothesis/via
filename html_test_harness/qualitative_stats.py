"""
Get some stats from the comments
"""

import json
from collections import defaultdict, Counter

from html_test_harness.domain import Domain
from html_test_harness.domain_store import DomainStore

domains = DomainStore()

global_count_total = 0
for domain in domains:
    global_count_total += domain.count


def cat_for_comment(comment):
    comment_map = {
        'bust': 'bust',
        'worse': 'ok',
        'ok': 'ok',
        'better': 'ok',
        'usable': 'ok'
    }

    for k, v in comment_map.items():
        if k in comment.lower():
            return v

    return 'other'


def get_stats(comments):
    stats = defaultdict(lambda: {'site': 0, 'count': 0})

    for domain_name, comment in comments.items():
        cat = cat_for_comment(comment)
        domain = domains.get(domain_name)

        stats[cat]['site'] += 1
        stats[cat]['count'] += domain.count
        stats['total']['site'] += 1
        stats['total']['count'] += domain.count

    return stats


def compare(comments):
    legacy_via = comments['legacy_via']
    new_via = comments['comment']

    counts = defaultdict(lambda: 0)

    for domain_name, new_comment in new_via.items():
        old_comment = legacy_via[domain_name]

        new_cat = cat_for_comment(new_comment)
        old_cat = cat_for_comment(old_comment)

        if new_cat == old_cat:
            if 'worse' in old_comment:
                counts['better'] += 1

            elif 'better' in old_comment:
                counts['worse'] += 1

            else:
                counts['same'] += 1

        elif new_cat is 'ok' and old_cat is 'bust':
            counts['newly_working'] += 1
        elif new_cat is 'bust' and old_cat is 'ok':
            counts['newly_broken'] += 1
        else:
            counts['other'] += 1

    return dict(counts)


def dump_stat(stats):
    count_total = 2073
    for cat in ['ok', 'bust', 'other']:
        count = stats[cat]['count']
        print(f"{cat} - Site: {stats[cat]['site']}, Count: {count} ({100* count/count_total:0.2f}%) ({100*count/global_count_total:0.2f}%)")


if __name__ == '__main__':
    with open('comments.json') as handle:
        comments = json.load(handle)

    legacy_via = get_stats(comments['legacy_via'])
    new_via = get_stats(comments['comment'])

    print("\nLegacy Via")
    dump_stat(legacy_via)

    print("\nNew Via")
    dump_stat(new_via)

    print("\n")
    for cat, value in compare(comments).items():
        print(cat, value)
