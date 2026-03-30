from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.stories.api_v1.permissions import IsAdminUser
from apps.payments.models import Payment, Donation
from apps.payments.api_v1.serializers import PaymentSerializer, DonationSerializer
from apps.user_account.utils import success_response

class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin endpoint to see entire payment history"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related('user', 'story').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)

class AdminDonationViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin endpoint to see entire donation history"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = DonationSerializer
    queryset = Donation.objects.select_related('donor', 'story').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)
