from datetime import timezone
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from ckeditor.fields import RichTextField


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True )
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True  # Không tạo model dưới CSDL


GENDER_CHOICES = (
    (0, 'Male'),
    (1, 'Female'),
    (2, 'N/A'),
)

ROLE_CHOICES = (
    (0, 'Applicant'),
    (1, 'Employer'),
)

COMPANY_CHOICES = (
    (0, 'Công ty TNHH'),
    (1, 'Công ty Cổ phần'),
    (2, 'Công ty tư nhân'),
)


class User(AbstractUser):
    avatar = CloudinaryField('avatar', null=True, blank=True)
    mobile = PhoneNumberField(region="VN", null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, null=True, blank=True)
    role = models.IntegerField(choices=ROLE_CHOICES, null=True, blank=True, default=0)

    class Meta:
        ordering = ['id']  # Sắp xếp theo thứ tự id tăng dần

class Invoice(models.Model):
    # Một người dùng có thể có nhiều hóa đơn
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount_total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    payment_status = models.CharField(max_length=20)
    payment_date = models.DateTimeField(auto_now_add=True, null=True)
    customer_email = models.EmailField(null=True, blank=True)
    product_item = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Invoice {self.stripe_session_id} - {self.user.username}"

# Nhà tuyển dụng
class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    companyName = models.CharField(max_length=255)
    address = models.CharField(max_length=255, null=True, blank=True)
    information = models.TextField(null=True, blank=True)
    total_staff = models.CharField(max_length=255, null=True, blank=True)#số lượng nhân sự trong công ty
    # Loại hình công ty (công ty TNHH, công ty cổ phần, v.v)
    company_type = models.IntegerField(choices=COMPANY_CHOICES, null=True, blank=True)
    logo = CloudinaryField('logo', null=True, blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ['id']


# Loại công việc
class EmploymentType(models.Model):

    type = models.CharField(max_length=100, null=True, blank=True)
    # Full-time; Part-time; Internship

    def __str__(self):
        return self.type
    class Meta:
        ordering = ['id']


# Bài tuyển dụng
class Job(BaseModel):
    company = models.ForeignKey(Company, models.CASCADE)
    image = CloudinaryField('image', null=True, blank=True)
    career = models.ForeignKey('Career', on_delete=models.PROTECT, null=True)
    employmenttype = models.ForeignKey(EmploymentType, on_delete=models.PROTECT, null=True)
    area = models.ForeignKey('Area', models.RESTRICT, null=True)
    title = models.CharField(max_length=255)
    deadline = models.DateField()
    quantity = models.IntegerField()    # Số nhân sự cần
    gender = models.IntegerField(choices=GENDER_CHOICES, default=0, null=True, blank=True)
    location = models.CharField(max_length=255)
    salary = models.CharField(max_length=255)
    position = models.CharField(max_length=255)   # Vị trí ứng tuyển
    description = models.TextField(null=True, blank=True)
    experience = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('company', 'title')
        ordering = ['deadline', 'id']


class Room(models.Model):
    sender = models.ForeignKey(User, related_name='sender_rooms', on_delete=models.CASCADE, null=True, blank=True)
    receiver = models.ForeignKey(User, related_name='receiver_rooms', on_delete=models.CASCADE, null=True,
                                 blank=True)
    job = models.ForeignKey(Job, related_name='job_room', on_delete=models.CASCADE, null=True,
                                 blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        # Đảm bảo mỗi cặp người dùng (sender, receiver) chỉ có một phòng chat.
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"ChatRoom between {self.sender.username} and {self.receiver.username}"


class Message(models.Model):
    message = models.TextField()
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    job = models.ForeignKey(Job, related_name='job_message', on_delete=models.CASCADE, null=True,
                            blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} in room {self.room.id}"

# Khu vực
class Area(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


# Người xin việc
class JobSeeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=255, null=True, blank=True)    # Vị trí muốn ứng tuyển
    skills = models.ManyToManyField('Skill', blank=True)
    areas = models.ManyToManyField('Area', blank=True)
    salary_expectation = models.CharField(max_length=255)
    experience = models.TextField(null=True, blank=True)
    cv = CloudinaryField('cv', null=True, blank=True)
    career = models.ForeignKey('Career', on_delete=models.RESTRICT, null=True, blank=True)

    def __str__(self):
        return self.user.username
    class Meta:
        ordering = ['id']


# Đơn xin việc
class JobApplication(BaseModel):
    is_student = models.BooleanField(default=False, null=True)  # Thêm để thực hiện truy vấn theo bài
    # Ngày nộp đơn xin việc
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)  # Thêm mới để thực hiện truy vấn theo bài
    job = models.ForeignKey(Job, models.RESTRICT, null=True, default=None)
    jobseeker = models.ForeignKey(JobSeeker, models.CASCADE, null=True)
    company = models.ForeignKey(Company, models.CASCADE, null=True) # CASCASDE : Nếu công ty bị xóa thì các đơn ứng tuyển liên quan cũng bị xóa
    status = models.ForeignKey('Status', models.RESTRICT, null=True, default='Pending')
    content = RichTextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('job', 'jobseeker')
        ordering = ['date', 'id']
    def __str__(self):
        return self.job.title + ", " + self.jobseeker.user.username + " apply"


class Status(models.Model):
    # Pending; Accepted; Rejected
    role = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.role


class Skill(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Career(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


# Tương tác
class Interaction(BaseModel):
    jobseeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.jobseeker_id} - {self.company_id} - {self.job_id}'


class Like(Interaction):
    class Meta:
        unique_together = [['jobseeker', 'job'], ['company', 'job']]
        ordering = ['id', ]


class Rating(Interaction):
    rating = models.SmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate from 1 to 5"
    )
    comment = models.CharField(max_length=255, default='No comment')
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    class Meta:
        ordering = ['id',]

    def __str__(self):
        return f'Rating: {self.rating}, Content: {self.comment}'


