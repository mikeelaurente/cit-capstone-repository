from fastapi import FastAPI
from .api_signup import register_api_signup_route
from .api_verify import register_api_verify_route
from .api_resend_code import register_api_resend_code_route
from .api_forgot_password import register_api_forgot_password_route
from .api_reset_password import register_api_reset_password_route
from .api_upload_capstone import register_api_upload_capstone_route
from .api_get_submissions import register_api_get_submissions_route
from .api_get_submission import register_api_get_submission_route
from .api_get_citation import register_api_get_citation_route

def configure_student_module(app: FastAPI):
    register_api_signup_route(app)
    register_api_verify_route(app)
    register_api_resend_code_route(app)
    register_api_forgot_password_route(app)
    register_api_reset_password_route(app)
    register_api_upload_capstone_route(app)
    register_api_get_submissions_route(app)
    register_api_get_submission_route(app)
    register_api_get_citation_route(app)
    # Student login now uses consolidated /api/login with type="student"
