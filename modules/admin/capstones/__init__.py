from fastapi import FastAPI

from modules.admin.capstones.api_create_capstone import register_api_create_capstone_route
from modules.admin.capstones.api_delete_capstone import register_api_delete_capstone_route
from modules.admin.capstones.api_update_capstone import register_api_update_capstone_route
from modules.admin.capstones.api_upload_docx import register_api_upload_docx_route
from modules.admin.capstones.api_admin_capstones import register_api_admin_capstones_route
from modules.admin.capstones.manage_capstones import register_manage_capstones_route

def configure_admin_capstone_module(app: FastAPI):
    register_manage_capstones_route(app)
    register_api_create_capstone_route(app)
    register_api_update_capstone_route(app)
    register_api_delete_capstone_route(app)
    register_api_upload_docx_route(app)
    register_api_admin_capstones_route(app)  # New admin API