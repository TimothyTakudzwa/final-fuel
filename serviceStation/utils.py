from datetime import timedelta
import os
from PIL import Image

from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage

def create_default_end_date():
    t = timezone.localtime() + timedelta(days=10)
    return t

def create_default_end_date_etinos():
    t = timezone.localtime() + timedelta(days=(365*3))
    return t