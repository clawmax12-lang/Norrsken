# Redaction — shared webfont assets

Owner-supplied archive: `redaction (3).zip`, attachment `384cdcdc-02a3-4bdc-8c12-8bbea8111eb1`. The nested `Redaction_2_001.zip` supplies these original WOFF2 files. Imported selectively and unchanged; no conversion, subsetting, duplicate OTFs, `__MACOSX` or `.DS_Store` files.

Copyright 2019 MCKL Inc. Supplied under dual SIL OFL 1.1 / LGPL 2.1. We redistribute under SIL OFL 1.1 with the original [OFL.txt](OFL.txt), including copyright and license. Preserve that file with every distributed copy. Font licensing does not relicense the application or imply the designers' endorsement.

| File | Use | SHA-256 |
| --- | --- | --- |
| [Redaction-Regular.woff2](Redaction-Regular.woff2) | Clean display regular, 400 | `13b7352c2729e67ccf99e64b579e1aa7d6c46202fe928b26e327925c75d28e31` |
| [Redaction-Bold.woff2](Redaction-Bold.woff2) | Clean display bold, 700 | `82e6cd057929b66d946b3a68570e618255381ce10bd1adcb7b812193d89ac3e7` |
| [Redaction-Italic.woff2](Redaction-Italic.woff2) | Clean display italic, 400 | `5d6cf7f6ee003b26dbb19ef34d828dbfd23fb54337e50c64ae7b07bf23874c4c` |
| [Redaction_20-Regular.woff2](Redaction_20-Regular.woff2) | Restrained distressed display, 400 | `7faedff3b274a92251a1f624f6895ec5028cb859ea36a6bdd91c056a49424216` |
| [Redaction_20-Bold.woff2](Redaction_20-Bold.woff2) | Restrained distressed display, 700 | `fb2049931a6a0c8f97a31edd314ea99fb9d91df91c558f9b6572e33a1716a9ec` |

Total font payload is 224,604 bytes. Clean Redaction is the default identity/headings/card-title face. Use Redaction20 sparingly at large sizes; 20 is the distressed design variant, not a weight. Keep dense UI/transcripts readable with the existing sans and timestamps with mono.

[Shared theme CSS](../../../docs/design/preflight-theme.css) defines `@font-face` with `font-display: swap` and `/fonts/redaction/` URLs for the existing Next.js app. Application integration remains the frontend owner's task; committing assets does not mean the deployed UI loads them. Preserve unused bold/italic as optional assets; do not preload every variant.
