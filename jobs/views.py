from jobs.models import Job, Rating
from jobs import serializers, perms, utils
from jobs import paginators
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from jobs import dao
from .dao import get_paid_invoices, get_latest_paid_invoice
from .models import JobApplication, Company, JobSeeker, User, Like, Status, Invoice
from .serializers import (JobApplicationSerializer, RatingSerializer, Career, EmploymentType, Area, JobSeekerCreateSerializer
                          ,AuthenticatedJobSerializer, LikeSerializer, JobSerializer, JobCreateSerializer,
                          JobApplicationStatusSerializer, AreaSerializer)
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .paginators import LikedJobPagination
from datetime import datetime, timedelta
from .filters import JobFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .schemas import jobSeeker_create_schema, employer_create_schema, num_application_schema

from jobPortal import settings
import stripe #Thanh toán với Stripe
from google.oauth2 import id_token  # Dùng để xác thực id_token của Google
from google.auth.transport import requests as gg_requests  # Dùng để gửi request xác thực token
from rest_framework.permissions import AllowAny
import redis
# Kết nối tới Redis
redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

# Create your views here.
# Làm việc với GenericViewSet
# Một ViewSet có thể add nhiều api
# ListAPIView = GET : Xem danh sách
# RetrieveAPIView = GET : Xem chi tiết
# DestroyAPIView = DELETE : Xóa
# CreateAPIView = POST : Tạo mới
# UpdateAPIView = PUT/PATCH = Cập nhật toàn bộ/ một phần
# ListCreateAPIView = GET + POST : Xem danh sách + tạo mới
# RetrieveUpdateAPIView = GET + PUT + PATCH : Xem chi tiết + cập nhật toàn phần + cập nhật một phần
# RetrieveDestroyAPIView = GET + DELETE : Xem chi tiết + xóa
# RetrieveUpdateDestroyAPIView = GET + PUT + PATCH + DELETE : Xem chi tiết + cập nhật toàn phần + cập nhật một phần + xóa


#######      THANH TOÁN   ########
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeCheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã xác thực

    def create(self, request):
        try:
            # Lấy price_id từ request body
            price_id = request.data.get('price_id')
            product_item = request.data.get('product_item')
            daily_post_limit = request.data.get('daily_post_limit')

            if not price_id:
                return Response({"error": "Price ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Check Redis for the user's purchase restriction
            user_id = request.user.id
            redis_key = f"purchase_limit:{user_id}"

            try:
                if redis_client.exists(redis_key):
                    return Response(
                        {"error": "Hãy kiểm tra lịch sử đơn hàng. Bạn chỉ có thể mua gói mới sau khi hết hạn!"},
                        status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "Redis connection failed: " + str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Tạo session thanh toán với price_id được gửi từ front-end
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                payment_method_types=['card'],
                mode='payment',
                success_url=settings.SITE_URL + '/payment_success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL + '?canceled=true',
            )

            # Lưu session với trạng thái pending
            invoice = Invoice(
                user=request.user,
                stripe_session_id=checkout_session.id,
                amount_total=0.00,  # Tổng số tiền sẽ được cập nhật sau
                currency='VNĐ',  # Bạn có thể điều chỉnh nếu cần
                payment_status='pending',  # Trạng thái ban đầu là pending
                product_item=product_item,  # Lưu tên sản phẩm
                daily_post_limit =daily_post_limit #Số lần đăng tin/1ngày
            )
            invoice.save()

            # Set the purchase restriction in Redis for 3 days
            redis_client.setex(redis_key, timedelta(days=3), "restricted")

            return Response({"url": checkout_session.url}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': 'Something went wrong: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def retrieve_payment(self, request):
        session_id = request.GET.get('session_id')

        if not session_id:
            return Response({"error": "Session ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Lấy thông tin session từ Stripe để cập nhật thông tin hóa đơn
            checkout_session = stripe.checkout.Session.retrieve(session_id)

            # Lấy hóa đơn từ database bằng session_id
            invoice = Invoice.objects.get(stripe_session_id=session_id)

            # Cập nhật thông tin thanh toán từ Stripe vào hóa đơn
            invoice.amount_total = checkout_session.amount_total / 100  # Chuyển từ cents sang đơn vị tiền tệ
            invoice.payment_status = checkout_session.payment_status
            invoice.customer_email = checkout_session.customer_details.email
            invoice.payment_date = timezone.now()  # Cập nhật thời gian thanh toán

            # Lưu lại hóa đơn sau khi cập nhật
            invoice.save()

            # Chuyển thông tin hóa đơn thành định dạng JSON
            invoice_data = {
                "session_id": invoice.stripe_session_id,
                "amount_total": str(invoice.amount_total),
                "currency": invoice.currency,
                "payment_status": invoice.payment_status,
                "payment_date": invoice.payment_date,
                "customer_email": invoice.customer_email,
                "product_item": invoice.product_item,
                "daily_post_limit": invoice.daily_post_limit, #số lần đăng tin/1 ngày
                "expiry_date": invoice.expiry_date  #ngày hết hạn gói đăng tin
            }

            return Response(invoice_data, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_invoices(self, request):
        try:
            # Lấy người dùng hiện tại từ request
            user = request.user

            # Lấy danh sách các hóa đơn của người dùng (truy vấn ở dao)
            invoices = get_paid_invoices(user)

            # Chuyển đổi các hóa đơn thành dạng JSON để trả về
            invoice_list = []
            for invoice in invoices:
                invoice_list.append({
                    "session_id": invoice.stripe_session_id,
                    "amount_total": str(invoice.amount_total),
                    "currency": invoice.currency,
                    "payment_status": invoice.payment_status,
                    "payment_date": invoice.payment_date,
                    "customer_email": invoice.customer_email,
                    "product_item": invoice.product_item,
                    "daily_post_limit": invoice.daily_post_limit,
                    "expiry_date": invoice.expiry_date
                })

            # Trả về danh sách hóa đơn dưới dạng JSON
            return Response({"invoices": invoice_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(active=True).order_by('id')
    queryset = Job.objects.order_by('id')
    serializer_class = serializers.JobSerializer

    # Thiết lập lớp phân trang (pagination class) cho một API view cụ thể.
    pagination_class = paginators.JobPaginator

    # Phần filter
    # GET /job/?min_salary=1000000:
    # Lấy danh sách tất cả các bài đăng có mức lương yêu cầu từ 1,000,000 VND trở lên
    # GET /job/?max_salary=2000000:
    # Lấy danh sách tất cả các bài đăng có mức lương yêu cầu dưới 2,000,000 VND.
    # GET /job/?min_salary=1000000&max_salary=2000000:
    # Lấy danh sách các bài đăng có mức lương yêu cầu từ 1,000,000 VND đến 2,000,000 VND.
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter

    # parser_classes = [parsers.MultiPartParser, ]
    def get_permissons(self):
        if self.action in ['destroy']:
            return [perms.EmIsAuthenticated()]
        return [permissions.AllowAny()]

    #ghi đè json
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.JobCreateSerializer

        if self.action == 'create_rating':
            return serializers.RatingSerializer

        if self.action == 'get_liked_job':
            return serializers.AuthenticatedJobSerializer

        if self.action == 'partial_update_rating':
            return serializers.RatingSerializer
        if self.action == 'list_apply':
            return serializers.JobApplicationStatusSerializer

        if self.action == 'partial_update_application':
            return serializers.JobApplicationStatusSerializer

        return self.serializer_class

    # Không endpoint
    # Tìm kiếm các bài đăng theo tiêu đề: /job/?title=example_title
    # Tìm kiếm các bài đăng theo id của nhà tuyển dụng: /job/?employer_id=example_employer_i
    # Tìm kiếm các bài đăng theo ngành nghề: /job/?career=example_career
    # Tìm kiếm các bài đăng theo loại hình công việc: /job/?employment_type=example_employment_type
    # Tìm kiếm các bài đăng theo địa điểm: /job/?location=example_location
    # Tìm kiếm kết hợp các tiêu chí: /job/?title=example_title&employer_id=example_employer_id&career=example_career

    def get_queryset(self):
        # Code xử lý lọc dữ liệu ở đây
        queries = self.queryset.order_by('-id')

        # LỌC CÁC BÀI ĐĂNG ĐÃ HẾT HẠN
        # for q in queries:
        #     if q.deadline <= timezone.now().date():
        #         q.active = False
        #         q.save()
        #     queries = queries.filter(active=True)

        # Kiểm tra nếu hành động là 'list' (tức là yêu cầu danh sách các bài đăng)
        if self.action == 'list':
            title = self.request.query_params.get('title')
            company_id = self.request.query_params.get('company_id')
            career = self.request.query_params.get('career')
            employment_type = self.request.query_params.get('employmenttype')
            location = self.request.query_params.get('location')

            # Lọc theo tiêu đề
            if title:
                queries = queries.filter(title__icontains=title)

            # Lọc theo id của nhà tuyển dụng
            if company_id:
                queries = queries.filter(company_id=company_id)

            # Lọc theo ngành nghề
            if career:
                queries = queries.filter(career__name__icontains=career)

            # Lọc theo loại hình công việc
            if employment_type:
                queries = queries.filter(employmenttype__type__icontains=employment_type)

            # Lọc theo địa điểm
            if location:
                queries = queries.filter(location__icontains=location)

        return queries

    #TẠO BÀI TUYỂN DỤNG
    def create(self, request, *args, **kwargs):
        user_id = request.user.id
        today_date = datetime.now().date()
        redis_key = f"job_posted:{user_id}:{today_date}"

        # Truy vấn hóa đơn gần nhất của người dùng
        invoice = get_latest_paid_invoice(user_id)

        # Kiểm tra nếu không có hóa đơn hoặc hóa đơn đã hết hạn
        if not invoice or invoice.is_expired:
            daily_post_limit = 1  # Chỉ được đăng 1 bài khi không có gói hợp lệ
        else:
            daily_post_limit = invoice.daily_post_limit  # Lấy số lượng bài đăng từ hóa đơn

        # Kiểm tra số bài đã đăng trong ngày qua Redis
        current_post_count = redis_client.get(redis_key)
        current_post_count = int(current_post_count) if current_post_count else 0

        if current_post_count >= daily_post_limit:
            return Response({"detail": f"Đã đạt giới hạn đăng {daily_post_limit} bài trong 1 ngày."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Tạo bài đăng tuyển dụng mới
        job_posting_data = request.data.copy()
        job_posting_data['company'] = request.user.company.id

        serializer = JobCreateSerializer(data=job_posting_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Cập nhật số lượng bài đã đăng vào Redis
        redis_client.set(redis_key, current_post_count + 1, ex=timedelta(days=1))

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    # Ghi đè lại hàm xóa job
    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        if request.user != job.company.user:
            return Response({"error": "You do not have permission to delete this job."},
                                status=status.HTTP_403_FORBIDDEN)
        job.delete()
        return Response({"message": "Job deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    # API lọc bài tuyển dụng theo mức lương
    # /recruitments_post/filter_salary/?min_salary=5000000 => bài đăng có mức lương từ 5,000,000 VND trở lên
    # /recruitments_post/filter_salary/?max_salary=10000000 => bài đăng có mức lương dưới 10,000,000 VND
    # /recruitments_post/filter_salary/?min_salary=5000000&max_salary=10000000 => bài đăng có mức lương từ 5000000 đến 10000000
    @action(detail=False, methods=['get'])
    def filter_salary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        min_salary = request.query_params.get('min_salary')
        max_salary = request.query_params.get('max_salary')

        if min_salary is not None:
            queryset = queryset.filter(salary__gte=min_salary)
        if max_salary is not None:
            queryset = queryset.filter(salary__lte=max_salary)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # API cập nhật active bài tuyển dụng => dùng để ẩn bài tuyển dụng
    @action(detail=True, methods=['patch'])
    def toggle_active(self, request, pk=None):
        job = get_object_or_404(Job, pk=pk)
        if job.company == request.user.company:
            job.active = not job.active
            job.save()
            serializer = JobSerializer(job)
            return Response({'status': 'success', 'data': serializer.data})
        else:
            return Response({'status': 'error', 'message': 'Unauthorized'}, status=403)

    # API xem danh sách bài đăng tuyển dụng phổ biến (được apply nhiều) (giảm dần theo số lượng apply)
    # /recruitments_post/popular/
    @action(detail=False, methods=['get'])
    def popular(self, request):
        try:
            # Lấy danh sách các bài đăng tuyển dụng được sắp xếp theo số lượng apply giảm dần
            # Truy vấn ngược
            jobs = dao.recruiment_posts_by_appy()
            # Phân trang cho danh sách bài đăng
            paginator = self.pagination_class()
            paginated_jobs = paginator.paginate_queryset(jobs, request)

            serializer = serializers.JobSerializer(paginated_jobs, many=True)

            paginated_data = paginator.get_paginated_response(serializer.data)


            return Response(paginated_data.data, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

    # API Đếm số lượng apply của 1 bài đăng theo id
    # /recruitments_post/<pk>/num_applications
    @action(detail=True, methods=['get'])
    @swagger_auto_schema(
        operation_description="Get the number of applications for a specific job posting",
        responses={
            200: openapi.Response(
                description="Number of applications",
                schema=num_application_schema
            )
        }
    )

    def num_applications(self, request, pk=None):
        try:
            num_applications = dao.count_apply_by_id_recruiment_post(pk)
            # Trả về số lượng đơn ứng tuyển dưới dạng JSON
            return Response({"num_applications": num_applications}, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

    # API lấy ds các ứng viên ứng tuyển vào 1 job
    # /jobs/<pk>/list_apply/
    @action(detail=True, methods=['get'])
    def list_apply(self, request, pk=None):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        job_applications = JobApplication.objects.filter(job=job)
        serializer = JobApplicationStatusSerializer(job_applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # API xem chi tiết một đơn ứng tuyển của một bài đăng tuyển dụng
    # /jobs/<pk>/applications/<application_id>/
    @action(detail=True, methods=['get'], url_path='applications/(?P<application_id>\d+)', url_name='view_application')
    def view_application(self, request, pk=None, application_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            job = get_object_or_404(Job, pk=pk)

            # Lấy đơn ứng tuyển từ application_id
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.job != job:
                return Response({"error": "Job application does not belong to this Job."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Serialize đơn ứng tuyển và trả về chi tiết
            serializer = JobApplicationSerializer(application)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job application not found."}, status=status.HTTP_404_NOT_FOUND)

    # API like 1 bài tuyển dụng
    # /jobs/<pk>/like/
    @action(methods=['post'], url_path='like', detail=True)
    def add_like(self, request, pk):
        user = getattr(request.user, 'jobseeker', None) or getattr(request.user, 'company', None)
        if user:
            li, created = Like.objects.get_or_create(
                    job=self.get_object(),
                    **{user.__class__.__name__.lower(): user}
                )
            if not created:
                li.active = not li.active
                li.save()
            return Response(AuthenticatedJobSerializer(self.get_object()).data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "User is not an applicant or employer."},
                            status=status.HTTP_400_BAD_REQUEST)

    #API kiểm tra trạng thái like
    # /jobs/<pk>/check_liked/
    @action(methods=['get'], url_path='check_liked', detail=True)
    def check_like(self, request, pk):
        job = self.get_object()
        user = getattr(request.user, 'jobseeker', None) or getattr(request.user, 'company', None)
        liked = Like.objects.filter(job=job, **{user.__class__.__name__.lower(): user}, active=1).exists()
        if not liked:
            return Response({'liked': False}, status=status.HTTP_200_OK)
        return Response({'liked': True }, status=status.HTTP_200_OK)


    # API lấy danh sách các bài yêu thích của user
    @action(methods=['get'], detail=False)
    def get_liked_job(self, request, pk=None):
        try:
            user = getattr(request.user, 'jobseeker', None) or getattr(request.user, 'company', None)
            liked = Like.objects.filter(
                **{user.__class__.__name__.lower(): user},
                active=True
            )
            paginator = LikedJobPagination()
            paginated_liked = paginator.paginate_queryset(liked, request)

            return paginator.get_paginated_response(LikeSerializer(paginated_liked, many=True).data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)



    # API ỨNG TUYỂN vào một bài đăng tuyển dụng
    # /jobs/<pk>/apply/
    @action(methods=['post'], detail=True)
    def apply(self, request, pk=None):
        try:
            # Kiểm tra xem bài đăng tuyển dụng tồn tại hay không
            job = get_object_or_404(Job, pk=pk)

            # Tạo một JobApplication mới
            job_application_data = {
                'job': job.id, #sử dụng từ url
                'jobseeker': request.user.jobseeker.id,  # user đã được xác định ở middleware
                'is_student': request.data.get('is_student', False),
                'date': datetime.now(),
                'status': request.data.get('status', 'Pending'),
                'content': request.data.get('content'),
            }
            serializer = JobApplicationSerializer(data=job_application_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Trả về thông tin về ứng tuyển mới được tạo dưới dạng JSON response
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)


    # API cập nhật một phần đơn ứng tuyển vào bài đăng tuyển dụng
    # /jobs/{pk}/applications/{application_id}/partial-update/
    @action(detail=True, methods=['patch'], url_path='applications/(?P<application_id>\d+)/partial-update',
            url_name='partial_update_application')
    def partial_update_application(self, request, pk=None, application_id=None):
        try:
            job = get_object_or_404(Job, pk=pk)
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.job != job:
                return Response({"error": "Job application does not belong to this Job."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền chỉnh sửa đơn ứng tuyển: Nhà tuyển dụng và admin mới được cập nhật
            if not (request.user.is_staff or request.user == job.company.user):
                return Response({"error": "You do not have permission to update this job application."},
                                status=status.HTTP_403_FORBIDDEN)

             # Cập nhật một phần của đơn ứng tuyển
            for k, v in request.data.items():
                if k == "status":
                    status_instance = get_object_or_404(Status, role=v)
                    setattr(application, k, status_instance)
                else:
                    setattr(application, k, v)
            application.save()

            return Response(serializers.JobApplicationSerializer(application).data, status=status.HTTP_200_OK)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job application not found."}, status=status.HTTP_404_NOT_FOUND)


    # API xóa đơn ứng tuyển vào bài đăng tuyển dụng
    # /jobs/{pk}/applications/{application_id}/delete/
    @action(detail=True, methods=['delete'], url_path='applications/(?P<application_id>\d+)/delete',
            url_name='delete_application')
    def delete_application(self, request, pk=None, application_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            job = get_object_or_404(Job, pk=pk)

            # Lấy đơn ứng tuyển từ application_id
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.job != job:
                return Response({"error": "Job application does not belong to this Job."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền xóa đơn ứng tuyển
            if request.user != application.jobseeker.user and not request.user.is_staff:
                return Response({"error": "You do not have permission to delete this job application."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa đơn ứng tuyển
            application.delete()
            return Response({"message": "Job application deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        except JobApplication.DoesNotExist:
            return Response({"error": "Job application not found."}, status=status.HTTP_404_NOT_FOUND)


    # API đánh giá một bài tuyển dụng
    # /jobs/<pk>/ratings/
    @action(methods=['get', 'post'], detail=True, url_path='ratings', url_name='ratings')
    def create_rating(self, request, pk=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            job = get_object_or_404(Job, pk=pk)

            if request.method == 'GET':
                # Lấy danh sách rating của bài đăng
                ratings = job.rating_set.all()

                # Phân trang danh sách rating
                paginator = paginators.RatingPaginator()
                paginated_ratings = paginator.paginate_queryset(ratings, request)

                # Serialize danh sách rating
                serializer = RatingSerializer(paginated_ratings, many=True)

                # Trả về danh sách rating đã phân trang
                return paginator.get_paginated_response(serializer.data)

            elif request.method == 'POST':
                try:
                    jobseeker = request.user.jobseeker
                except JobSeeker.DoesNotExist:
                    raise PermissionDenied("Chỉ JobSeeker mới được phép tạo đánh giá.")

                # Tạo một đánh giá mới
                rating = Rating.objects.create(
                    job=job,
                    jobseeker=jobseeker,
                    rating=request.data.get('rating'),
                    comment=request.data.get('comment'),
                )
                serializer = RatingSerializer(rating)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


    # API cập nhật rating một bài đăng tuyển dụng
    # /jobs/{pk}/ratings/{rating_id}/partial-update/
    @action(detail=True, methods=['patch'], url_path='ratings/(?P<rating_id>\d+)/partial-update')
    def partial_update_rating(self, request, pk=None, rating_id=None):
        try:
            job = get_object_or_404(Job, pk=pk)# Lấy bài đăng tuyển dụng từ pk
            rating = get_object_or_404(Rating, pk=rating_id)# Lấy comment từ comment_id
            if rating.job != job:   # Kiểm tra xem comment có thuộc về bài đăng tuyển dụng không
                return Response({"error": "Rating does not belong to this job."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Kiểm tra quyền chỉnh sửa Rating: chỉ người tạo mới được chỉnh sửa, admin cũng không được cập nhật
            user = getattr(request.user, 'jobseeker', None) or getattr(request.user, 'company', None)
            if user != rating.jobseeker and user != rating.company:
                return Response({"error": "You do not have permission to delete this rating."},
                            status=status.HTTP_403_FORBIDDEN)

            # Serialize và trả về thông tin cập nhật của rating
            serializer = RatingSerializer(rating, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        except Rating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)


    # API xóa rating của một bài đăng tuyển dụng
    # /jobs/<pk>/ratings/<rating_id>/delete/
    @action(detail=True, methods=['delete'], url_path='ratings/(?P<rating_id>\d+)/delete',
            url_name='delete_rating')
    def delete_rating(self, request, pk=None, rating_id=None):
        try:
            # Lấy bài đăng tuyển dụng từ pk
            job = get_object_or_404(Job, pk=pk)

            # Lấy rating từ rating_id
            rating = get_object_or_404(Rating, pk=rating_id)

            # Kiểm tra xem rating có thuộc về bài đăng tuyển dụng không
            if rating.job != job:
                return Response({"error": "Rating does not belong to this recruitment post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền xóa rating: chỉ có người tạo và admin mới được xóa
            user = getattr(request.user, 'jobseeker', None) or getattr(request.user, 'company', None)
            if user != rating.jobseeker and user != rating.company and not request.user.is_staff:
                return Response({"error": "You do not have permission to delete this comment."},
                                status=status.HTTP_403_FORBIDDEN)

            # Xóa rating
            rating.delete()

            return Response({"message": "Rating deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        except Rating.DoesNotExist:
            return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)



class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.ListAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer
    # permission_classes = [IsAuthenticated]  # Chỉ cho phép truy cập khi đã đăng nhập

    def get_serializer_class(self):
        if self.action == 'create_applicant':
            return serializers.JobSeekerSerializer
        if self.action == 'create_employer':
            return serializers.CompanyCreateSerializer
        if self.action == 'list':
            return serializers.UserDetailSerializer

        return self.serializer_class


    # API xem chi tiết tài khoản hiện (chỉ xem được của mình) + cập nhật tài khoản (của mình)
    # /users/current-user/
    @action(methods=['get'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        # Đã được chứng thực rồi thì không cần truy vấn nữa => Xác định đây là người dùng luôn
        # user = user hiện đang đăng nhập
        user = request.user
        if user.is_authenticated:
            return Response(serializers.UserDetailSerializer(user).data)
        else:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializers.UserDetailSerializer(user).data)

    # API cập nhật một phần cho User
    @action(methods=['patch'], url_path='patch-current-user', detail=False)
    def patch_current_user(self, request):
        # user = user hiện đang đăng nhập
        user = request.user
        # Khi so sánh thì viết hoa hết
        if request.method.__eq__('PATCH'):

            for k, v in request.data.items():
                # Thay vì viết user.first_name = v
                setattr(user, k, v)
            user.save()

        return Response(serializers.UserSerializer(user).data)


    # API xóa tài khoản
    # /users/<user_id>/delete-account/
    @action(detail=True, methods=['delete'], url_path='delete-account')
    def delete_account(self, request, pk=None):
        try:
            # Lấy user từ pk hoặc raise 404 nếu không tìm thấy
            user = get_object_or_404(User, pk=pk)

            # Kiểm tra quyền hạn: Chỉ người tạo mới có quyền xóa hoặc admin
            if request.user.is_staff or request.user == user:
                user.delete()
                return Response({"message": "User account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "You do not have permission to delete this user account."},
                                status=status.HTTP_403_FORBIDDEN)

        except User.DoesNotExist:
            return Response({"error": "User account not found."}, status=status.HTTP_404_NOT_FOUND)

    # API tạo APPLICANT
    # /users/<user_id>/create_applicant/
    @action(detail=True, methods=['post'], url_path='create_applicant')
    @swagger_auto_schema(
        request_body= jobSeeker_create_schema
    )
    def create_jobSeeker(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        serializer = serializers.JobSeekerCreateSerializer(data=request.data)
        if serializer.is_valid():
            job_seeker = serializer.save(user=user)

        # Trả về dữ liệu với skills và areas
            response_data = serializer.data
            # response_data['skills'] = SkillSerializer(job_seeker.skills, many=True).data
            response_data['areas'] = AreaSerializer(job_seeker.areas, many=True).data

            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # /users/<user_id>/create_employer/
    @action(detail=True, methods=['post'], url_path='create_employer')
    @swagger_auto_schema(
        request_body= employer_create_schema
    )
    def create_company(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        serializer = serializers.CompanyCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=['post'], url_path='google-login', detail=False, permission_classes=[AllowAny])
    def google_login(self, request):
        id_token_from_client = request.data.get('id_token')
        # print("Received ID token:", id_token_from_client)
        if not id_token_from_client:
            return Response({'error': 'Mã xác thực không được cung cấp'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_from_client,
                gg_requests.Request(),
                audience='611474340578-ilfvgku96p9c6iim54le53pnhimvi8bv.apps.googleusercontent.com'
            )
            print("ID info:", idinfo)
            user_email = idinfo.get('email')
            user_name = idinfo.get('name')
            user_avatar = idinfo.get('picture')

            if not user_email:
                return Response({'error': 'Không tìm thấy email trong mã xác thực'}, status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra xem người dùng đã tồn tại hay chưa
            user = User.objects.filter(email=user_email).first()  # Tìm người dùng theo email
            created = False

            if user is None:
                # Nếu không tồn tại người dùng, tạo người dùng mới
                user = User.objects.create(
                    username=user_name,
                    email=user_email,
                    avatar=utils.upload_image_from_url(user_avatar),
                    role=0  # Gán role = 0 mặc định cho người dùng mới
                )
                created = True  # Đánh dấu là người dùng mới được tạo

                # Nếu người dùng đã tồn tại, không cần tạo mới, chỉ cần cập nhật avatar nếu cần
            else:
                user.avatar = utils.upload_image_from_url(user_avatar)
                user.save()

            access_token, refresh_token = utils.create_user_token(user=user)
            if not access_token or not refresh_token:
                return Response({'error': 'Token creation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                },
                'created': created,
                'token': {
                    'access_token': access_token.token,
                    'expires_in': 36000,
                    'refresh_token': refresh_token.token,
                    'token_type': 'Bearer',
                    'scope': access_token.scope,
                }
            })
        except ValueError as e:
            print(e)
            return Response({'error': 'Xác thực không thành công', 'details': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class CompanyViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.CreateAPIView, generics.UpdateAPIView):
    queryset = Company.objects.all()
    serializer_class = serializers.CompanySerializer

    def get_serializer_class(self):
        if self.action == 'get_list_job':
            return serializers.JobSerializer
        if self.action == 'list_applications':
            return JobApplicationStatusSerializer
        else:
            return serializers.CompanySerializer

    # Tạo mới Employer
    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role == 1:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)  # Lưu đối tượng Employer vào cơ sở dữ liệu
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'User is not a verified company.'}, status=status.HTTP_403_FORBIDDEN)

    # API lấy danh sách đơn ứng tuyển vào các job của NTD tạo ra
    @action(detail=False, methods=['get'])
    def list_applications(self, request):
        user = request.user
        if not hasattr(user, 'company'):  # Nếu không phải là công ty
            return Response({'detail': 'User is not  an Employer'}, status=status.HTTP_403_FORBIDDEN)

        # Lấy công ty của người dùng
        company = user.company
        # Lấy tất cả các công việc của công ty
        jobs = Job.objects.filter(company=company)
        # Lấy tất cả các ứng viên ứng tuyển vào các công việc của công ty
        applications = JobApplication.objects.filter(job__in=jobs)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    # API xem danh sách các bài tuyển dụng mà user đó đã đăng (khi user là 1 employer)
    @action(methods=['get'], detail=False, url_path='list_job')
    def get_list_job(self, request, pk=None):
        user = request.user

        # Kiểm tra xem user hiện tại có phải employer không
        if not hasattr(user, 'company'):
            return Response({'error': 'User is not an Employer'}, status=status.HTTP_400_BAD_REQUEST)

        jobs = Job.objects.filter(company__user=user)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class JobSeekerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = JobSeeker.objects.all()
    serializer_class = serializers.JobSeekerSerializer
    # Thiết lập lớp phân trang (pagination class) cho một API view cụ thể.
    pagination_class = paginators.JobPaginator

    # Không có endpoint
    # Lấy danh sách ứng viên có kỹ năng là "Python" và "Java":
    # /applicants/?skills=Python&skills=Java
    # Lấy danh sách ứng viên muốn làm việc ở khu vực "quận 3":
    # /applicants/?areas=quan3
    # Lấy danh sách ứng viên có kỹ năng là "Python" và muốn làm việc ở khu vực "Hà Nội":
    # /applicants/?skills=Python&areas=Hanoi

    def create(self, request, *args, **kwargs):
        user = request.user

        if user.role == 0:
            serializer = JobSeekerCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)  # Lưu đối tượng Employer vào cơ sở dữ liệu
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'User is not a verified applicant.'}, status=status.HTTP_403_FORBIDDEN)

    def get_queryset(self):
        skills = self.request.query_params.getlist('skills')
        areas = self.request.query_params.getlist('areas')
        careers = self.request.query_params.getlist('careers')
        position = self.request.query_params.get('position')

        queryset = JobSeeker.objects.all()

        if skills:
            # .distinct() trong Django ORM được sử dụng để loại bỏ các bản ghi trùng lặp từ kết quả truy vấn
            queryset = queryset.filter(skills__name__in=skills).distinct()

        if areas:
            queryset = queryset.filter(areas__name__in=areas).distinct()

        if careers:
            queryset = queryset.filter(career__name__in=careers)
        if position:
            queryset = queryset.filter(position__icontains=position)
        return queryset



    # API xem danh sách các bài tuyển dụng mà user đó đã apply (khi user là 1 applicant)
    @action(methods=['get'], detail=False, url_path='list_job_apply')
    def get_list_job_apply(self, request):
        user = request.user

        # Kiểm tra xem user hiện tại có phải applicant không
        if not hasattr(user, 'jobseeker'):
            return Response({'error': 'User is not an Job Seeker'}, status=status.HTTP_400_BAD_REQUEST)

        jobapplications = JobApplication.objects.filter(jobseeker__user=user, job__active=True)
        serializer = JobApplicationStatusSerializer(jobapplications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CareerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Career.objects.all()
    serializer_class = serializers.CareerSerializer


class EmploymentTypeViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = EmploymentType.objects.all()
    serializer_class = serializers.EmploymentTypeSerializer


class AreaViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Area.objects.all()
    serializer_class = serializers.AreaSerializer


# class SkillViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
#     queryset = Skill.objects.all()
#     serializer_class = serializers.SkillSerializer
