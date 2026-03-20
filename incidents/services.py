import uuid
import logging
from datetime import datetime, timezone
import requests
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)

# MongoDB instance
_mongo_client = None
def get_mongo_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.MONGODB_URI)
    return _mongo_client[settings.MONGODB_DB]

def get_events_collection():
    return get_mongo_db()["incident_events"]


def record_event(incident_id: str, event_type: str, payload: dict, metadata: dict = None):
    collection = get_events_collection()
    event = {
        "incidentId": str(incident_id),
        "type": event_type,
        "occurredAt": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "metadata": metadata or {"correlationId": str(uuid.uuid4())},
    }
    try:
        result = collection.insert_one(event)
        logger.info(f"Event recorded: {event_type} for incident {incident_id}")
        return event
    except Exception as e:
        logger.error(f"Failed to record event: {e}")
        raise

def get_incident_timeline(incident_id: str) -> list:
    collection = get_events_collection()
    events = list(
        collection.find(
            {"incidentId":str(incident_id)},
            {"_id":0}
        ).sort("occurredAt",1)
    )
    return events

def fetch_service_info(service_id: str) -> dict:
    url = f"{settings.SERVICE_CATALOG_URL}/services/{service_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 404:
            return {"success": False, "error": "Service not found", "status_code": 404}
        else:
            return {"success": False, "error": f"Unexpected status: {response.status_code}"}
    except requests.Timeout:
        return {"success": False, "error": "Timeout calling Service Catalog"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection error to Service Catalog"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_and_record_service_catalog(incident_id: str, service_id: str):
    result = fetch_service_info(service_id)
    record_event(incident_id=incident_id, event_type="service_catalog_snapshot",payload=result)
    return result