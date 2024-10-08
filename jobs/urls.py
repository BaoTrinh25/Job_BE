from rest_framework import routers
from . import views
from django.urls import path, include
from .views import StripeCheckoutViewSet


# Tạo đối tượng
router = routers.DefaultRouter()
# Phần đầu tiên là prefix, tiếp đầu ngữ -> Phần đầu mà URL nó tạo ra cho mình
# Phần thứ 2 là viewsest
# "jobs" là đường dẫn URL mà view set sẽ được đăng ký vào.
# views.JobViewSet là view set mà bạn muốn đăng ký.

router.register('jobs', views.JobViewSet, basename="jobs")
router.register('users', views.UserViewSet, basename='users')
router.register('companies', views.CompanyViewSet, basename='companies')
router.register('jobseeker', views.JobSeekerViewSet, basename='jobseeker')
router.register('careers', views.CareerViewSet, basename='careers')
router.register('employmenttypes', views.EmploymentTypeViewSet, basename='employmenttypes')
router.register('areas', views.AreaViewSet, basename='areas')
# router.register('skills', views.SkillViewSet, basename='skills')




urlpatterns = [
    path('', include(router.urls)),
    path('payment_stripe/payment/', StripeCheckoutViewSet.as_view({'post': 'create'}), name='create_invoice'),
    path('payment_success/', StripeCheckoutViewSet.as_view({'get': 'retrieve_payment'}), name='payment-success'),
    path('invoices/', StripeCheckoutViewSet.as_view({'get': 'list_invoices'}), name='list_invoices'),
]