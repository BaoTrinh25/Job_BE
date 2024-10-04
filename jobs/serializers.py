from rest_framework import serializers
from jobs.models import (User, JobSeeker, Skill, Area, Career, EmploymentType, Company, Status, Job, Invoice,
                         Rating, JobApplication, Like)
from django.contrib.auth import get_user_model
from .models import COMPANY_CHOICES
from django.utils.html import strip_tags #loại bỏ thẻ html bên trong richtextfield
from datetime import datetime


# class AvatarSerializer(serializers.ModelSerializer):

#   def to_representation(self, instance):
#         req = super().to_representation(instance)
#         req['image'] = instance.image.url
#         return req


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'user', 'product_item', 'payment_date', 'daily_post_limit', 'expiry_date', 'is_active',
                  'is_expired']


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


class EmploymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentType
        fields = ['id', 'type']


class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = ['id', 'role']


# Dùng để tạo User
class UserSerializer(serializers.ModelSerializer):
    # CHỈ ĐƯỜNG DẪN TUYỆT ĐỐI ẢNH ĐƯỢC UP TRÊN CLOUDINARY
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.avatar:
            req['avatar'] = instance.avatar.url
        return req

    class Meta:
        model = User
        # Qua models.py -> ctrl + trỏ vào AbstractUser để thấy được các trường của User
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'gender', 'email', 'mobile', 'avatar', 'role', 'is_staff']

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
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'mobile', 'avatar', 'role', 'jobSeeker', 'company', 'gender', 'is_staff']
        depth = 1



class JobSeekerCreateSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all(), required=False)
    areas = serializers.PrimaryKeyRelatedField(many=True, queryset=Area.objects.all(), required=False)
    career = serializers.PrimaryKeyRelatedField(queryset=Career.objects.all(), required=False, allow_null=True)

    class Meta:
        model = JobSeeker
        fields = ['id','position', 'salary_expectation', 'experience', 'cv', 'skills', 'areas', 'career']

    def create(self, validated_data):
        skills_data = validated_data.pop('skills', [])
        areas_data = validated_data.pop('areas', [])
        career_data = validated_data.pop('career', None)

        jobseeker = JobSeeker.objects.create(**validated_data)

        if skills_data:
            jobseeker.skills.set(skills_data)

        if areas_data:
            jobseeker.areas.set(areas_data)

        if career_data:
            jobseeker.career = career_data

        jobseeker.save()
        return jobseeker

    # def to_representation(self, instance):
    #     req = super().to_representation(instance)
    #     # Nếu ảnh khác null mới làm
    #     if instance.cv:
    #         req['cv'] = instance.cv.url
    #     return req
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Thêm tên cho các trường skills và areas
        rep['skills'] = SkillSerializer(instance.skills, many=True).data
        rep['areas'] = AreaSerializer(instance.areas, many=True).data
        # Nếu ảnh khác null mới làm
        if instance.cv:
            rep['cv'] = instance.cv.url
        return rep


# Dùng để hiển thị Applicant
class JobSeekerSerializer(serializers.ModelSerializer):

    skills = SkillSerializer(many=True)
    areas = AreaSerializer(many=True)
    career = CareerSerializer()

    class Meta:
        model = JobSeeker
        fields = ['id','position', 'skills', 'areas', 'salary_expectation', 'experience', 'cv', 'career']

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
        fields = ['id', 'companyName', 'information', 'address', 'logo', 'total_staff', 'company_type',
                  'company_type_display']

    def get_company_type_display(self, obj):
        return dict(COMPANY_CHOICES).get(obj.company_type)

    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.logo:
            req['logo'] = instance.logo.url
        return req


# Phần để tạo
class CompanyCreateSerializer(serializers.ModelSerializer):
    company_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'companyName', 'information', 'address', 'logo', 'total_staff', 'company_type',
                  'company_type_display']

    def get_company_type_display(self, obj):
        return dict(COMPANY_CHOICES).get(obj.company_type)


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    career = CareerSerializer()
    employmenttype = EmploymentTypeSerializer()
    area = AreaSerializer()
    created_date = serializers.SerializerMethodField()
    deadline = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y"])
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return UserDetailSerializer(obj.company.user).data

    # Tạo đường dẫn tuyệt đối cho trường image (image upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req

    #Format lại giá trị ngày
    def get_created_date(self, instance):
        if instance.created_date:
            return instance.created_date.strftime("%d/%m/%Y")
        return ""

    def get_deadline(self, instance):
        if instance.deadline:
            return instance.deadline.strftime("%d/%m/%Y")
        return ""

    def update(self, instance, validated_data):
        career_data = validated_data.pop('career', None)
        employment_type_data = validated_data.pop('employmenttype', None)

        # Update the main Job instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle nested Career updates
        if career_data:
            career_instance = instance.career
            for attr, value in career_data.items():
                setattr(career_instance, attr, value)
            career_instance.save()

        # Handle nested EmploymentType updates
        if employment_type_data:
            employmenttype_instance = instance.employmenttype
            for attr, value in employment_type_data.items():
                setattr(employmenttype_instance, attr, value)
            employmenttype_instance.save()

        instance.save()
        return instance

    class Meta:
        model = Job
        fields = ['id', 'user', 'company', 'image', 'career', 'employmenttype', 'area', 'title', 'deadline',
        'quantity', 'location', 'salary', 'description', 'experience', 'created_date', 'active', 'position']


class JobCreateSerializer(serializers.ModelSerializer):

    deadline = serializers.DateField(input_formats=['%d/%m/%Y'], format="%d/%m/%Y")

    # Tạo đường dẫn tuyệt đối cho trường image (image upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req

    def validate_deadline(self, value):
        if value:
            if value < datetime.now().date():
                raise serializers.ValidationError("Deadline không thể là ngày trong quá khứ")
        return value

    class Meta:
        model = Job
        fields = '__all__'


class AuthenticatedJobSerializer(JobSerializer):
    liked = serializers.SerializerMethodField()

    def get_liked(self, job):
        return job.like_set.filter(active=True).exists()

    class Meta:
        model = JobSerializer.Meta.model
        fields = JobSerializer.Meta.fields + ['liked']


class RatingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()

    def get_user(self, obj):
        if obj.jobseeker and obj.jobseeker.user:
            return UserDetailSerializer(obj.jobseeker.user).data
        return None

    #Format lại giá trị ngày
    def get_created_date(self, instance):
        if instance.created_date:
            return instance.created_date.strftime("%d/%m/%Y %H:%M")
        return ""

    class Meta:
        model = Rating
        fields = ['id', 'rating', 'comment', 'user', 'created_date', 'job']  # Chỉ hiển thị các trường cần thiết
        depth = 1
        extra_kwargs = {
            'rating': {'required': True}
        }


class RatingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']


class JobApplicationSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField(read_only=True)
    date = serializers.SerializerMethodField()
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    user = serializers.SerializerMethodField()
    content = serializers.CharField()
    jobseeker = serializers.PrimaryKeyRelatedField(queryset=JobSeeker.objects.all(), write_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'is_student', 'job', 'jobseeker', 'user', 'content', 'status', 'date']
        read_only_fields = ['status']
        depth = 1

    def create(self, validated_data):
        validated_data['status'] = Status.objects.get(role='Pending')
        return super().create(validated_data)

    # Thêm phương thức get_date để định nghĩa cách trả về giá trị cho 'date'
    def get_date(self, obj):
        if obj.date:
            return obj.date.strftime("%d/%m/%Y %H:%M")
        return ""

    def get_user(self, obj):
        if obj.jobseeker and obj.jobseeker.user:
            return UserDetailSerializer(obj.jobseeker.user).data
        return None


    def get_content(self, obj):
        # Sử dụng strip_tags để loại bỏ thẻ HTML, chỉ giữ lại nội dung văn bản
        return strip_tags(obj.content)


class JobApplicationStatusSerializer(serializers.ModelSerializer):
    job = JobSerializer()
    status = StatusSerializer()
    date = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    content = serializers.CharField()
    jobseeker = serializers.PrimaryKeyRelatedField(queryset=JobSeeker.objects.all(), write_only=True)

    #Format lại giá trị ngày
    def get_date(self, instance):
        if instance.created_date:
            return instance.date.strftime("%d/%m/%Y %H:%M")
        return ""

    def get_user(self, obj):
        if obj.jobseeker and obj.jobseeker.user:
            return UserDetailSerializer(obj.jobseeker.user).data
        return None

    def get_content(self, obj):
        # Sử dụng strip_tags để loại bỏ thẻ HTML, chỉ giữ lại nội dung văn bản
        return strip_tags(obj.content)

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'user', 'jobseeker', 'status', 'content', 'is_student', 'date']


class LikeSerializer(serializers.ModelSerializer):
    job = JobSerializer()

    class Meta:
        model = Like
        fields = '__all__'
