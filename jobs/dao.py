from jobs.models import (JobApplication, Job, Company, JobSeeker, EmploymentType,
                         Career, Rating, Like, User,
                         )
from django.db.models import Count, Q, Avg
from datetime import datetime
from django.db.models.functions import ExtractQuarter, ExtractYear, TruncMonth


# Theo đề bài: Viết câu truy vấn đếm số đơn ứng tuyển của sinh viên theo nghề qua các quý và năm
def count_job_application_quarter_career():
    queryset = JobApplication.objects.filter(is_student=True) \
        .annotate(quarter=ExtractQuarter('date'), year=ExtractYear('date')) \
        .values('job__career__name', 'quarter', 'year') \
        .annotate(total_applications=Count('id')).order_by('total_applications', 'year', 'quarter')

    return queryset


# Tìm các bài đăng tuyển việc làm trên mức lương người dùng nhập
def search_salary_recruiment_post(salary):
    return Job.objects.filter(salary__gte=salary).order_by('-salary')


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

# Tìm danh sách các apply của một bài đăng tuyển dụng (ID mình nhập vào)
def recruiment_posts_apply_by_ID(id):
    # Lấy bài đăng tuyển dụng từ pk (primary key)
    job = Job.objects.get(pk=id)
    # Lấy danh sách các ứng tuyển liên quan đến bài đăng này
    applications = job.jobapplication_set.all()
    return applications


# Tìm bài đăng tuyển được yêu thích nhất (dựa vào lượt like)
def recruiment_posts_most_like_first_by_ID():
    # Lấy bài đăng tuyển dụng được sắp xếp theo số lượng lượt thích giảm dần
    return Job.objects.annotate(num_likes=Count('like')).order_by('-num_likes').first()


# #################################################################################################

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

# Đếm số lượng đơn xin việc là giới tính nữ
def count_female_job_applications():
    return JobApplication.objects.filter(applicant__user__gender=1).count()

# Đếm số lượng bài tuyển dụng là giới tính nữ
def count_recruitment_posts_with_female_employees():
    return Job.objects.filter(gender=1).count()

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

# Đếm số lượng bài đăng tuyển dụng theo vị trí địa lý
def count_recruitment_posts_by_location():
    job_by_location = Job.objects.values('location').annotate(
        total=Count('id')
    ).order_by('-total')

    return job_by_location



# Đếm số lượng ứng viên có mức lương mong đợi trên 15 triệu VND
def count_applicants_with_high_salary_expectation():
    applicants_with_high_salary_expectation = JobSeeker.objects.filter(
        salary_expectation__gt=15000000
    ).count()

    return applicants_with_high_salary_expectation


# Đếm số lượng bài đăng tuyển dụng có vị trí là "Nhân viên kinh doanh"
def count_recruitment_posts_with_sales_position():
    recruitment_posts_with_sales_position = Job.objects.filter(
        position__icontains='nhân viên kinh doanh'
    ).count()

    return recruitment_posts_with_sales_position

