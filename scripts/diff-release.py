import subprocess
import sys
import re


rx_oneline = re.compile(r"^(?P<commit>[a-f0-9]{40}) (?P<msg>.*?)(\(#(?P<pr>\d+)\))?$")


def do_diff_release(ref_old, ref_new):

    # To ensure latest information from the repository, first fetch all branches
    # and use the "origin" refspec prefix.
    subprocess.run(['git', 'fetch'], capture_output=True)
    if not ref_old.startswith('origin/'):
        ref_old = 'origin/' + ref_old
    if not ref_new.startswith('origin/'):
        ref_new = 'origin/' + ref_new

    proc = subprocess.run([
        'git', 'merge-base', ref_old, ref_new,
    ], capture_output=True)
    common_ancestor = proc.stdout.strip().decode()

    proc = subprocess.run([
        'git', 'rev-list', '--pretty=oneline', f'{common_ancestor}..{ref_old}',
    ], capture_output=True)
    old_rev_list = proc.stdout.decode().splitlines()

    proc = subprocess.run([
        'git', 'rev-list', '--pretty=oneline', f'{common_ancestor}..{ref_new}',
    ], capture_output=True)
    new_rev_list = proc.stdout.decode().splitlines()

    pr_desc_map = {}

    old_pr_set = set()
    for rev in old_rev_list:
        if (
            (m := rx_oneline.search(rev.strip())) is not None and
            (pr := m.group('pr')) is not None
        ):
            old_pr_set.add(int(pr))
            pr_desc_map[int(pr)] = m.group('msg')

    new_pr_set = set()
    for rev in new_rev_list:
        if (
            (m := rx_oneline.search(rev.strip())) is not None and
            (pr := m.group('pr')) is not None
        ):
            new_pr_set.add(int(pr))
            pr_desc_map[int(pr)] = m.group('msg')

    print()
    print(f"The common ancestor commit:\n{common_ancestor}")

    print()
    print(f"All PRs in the {ref_new} branch since {common_ancestor[:12]}:")
    print("  " + ", ".join(map(str, sorted(new_pr_set))))

    print()
    print(f"All PRs in the {ref_old} branch since {common_ancestor[:12]}:")
    print("  " + ", ".join(map(str, sorted(old_pr_set))))

    print()
    print(f"PRs only in the {ref_new} branch:")
    for pr in sorted(new_pr_set - old_pr_set, reverse=True):
        print(f"  {pr} {pr_desc_map[pr]}")

    print()
    print(f"PRs only in the {ref_old} branch:")
    for pr in sorted(old_pr_set - new_pr_set, reverse=True):
        print(f"  {pr} {pr_desc_map[pr]}")


if __name__ == "__main__":
    do_diff_release(sys.argv[1], sys.argv[2])
