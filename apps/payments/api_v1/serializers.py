from rest_framework import serializers
from apps.payments.models import Payment, Donation

class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_email', 'user_name', 'story', 'story_title', 'amount', 'status', 'created_at']


class DonationSerializer(serializers.ModelSerializer):
    donor_email = serializers.EmailField(source='donor.email', read_only=True)
    donor_name = serializers.CharField(source='donor.name', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)

    class Meta:
        model = Donation
        fields = ['id', 'donor', 'donor_email', 'donor_name', 'story', 'story_title', 'amount', 'platform_fee', 'created_at']
