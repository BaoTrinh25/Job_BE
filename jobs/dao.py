from jobs.models import (JobApplication, Job, Company, JobSeeker, EmploymentType,
                         Career, Invoice,
                         )
from django.db.models import Count, Q, Avg
from django.db.models.functions import ExtractQuarter, ExtractYear, TruncMonth

#Truy vấn và trả về danh sách các hóa đơn đã thanh toán của người dùng.
def get_paid_invoices(user):
    return Invoice.objects.filter(user=user, payment_status='paid')

# Truy vấn hóa đơn được thanh toán gần nhất của người dùng.
def get_latest_paid_invoice(user_id):
    return Invoice.objects.filter(user_id=user_id, payment_status='paid').order_by('-payment_date').first()


# Theo đề bài: Viết câu truy vấn đếm số đơn ứng tuyển của sinh viên theo nghề qua các quý và năm
def count_job_application_quarter_career():
    queryset = JobApplication.objects.filter(is_student=True) \
        .annotate(quarter=ExtractQuarter('date'), year=ExtractYear('date')) \
        .values('job__career__name', 'quarter', 'year') \
        .annotate(total_applications=Count('id')).order_by('total_applications', 'year', 'quarter')

    return queryset


# Tìm danh sách các bài đăng tuyển dụng được sắp xếp theo số lượng apply giảm dần
def recruiment_posts_by_appy():
    return Job.objects.filter(active=True).annotate(
                num_applications=Count('jobapplication')).order_by('-num_applications')

# Đếm số lượng đơn ứng tuyển theo mỗi bài đăng tuyển dụng (id mình nhập vào)
def count_apply_by_id_recruiment_post(id):
    # Lấy bài đăng tuyển dụng theo pk (primary key)
    job = Job.objects.get(pk=id)
    # Đếm số lượng đơn ứng tuyển cho bài đăng này
    return job.jobapplication_set.count()  # jobapplication_set : truy vấn ngược


# Đếm số lượng bài tuyển dụng của mỗi nhà tuyển dụng
def count_recruitment_posts_per_employer():
    return Company.objects.annotate(num_recruitment_posts=Count('job'))


# Đếm số lượng đơn xin việc của mỗi ứng viên
def count_job_applications_per_applicant():
    return JobSeeker.objects.annotate(num_job_applications=Count('jobapplication'))


# Đếm số lượng bài tuyển dụng theo loại công việc
def count_recruitment_posts_per_employment_type():
    return EmploymentType.objects.annotate(num_recruitment_posts=Count('job'))


# Đếm số lượng bài tuyển dụng theo ngành nghề
def count_recruitment_posts_per_career():
    return Career.objects.annotate(num_recruitment_posts=Count('job'))


# Đếm số lượng đơn xin việc theo tháng
def count_job_applications_per_month():
    return JobApplication.objects.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_applications=Count('id')
    )

# Đếm số bài tuyển dụng theo nghề
def count_recruitment_posts_by_career():
    return Job.objects.values('career__name').annotate(total_posts=Count('id'))



