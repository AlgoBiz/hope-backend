from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.payments.api_v1.views import AdminPaymentViewSet, AdminDonationViewSet

router = DefaultRouter()
router.register(r'admin/payments', AdminPaymentViewSet, basename='admin-payments')
router.register(r'admin/donations', AdminDonationViewSet, basename='admin-donations')

app_name = 'payments_api_v1'

urlpatterns = [
    path('', include(router.urls)),
]
