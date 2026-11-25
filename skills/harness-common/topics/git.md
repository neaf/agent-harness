# git

Facts about git that the skills depend on. Checked on 2026-11-25 with git 2.56.0, in throwaway repositories under `mktemp -d` with no user or system config (`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`).

Adapter: `skills/attack-plan-milestone-execute/scripts/build_integration_branch.py` (`git`, `git_or_fail`). From Phase 9 on: `skills/harness-common/scripts/git.py`.

## `merge-tree --write-tree`

| Fact | Source |
|---|---|
| `git merge-tree --write-tree <a> <b>` computes the merge tree without touching the work tree or the index. | `man git-merge-tree` (git 2.56.0) |
| The mode arrived in git 2.38. | [git 2.38.0 release notes](https://github.com/git/git/blob/master/Documentation/RelNotes/2.38.0.adoc) |

### Quirk: old git reports a conflict

- Symptom: on git older than 2.38 the script prints `CONFLICT merging <head>`.
- Cause: the option is unknown there, and the script reads every non-zero exit of `merge-tree` as a conflict.
- Workaround: check `git --version` first and stop with "needs git 2.38 or later" (Phase 9).
- Code: `build_integration_branch.py:11` (docstring), `:78-80`.

## `commit-tree` needs an identity

- Symptom: `git commit-tree` fails with `Author identity unknown`.
- Cause: no `user.name` and `user.email` are configured. Checked: a repo with no config fails this way.
- Workaround: check the identity before the first merge, and name the missing key in the error.
- Code: `build_integration_branch.py:82`.

## Fetch and remote branches

| Fact | Source |
|---|---|
| A default clone has the fetch refspec `+refs/heads/*:refs/remotes/origin/*`, so `git fetch origin <branch>` updates `origin/<branch>`. | Scripted check, full clone |
| A `--single-branch` clone has the refspec `+refs/heads/<branch>:refs/remotes/origin/<branch>` only. | Scripted check |
| `git ls-remote --heads origin <branch>` finds a remote branch whatever the refspec. | Scripted check |

### Quirk: fetch does not update the remote-tracking ref in a single-branch clone

- Symptom: after `git fetch origin other` in a single-branch clone, `origin/other` does not exist. Only `FETCH_HEAD` is set.
- Cause: the fetch refspec does not cover `other`.
- Workaround: fetch with an explicit refspec, `git fetch origin +refs/heads/<b>:refs/remotes/origin/<b>`, and test existence with `ls-remote` apart from the fetch.
- Code: `build_integration_branch.py:55-56` (fetch, then `rev` of `<remote>/<branch>` at `:77`).

## Tags

- Symptom: `git tag <name>` fails and asks for a tag message.
- Cause: a global config with `tag.gpgSign=true` makes every tag an annotated, signed tag.
- Workaround: `git tag -a <name> -m "<message>"`.
- Code: rearchitect Stage 0 tags the base (`skills/rearchitect/SKILL.md`). Source: observed when this run created `rearch-base` (rearchitect audit X1).

## `.git/info/exclude` and worktrees

| Fact | Source |
|---|---|
| `info/exclude` lives in the common git dir. A linked worktree resolves `git rev-parse --git-path info/exclude` to the main checkout's `.git/info/exclude`. | Scripted check, `git worktree add` |
| So one exclude file covers every worktree of a repository, and it is never committed. | follows from the row above |

Code: `skills/harness-common/references/state.md` "Private state", cited by `skills/ai-notes/SKILL.md` and `references/publishing.md`.
