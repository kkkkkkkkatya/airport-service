import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Airplane, Flight, Airport, AirplaneType
from airport.serializers import AirplaneSerializer, AirplaneReadSerializer

AIRPLANE_URL = reverse("airport:airplane-list")
FLIGHT_URL = reverse("airport:flight-list")


def sample_airplane_type(**params):
    defaults = {
        "name": "Sample airplane type",
    }
    defaults.update(params)

    return AirplaneType.objects.get_or_create(name=defaults["name"], defaults=defaults)[0]


def sample_airplane(**params):
    defaults = {
        "name": "Sample airplane",
        "rows": 10,
        "seats_in_row": 4,
        "airplane_type": sample_airplane_type(),
    }
    defaults.update(params)

    return Airplane.objects.create(**defaults)


def image_upload_url(airplane_id):
    """Return URL for recipe image upload"""
    return reverse("airport:airplane-upload-image", args=[airplane_id])


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplanes(self):
        airplane_type = sample_airplane_type()
        sample_airplane(airplane_type=airplane_type)
        sample_airplane(airplane_type=airplane_type)

        res = self.client.get(AIRPLANE_URL)

        airplanes = Airplane.objects.order_by("id")
        serializer = AirplaneReadSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_airplanes_by_airplane_type(self):
        airplane_type1 = AirplaneType.objects.create(name="Boeing")
        airplane_type2 = AirplaneType.objects.create(name="Airbus")

        airplane1 = sample_airplane(name="Boeing 747", airplane_type=airplane_type1)
        airplane2 = sample_airplane(name="Boeing 777", airplane_type=airplane_type1)
        airplane3 = sample_airplane(name="Airbus A320", airplane_type=airplane_type2)

        res = self.client.get(AIRPLANE_URL, {"airplane_type": airplane_type1.id})

        serializer1 = AirplaneReadSerializer(airplane1)
        serializer2 = AirplaneReadSerializer(airplane2)
        serializer3 = AirplaneReadSerializer(airplane3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_retrieve_airplane_detail(self):
        airplane = sample_airplane()

        url = detail_url(airplane.id)
        res = self.client.get(url)

        serializer = AirplaneReadSerializer(airplane)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "Airplane",
            "rows": 6,
            "seats_in_row": 3,
            "airplane_type": airplane_type.id,  # Use ID instead of object
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type = AirplaneType.objects.create(name="Boeing")
        payload = {
            "name": "Airplane",
            "rows": 6,
            "seats_in_row": 3,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(id=res.data["id"])
        for key in payload.keys():
            if key == "airplane_type":
                self.assertEqual(payload[key], airplane.airplane_type.id)  # Compare IDs
            else:
                self.assertEqual(payload[key], getattr(airplane, key))


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.airplane = sample_airplane()

    def tearDown(self):
        self.airplane.image.delete()

    def test_upload_image_to_airplane(self):
        """Test uploading an image to an airplane"""
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.airplane.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.airplane.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.airplane.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_airplane_list_should_not_work(self):
        airp = AirplaneType.objects.create(name="Boeing")
        url = AIRPLANE_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Airplane",
                    "rows": 6,
                    "seats_in_row": 3,
                    "airplane_type": airp.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(name="Airplane")
        self.assertFalse(airplane.image)

    def test_image_url_is_shown_on_airplane_detail(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.airplane.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_airplane_list(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(AIRPLANE_URL)

        self.assertIn("image", res.data[0].keys())

    def test_put_airplane_not_allowed(self):
        payload = {
            "name": "New airplane",
            "rows": 8,
            "seats_in_row": 4,
        }

        url = detail_url(self.airplane.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_airplane_not_allowed(self):
        url = detail_url(self.airplane.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
