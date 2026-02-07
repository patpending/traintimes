# CLAUDE.md - Session Continuity & Project Standards

## Session Startup Checklist

Every session MUST begin with these steps before doing any work:

1. **Read `learnings.json`** in the project root. This contains accumulated project knowledge, recent changes, known issues, and architectural decisions from previous sessions. Understand the current state before making changes.

2. **Read the git log** (`git log --oneline -20`) to understand what has happened in recent sessions. Cross-reference with learnings.json to build a complete picture.

3. **Read the CHANGELOG** (`traintimes-addon/CHANGELOG.md`) for release-level context.

4. **If tests exist**, run them before making any changes to establish a baseline. Currently there are no automated tests (see "Testing" section below). If tests have been added since this was written, run them.

## Session Shutdown Checklist

Before the end of every session, or when you sense context is getting long:

1. **Update `learnings.json`** with:
   - What was done this session (summary of changes)
   - Any new known issues discovered
   - Decisions made and why
   - Anything the next session needs to know
   - Current project status
   - Update the `last_session` date

2. **If tests exist**, run them and confirm they pass. Do not leave the codebase in a broken state.

3. **Update `traintimes-addon/CHANGELOG.md`** if a version was bumped.

4. **Commit learnings.json** (and any other continuity files) to git so they're available in future sessions and survive mothballing.

## Architecture & Diagrams

### When to update `docs/architecture.md`

Create or update architecture documentation when:
- A new deployment mode or component is added
- The data flow between components changes
- New external APIs or services are integrated
- The integration's entity structure changes significantly

The project currently has **three deployment modes**:
1. **Standalone** (`standalone/`) - Flask web app, no HA required
2. **HA Add-on** (`traintimes-addon/`) - Docker container with bundled integration
3. **HA Custom Component** (`custom_components/uk_train_departures/`) - Direct HACS-style integration

### Entity Relationship Diagrams

This project is **stateless** - it has no database. All data comes live from the National Rail Darwin SOAP API. If persistent storage is ever added (SQLite, database, etc.), create an ERD in `docs/erd.md` using Mermaid syntax and keep it updated with every schema change.

## Testing

There are currently **no automated tests**. Test dependencies are commented out in `requirements.txt`. If tests are added:
- Run the full suite before AND after changes
- Never commit code that breaks existing tests
- Add tests for new functionality

## Versioning

- The **canonical version** lives in `traintimes-addon/config.yaml` (the `version:` field). This is what Home Assistant uses to detect updates.
- `custom_components/uk_train_departures/manifest.json` also has a `version` field. **Keep both in sync.**
- Version scheme: `MAJOR.MINOR.PATCH` (currently 2.0.x series)
- Bump version in BOTH files when releasing changes
- Update `traintimes-addon/CHANGELOG.md` with every version bump

## Code Patterns

- **Darwin API**: SOAP/XML over HTTPS. The API wrapper exists in two places: `custom_components/uk_train_departures/api.py` (async, aiohttp) and `standalone/darwin_api.py` / `traintimes-addon/darwin_api.py` (sync, zeep). Changes to API handling may need to be reflected in both.
- **HA Integration**: Follows the standard HA pattern - `coordinator.py` fetches data every 30s, sensors read from coordinator.data.
- **Sensor states**: When no trains are available, sensors should show "No train" (not None/unknown). Attributes must be explicitly cleared with all keys present to prevent stale values.

## CRITICAL: Addon Bundled Integration Copy

The addon at `traintimes-addon/` has its **own copy** of the HA integration at `traintimes-addon/custom_components/uk_train_departures/`. The addon's `run.sh` deploys THIS copy to `/config/custom_components/` on HA startup — NOT the root `custom_components/`.

**After ANY change to files in `custom_components/uk_train_departures/`, you MUST sync to the addon copy:**

```bash
rsync -av --delete --exclude='__pycache__' \
  custom_components/uk_train_departures/ \
  traintimes-addon/custom_components/uk_train_departures/
```

Forgetting this means changes will exist in git but never reach the running HA instance.

## Project Mothballing

When this project goes dormant:
1. Ensure `learnings.json` has a comprehensive `project_status` entry
2. Ensure all work is committed and pushed
3. Add a `mothballed` flag and date in learnings.json
4. Document any pending work or known issues clearly

When resuming a mothballed project:
1. Follow the Session Startup Checklist above
2. Check if dependencies need updating
3. Check if the Darwin API has changed (namespace versions, endpoints)
4. Check if HA integration patterns have evolved

## Files That Must Be Committed to Git

These continuity files MUST be tracked in git (not gitignored):
- `CLAUDE.md` (this file)
- `learnings.json`
- `traintimes-addon/CHANGELOG.md`
- `docs/` directory (when created)

## Sensitive Files - NEVER Commit

- `config.yaml` (root - contains API tokens)
- `nre_credentials.txt`
- `.claude/` directory
