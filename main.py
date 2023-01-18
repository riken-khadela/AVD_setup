from conf import LOG_LEVEL, LOG_DIR
from conf import PRJ_PATH
from utils import set_log

LOGGER = set_log(PRJ_PATH, __file__, __name__, log_level=LOG_LEVEL,
                 log_dir=LOG_DIR)
