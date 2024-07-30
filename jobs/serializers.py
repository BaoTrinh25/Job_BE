from rest_framework import serializers
from jobs.models import (User, JobSeeker, Skill, Area, Career, EmploymentType, Company, Status, Job,
                         Rating, Comment, JobApplication, Notification)
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import COMPANY_CHOICES


User = get_user_model()

class EmploymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentType
        fields = ['id', 'type']


class StatusSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'role']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name']

class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = ['id', 'name']


class JobSeekerCreateSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all(), required=False)
    areas = serializers.PrimaryKeyRelatedField(many=True, queryset=Area.objects.all(), required=False)
    career = serializers.PrimaryKeyRelatedField(queryset=Career.objects.all(), required=False, allow_null=True)

    class Meta:
        model = JobSeeker
        fields = ['position', 'salary_expectation', 'experience', 'cv', 'skills', 'areas', 'career']

    def create(self, validated_data):
        skills_data = validated_data.pop('skills', [])
        areas_data = validated_data.pop('areas', [])
        career_data = validated_data.pop('career', None)

        job_seeker = JobSeeker.objects.create(**validated_data)

        if skills_data:
            job_seeker.skills.set(skills_data)

        if areas_data:
            job_seeker.areas.set(areas_data)

        if career_data:
            job_seeker.career = career_data

        job_seeker.save()
        return job_seeker

    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req


class JobSeekerSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    areas = serializers.SerializerMethodField()
    career = serializers.SerializerMethodField()

    def get_skills(self, obj):
        skills = obj.skills.all()
        return SkillSerializer(skills, many=True).data

    def get_areas(self, obj):
        areas = obj.areas.all()
        return AreaSerializer(areas, many=True).data

    def get_career(self, obj):
        if obj.career:
            return CareerSerializer(obj.career).data
        return None

    class Meta:
        model = JobSeeker
        fields = ['position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']

    # Thêm đường dẫn cho ảnh của CV
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.cv:
            req['cv'] = instance.cv.url
        return req


# Phần để hiển thị
class CompanySerializer(serializers.ModelSerializer):
    company_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'companyName', 'position', 'information', 'address', 'company_type',
                  'company_type_display']

    def get_company_type_display(self, obj):
        return dict(COMPANY_CHOICES).get(obj.company_type)


# Phần để tạo
class CompanyCreateSerializer(serializers.ModelSerializer):
    company_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'companyName', 'position', 'information', 'address', 'company_type',
                  'company_type_display']

    def get_company_type_display(self, obj):
        return dict(COMPANY_CHOICES).get(obj.company_type)



# Dùng để tạo User
class UserSerializer(serializers.ModelSerializer):
    # CHỈ ĐƯỜNG DẪN TUYỆT ĐỐI ẢNH ĐƯỢC UP TRÊN CLOUDINARY
    # to_representation tùy chỉnh cách biểu diễn (representation) của một đối tượng (instance) khi nó được chuyển đổi thành dữ liệu JSON
    # hoặc dữ liệu khác để trả về cho client.
    # instance ở đây là User
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.avatar:
            req['avatar'] = instance.avatar.url
        return req

    class Meta:
        model = User
        # Qua models.py -> ctrl + trỏ vào AbstractUser để thấy được các trường của User
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'gender', 'email', 'mobile', 'avatar', 'role']

        # Thiết lập mật khẩu chỉ để ghi
        extra_kwargs = {
            'password': {
                'write_only': True
            }

        }

    # Băm mật khẩu
    def create(self, validated_data):
        data = validated_data.copy()
        user = User(**data)
        user.set_password(data['password'])
        user.save()
        return user


# Phần để hiển thị
class UserDetailSerializer(serializers.ModelSerializer):
    # Serializer cho thông tin của Applicant
    jobSeeker = serializers.SerializerMethodField(source='jobseeker')
    # Serializer cho thông tin của Employer
    company = serializers.SerializerMethodField(source='company')

    # Phương thức để lấy thông tin của Applicant
    def get_jobSeeker(self, obj):
        try:
            jobseeker = getattr(obj, 'jobseeker', None)
            return JobSeekerSerializer(jobseeker).data
        except JobSeeker.DoesNotExist:
            return None

    # Phương thức để lấy thông tin của Employer
    def get_company(self, obj):
        try:
            company = getattr(obj, 'company', None)
            return CompanySerializer(company).data
        except Company.DoesNotExist:
            return None

    # Tạo đường dẫn tuyệt đối cho trường avatar (avatar upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.avatar:
            req['avatar'] = instance.avatar.url
        return req

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'mobile', 'avatar', 'role', 'jobSeeker', 'company']
        depth = 1


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    career = CareerSerializer()
    employmenttype = EmploymentTypeSerializer()
    area = AreaSerializer()

    # Tạo đường dẫn tuyệt đối cho trường image (image upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req

    # Format lại giá trị ngày
    def get_created_date(self, instance):
        if instance.created_date:
            return instance.created_date.strftime("%d/%m/%Y %H:%M:%S")
        return ""
    def get_deadline(self, instance):
        if instance.deadline:
            return instance.deadline.strftime("%d/%m/%Y")
        return ""

    class Meta:
        model = Job
        fields = '__all__'

class JobCreateSerializer(serializers.ModelSerializer):

    # Tạo đường dẫn tuyệt đối cho trường image (image upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req

    # Format lại giá trị ngày
    def get_created_date(self, instance):
        if instance.created_date:
            return instance.created_date.strftime("%d/%m/%Y %H:%M:%S")
        return ""
    def get_deadline(self, instance):
        if instance.deadline:
            return instance.deadline.strftime("%d/%m/%Y")
        return ""

    class Meta:
        model = Job
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    # Một comment cho 1 người tạo nên không gán many = True
    # employer = EmployerSerializer()
    # applicant = ApplicantSerializer()
    company = serializers.SerializerMethodField()
    jobSeeker = serializers.SerializerMethodField()

    def get_employer(self, obj):
        return CompanySerializer(obj.company).data

    def get_applicant(self, obj):
        return JobSeekerSerializer(obj.jobSeeker).data

    class Meta:
        model = Comment
        fields = '__all__'
        depth = 1


class JobApplicationSerializer(serializers.ModelSerializer):
    jobSeeker = JobSeekerSerializer()
    status = StatusSerialzier()
    job = JobSerializer()

    class Meta:
        model = JobApplication
        fields = ['is_student', 'job', 'jobSeeker', 'content', ]
        read_only_fields = ['status']
        depth = 1

    def create(self, validated_data):
        validated_data['status'] = Status.objects.get(role='Pending')
        return super().create(validated_data)


class JobApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'jobSeeker', 'status', 'content']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notification
        fields = '__all__'
