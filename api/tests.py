from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Ride, UserLocation, RideLocations
import simplejson as json


class UserViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.driver1_data = {"username": "driver1", "password": "testpassword"}
        self.driver2_data = {"username": "driver2", "password": "testpassword"}
        self.rider1_data = {"username": "rider1", "password": "testpassword"}
        self.rider2_data = {"username": "rider2", "password": "testpassword"}

    def test_create_users(self):
        response = self.client.post(
            "/api/user/", self.driver1_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            "/api/user/", self.driver2_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            "/api/user/", self.rider1_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            "/api/user/", self.rider2_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class RideViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.rider1 = User.objects.create(username="rider1", password="testpassword")
        self.rider2 = User.objects.create(username="rider2", password="testpassword")
        self.driver1 = User.objects.create(username="driver1", password="testpassword")
        self.driver2 = User.objects.create(username="driver2", password="testpassword")
        self.ride_data = {
            "pickup_location": "Location A",
            "dropoff_location": "Location B",
            "current_latitude": 12.345678,
            "current_longitude": 23.456789,
            "rider_id": self.rider1.id,
            "driver_id": self.driver1.id,
        }

    def test_create_ride(self):
        self.assertEqual(type(self.rider1.id), int)
        response = self.client.post(
            "/api/ride/", self.ride_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ride_lifecycle(self):
        ride = Ride.objects.create(**self.ride_data)
        ride_id = ride.id

        # Start ride
        response = self.client.post(
            f"/api/ride/{ride_id}/start/", format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "started")

        # Complete ride
        response = self.client.post(
            f"/api/ride/{ride_id}/complete/", format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")

        response = self.client.post(
            f"/api/ride/{ride_id}/cancel/", format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_retrieve_ride(self):
        ride = Ride.objects.create(**self.ride_data)
        ride_id = ride.id
        response = self.client.get(f"/api/ride/{ride_id}/", format="json", follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_rides(self):
        Ride.objects.create(**self.ride_data)
        self.ride_data["rider_id"] = self.rider2.id
        Ride.objects.create(**self.ride_data)
        response = self.client.get("/api/ride/", format="json", follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_ride_location(self):
        ride = Ride.objects.create(**self.ride_data)
        ride_id = ride.id
        new_location = {"current_latitude": 23.456789, "current_longitude": 34.56789}
        response = self.client.patch(
            f"/api/ride/{ride_id}/", new_location, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            float(response.data["current_latitude"]),
            float(new_location["current_latitude"]),
        )
        self.assertEqual(
            float(response.data["current_longitude"]),
            float(new_location["current_longitude"]),
        )

    def test_ride_locations(self):
        ride = Ride.objects.create(**self.ride_data)
        ride_id = ride.id
        RideLocations.objects.create(
            ride=ride, locations=json.dumps([(12.345678, 23.456789)])
        )
        response = self.client.get(
            f"/api/ride/{ride_id}/locations/", format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [[12.345678, 23.456789]])


class UserLocationViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.driver1 = User.objects.create(username="driver1", password="testpassword")
        self.driver2 = User.objects.create(username="driver2", password="testpassword")
        self.rider1 = User.objects.create(username="rider1", password="testpassword")
        self.rider2 = User.objects.create(username="rider2", password="testpassword")
        self.location_data = {
            "latitude": 12.345678,
            "longitude": 23.456789,
            "driver_or_rider": "d",
            "user_id": self.driver1.id,
        }

    def test_create_user_location(self):
        response = self.client.post(
            "/api/location/", self.location_data, format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_user_location(self):
        user_location = UserLocation.objects.create(**self.location_data)
        response = self.client.get(
            f"/api/location/{user_location.user.id}/", format="json", follow=True
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_location(self):
        user_location = UserLocation.objects.create(**self.location_data)
        new_data = {"latitude": 23.456789, "longitude": 34.56789}
        response = self.client.patch(
            f"/api/location/{user_location.user.id}/",
            new_data,
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["latitude"], new_data["latitude"])
        self.assertEqual(response.data["longitude"], new_data["longitude"])

    def test_available_drivers(self):
        rider_location = UserLocation.objects.create(
            user_id=self.rider1.id,
            latitude=12.345678,
            longitude=23.456789,
            driver_or_rider="r",
        )
        driver_location1 = UserLocation.objects.create(
            user_id=self.driver1.id,
            latitude=12.346678,
            longitude=23.457789,
            driver_or_rider="d",
        )
        driver_location2 = UserLocation.objects.create(
            user_id=self.driver2.id,
            latitude=12.23123,
            longitude=23.12313,
            driver_or_rider="d",
        )
        response = self.client.get(
            f"/api/location/{self.rider1.id}/available_drivers/",
            format="json",
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        drivers = response.data

        self.assertEqual(drivers[0].get("driver"), self.driver1.id)
