import math
import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Incident
from .serializers import (
    IncidentCreateSerializer,
    IncidentStatusSerializer,
    IncidentResponseSerializer,
    IncidentDetailSerializer,
)
from .services import record_event, fetch_and_record_service_catalog

logger = logging.getLogger(__name__)

@api_view(["GET", "POST"])
def incidents_root(request):
    if request.method == "POST":
        return create_incident(request)
    return list_incidents(request)

def health_check(request):
    return JsonResponse({"status": "ok", "service": "incident-api"})

def create_incident(request):
    serializer = IncidentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    incident = Incident.objects.create(
        title=data["title"],
        description=data.get("description", ""),
        severity=data["severity"],
        service_id=data["service_id"],
    )

    record_event(
        incident_id=str(incident.id),
        event_type="incident_created",
        payload={
            "title": incident.title,
            "severity": incident.severity,
            "serviceId": incident.service_id
        },
    )

    fetch_and_record_service_catalog(
        incident_id=str(incident.id),
        service_id=incident.service_id,
    )

    response_serializer = IncidentResponseSerializer(incident)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)

def list_incidents(request):
    queryset = Incident.objects.all()

    filter_status = request.query_params.get("status")
    if filter_status:
        queryset = queryset.filter(status=filter_status)

    filter_severity = request.query_params.get("severity")
    if filter_severity:
        queryset = queryset.filter(severity=filter_severity)

    filter_service = request.query_params.get("serviceId")
    if filter_service:
        queryset = queryset.filter(service_id=filter_service)

    search_q = request.query_params.get("q")
    if search_q:
        queryset = queryset.filter(title__icontains=search_q)

    sort_param = request.query_params.get("sort", "createdAt_desc")
    sort_map = {
        "createdAt_desc": "-created_at",
        "createdAt_asc": "created_at",
        "severity_desc": "-severity",
        "severity_asc": "severity",
    }
    order_by = sort_map.get(sort_param, "-created_at")
    queryset = queryset.order_by(order_by)

    # Paginacion
    # Paginación
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("pageSize", 10)), 1), 100)
    except (ValueError, TypeError):
        page = 1
        page_size = 10

    total = queryset.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    incidents = queryset[offset : offset + page_size]

    serializer = IncidentResponseSerializer(incidents, many=True)
    return Response({
        "data": serializer.data,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    })

@api_view(["GET"])
def get_incident(request, incident_id):
    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return Response({"error": "Incident not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = IncidentDetailSerializer(incident)
    return Response(serializer.data)

@api_view(["PATCH"])
def update_incident_status(request, incident_id):
    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return Response({"error": "Incident not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = IncidentStatusSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    old_status = incident.status
    new_status = serializer.validated_data["status"]

    incident.status = new_status
    incident.save()

    record_event(
        incident_id=str(incident.id),
        event_type="incident_status_changed",
        payload={
            "previousStatus": old_status,
            "newStatus": new_status,
        },
    )

    response_serializer = IncidentResponseSerializer(incident)
    return Response(response_serializer.data)