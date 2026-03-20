from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from incidents.models import Incident
import uuid


class ListIncidentsTestCase(SimpleTestCase):

    def _make_incident(self, **kwargs):
        defaults = {
            "id": uuid.uuid4(),
            "title": "Test incident",
            "severity": "HIGH",
            "status": "OPEN",
            "service_id": "payments-api",
        }
        defaults.update(kwargs)
        mock = MagicMock(spec=Incident)
        for k, v in defaults.items():
            setattr(mock, k, v)
        return mock

    @patch("incidents.views.Incident.objects")
    def test_list_returns_200_with_pagination(self, mock_objects):
        incidents = [self._make_incident(), self._make_incident(title="Otro incidente")]

        mock_qs = MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = len(incidents)
        mock_qs.__getitem__ = lambda self, s: incidents

        response = self.client.get("/incidents")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("data", body)
        self.assertIn("total", body)
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["page"], 1)

    @patch("incidents.views.Incident.objects")
    def test_list_empty_returns_200(self, mock_objects):
        mock_qs = MagicMock()
        mock_objects.all.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__getitem__ = lambda self, s: []

        response = self.client.get("/incidents")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"], [])
        self.assertEqual(body["total"], 0)
        self.assertEqual(body["totalPages"], 1)

