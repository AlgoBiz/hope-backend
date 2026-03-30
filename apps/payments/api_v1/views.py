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
        from django.db.models import Sum
        qs = self.filter_queryset(self.get_queryset())
        
        paid_qs = qs.filter(status='paid')
        revenue = paid_qs.aggregate(total=Sum('amount'))['total'] or 0
        completed_payment_count = paid_qs.count()
        verification_payment_count = qs.count()
        
        stats = {
            'revenue': float(revenue),
            'completed_payment': completed_payment_count,
            'verification_payment_count': verification_payment_count,
        }

        page = self.paginate_queryset(qs)
        if page is not None:
            response = self.get_paginated_response(self.get_serializer(page, many=True).data)
            if hasattr(response, 'data') and isinstance(response.data, dict):
                response.data['stats'] = stats
            return response
            
        return success_response(data={
            'results': self.get_serializer(qs, many=True).data,
            'stats': stats
        })

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
