"""Khởi tạo Flask App và gom các thành phần cốt lõi để tương thích ngược."""
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, Response
from jinja2 import FileSystemLoader
import sqlite3
import csv
import io
import os
import qrcode
from qrcode.image.pil import PilImage
from datetime import date, datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from .config import DB, SECRET_KEY, STATIC_DIR, TEMPLATE_DIR, TEMPLATE_SEARCH_PATHS
from .database import db, init_db
from .middleware import login_required, reader_required, password_matches, log_action

__all__ = [
    "app",
    "render_template",
    "request",
    "redirect",
    "url_for",
    "flash",
    "session",
    "abort",
    "Response",
    "FileSystemLoader",
    "sqlite3",
    "csv",
    "io",
    "os",
    "qrcode",
    "PilImage",
    "date",
    "datetime",
    "timedelta",
    "wraps",
    "generate_password_hash",
    "check_password_hash",
    "secrets",
    "DB",
    "SECRET_KEY",
    "STATIC_DIR",
    "TEMPLATE_DIR",
    "TEMPLATE_SEARCH_PATHS",
    "db",
    "init_db",
    "login_required",
    "reader_required",
    "password_matches",
    "log_action",
]

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.jinja_loader = FileSystemLoader(TEMPLATE_SEARCH_PATHS)
app.secret_key = SECRET_KEY


@app.context_processor
def inject():
    return {
        "logged_in": "employee_id" in session,
        "employee_name": session.get("employee_name"),
    }
