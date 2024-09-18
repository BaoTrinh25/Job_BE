from drf_yasg import openapi


jobSeeker_create_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
                properties={
                    'skills': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_INTEGER)
                    ),
                    'areas': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_INTEGER)
                    ),
                    'position': openapi.Schema(type=openapi.TYPE_STRING),
                    'salary_expectation': openapi.Schema(type=openapi.TYPE_STRING),
                    'experience': openapi.Schema(type=openapi.TYPE_STRING),
                    'cv': openapi.Schema(type=openapi.TYPE_STRING),
                    'career': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )

employer_create_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
                properties={
                    'companyName': openapi.Schema(type=openapi.TYPE_STRING),
                    'position': openapi.Schema(type=openapi.TYPE_STRING),
                    'information': openapi.Schema(type=openapi.TYPE_STRING),
                    'address': openapi.Schema(type=openapi.TYPE_STRING),
                    'company_type': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )

apply_job_schema = openapi.Schema(
            type=openapi.TYPE_OBJECT,
                properties={
                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                    'is_student': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'job': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'jobseeker': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )

num_application_schema = openapi.Schema(
            type=openapi.TYPE_OBJECT,
                properties={
                    'num_applications': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )

