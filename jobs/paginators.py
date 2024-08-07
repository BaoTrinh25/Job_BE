from rest_framework.pagination import PageNumberPagination

class JobPaginator(PageNumberPagination):
    page_size = 10  # Mỗi trang sẽ chứa tối đa 10 bài đăng tuyển dụng.
    max_page_size = 20

class CommentPaginator(PageNumberPagination): # Phân trang cho Comment
    page_size = 10
    max_page_size = 20

class JobApplicationPagination(PageNumberPagination): #Phân trang cho List Applied Job for Applicant
    page_size = 10  # Số lượng items trên mỗi trang
    page_size_query_param = 'page_size'
    max_page_size = 20  # Số lượng tối đa items trên mỗi trang

class LikedJobPagination(PageNumberPagination): #Phân trang cho danh sách Job đã like - Applicant
    page_size = 10  # Số lượng items trên mỗi trang
    page_size_query_param = 'page_size'
    max_page_size = 20  # Số lượng tối đa items trên mỗi trang

# Phân trang reply comment
class CommentReplyPaginator(PageNumberPagination):
    page_size = 10  # Số lượng reply comment hiển thị trên mỗi trang
    max_page_size = 20

# Phân trang cho Rating
class RatingPaginator(PageNumberPagination):
    page_size = 10  # Số lượng rating hiển thị trên mỗi trang
    max_page_size = 20

# Phân trang cho Applicant
class JobSeekerPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20

# Phân trang cho User
class UserPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20

# Phân trang cho Application
class ApplicationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20