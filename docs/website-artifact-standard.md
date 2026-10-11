# Website artifact standard

Status: proposed, 2026-10-11.

Use one versioned metadata contract to describe generated reports, documentation sites, local viewers and application exports. Existing builders can adopt the contract without changing runtime.

New static report generators should use uv-managed Python, Jinja2, local CSS and small JavaScript modules. Existing Astro, MkDocs, Gradio and native apps remain supported through adapters. Generated navigation and page records reduce manual maintenance.

## Public inventory boundary

Keep the repository inventory generator and its approved stable IDs. An approved private repository listing does not authorize publication of its content.

A future public artifact projection needs an explicit allowlist. Candidate fields are an approved repository ID and name, an approved artifact ID and title, output mode, and an approved public URL. Exclude local paths, source documents, captions, work records, attachments, private descriptions and search text by default. Unknown visibility or missing approval must fail closed.

Do not copy the private workspace audit into this public repository. Do not infer artifact approval from repository approval. Build and publish remain separate operations.

## Tasks

1. Define a versioned public artifact DTO from approved inventory snapshots.
2. Add tests for unknown private IDs, repository renames, missing repositories and excluded fields.
3. Generate a public-safe artifact index from that DTO.
4. Preserve current generated repository tables and scheduled sync behavior.

The private core workspace owns the architecture plan and per-project adoption audit. The tables core owns database choices. A local catalog can use rebuildable SQLite when queries justify it. Public index generation must not require access to private raw data.
