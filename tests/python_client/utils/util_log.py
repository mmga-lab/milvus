from loguru import logger
import sys

from config.log_config import log_config


class TestLog:
    def __init__(self, log_debug, log_info, log_err, log_worker):
        self.log_debug = log_debug
        self.log_info = log_info
        self.log_err = log_err
        self.log_worker = log_worker
        self.log = logger

        config = {
            self.log_debug: "DEBUG",
            self.log_info: "INFO",
            self.log_err: "ERROR",
            self.log_worker: "DEBUG"
        }
        try:
            encoding = "utf-8"
            enqueue = True
            for file, level in config.items():
                self.log.add(
                    sink=file, level=level, encoding=encoding,
                    enqueue=enqueue, rotation="500MB", retention="1 week",
                    # colorize=True
                )

            self.log.add(sys.stdout, level="DEBUG", colorize=False)

        except Exception as e:
            print("Can not use %s or %s or %s to log. error : %s" % (log_debug, log_info, log_err, str(e)))


"""All modules share this unified log"""
log_debug = log_config.log_debug
log_info = log_config.log_info
log_err = log_config.log_err
log_worker = log_config.log_worker
test_log = TestLog(log_debug, log_info, log_err, log_worker).log
