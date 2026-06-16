---
name: commitdetails-update-track-all-changes
description: 'Update CommitDetails changelog entries when user says Update CommitDetails. Append all commits since the latest CommitDetails date with date, author, and SHA per commit, and include current uncommitted change summaries with date and author.'
argument-hint: 'Target file path if not CommitDetails.txt (optional)'
user-invocable: true
disable-model-invocation: false
---

# CommitDetails Update To Track All Changes

## What This Skill Produces
This skill appends a dated update entry to a CommitDetails Change Log section.
It lists every commit from the latest CommitDetails log date up to now, one concise line per commit, ordered oldest to newest.
Each commit line includes Date, Author, and SHA.
It also appends a short summary of current uncommitted working tree changes (if any), with Date and Author but without SHA, as the final line of the entry.

## When To Use
Use this skill when the user says any of these triggers:
- Update CommitDetails

## Inputs
- Optional argument: target CommitDetails path.
- Default target file: CommitDetails.txt in the current workspace.

## Procedure
1. Identify the target file.
2. Ensure the file has a section named Change Log.
3. Determine whether this is the first run:
- First run is true if no prior Update CommitDetails entries exist.
4. Build a timestamp using local date and time in this format: YYYY-MM-DD HH:mm.
5. If first run:
- Append one entry with the timestamp.
- Set details to: Initial Test Program.
6. If not first run:
- Find committed changes since the most recent CommitDetails entry timestamp and include all commits up to present.
- Use git history with metadata and touched files, for example:
  - `git log --reverse --since="<last_entry_time>" --pretty=format:"__COMMIT__ %h|%an|%ad|%s" --date=format:"%Y-%m-%d %H:%M" --name-status`
- For each commit, write one concise but precise summary line. Prefer the commit subject and file-change context.
- Include these fields for every commit line:
  - Date: commit date/time
  - Author: commit author name
  - SHA: short commit SHA
- Commit lines must be written top to bottom in chronological order (oldest commit first, newest commit last).
- If no committed changes are detected, append: No committed code changes detected since last update.
7. Detect uncommitted current-folder changes (tracked, staged/unstaged, and untracked).
- Use working tree status and diffs, for example:
  - `git status --porcelain`
  - `git diff --name-status`
  - `git diff --cached --name-status`
- If uncommitted changes exist, append a short sub-section summarizing what changed now.
- For each uncommitted summary line include:
  - Date: current local date/time
  - Author: current git user.name (fallback: Unknown)
  - No SHA field.
  - Position: write uncommitted summary as the last line after all committed lines.
8. Append the new timestamped entry to the Change Log section.
9. Verify quality checks before finishing.
10. Send a final chat confirmation message after a successful write:
- CommitDetails file is updated successfully.

## Decision Rules
- If both CommitDetails.txt and README.md exist, prefer CommitDetails.txt unless the user gives an explicit path.
- If no previous entry marker is parseable, treat as first run.
- If no committed changes are detected, append: No committed code changes detected since last update.
- If uncommitted changes are not present, do not add an uncommitted section.
- If user requests summary precision, keep each commit summary to one short sentence that still identifies the module/file area changed.
- Always render committed lines in oldest-to-newest order.
- If uncommitted changes exist, they must be the final line(s) in the entry.

## Quality Checks
- Entry includes date and time.
- Initial run details are exactly Initial Test Program.
- New entry is appended, not replacing prior history.
- Committed summary reflects all commits since the last logged timestamp.
- Each committed line includes Date, Author, and SHA.
- Uncommitted section (when present) includes Date and Author and excludes SHA.
- Committed lines are ordered top-to-bottom from oldest to newest.
- Uncommitted summary line(s), if present, appear after all committed lines.
- Preserve existing file formatting and line endings.
- Final chat feedback is sent confirming success.

## Chat Feedback
After updating the file successfully, always reply with this exact sentence:

CommitDetails file is updated successfully.

## Output Format Template
Use this structure for each appended entry:

### YYYY-MM-DD HH:mm
- Commit: <short precise summary> (Date: YYYY-MM-DD HH:mm, Author: Jane Doe, SHA: abc1234)
- Commit: <short precise summary> (Date: YYYY-MM-DD HH:mm, Author: John Smith, SHA: def5678)

The commit list above must be ordered oldest to newest.

If there are uncommitted changes at update time, append:

- Uncommitted: <short precise summary> (Date: YYYY-MM-DD HH:mm, Author: Jane Doe)
- Uncommitted: <short precise summary> (Date: YYYY-MM-DD HH:mm, Author: Jane Doe)

The uncommitted line(s) must be placed at the end, after all commit lines.

For first run, use:

### YYYY-MM-DD HH:mm
- Initial Test Program (SHA: n/a, Author: n/a)
