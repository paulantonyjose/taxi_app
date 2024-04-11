from rest_framework import viewsets, status
from .models import Ride, UserLocation, RideLocations
from .serializers import UserSerializer, RideSerializer, UserLocationSerializer
from django.contrib.auth.models import User
import math
from rest_framework.decorators import action
from rest_framework.response import Response
import simplejson as json


def calculate_distance(latitude1, longitude1, latitude2, longitude2):
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    """
    R = 6371  # Earth's radius in kilometers
    phi1 = math.radians(latitude1)
    phi2 = math.radians(latitude2)
    delta_phi = math.radians(latitude2 - latitude1)
    delta_lambda = math.radians(longitude2 - longitude1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RideViewSet(viewsets.ModelViewSet):
    """
    POST /ride/: Create a new ride
    GET /ride/{id}/: Retrieve a specific ride
    GET /ride/: List all rides
    Patch /ride/{id}/: Update a specific ride

    """

    queryset = Ride.objects.filter(
        status__in=["accepted", "started", "pending", "completed"]
    )
    serializer_class = RideSerializer
    lookup_field = "rider__id"
    lookup_url_kwarg = "rider_id"

    def perform_create(self, serializer):
        rider_id = self.request.data.get("rider_id")
        serializer.save(rider_id=rider_id)

    @action(detail=True, methods=["post"])
    def start(self, request, rider_id=None):
        """
        Start a ride.

        This endpoint allows the driver to start a ride. It updates the ride's status to 'started' and saves the ride.

        Parameters:
        pk (int): The ID of the ride to start.

        Returns:
        A serialized representation of the updated ride.

        Url:
        POST /ride/{id}/start/

        """
        ride = self.get_object()
        ride.status = "started"
        ride.save()
        return Response(self.get_serializer(ride).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def complete(self, request, rider_id=None):
        """
        Complete a ride.

        This endpoint allows the driver to complete a ride. It updates the ride's status to 'completed' and saves the ride.

        Parameters:
        pk (int): The ID of the ride to complete.

        Returns:
        A serialized representation of the updated ride.

        Url:
        POST /ride/{id}/complete/

        """
        ride = self.get_object()
        ride.status = "completed"
        ride.save()
        return Response(self.get_serializer(ride).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, rider_id=None):
        """
        Cancel a ride.

        This endpoint allows the rider to cancel a ride. It updates the ride's status to 'cancelled' and saves the ride.

        Parameters:
        pk (int): The ID of the ride to cancel.

        Returns:
        A serialized representation of the updated ride.

        Url:
        POST /ride/{id}/cancel/

        """
        ride = self.get_object()
        ride.status = "cancelled"
        ride.save()
        return Response(self.get_serializer(ride).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def accept(self, request, rider_id=None):
        """
        Accept a ride request.

        This endpoint allows a driver to accept a ride request. It updates the ride's status to 'accepted' and sets the driver for the ride.


        Returns:
        A serialized representation of the updated ride.

        Url:
        POST /ride/{id}/cancel/
        """
        ride = self.get_object()
        if ride.status == "pending":
            ride.driver = request.user
            ride.status = "accepted"
            ride.save()
            return Response(self.get_serializer(ride).data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Ride is not in a pending state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def locations(self, request, rider_id=None):
        """
        For location tracking, get's all the ride's locations

        Parameters:
        pk (int): The ID of the ride to start.


        Url:
        POST /ride/{id}/locations/

        """
        ride = self.get_object()
        locations = (
            RideLocations.objects.filter(ride=ride)
            .values("locations")
            .first()
            .get("locations")
        )
        if locations:
            return Response(json.loads(locations), status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "There are no locations recorded at the moment."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserLocationViewSet(viewsets.ModelViewSet):
    """
    POST /location/: Create a user's location
    GET /location/{user_id}/: Retrieve a specific user's location
    PATCH /location/user_id/: Update a specific user's location
    GET /location/{user_id}/available_drivers/ :list of available drivers
    """

    queryset = UserLocation.objects.all()
    serializer_class = UserLocationSerializer
    lookup_field = "user__id"
    lookup_url_kwarg = "user_id"

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        serializer.save(user_id=user_id)

    @action(detail=True, methods=["get"])
    def available_drivers(self, request, user_id=None):

        user_location = self.get_object()

        drivers = Ride.objects.filter(
            status__in=["accepted", "started", "completed"]
        ).values_list("driver_id", flat=True)

        available_drivers = UserLocation.objects.filter(driver_or_rider="d").exclude(
            user_id__in=drivers
        )
        drivers = []
        for driver_location in available_drivers:
            distance = calculate_distance(
                user_location.latitude,
                user_location.longitude,
                driver_location.latitude,
                driver_location.longitude,
            )
            if distance < 5:
                drivers.append(
                    {"driver": driver_location.user.id, "distance": distance}
                )
        drivers.sort(key=lambda x: x["distance"])
        return Response(drivers)
