"""
Run the tests against a throwaway database and upload folder so they never
touch the real plant_disease.db or uploads/ directory.
"""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="plantcare_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_tmp, "test.db").replace("\\", "/")
os.environ["UPLOAD_DIR"] = os.path.join(_tmp, "uploads")
