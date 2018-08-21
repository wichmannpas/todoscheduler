from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'workhours_weekday',
            'workhours_weekend',
            'default_schedule_duration',
            'default_schedule_full_duration_max',
            'password',
        )

    username = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True, min_length=6)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        return super().update(instance, validated_data)
