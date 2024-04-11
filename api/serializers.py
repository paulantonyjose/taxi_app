from rest_framework import serializers
from .models import Ride, UserLocation
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RideSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ride
        fields = [
            "id",
            "rider_id",
            "driver_id",
            "pickup_location",
            "dropoff_location",
            "status",
            "current_latitude",
            "current_longitude",
            "created_at",
            "updated_at",
        ]


class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ["user_id", "latitude", "longitude", "driver_or_rider", "updated_at"]
