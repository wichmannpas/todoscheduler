from rest_framework import serializers

from .models import Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = (
            'title',
            'description',
            'color',
        )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
