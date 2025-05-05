import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    IN_DATA_PATH = Path(os.path.abspath("in_data.txt"))
    PROXIES_PATH = Path(os.path.abspath("proxies.txt"))
    OUT_DATA_PATH = Path(os.path.abspath("out_data.csv"))
    PARSED_DATA_PATH = Path(os.path.abspath("parsed_data.txt"))
    PROCESSES_COUNT = int(os.getenv("PROCESSES_COUNT").strip())
    REQUEST_TO_CHANGE_ADDRESS_TIMEOUT = int(os.getenv("REQUEST_TO_CHANGE_ADDRESS_TIMEOUT").strip())
