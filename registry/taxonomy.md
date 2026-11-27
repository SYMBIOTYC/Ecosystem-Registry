# Registry model and operating rules

## Canonical record types
Organization, Product, Project, Service, Website, Tool, Technology, Infrastructure, Integration, Application, Interface, Person / Team.

## Required fields
`id,name,type,parent_id,description,owner,repository,evidence_url,lifecycle_status,evidence_level,evidence_note,dependencies,last_verified_utc`.

The seed CSV uses the first nine fields; timestamps and dependencies are tracked in the repository inventory and will be normalized in the next schema revision.

## Lifecycle status
- `PRODUCTION`: independently checked live and operational.
- `BETA`: accessible pre-release verified.
- `DEVELOPMENT`: active source or implementation exists; production not proven.
- `PLANNED`: explicitly planned, no implementation evidence.
- `ARCHIVED`: intentionally discontinued or repository archived.
- `UNVERIFIED`: lifecycle unknown or only a name/claim exists.

## Evidence level
- `VERIFIED`: authoritative GitHub metadata/source or direct operational evidence for the stated fact.
- `PARTIAL`: some evidence exists but deployment, ownership, or behavior remains unverified.
- `UNVERIFIED`: only a user-provided name or uncorroborated reference exists.

## Counting and deduplication
1. A repository is not automatically a separate product. Track repository inventory separately from asset records.
2. A product family is counted once; its applications, interfaces, integrations and infrastructure are linked children.
3. A website and its web application are separate only if they are independently identifiable.
4. A private repository is a valid inventory record; never expose its source, secrets or private artifacts.
5. A user-owned repository is not automatically a SYMBIOTYC asset. Record its owner and keep ecosystem relationship unverified until source/owner evidence confirms it.
6. Two repositories with similar names (e.g. `cy-cli` and `CY_CLI`) are separate repository records until proven mirrors or duplicates.
7. Technologies and third-party dependencies are not counted as products.
8. People and teams are counted separately from software assets; do not infer personal roles.

## Governance
- Keep IDs stable; never recycle them.
- Every count must state its scope and snapshot date.
- Do not claim a service is in production from repository existence, README text, CI success or a configured homepage alone.
- For cloud workloads, distinguish ephemeral GitHub-hosted CI from persistent compute, VPS, workers and deployed endpoints.
- Keep private implementation and public wrappers as separate trust boundaries.
## CSV schema integrity

- `registry/records.csv` has exactly 13 columns in the header; every data row must contain exactly 13 fields in the same order.
- Evidence-source labels and supplemental provenance notes belong in `evidence_note` unless a versioned schema change explicitly adds a new column and migrates every row.
- Before committing CSV changes, validate the field count for every row, lifecycle/evidence enums, required IDs/names/types, and uniqueness of stable IDs.
- Do not infer a lifecycle state from evidence strength: `lifecycle_status` and `evidence_level` are independent fields.
