# Game families in the manifest

Game repositories use their own naming scheme, for example `ABN-124-shooter`
and `ABN-685-wheel`. This page is the public summary of the rule. The full
rule and the list of blocked family codes are in a private repository
(`000-0-workspace/docs/game-family-naming.md`). This page also tells how the
manifest treats game repositories.

Decided by the owner on 2026-10-15.

## The name

```
<FAMILY>-<NUMBER>-<mechanic>
```

- `FAMILY`: 3 uppercase base-36 characters without `I` and `O`. The first
  character is a letter.
- `NUMBER`: 3 digits. `000` is the family index, `100`–`199` are base games,
  `200`–`499` are updates, patches and assets, and `500`–`999` are DLC that a
  key unlocks. `001`–`099` are not allowed.
- `mechanic`: lowercase words joined by hyphens.

Names that start with a digit are for system, software and work projects.
Names that start with a letter, in this scheme, are game families.

## Visibility

A game repository is private when it is made, as all other repositories. The
manifest shows the names of private repositories. A name does not give access
to the contents. Only the owner gives access.

## Current state of the sync

`scripts/sync_manifest.py` does not know game families yet.

- A private game repository without an entry in `inventory-config.json` does
  not show in the manifest. The sync gives no warning.
- A game repository with an entry stops the sync with this error:

  ```
  Repository requires personal/work classification
  ```

  The categories `personal` and `work` stop the error, but the manifest then
  shows the game in the wrong section. Do not use them for a game repository.

Do not make a game repository on GitHub before the sync supports game
families. After the change, give each private game repository an entry with
the category `auto` in `inventory-config.json`. The sync then puts it in the
games section by its name.

## Planned change

These changes are not made yet. They need an owner decision.

1. Classify a name that matches the game family pattern as `games`:

   ```
   ^[A-HJ-NP-Z][0-9A-HJ-NP-Z]{2}-(000|[1-9][0-9]{2})-[a-z0-9]+(-[a-z0-9]+)*$
   ```

2. Add `games` to `ACTIVE` in `scripts/sync_manifest.py`.
3. Add a "Games" section with a `| Repository |` table to `README.md`. The
   sync replaces each `| Repository |` table in order. If the number of tables
   is not the same as the number of groups in `ACTIVE`, the sync stops with
   "Page layout changed: unexpected number of tables".
4. Add tests for the new group in `tests/`.
