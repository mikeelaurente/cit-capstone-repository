from fastapi import FastAPI

from modules.admin.users.api_delete_user import register_api_delete_user_route
from modules.admin.users.api_get_user import register_api_get_user_route
from modules.admin.users.api_get_users import register_api_get_users_route
from modules.admin.users.api_update_user import register_api_update_user_route
from modules.admin.users.api_admin_users import register_api_admin_users_route
from modules.admin.users.create_user import register_create_user_route
from modules.admin.users.manage_users import register_manage_users_route


def configure_admin_users_module(app: FastAPI):
    register_create_user_route(app)
    register_manage_users_route(app)
    register_api_get_users_route(app)
    register_api_get_user_route(app)
    register_api_update_user_route(app)
    register_api_delete_user_route(app)
    register_api_admin_users_route(app)  # New admin API