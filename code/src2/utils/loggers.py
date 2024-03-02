import logging
import os

def set_logging_tool(log_file):

    if not os.path.isfile(log_file):
        open(log_file, "w+").close()

    console_logging_format = "%(levelname)s %(module)s %(message)s"
    file_logging_format = "%(levelname)s: %(module)s: %(asctime)s: %(message)s"

    # configure logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format=console_logging_format)

    # create a file handler for output file
    handler = logging.FileHandler(log_file)

    # set the logging level for log file
    handler.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter(file_logging_format)
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    return logger