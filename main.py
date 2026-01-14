from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import PathConfig
from modules.admin.capstones import configure_admin_capstone_module
from modules.admin.users import configure_admin_users_module
from modules.auth import configure_auth_module
from modules.capstones import configure_capstone_module
from modules.home import configure_home_module
from modules.student import configure_student_module
from modules.statistics import configure_statistics_module

PathConfig.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PathConfig.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


import os
print("############################")
print(os.getenv('OPENAI_API_KEY'))
print("############################")

# ------------------------------
# FastAPI app setup
# ------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=str(PathConfig.UPLOAD_DIR)), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Routes (Frontend pages)
# ------------------------------

configure_home_module(app)
configure_capstone_module(app)
configure_auth_module(app)
configure_admin_users_module(app)
configure_admin_capstone_module(app)
configure_student_module(app)
configure_statistics_module(app)

