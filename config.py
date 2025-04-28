import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    IN_DATA_PATH = Path(os.path.abspath("in_data.txt"))
    PROXIES_PATH = Path(os.path.abspath("proxies.txt"))
    OUT_DATA_PATH = Path(os.path.abspath("out_data.csv"))
    PROCESSES_COUNT = int(os.getenv("PROCESSES_COUNT").strip())
    HEADLESS = bool(int(os.getenv("HEADLESS").strip()))
