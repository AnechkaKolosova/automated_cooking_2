from rest_framework import serializers

from device_statistics.models import Metric


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ('id', 'device', 'user', 'type', 'temp', 'dt', 'photo', 'longitude', 'latitude', 'humidity')
        read_only_fields = ('id',)
