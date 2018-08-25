from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = (
            'title',
            'description',
            'color',
        )

    def validate_color(self, value: str) -> str:
        value = value.lower()

        if len(value) != 6 or not all(
                char in '0123456789abcdef'
                for char in value):
            raise ValidationError('not a valid color value')

        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
