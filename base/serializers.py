from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'workhours_weekday',
            'workhours_weekend',
            'default_schedule_duration',
            'default_schedule_full_duration_max',
        )
