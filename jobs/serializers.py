from rest_framework import serializers
from jobs.models import (User, JobSeeker, Skill, Area, Career, EmploymentType, Company, Status, Job,
                         Rating, JobApplication, Notification, Like)
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import COMPANY_CHOICES
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class RefreshTokenSerializer(serializers.Serializer):
    accessToken = serializers.CharField()
    roles = serializers.CharField()


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

    def to_representation(self, instance):
        rep = super().to_representation(instance)
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


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    career = CareerSerializer()
    employmenttype = EmploymentTypeSerializer()
    area = AreaSerializer()
    created_date = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()

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

    class Meta:
        model = Job
        fields = ['id', 'company', 'image', 'career', 'employmenttype', 'area', 'title', 'deadline',
        'quantity', 'location', 'salary', 'description', 'experience', 'created_date']


class JobCreateSerializer(serializers.ModelSerializer):
    # Tạo đường dẫn tuyệt đối cho trường image (image upload lên Cloudinary)
    def to_representation(self, instance):
        req = super().to_representation(instance)
        # Nếu ảnh khác null mới làm
        if instance.image:
            req['image'] = instance.image.url
        return req

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
        return UserDetailSerializer(obj.jobseeker.user).data

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


class JobApplicationSerializer(serializers.ModelSerializer):

    jobseeker = serializers.PrimaryKeyRelatedField(queryset=JobSeeker.objects.all(), write_only=True)
    status = serializers.PrimaryKeyRelatedField(read_only=True)
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), write_only=True)
    created_date = serializers.SerializerMethodField()

    class Meta:
        model = JobApplication
        fields = ['id', 'is_student', 'job', 'jobseeker', 'content', 'status']
        read_only_fields = ['status']
        depth = 1

    def create(self, validated_data):
        validated_data['status'] = Status.objects.get(role='Pending')
        return super().create(validated_data)


class JobApplicationStatusSerializer(serializers.ModelSerializer):

    job = JobSerializer()
    jobseeker = JobSeekerSerializer()
    status = StatusSerializer()
    created_date = serializers.SerializerMethodField()

    #Format lại giá trị ngày
    def get_created_date(self, instance):
        if instance.created_date:
            return instance.created_date.strftime("%d/%m/%Y %H:%M")
        return ""

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'jobseeker', 'status', 'content', 'is_student', 'created_date']


class LikeSerializer(serializers.ModelSerializer):
    job = JobSerializer()

    class Meta:
        model = Like
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notification
        fields = '__all__'
