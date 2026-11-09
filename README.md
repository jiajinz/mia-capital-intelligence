# MIA Capital Intelligence

MIA Capital Intelligence is an independent portfolio project.
The Airport Infrastructure & Capital Projects Explorer helps readers find Miami-Dade County airport project records, compare reported estimates within one report, and trace figures to their source pages. The directory covers 222 source observations across two quarterly reports. The contract spending view covers four contracts across July–September 2026 when the reviewed financial record is provisioned.

## Run the explorer locally

From the repository root on macOS or Linux:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

Open the local URL printed by Streamlit. See the [operating guide](docs/RUN_PUBLIC_DIRECTORY.md) for financial review and release checks.

## Run the tests

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

See the [source audit](docs/SOURCE_AUDIT.md#reproduce-the-audit) for the optional PDF checks.

## PyCharm

Open the repository root and select the existing `.venv/bin/python` as the project interpreter. In **Run → Edit Configurations**, add a **Python Tests → pytest** configuration named **Stage 0 tests** with the `tests` directory as the target and the repository root as its working directory. Set a breakpoint in `verify_pdf` and debug a test from `tests/test_source_identity.py` to see how the digest and error branches work. [PyCharm pytest configuration](https://www.jetbrains.com/help/pycharm/run-debug-configuration-py-test.html)

For PDF debugging, create a **Python** configuration targeting `scripts/profile_infrastructure.py`. Use the same interpreter and working directory, and set `PYTHONPATH` to the repository's `src` directory. Install the optional dependency as described in the audit. Break on the `page.crop` call and compare the ID's vertical coordinates with the amount column on the rendered PDF.

## Project references

- [Project state](docs/PROJECT_STATE.md)
- [Source audit](docs/SOURCE_AUDIT.md)
- [Preliminary data dictionary](docs/DATA_DICTIONARY.md)
- [Product and architecture decisions](docs/DECISIONS.md)
- [Independent review packet](docs/REVIEW_PACKET.md)
