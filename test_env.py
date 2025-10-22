import os
from dotenv import load_dotenv

load_dotenv()

print(f"OLT_HOST: {os.getenv('OLT_HOST')}")
print(f"OLT_PORT: {os.getenv('OLT_PORT')}")
print(f"OLT_USERNAME: {os.getenv('OLT_USERNAME')}")
print(f"OLT_PASSWORD: {os.getenv('OLT_PASSWORD')}")
