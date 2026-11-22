# Documentation claim auditor

This offline static auditor compares documented claims about the checked capability with Python source evidence. It never executes inspected code.

## Usage

```sh
python3 -m pip install .
barcode-generation-claim-audit audit . --json
python3 -m barcode_generation_claim_audit audit . --verbose
```

The repository path defaults to the current directory. Repeat `--ignore PREFIX` to exclude paths, and use `--fail-on medium` to include test-only findings. Exit status is 0 for PASS, 2 for findings at the selected threshold, and 1 for usage or I/O errors. Use `--version` to show the version.

The finding identifiers are:

```text
documented-barcode-generation-claim-false
documented-no-barcode-generation-claim-false
```

## Differentiation

The checked operation encodes data into a one-dimensional strip. Other families cover encoding data into a two-dimensional matrix, decoding an existing code, synthesising pictures from content or models, printing marks on paper, and saving a picture with no code leg. Those operations are outside this audit.

The phrase lists also exclude spreadsheet reading and generation, word-document reading and generation, presentation reading and generation, PDF extraction, generation, merging, splitting, encryption, rotation, form-filling, watermarking, redaction, compression and annotation, table extraction, OCR, document extraction, e-signature, payment processing, video editing, screen recording, video generation, and QR code generation claims.

## Limitations

This phrase can describe a future roadmap feature:

```text
barcode generation
```

This phrase can describe a person, web page, or artwork:

```text
barcode generator
```

This phrase can describe a test fixture or an unshipped sample:

```text
generate barcode
```

This phrase can describe a Makefile target:

```text
make barcode
```

This phrase can describe a third-party dashboard:

```text
create barcode
```

This phrase can describe payload transport:

```text
encode barcode
```

This phrase can describe displaying an existing code:

```text
render barcode
```

This phrase can describe a scan result:

```text
output barcode
```

- The class pair accepts an output method on any base, including an unrelated object.
- The class pair does not trace whether output acts on the constructed object.
- The encoder pair accepts an output method on any base, including an unrelated object.
- The encoder pair does not trace whether output acts on the constructed object.
- The factory requires two positional arguments or a code keyword; a one-argument call only returns a class, even if later used.
- The shortcut counts even if its output is never checked.
- The treepoem call counts even if its result is never saved or shown.
- The class build method counts even if it writes no file.
- A bare library import is not evidence.
- A roadmap, changelog or TODO claim still counts.
- A denial outside the denial list is not recognised and a positive phrase may still count.
- Documents outside the root README and directories named docs are not read.
- Evidence split across modules is missed.
- A locally defined route name shadows the route, even for a wrapper.
- Dead code counts as evidence.
- Subprocess commands such as zint are not evidence.
- A QR operation alone is not evidence.
- A decode call alone is not evidence.
- A locally defined generic name is shadowed.
- Alias chains the tracer cannot follow are missed.
- Exact phrases are matched without semantic interpretation.
- Implementations in other languages are invisible.
- Runtime-only routes are invisible because code is not executed and the network is not accessed.
- The class construction and output legs must be in one module.
- The encoder construction and output legs must be in one module.
- A lone class construction with no output call is not evidence.
- A lone output method call with no class construction is not evidence.
- A lone encoder construction with no output call is not evidence.
- A lone output method call with no encoder construction is not evidence.
- A bare class lookup call alone is not evidence.
- A bare barcode-type access alone is not evidence.
- Two-dimensional encoder classes are outside this family.
- A bare name reference without a call is not evidence.
- Strings or comments mentioning the capability are not evidence.
- A filename or extension literal alone is not evidence.
- Syntax-invalid files provide no evidence.
- Image saving alone is not evidence.
- Plotting alone is not evidence.
- Opening or displaying an image alone is not evidence.
- Static matching does not establish whether a detected operation is correct.
