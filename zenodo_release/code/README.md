# MoTrans-15 v2.1.1 Code Package

This directory contains the Python pipeline, verification suite, and regression tests for MoTrans-15.

## Important Redistribution Notice Regarding Raw Data
- `data/raw` contains proprietary vendor feeds and web archives which **cannot be redistributed** under public Zenodo license terms.
- The packaged parquet analysis tables in `../data/` are pre-built, bitwise-certified, and ready for immediate research consumption.
- To execute the end-to-end raw data ingestion pipeline (`python -m src.pipeline`), primary sources must be retrieved directly in accordance with vendor terms.

## Running Tests
To run the unit test suite:
```bash
pytest
```
