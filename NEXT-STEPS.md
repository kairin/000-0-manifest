# Next steps

## agy round 2 checklist (2026-10-18)

This checklist is the working copy of the round 2 tasks for `000-0-manifest`. The [round 2 review](../000-0-workspace/docs/core-agy-review-round2-2026-10-18.md#000-0-manifest) gives the evidence, and the [decision record](../000-0-workspace/docs/core-agy-decisions-2026-10-18.md) gives the reasons for the decided items. Where an earlier status in this file disagrees with this section, use this section.

### Status

"Ruled now" is the verified status. "Target" is the status after every task below passes on this host, before any delivery.

| Task | Ruled now | Target |
|---|---|---|
| M-01 | accepted | accepted (unchanged) |
| M-02 | tested | accepted |
| M-03 | tested | tested (unchanged) |
| M-04 | tested | accepted |
| M-05 | tested | accepted |
| M-06 | tested | accepted |
| M-07 | accepted | accepted (unchanged) |
| M-08 | blocked | blocked (unchanged) |
| M-09 | in-progress | in-progress (unchanged) |
| M-10 | blocked | blocked (unchanged) |
| M-11 | deferred | deferred (unchanged) |

### Why round 1 failed here

**M-01 (accepted, PARTIAL).** Created: docs/core-system-contract.md, docs/release-policy.md, README/AGENTS routes. Criteria met in substance (plan 105-119). Defect: release-policy.md uses `status` (unestablished|candidate|accepted), `accepted_ref`, member `tag`, kinds `accepted-commit-only`, `shipment-unestablished`, `containing-baseline-commit`; the schema/layout/validator/AI-15 use `snapshot_status`, `baseline_ref`/`baseline_tag`/`manifest_commit`, `release_tag`, `accepted-commit-source`, `unestablished`, `manifest-self`; contract line 50 says `build_inputs`, schema line 149 `build_dependencies`. A consumer reading the policy cannot find its fields in the data. Root cause: schema and data were named after the contract was written and the contract was not reconciled. Evidence: stale lint receipts, no hashes for the two new docs, bare consumer "accepted" strings.

**M-02 (accepted -> tested, PARTIAL).** Created: core-layout.schema.json, 12 fixtures. Unmet (plan 131): "fixtures cover every allowed field/type ... and identity kinds": no fixture uses `accepted-commit-source`; `valid_routed_private_component.json` fails the schema (owner_route `#fragment` violates the schema pattern; validator accepts it via SAFE_OWNER_ROUTE_RE), reproduced with jsonschema 4.19.1 (appendix script `manifest_schema_check.py`), so the "valid" fixture does not exemplify the schema; no test validates any fixture against the schema, and validate_core_layout.py only checks the schema `title`. Evidence: input hash points at the contract, not the schema. Root cause: schema and validator written independently with no parity test.

**M-03 (accepted -> tested, PARTIAL).** Created: core-layout.json (14 components, 9 IDs in order, 6 targets). Unmet (plan 157, 164): "source refs verified against pinned owner tree ... exact pinned-source evidence". Components carry no commit or blob hash (checked: no `commit`/`sha256` keys in any component); the only verification is path existence in live dirty trees (`--workspace ~/Apps`), and several target paths (ghostty local-bin/ghostty-build.py, ai local-bin/update-core.py) exist only as uncommitted files. Root cause: no pin collection step.

**M-04 (accepted -> tested, PARTIAL; overrules verifier PASS).** Created: scripts/validate_core_layout.py (1145 lines), tests/test_core_layout.py (12 tests). Defect: validate_core_layout.py:20-21 and :1065 set `allow_synthetic = resolved_layout_path.name == "valid_variable_n_plus_one.json"`, and :280-282 then inject ID 9999999999 into the approved inventory. Consequences: (a) a production validator accepts an undeclared ID for any layout file with that name and empty components, violating M-02's failure criterion "undeclared IDs accepted" (plan 142) and M-04's "invalid ... passes" (plan 195); (b) the N+1 acceptance case (plan 183) is proven only through this bypass. Checkpoint (plan 197) requires "manifest-only/N+1 cases" in the test module: no manifest-only temporary-checkout test and no unsupported-schema test exist (verifier probes covered them manually; the suite does not). Root cause: test fixture need solved in production code instead of by passing a synthetic inventory.

**M-05 (accepted -> tested, PARTIAL).** Created: workspace mode in the same files. Met: missing checkout exit 2, symlink escape, authored duplicate, generated drift. Unmet (plan 209, 221, 223): "dirty/ahead source is not reset ... silently accepted" fails, and the checkpoint says "Exercise temporary ... dirty ... inputs": no test creates a dirty/ahead git repo and asserts status/HEAD unchanged or a visible dirty note; validator is git-free, so dirty state is silently accepted with no report. "against pinned inputs" (plan 208) absent (same as M-03).

**M-06 (accepted -> tested, PARTIAL).** Created: scripts/check_public_tree.py, tests/test_public_tree.py, local-sync.md section. Met: whole tree incl. rendered pages, file:line-only findings, allowlisted noreply/pass paths. Unmet (plan 235): "usernames ... private topology ... rejected": the verifier's probe (appendix script `manifest_public_tree_probe.py`) shows bare usernames, internal hostnames, dataset paths, `/root`, `/var/home/<u>`, generic `password=`/`Bearer`/`API_KEY=` pass. Step 3 "human review of new public fields" (plan 242) unrecorded. Design note for the fix: a public repo cannot hold a plaintext denylist of the owner's username; use sha256-hashed tokens or obtain an owner-approved documented scope reduction.

**M-08 (accepted -> blocked, FAIL).** Created: nothing new beyond M-03's layout; evidence is four commands plus three self-declared consumer rows. Unmet: dependency GH-02 is `tested` (plan 284; gate status rule); "every assembly input resolvable by exact commit/hash" (plan 287, 298): no payload commit/sha recorded in M-08 evidence; the layout's `manifest_commit` d61cea92 is HEAD, which does not contain core-layout.json (untracked), so M0 is not resolvable by commit; "verify GH-02/DF-02/AI-02 exact input parity receipts and hashes" (plan 301) absent; "Ran 76 tests" not reproducible (51). Root cause: freeze claimed before dependencies and before any committed revision existed. A real freeze needs a manifest commit (owner delivery).

**M-09 (tested -> in-progress, FAIL).** Created: review_notes text with seven commits. Defect: `git cat-file -t 395f85b865f44fb9614a0c617f53da2f700c3d95` in 000-0-tables and `git cat-file -t be7b14807f34a6dfbb9703c0331e020bbdd9c6a3` in 000-0-tmux-cheat-sheet both fail ("could not get object info"); real HEADs are 3b1462e5 and fa372360. The other five equal current HEADs of dirty trees (manifest's does not contain the layout). The proposals are not recorded in core-layout.json (all seven still `unestablished`, null commit) and the manifest self marker required by plan 312 is absent (policy says `containing-baseline-commit`, schema `manifest-self`, layout `unestablished`). Compatibility `evidence_route`s point at prose docs, not receipts (plan 308). Consumer_check text says "--select-baseline reports candidate" while it reports `unestablished`. Root cause: commits recorded without `git cat-file`/`rev-parse` verification.

**M-11 (deferred, DEFERRED-CORRECT with doc fix).** docs/local-sync.md:282 "Registry boundary and duplication measurement (M-11)" measures inventory-vs-layout ID overlap (9/94). Plan 365/370 asks for repeated publisher maintenance cost and scheduled exception/hooks. The deferral outcome is allowed; the section must say that measurement was not performed.

### Do not delete or overwrite

- In every repository: Git branches, tags, stashes, reflog, untracked and ignored files. Do not run `git reset --hard`, `git clean`, a force push or a branch delete. Do not delete a dated receipt or a historical document.
- In `000-0-manifest`: Published pages other than the four declared pages, tags and accepted refs, and `inventory-config.json` entries.
- Allowed deletion in `000-0-manifest`: Generated pages that `sync_manifest.py` regenerates.

Apply the six delete rules of the [preservation contract](../000-0-workspace/docs/core-agy-review-round2-2026-10-18.md#preservation-contract-what-you-must-not-delete-or-overwrite) to every delete, move or replace operation.

### Tasks

Do the tasks from top to bottom. Each line gives: ID | parent or source | priority | files | what to do | acceptance check with its negative case | depends on. Tick a box only after its acceptance check passes and you have recorded the real command and exit code.

- [ ] **M-04.R1** | M-04 | P1 | scripts/validate_core_layout.py:20-21, :280-282, :1065; tests/test_core_layout.py | Remove the filename-keyed synthetic path. Make the N+1 test pass a synthetic inventory (10 IDs) through the existing `inventory_path`/`inventory_data` parameter. | Negative: `cp tests/fixtures/core-layout/valid_variable_n_plus_one.json /tmp/valid_variable_n_plus_one.json; python3 scripts/validate_core_layout.py /tmp/valid_variable_n_plus_one.json` -> exit != 0 "not in inventory-config.json"; positive: N+1 unit test passes with the synthetic inventory. | none
- [ ] **M-04.R2** | M-04 | P1 | tests/test_core_layout.py | Add required checkpoint cases: manifest-only temporary checkout (copy scripts+schema+layout+inventory to a temp dir, `env -i python3 -I`), unsupported `schema_version` (2, True), target-owner-outside-target-scope. | 15+ tests OK; each negative asserts the specific error. | none
- [ ] **M-02.R1** | M-02 (+M-01, M-03) | P1 | docs/release-policy.md, docs/core-system-contract.md:50, core-layout.schema.json, core-layout.json | Reconcile names one way (recommended: contract text adopts the shipped machine names `snapshot_status`, `baseline_ref`/`baseline_tag`/`manifest_commit`, `release_tag`, `build_dependencies`, kinds `published-component-release`/`accepted-commit-source`/`unestablished`/`manifest-self`); resolve the manifest self-identity contradiction (policy s1 `containing-baseline-commit` vs s2 `shipment-unestablished` vs layout `unestablished`); update "proposed core-layout.json sidecar" wording. | grep of policy for `accepted_ref|accepted-commit-only|shipment-unestablished|containing-baseline-commit|build_inputs` returns 0 (or the schema is changed and all fixtures/validator/AI-15 follow); ste-lint <= 2.5; AI-15.R2 then re-pins digests. | none; triggers AI-15.R2, WS-LEDGER re-hash
- [ ] **M-02.R2** | M-02 | P1 | tests/test_core_layout.py; schema pattern for owner_route | Add a test validating every fixture against core-layout.schema.json with a stdlib structural check (or vendored minimal validator); fix the `#fragment` owner_route mismatch so `valid_routed_private_component.json` is schema-valid; add a fixture for `accepted-commit-source` and negative baseline-identity fixtures (unestablished with a commit; accepted with null commit). | jsonschema run (appendix script `manifest_schema_check.py`) shows all `valid_*` valid and all `invalid_*` invalid; new fixtures exercised by the validator tests. | none
- [ ] **M-03.R1** | M-03 | P1 | ledger M-03 (and optionally a sidecar receipt doc) | Record per-component pinned-source evidence: for each current/target `source` path the owner repo HEAD and blob sha256 (`git hash-object` / sha256) at review time; mark paths that exist only uncommitted. Commit-level pins need owner delivery (OWNER). | Table has 14 rows; each hash recomputable. | none for hashes; OWNER for commit pins
- [ ] **M-05.R1** | M-05 | P1 | tests/test_core_layout.py | Disposable git repo test: dirty + untracked + ahead-of-origin sibling under a temp workspace root; assert `git status --porcelain`, HEAD and file hashes identical before/after `--workspace`; assert a visible "dirty/ahead not verified" note in output. Add directory-symlink and guide-link escape tests (verifier probe3). | Tests pass; mutation negative asserts unchanged. | none
- [ ] **M-08.R1** | M-08 | P1 | ledger M-08 | Status -> `blocked`; `incomplete`: GH-02 tested, no committed manifest revision containing the layout, payload inputs unpinned; record payload identities now as (repo, path, working-tree sha256, "uncommitted") for ghostty-build.py 4e648748..., bash-tool-updates.py 1d1e9a3b..., update-core.py 5b3ff4c1...; fix "76 tests" -> 51. | Entry consistent; dependency script shows no accepted task over a non-accepted dependency. | GH-02 acceptance (OWNER), delivery of manifest (OWNER)
- [ ] **M-09.R1** | M-09 | P1 | ledger M-09 review_notes; core-layout.json candidate rows (or a receipt doc) | Replace tables/tmux commits with verified ones (`git -C <repo> rev-parse --verify <sha>^{commit}` for each of the seven); record proposals in reviewable form (candidate fields or receipt) rather than prose; add the manifest self marker consistent with M-02.R1; replace `evidence_route` prose targets with actual compatibility receipts or mark rows `incomplete`; correct consumer_check wording (`--select-baseline` -> unestablished). Status `in-progress`. | Script: all seven `git cat-file -t` return `commit`; validator exit 0; select-baseline still unestablished. | M-02.R1, M-08.R1; any delivery changes HEADs (re-take pins after commits)
- [ ] **M-NUM.R1** | decision record | `docs/release-policy.md` section 4, `core-layout.schema.json` (`release_tag`/`baseline_tag` patterns), `tests/test_core_layout.py` | Replace "pending owner decision" with the decided format and namespaces; add schema patterns `^update-v|dev-tools-v...` for component tags and `^baseline-v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|\d{3})$` for `baseline_tag`; fixtures: `baseline-v1.0.001` valid, `baseline-v1.0.1000`, `baseline-v1.0.0001`, `v1.0.001` invalid. | Acceptance: validator rejects the three negatives with the pattern error, accepts the positive; `ste-lint <= 2.5`. | after M-02.R1; triggers AI-15.R2 (digests change).
- [ ] **M-10.R2** | decision record | `docs/release-policy.md` section 3 step 4 | State that promotion = `gh release create baseline-v1.0.001 --target <M1 merge sha>` in the owner's delivery; LKG rule unchanged. | Lint pass; AI-15 digest re-pin. | M-NUM.R1.
- [ ] **M-09.R2** | decision record | `docs/release-policy.md` (new section "Shipment selection rule"), `scripts/validate_core_layout.py` (new `--verify-shipments WORKSPACE`), `tests/test_core_layout.py` | Encode checks (a)-(d) of the rule; `--verify-shipments` exits 1 naming the first failing member; test with a scratch repo (commit on main vs commit not on origin/main vs nonexistent sha). | Negative: nonexistent sha -> exit 1 "not a commit"; branch-only sha -> exit 1 "not on origin/main"; positive scratch -> exit 0. | M-09.R1.
- [ ] **M-06.R1'** | decision record (replaces M-06.R1) | `scripts/check_public_tree.py`, `tests/test_public_tree.py`, `docs/local-sync.md` | Add the generic rules; report skipped non-UTF8 files; document the scope: "identifiers (usernames, hostnames, dataset or repo names) are allowed; absolute home paths, contact data and credential patterns are rejected; topology is human-reviewed". | Appendix probe `manifest_public_tree_probe.py`: the path/credential cases CAUGHT, identifier-only cases documented as out of scope; 14 existing cases single-finding; no value in output. | none. M-06.R2 as written.
- [ ] **M-PIN.R1** | decision record | `scripts/take_pins.py` (new, offline, read-only on repos) | For each component source path: owner repo `rev-parse HEAD`, `git status --porcelain -- <path>` must be empty, blob sha256; writes a JSON receipt; exits 1 if any path is dirty (so pins are only taken on clean, delivered trees). | Negative: dirty path -> exit 1; positive on clean scratch repo -> receipt. | none.
- [ ] **M-02.R3** | M-02 | P2 | ledger M-02 | Input hash -> schema 0fbe6ab2... plus each fixture's sha256; replace "python3 fixture inspection" with the real command; field-to-fixture coverage table. | Entry reproducible. | none
- [ ] **M-03.R2** | M-03 | P2 | core-layout.json tables-compose `owner_route` | Justify or replace `docker/README.md` as an "approved private route" (it is a public relative path); list the audited-overlap set the 14 components were checked against. | Note in ledger/contract. | none
- [ ] **M-06.R2** | M-06 | P2 | ledger M-06 | Record the human review of new public fields (who/when/what). | Entry present. | none
- [ ] **M-07.R1** | M-07 | P2 | ledger M-07 | Note mock limits (git/gh/publish patched; argument lists asserted, not real index). | Entry present. | none
- [ ] **M-08.R2** | M-08 | P2 | validation run | Run `validate_core_layout.py --require-executable-inputs` on the real layout and record the result (expected: fails on routed-only `tables-compose`), so "no routed-only executable input accepted" is demonstrated rather than asserted. | Recorded exit code and message. | none
- [ ] **M-10.R1** | M-10 | P2 | manifest fixtures | Add "later nightly commit does not alter selected snapshot" and "offline cached identity freshness unknown" fixtures without promoting. | Tests pass. | AI-15
- [ ] **M-11.R1** | M-11 | P2 | docs/local-sync.md:282 section | State that publisher-reuse measurement (repeated maintenance cost, scheduled exception/hooks) was not performed and G-MEASURE stays open; keep the ID-overlap note as dated context or remove hard-coded counts. | Lint <= 2.5; section no longer labels the overlap as the M-11 measurement. | none
- [ ] **M-01.R1** | M-01 | P2 | ledger M-01 | Re-run ste-lint on hashed files and record (1066/769/1764/897 words); add sha256 of both contract docs; replace bare consumer "accepted" strings with file:line receipts (each sibling README/AGENTS link). | Receipts reproducible. | after M-02.R1
- [ ] **M-LEDGER.R1** | all M | P2 | ledger M-01..M-11 | Re-pin: HEAD d61cea92 + dirty paths (AGENTS.md, README.md, docs/local-sync.md, scripts/sync_manifest.py, tests/test_sync_manifest.py; untracked core-layout.json, core-layout.schema.json, docs/core-system-contract.md, docs/release-policy.md, scripts/check_public_tree.py, scripts/validate_core_layout.py, tests/fixtures/, tests/test_core_layout.py, tests/test_public_tree.py) with sha256; suite count 40. | WS-06.R2 script clean for manifest. | after code items
- [ ] **M-07.R2** | M-07 | P3 | tests/test_sync_manifest.py | One real-git temp-repo staging test asserting only the four pages are in the index. | Passes. | none

### Physical constraints (not agy work on this host)

- Commit pins (M-03, M-08, M-09) and the baseline tag wait for the owner's delivery request (standing rule).

**Status:** to do.

This repository has follow-up work from the review of 2026-10-07 (task T25).
The owner keeps the full instructions in private notes, because they contain
local paths. Ask the owner for them before you start.

When the work is done, delete this file.

## Follow-ups from the inventory check of 2026-10-12

Each item needs an owner decision. Remove an item when it is resolved.

- [ ] Finish the `000-333-stay-up` privacy clean-up. The owner decided on
      2026-10-12 that it stays public as a tool for anyone, with no personal
      or work details. The repository files are clean; the remaining items
      are on GitHub and need the owner. Details are in the owner's notes.
- [ ] Archived repositories with open Dependabot pull requests. Archived
      repositories are read-only. To close a pull request, unarchive the
      repository, close it, and archive the repository again:
      `MetaSpec-Kyocera` #10, `win-qemu` #2, `google-gemini-codes` #6,
      `stable-diffusion-webui-forge` #1.
- [ ] Archived repositories whose default branch is not `main`: `master` in
      `comf-agx-orin`, `gitg`, `linformer`, `ubuntu-video-playback` and
      `Vizy-Unsupported-Remake`; `main-kairin` in `jetson-containers`. Decide
      whether to leave them as they are.
