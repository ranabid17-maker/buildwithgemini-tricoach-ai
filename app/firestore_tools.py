# Copyright 2026 Google LLC
# Firestore tools for simple-agent catalog
from typing import Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-11b4cbda191e"


def _get_db():
    return firestore.Client(project=PROJECT_ID)


def get_firestore_catalog(
    category: str = "",
    query: str = "",
) -> str:
    """Read items from the Firestore catalog collection.

    Args:
        category: Filter items by category (e.g. 'weather', 'services', 'tools', 'support').
        query: Filter items matching a search term in name or description.

    Returns:
        Formatted string listing items retrieved from Firestore.
    """
    db = _get_db()
    collection_ref = db.collection("catalog")

    try:
        docs = collection_ref.stream()
        results = []
        category_lower = category.lower() if category else ""
        query_lower = query.lower() if query else ""

        for doc in docs:
            data = doc.to_dict()
            if category_lower and category_lower not in data.get("category", "").lower():
                continue
            if query_lower and (query_lower not in data.get("name", "").lower() and query_lower not in data.get("description", "").lower()):
                continue
            results.append(data)

        if not results:
            return f"No items found in Firestore matching criteria (category='{category}', query='{query}')."

        formatted_items = []
        for item in results:
            formatted_items.append(
                f"- ID: {item.get('id')}\n"
                f"  Name: {item.get('name')}\n"
                f"  Category: {item.get('category')}\n"
                f"  Description: {item.get('description')}\n"
                f"  Status: {item.get('status', 'Active')}"
            )

        return "Catalog items retrieved from Firestore:\n" + "\n\n".join(formatted_items)
    except Exception as e:
        return f"Firestore query error: {str(e)}"


def add_firestore_item(
    item_id: str,
    name: str,
    category: str,
    description: str,
    status: str = "Active",
) -> str:
    """Add or update an item entry in the Firestore catalog collection.

    Args:
        item_id: Unique slug identifier for item (e.g., 'sf-weather-alert').
        name: Display name of the item.
        category: Item category (e.g. 'weather', 'services', 'tools').
        description: Description of the item.
        status: Item status (e.g. 'Active', 'Maintenance', 'Archived').

    Returns:
        Confirmation message of Firestore document write.
    """
    try:
        db = _get_db()
        item_doc = {
            "id": item_id,
            "name": name,
            "category": category,
            "description": description,
            "status": status,
        }
        db.collection("catalog").document(item_id).set(item_doc)
        return f"Successfully added item '{name}' ({item_id}) to Firestore collection 'catalog'."
    except Exception as e:
        return f"Firestore write error for item '{item_id}': {str(e)}"
