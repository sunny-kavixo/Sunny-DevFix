# Approval-bound patch safety

Sunny DevFix can apply a reviewed suggestion only when the server operator opts in
to specific project roots. Patch writes are disabled by default.

```bash
export DEVFIX_PROJECT_ROOTS="/absolute/path/to/project"
```

Multiple roots use the platform path separator (`:` on macOS/Linux and `;` on
Windows). The workflow is deliberately split into three API calls:

1. `POST /api/patches/preview` validates the root, relative path, current content,
   and proposed content without writing. It returns a five-minute approval token
   bound to the exact before/after bytes.
2. `POST /api/patches/apply` requires that token and `confirm: true`. It rejects a
   stale preview and uses an atomic same-directory replacement.
3. `POST /api/patches/rollback` requires the returned rollback token and
   `confirm: true`. Rollback is withheld if the file changed after applying.

Absolute paths, traversal outside an authorized root, symlink escapes, missing
files, non-UTF-8 files, and files over 20,000 bytes are rejected. Approval and
rollback tokens are one-time, process-local, expire after five minutes, and are
invalid after a server restart. This feature never executes the patched code.
