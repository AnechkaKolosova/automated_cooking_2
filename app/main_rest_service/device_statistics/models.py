from django.db import models
from django.contrib.auth.models import User


class Metric(models.Model):
    device = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_user')
    type = models.CharField(max_length=50)
    temp = models.FloatField()
    longitude = models.FloatField()
    latitude = models.FloatField()
    humidity = models.FloatField()
    photo = models.TextField()
    dt = models.DateTimeField(auto_now=True)
