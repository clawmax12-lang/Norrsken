# tablehopp fixture brief (FR-01)

`brief.json` is the demo brief for tablehopp. It holds **only facts we know**:

| Field | Value | Source |
| --- | --- | --- |
| `product_name` | `tablehopp` | known |
| `goal_note` | `Launching 7 Oct` | known launch date |

Every other field is `PLACEHOLDER: William to supply`: `one_liner`, `audience` and the three
`screenshots`. Nothing here is a product claim; do not fill the placeholders from guesses.

Two fields cannot hold placeholder text:

- `goal` is an enum (`signups`, `downloads`, `understand`, `purchase`). It is set to
  `understand`, the most neutral value, only so the file validates. William to confirm.
- `brand_color` and `logo` are optional and left `null`.

The file validates against the `Brief` contract (`preflight.intake.load_fixture_brief`), but its
screenshot entries are not files, so it cannot be run through the pipeline until William supplies
three real PNG or JPG screenshots and replaces the placeholders. Automated tests never use this
file as an image source; they generate synthetic images in temporary directories.
