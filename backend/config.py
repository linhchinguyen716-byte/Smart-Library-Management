"""Cấu hình đường dẫn và biến môi trường cho hệ thống Smart Library."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEMPLATE_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

TEMPLATE_SEARCH_PATHS = [
    TEMPLATE_DIR,
    os.path.join(TEMPLATE_DIR, "layouts"),
    os.path.join(TEMPLATE_DIR, "auth"),
    os.path.join(TEMPLATE_DIR, "admin"),
    os.path.join(TEMPLATE_DIR, "reader"),
]

DB = os.path.join(BASE_DIR, "library.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "library-management-demo-change-before-deploy")
