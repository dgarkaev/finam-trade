"""
Файл конфигурации
"""
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.
import os

# REDIS
REDIS_URL = os.getenv('REDIS_URL')
STREAM_ROOT =  os.getenv('STREAM_ROOT')