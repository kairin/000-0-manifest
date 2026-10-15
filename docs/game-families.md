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

## How the sync lists game repositories

`scripts/sync_manifest.py` puts a game repository in section 7, "Game
families", of `README.md`. The order of the checks is:

1. An archived repository goes to the archive, also a game repository.
2. A fork goes to the forks.
3. A name that matches the game family pattern goes to "Game families":

   ```
   ^[A-HJ-NP-Z][0-9A-HJ-NP-Z]{2}-(000|[1-9][0-9]{2})-[a-z0-9]+(-[a-z0-9]+)*$
   ```

4. Other names follow the tier prefixes.

The table shows the GitHub About description of each game repository. The
manifest is public, so the description must contain only general data: the
family code and the type of repository. For example: "ABN family. Base
game." or "ABN family. Downloadable content." Do not describe the game
mechanics, the rules, a puzzle, a key, the story or other contents of a
private repository.

## Make a game repository

A game repository is private when it is made. The manifest does not show an
unlisted private repository, and gives no warning. So, for each new private
game repository:

1. Make the repository on GitHub.
2. Add an entry to `inventory-config.json` with its numeric REST API `id`,
   its name, and the category `auto`.
3. Run `python3 scripts/sync_manifest.py --dry-run`. The repository shows in
   "Game families".

Do not use the category `personal` or `work` for a game repository. A name
that does not match the pattern, for example `ABN-050-x`, stops the sync with
"Repository requires personal/work classification".
