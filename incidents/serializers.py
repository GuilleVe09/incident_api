from rest_framework import serializers
from .models import Incident


class IncidentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    severity = serializers.ChoiceField(choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    serviceId = serializers.CharField(max_length=100, source="service_id")

class IncidentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"])

class IncidentResponseSerializer(serializers.ModelSerializer):
    serviceId = serializers.CharField(source="service_id")
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")

    class Meta:
        model = Incident
        fields = [
            "id",
            "title",
            "description",
            "severity",
            "status",
            "serviceId",
            "createdAt",
            "updatedAt"
        ]

class IncidentDetailSerializer(serializers.ModelSerializer):
    serviceId = serializers.CharField(source="service_id")
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            "id",
            "title",
            "description",
            "severity",
            "status",
            "serviceId",
            "createdAt",
            "updatedAt",
            "timeline"
        ]

    def get_timeline(self, obj):
        from .services import get_incident_timeline
        return get_incident_timeline(str(obj.id))
