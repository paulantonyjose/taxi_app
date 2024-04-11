from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
import simplejson as json


class Ride(models.Model):
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rider")
    driver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="driver", null=True, blank=True
    )
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("started", "Started"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
    )
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="location")
    latitude = models.FloatField()
    longitude = models.FloatField()
    driver_or_rider = models.CharField(
        max_length=1,
        choices=[
            ("d", "d"),
            ("r", "r"),
        ],
        default="d",
    )
    updated_at = models.DateTimeField(auto_now=True)


class RideLocations(models.Model):
    """For location tracking"""

    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name="location")
    locations = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)


@receiver(pre_save, sender=Ride)
def compare_latitude_changes(sender, instance, **kwargs):
    try:
        previous_instance = Ride.objects.get(pk=instance.pk)

        if (
            instance.current_latitude != previous_instance.current_latitude
            or instance.current_longitude != previous_instance.current_longitude
        ):
            ride_locations = RideLocations.objects.get_or_create(ride_id=instance.id)[0]
            if ride_locations:
                if ride_locations.locations:
                    locations = json.loads(ride_locations.locations) + [
                        (instance.current_latitude, instance.current_longitude)
                    ]
                else:
                    locations = [
                        (instance.current_latitude, instance.current_longitude)
                    ]
            ride_locations.locations = json.dumps(locations)
            ride_locations.save()

    except Ride.DoesNotExist:
        # New instance being saved
        pass  # Handle as needed for new instances
