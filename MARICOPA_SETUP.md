# Maricopa County Assessor API Setup (Optional)

This project can optionally use a Maricopa County Assessor API as an **AZ-only enrichment source**.

## What it’s used for
- Filling missing property fields when ATTOM is incomplete (especially):
  - APN / parcel number
  - Year built
  - Lot size (sqft)
  - Building sqft (sometimes)
  - Assessed / market value and last transfer (stored in debug metadata)

It is **disabled by default** and will never run unless you explicitly enable it.

## Environment variables
Add these to your `.env`:

- `MARICOPA_ASSESSOR_ENABLED=true`
- `MARICOPA_ASSESSOR_BASE_URL=https://mcassessor.maricopa.gov` (default)
- `MARICOPA_ASSESSOR_API_KEY=...` (required; this is your **token**)

### Endpoint configuration (defaults shown)
If your provider uses different paths/param names, override these:

- `MARICOPA_ASSESSOR_SEARCH_PATH=/search/property/`
- `MARICOPA_ASSESSOR_ADDRESS_PARAM=q`
- `MARICOPA_ASSESSOR_TIMEOUT_SECONDS=30`

### Authentication configuration
You can authenticate either via **header** or **query parameter**:

**Header (default)**
- `MARICOPA_ASSESSOR_API_KEY_HEADER=AUTHORIZATION`

**Query param (alternative)**
- `MARICOPA_ASSESSOR_API_KEY_QUERY_PARAM=api_key` (example)

If `MARICOPA_ASSESSOR_API_KEY_QUERY_PARAM` is set, the key will be sent as a query param.
Otherwise it will be sent as a header.

## How it’s integrated
- Runs only when:
  - `state == "AZ"`
  - enabled/configured
  - and key fields are missing (`year_built`, `lot_size_sqft`, `square_feet`)
- It **only fills missing fields** (it will not overwrite ATTOM values).
- Raw response is stored in:
  - `subject_property.mls_data["maricopa_assessor"]`

## API reference
See the official Maricopa County Assessor API documentation PDF: [`https://www.mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf`](https://www.mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf)

## Verify it’s enabled
Open the status endpoint:

- `http://localhost:5050/api/status`

Look for:
- `maricopa_assessor_enabled: true`


