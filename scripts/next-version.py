import re
import subprocess
import sys

bump_rank = {
    "none": 0,
    "patch": 1,
    "minor": 2,
    "major": 3,
}

type_bump = {
    "feat": "minor",
    "fix": "patch",
    "chore": "none",
    "docs": "none",
    "ci": "none",
    "test": "none",
    "build": "none",
    "style": "none",
    "refactor": "none",
}

header_re = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]*\))?(?P<breaking>!)?:")
breaking_re = re.compile(r"^BREAKING[ -]CHANGE:")

last_tag = sys.argv[1]
version_re = re.compile(r"^v(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)$")

if last_tag == "none":
    major = minor = patch = 0
else:
    match = version_re.match(last_tag)
    if match is None:
        sys.stderr.write("Unknown tag " + last_tag + "\n")
        sys.exit(1)
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))


def git(*args):
    return subprocess.run(["git", *args], stdout=subprocess.PIPE, text=True, check=True).stdout


def commits(last):
    if last == "none":
        revision_range = "HEAD"
    else:
        revision_range = last + "..HEAD"
    try:
        log = git("log", "--format=%s%n%b%n--", revision_range)
    except subprocess.CalledProcessError:
        sys.stderr.write("Cannot read the commit range " + revision_range + "\n")
        sys.exit(1)
    return log.split("\n--\n")


def commit_bump(commit):
    lines = commit.split("\n", 1)
    subject = lines[0]
    body = lines[1] if len(lines) > 1 else ""

    match = header_re.match(subject.strip())
    bump = "none"
    if match is not None:
        bump = type_bump.get(match.group("type").lower(), "none")
        if match.group("breaking") is not None:
            bump = "major"

    for line in body.splitlines():
        if breaking_re.match(line.strip()):
            bump = "major"

    return bump


bump = "none"
for commit in commits(last_tag):
    if commit.strip() == "":
        continue
    commit_class = commit_bump(commit)
    if bump_rank[commit_class] > bump_rank[bump]:
        bump = commit_class

if bump == "none":
    print("none")
    sys.exit(0)

if bump == "major":
    major += 1
    minor = 0
    patch = 0
elif bump == "minor":
    minor += 1
    patch = 0
else:
    patch += 1

print(str(major) + "." + str(minor) + "." + str(patch))
