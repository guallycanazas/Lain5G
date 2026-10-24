#!/usr/bin/env python3
"""Exercise subscriber API CRUD against a disposable MongoDB database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient
from pymongo import MongoClient

from backend.app.dependencies import get_subscriber_service, settings_dependency
from backend.app.main import create_app
from backend.app.services.open5gs_connection_service import Open5GSConnectionService
from backend.app.services.subscriber_service import SubscriberService
from backend.app.settings import Settings


ROOT = Path(__file__).resolve().parents[2]
SOURCE_IMSI = "001019876543210"
CLONE_IMSI = "001019876543211"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", required=True)
    args = parser.parse_args()

    database = args.mongo_uri.rstrip("/").rsplit("/", 1)[-1].split("?", 1)[0]
    settings = Settings(
        project_root=ROOT,
        dry_run=False,
        mutating_operations_enabled=True,
        open5gs_mongo_uri=args.mongo_uri,
        open5gs_mongo_database=database,
        open5gs_docker_network="",
        subscriber_operation_timeout=5,
    )
    connection = Open5GSConnectionService(settings)
    service = SubscriberService(settings, connection)
    app = create_app()
    app.dependency_overrides[settings_dependency] = lambda: settings
    app.dependency_overrides[get_subscriber_service] = lambda: service
    mongo = MongoClient(args.mongo_uri, serverSelectionTimeoutMS=5000)
    mongo[database].drop_collection("subscribers")

    try:
        payload = json.loads((ROOT / "src/backend/tests/fixtures/subscribers/subscriber_valid.json").read_text())
        payload["imsi"] = SOURCE_IMSI

        with TestClient(app) as client:
            status = client.get("/api/subscribers/connection?profile=5g-sa-x310")
            assert status.status_code == 200 and status.json()["status"] == "connected"

            created = client.post("/api/subscribers?profile=5g-sa-x310", json=payload)
            assert created.status_code == 201 and created.json()["persisted"] is True
            assert payload["security"]["k"] not in created.text

            listed = client.get(f"/api/subscribers?profile=5g-sa-x310&search={SOURCE_IMSI}")
            assert listed.status_code == 200 and listed.json()["total"] == 1
            assert payload["security"]["k"] not in listed.text

            detail = client.get(f"/api/subscribers/{SOURCE_IMSI}?profile=5g-sa-x310")
            assert detail.status_code == 200
            assert detail.json()["security"]["sqn"] == "************"

            updated = client.patch(
                f"/api/subscribers/{SOURCE_IMSI}?profile=5g-sa-x310",
                json={"msisdn": "51900000001"},
            )
            assert updated.status_code == 200
            assert updated.json()["subscriber"]["msisdn"] == "51900000001"

            cloned = client.post(
                f"/api/subscribers/{SOURCE_IMSI}/clone?profile=5g-sa-x310",
                json={"new_imsi": CLONE_IMSI, "new_msisdn": "51900000002"},
            )
            assert cloned.status_code == 201
            assert cloned.json()["subscriber"]["imsi"] == CLONE_IMSI

            records = list(mongo[database].subscribers.find({"imsi": {"$in": [SOURCE_IMSI, CLONE_IMSI]}}))
            assert len(records) == 2
            assert records[0]["security"]["k"] == records[1]["security"]["k"]

            for imsi in (CLONE_IMSI, SOURCE_IMSI):
                removed = client.request(
                    "DELETE",
                    f"/api/subscribers/{imsi}?profile=5g-sa-x310",
                    json={"confirm": True},
                )
                assert removed.status_code == 200

            remaining = client.get("/api/subscribers?profile=5g-sa-x310")
            assert remaining.status_code == 200 and remaining.json()["total"] == 0

        print("PASS: subscriber API connected to disposable MongoDB; list/create/detail/redaction/edit/clone/delete/cleanup")
    finally:
        mongo[database].drop_collection("subscribers")
        mongo.close()
        app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
