from jobs.models import Job, Rating
from jobs import serializers, perms
from jobs import paginators
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from jobs import dao
from .models import JobApplication, Company, JobSeeker, User, Notification, Like, Status, Invoice
from .serializers import (JobApplicationSerializer, RatingSerializer, Career, EmploymentType, Area, JobSeekerCreateSerializer
                          ,AuthenticatedJobSerializer, LikeSerializer, JobSerializer, JobCreateSerializer,
                          JobApplicationStatusSerializer, NotificationSerializer,Skill, SkillSerializer, AreaSerializer, InvoiceSerializer)
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .paginators import LikedJobPagination
from datetime import datetime
from .filters import JobFilter
from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .schemas import apply_job_schema, jobSeeker_create_schema, employer_create_schema, num_application_schema

from jobPortal import settings
import stripe
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView



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
        """ THANH TOÁN """
        try:
            # Lấy price_id từ request body
            price_id = request.data.get('price_id')

            if not price_id:
                return Response({"error": "Price ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Tạo session thanh toán với price_id được gửi từ front-end
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price_id,  # Dùng price_id từ yêu cầu
                        'quantity': 1,
                    },
                ],
                payment_method_types=['card'],
                mode='payment',
                success_url=settings.SITE_URL + '/payment_success?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL + '?canceled=true',
            )

             # Save the session to the database with a pending state
            invoice = Invoice(
                user=request.user,
                stripe_session_id=checkout_session.id,
                amount_total=0.00
            )
            invoice.save()

            return Response({"url": checkout_session.url}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': 'Something went wrong: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

     # xem chi tiết hóa đơn
    def retrieve(self, request, session_id=None, *args, **kwargs):  # Đảm bảo session_id được nhận từ tham số
        """ CHI TIẾT HÓA ĐƠN """
        try:
            # Tìm hóa đơn bằng stripe_session_id
            invoice = Invoice.objects.get(stripe_session_id=session_id, user=request.user)
            serializer = InvoiceSerializer(invoice)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            print(f"Session ID: {session_id}, User ID: {request.user.id}")  # Ghi lại thông tin
            return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # danh sách hóa đơn
    def list(self, request):
        """ DANH SÁCH HÓA ĐƠN """
        invoices = Invoice.objects.filter(user=request.user)
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


#     # CẬP NHẬT THÔNG TIN SAU THANH TOÁN
#     @action(detail=False, methods=['get'], url_path='payment-success')
#     def payment_success(self, request):
#         """ CẬP NHẬT THÔNG TIN SAU THANH TOÁN """
#         session_id = request.query_params.get('session_id')

#         if not session_id:
#             return Response({"error": "Session ID is required."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Lấy thông tin session từ Stripe
#             session = stripe.checkout.Session.retrieve(session_id)

#             if session.payment_status == 'paid':
#                 # Tìm hóa đơn trong database dựa trên session_id
#                 try:
#                     invoice = Invoice.objects.get(stripe_session_id=session_id, user=request.user)
#                 except Invoice.DoesNotExist:
#                     return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

#                 # Cập nhật thông tin thanh toán
#                 invoice.amount_total = session.amount_total / 100  # Số tiền trả về từ Stripe theo cent
#                 invoice.currency = session.currency
#                 invoice.payment_status = session.payment_status
#                 invoice.payment_date = timezone.now()

#                 # Lấy email khách hàng từ session nếu có
#                 if session.customer_details:
#                     invoice.customer_email = session.customer_details.email

#                 invoice.save()

#                 return Response({
#                     "message": "Payment successful",
#                     "invoice": {
#                         "invoice_id": invoice.id,
#                         "session_id": invoice.stripe_session_id,
#                         "amount_total": invoice.amount_total,
#                         "currency": invoice.currency,
#                         "payment_status": invoice.payment_status,
#                         "payment_date": invoice.payment_date,
#                         "customer_email": invoice.customer_email,
#                     }
#                 }, status=status.HTTP_200_OK)

#             else:
#                 return Response({"error": "Payment not successful"}, status=status.HTTP_400_BAD_REQUEST)

#         except stripe.error.StripeError as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         except Exception as e:
#             return Response({'error': 'Something went wrong: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# class InvoiceView(APIView):
#     def get(self, request, session_id):
#         try:
#             # Lấy session thanh toán từ Stripe bằng session_id
#             checkout_session = stripe.checkout.Session.retrieve(session_id)

#             # Lấy thông tin thanh toán từ PaymentIntent
#             payment_intent = stripe.PaymentIntent.retrieve(checkout_session.payment_intent)

#             # Trả về thông tin hóa đơn cho front-end
#             return Response({
#                 'id': payment_intent.id,
#                 'customer_email': checkout_session.customer_details['email'],
#                 'amount_total': payment_intent.amount / 100,  # Đơn vị từ cents sang tiền tệ
#                 'currency': payment_intent.currency,  # Tiền tệ của thanh toán
#                 'payment_status': payment_intent.status,
#                 'payment_date': payment_intent.created,
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



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

    # Ghi đè lại hàm TẠO JOB
    def create(self, request, *args, **kwargs):

        # Lấy toàn bộ dữ liệu từ request.data
        job_posting_data = request.data.copy()

        # Cập nhật trường company
        job_posting_data['company'] = request.user.company.id

        serializer = JobCreateSerializer(data= job_posting_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

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

    # API lấy danh sách các bài tuyển dụng đã apply của ứng viên (theo id bài tuyển dụng)
    # /jobs/<pk>/list_apply/
    @action(detail=True, methods=['get'])
    def list_apply(self, request, pk=None):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        job_applications = JobApplication.objects.filter(job=job)
        serializer = JobApplicationSerializer(job_applications, many=True)
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


    # Viết API ẩn bài đăng tuyển dựa theo ID (người dùng nhập)
    # /jobs/<pk>/hide_post/
    # @action(detail=True, methods=['post'])
    # def hide_job(self, request, pk=None):
    #     try:
    #         post = Job.objects.get(pk=pk)
    #         if request.method == 'POST':
    #             post.active = False
    #             post.save()
    #             return Response({"message": "Job hidden successfully."}, status=status.HTTP_200_OK)
    #         else:
    #             return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    #     except Job.DoesNotExist:
    #         return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)


    # API ứng tuyển vào một bài đăng tuyển dụng
    # /jobs/<pk>/apply/
    @action(methods=['post'], detail=True)
    @swagger_auto_schema(
        request_body= apply_job_schema
    )
    def apply(self, request, pk=None):
        try:
            # Kiểm tra xem bài đăng tuyển dụng tồn tại hay không
            job = get_object_or_404(Job, pk=pk)

            # Tạo một JobApplication mới
            job_application_data = {
                'job': job.id,
                'jobseeker': request.user.jobseeker.id,  # user đã được xác định ở middleware
                'is_student': request.data.get('is_student', False),
                # Lấy trường is_student từ request.data, mặc định là False nếu không có
                'date': datetime.now(),  # Sử dụng ngày giờ hiện tại cho trường date
                'status': request.data.get('status', 'Pending'),
                # Lấy trường status từ request.data, mặc định là 'Pending' nếu không có
                'content': request.data.get('content'),  # Lấy trường content từ request.data
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
            # Lấy bài đăng tuyển dụng từ pk
            job = get_object_or_404(Job, pk=pk)

            # Lấy đơn ứng tuyển từ application_id
            application = get_object_or_404(JobApplication, pk=application_id)

            # Kiểm tra xem đơn ứng tuyển có thuộc về bài đăng tuyển dụng không
            if application.job != job:
                return Response({"error": "Job application does not belong to this Job."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra quyền chỉnh sửa đơn ứng tuyển: Nhà tuyển dụng và admin mới được cập nhật
            # if not request.user.is_staff and request.user != application.company:
            if not (request.user.is_staff or request.user == job.company.user):
                return Response({"error": "You do not have permission to update this job application."},
                                status=status.HTTP_403_FORBIDDEN)

             # Cập nhật một phần của đơn ứng tuyển
            for k, v in request.data.items():
                if k == "status":
                    # Giả sử v là tên của trạng thái, tìm đối tượng Status tương ứng
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
                # Tạo một đánh giá mới
                user = getattr(request.user, 'jobseeker', None)
                if user:
                    rating = Rating.objects.create(
                        job=job,
                        rating=request.data.get('rating'),
                        comment=request.data.get('comment'),
                        jobseeker=jobseeker
                    )
                    serializer = RatingSerializer(rating)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    # Nếu không phải JobSeeker, trả về lỗi
                    return Response({"error": "User is not authorized to create a rating."},
                                    status=status.HTTP_403_FORBIDDEN)

        except Job.DoesNotExist:
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

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


    # API xóa rating trong bài đăng tuyển dụng => Xóa luôn các comment là con
    # /jobs/<pk>/rating/<rating_id>/delete/
    # @action(detail=True, methods=['delete'], url_path='rating/(?P<rating_id>\\d+)/delete', url_name='delete_rating')
    # def delete_rating(self, request, pk=None, rating_id=None):
    #     try:
    #         job = get_object_or_404(Job, pk=pk)
    #         rating = get_object_or_404(Rating, pk=rating_id)

    #         if rating.job != job:
    #             return Response({"error": "Rating does not belong to this job."},
    #                             status=status.HTTP_400_BAD_REQUEST)

    #         user = getattr(request.user, 'jobseeker', None) or getattr(request.user, 'company', None)
    #         if user != rating.jobseeker and user != rating.company and not request.user.is_staff:
    #             return Response({"error": "You do not have permission to delete this rating."},
    #                             status=status.HTTP_403_FORBIDDEN)

    #         rating.delete()
    #         return Response({"message": "Rating deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    #     except Job.DoesNotExist:
    #         return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
    #     except Rating.DoesNotExist:
    #         return Response({"error": "Rating not found."}, status=status.HTTP_404_NOT_FOUND)



class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.ListAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer
    # Dùng upload ảnh lên Cloud
    # parser_classes = [parsers.MultiPartParser, ]
    permission_classes = [IsAuthenticated]  # Chỉ cho phép truy cập khi đã đăng nhập

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
        # Đã được chứng thực rồi thì không cần truy vấn nữa => Xác định đây là người dùng luôn
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
        #     serializer.save(user=user)
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # else:
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            job_seeker = serializer.save(user=user)

        # Trả về dữ liệu với skills và areas
            response_data = serializer.data
            response_data['skills'] = SkillSerializer(job_seeker.skills, many=True).data
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


    # API xem thông báo
    # /applicants/notifications/
    @action(detail=False, methods=['get'], url_path='notifications')
    def get_notifications(self, request):
        user = request.user

        # Kiểm tra xem người dùng là admin hay không => admin thì xuất hết thông báo (sắp theo mới nhất)
        if user.is_staff or user.is_superuser:
            notifications = Notification.objects.all().order_by('-created_date')
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Nếu không phải admin, kiểm tra xem là applicant hay không
        if not hasattr(user, 'jobseeker'):
            return Response({'error': 'User is not an Job Seeker'}, status=status.HTTP_400_BAD_REQUEST)

        job_seeker = user.jobseeker
        notifications = Notification.objects.filter(user=job_seeker.user).order_by('-created_date')  # (sắp theo mới nhất)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == 'get_list_job_apply':
            return serializers.JobSerializer

        return self.serializer_class

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


class SkillViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Skill.objects.all()
    serializer_class = serializers.SkillSerializer
