# Lain5G-Lab Frontend

React and TypeScript frontend for operating Lain5G-Lab through the FastAPI API.
The operator interface is English-only.

## Development

```bash
make frontend-install
make frontend-dev
```

## Tests and Build

```bash
make frontend-test
make frontend-build
```

## Subscribers

The `/subscribers` route lists, creates, edits, clones, and deletes Open5GS
subscriber records through FastAPI.

The frontend does not receive or store complete secrets. K, OP, and OPc are sent
only during creation or editing and are never stored in `localStorage` or URLs.
