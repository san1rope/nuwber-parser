import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    IN_DATA_PATH = Path(os.path.abspath("in_data.txt"))
    PROXIES_PATH = Path(os.path.abspath("proxies.txt"))
    MAX_PROCESSES_COUNT = int(os.getenv("MAX_PROCESSES_COUNT").strip())
