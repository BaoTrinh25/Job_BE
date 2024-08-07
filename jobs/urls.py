from rest_framework import routers
from jobs import views
from django.urls import path, include
from .views import refresh_token, login, logout
from .views import google_login

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
router.register('skills', views.SkillViewSet, basename='skills')



urlpatterns = [
    path('', include(router.urls)),
    path('refresh_token/', refresh_token, name='refresh_token'),
    # path('login/', login, name='login'),
    # path('logout/', logout, name='logout'),
    path('auth_google', google_login, name='google_login'),

    # Phần OAuth2
    # path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

]