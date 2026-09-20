# Copyright 2026 Google LLC
# Seed script for Firestore catalog collection
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-11b4cbda191e"

SEED_ITEMS = [
    {
        "id": "sf-weather-alert",
        "name": "San Francisco Weather Advisory",
        "category": "weather",
        "description": "Live coastal fog and weather advisory for the Bay Area region.",
        "status": "Active",
    },
    {
        "id": "ny-weather-alert",
        "name": "New York Weather Advisory",
        "category": "weather",
        "description": "Clear skies and sunny temperature report for New York Metropolitan area.",
        "status": "Active",
    },
    {
        "id": "time-zone-service",
        "name": "Global Time Zone Lookup Service",
        "category": "services",
        "description": "Precision timezone calculation and current local timestamp service.",
        "status": "Active",
    },
    {
        "id": "allergy-safety-monitor",
        "name": "Allergy & Health Safety Tracker",
        "category": "safety",
        "description": "Persistent memory tracker logging dietary restrictions and medical allergies.",
        "status": "Active",
    },
]


def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("catalog")

    for item in SEED_ITEMS:
        item_id = item["id"]
        collection_ref.document(item_id).set(item)
        print(f"✅ Seeded document: {item_id} -> {item['name']}")

    print("\n🎉 Firestore database successfully seeded!")


if __name__ == "__main__":
    seed_database()
