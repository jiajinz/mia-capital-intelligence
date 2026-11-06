# MIA Capital Intelligence

MIA Capital Intelligence is an independent portfolio project. It has no affiliation with MDAD or HNTB and provides no official project status or engineering risk ratings.

The product asks which publicly reported airport projects merit a management follow-up, what changed between reports, and which source rows support that follow-up. Stage 0 is the source audit and engineering baseline. Start with the [independent review packet](docs/REVIEW_PACKET.md).

## Run Stage 0 locally

From the repository root on macOS or Linux:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

The metadata tests run offline. The optional PDF audit requires the public source files and pdfplumber. See the [source audit](docs/SOURCE_AUDIT.md#reproduce-the-audit) for exact acquisition and reproduction commands.

## PyCharm

Open the repository root and select the existing `.venv/bin/python` as the project interpreter. In **Run → Edit Configurations**, add a **Python Tests → pytest** configuration named **Stage 0 tests** with the `tests` directory as the target and the repository root as its working directory. Set a breakpoint in `verify_pdf` and debug a test from `tests/test_source_identity.py` to see how the digest and error branches work. [PyCharm pytest configuration](https://www.jetbrains.com/help/pycharm/run-debug-configuration-py-test.html)

For PDF debugging, create a **Python** configuration targeting `scripts/profile_infrastructure.py`. Use the same interpreter and working directory, and set `PYTHONPATH` to the repository's `src` directory. Install the optional dependency as described in the audit. Break on the `page.crop` call and compare the ID's vertical coordinates with the amount column on the rendered PDF.

## Project references

- [Project state](docs/PROJECT_STATE.md)
- [Source audit](docs/SOURCE_AUDIT.md)
- [Preliminary data dictionary](docs/DATA_DICTIONARY.md)
- [Product and architecture decisions](docs/DECISIONS.md)
- [Independent review packet](docs/REVIEW_PACKET.md)
