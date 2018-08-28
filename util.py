import functools
import logging
import traceback
import datetime
import os

import sqlalchemy.types as types
import json

# class StringyJSON(types.TypeDecorator):
#     impl = types.TEXT

#     def process_bind_param(self, value, dialect):
#         if value is not None:
#             value = json.dumps(value)
#         return value

#     def process result_value(self, value, dialect):
#         if value is not None:
#             value = json.loads(value)
#         return value

# MagicJSON = types.JSON().with_variant(StringyJSON, 'sqlite')

# def time_str():
#     return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#log_file = open(os.path.join("logs", time_str() + ".txt"), "w")

#def log(message):
    #log_file.write(time_str() + " : " + message)

#https://www.blog.pythonlibrary.org/2016/06/09/python-how-to-create-an-exception-logging-decorator/
def exception(function):
    """
    A decorator that wraps the passed in function and logs 
    exceptions should one occur
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception, err:
            traceback.print_exc()
            #traceback.print_exc(file=log_file)
    return wrapper


 
# def create_logger():
#     """
#     Creates a logging object and returns it
#     """
#     logger = logging.getLogger("example_logger")
#     logger.setLevel(logging.INFO)
 
#     # create the logging file handler
#     fh = logging.FileHandler("/path/to/test.log")
 
#     fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     formatter = logging.Formatter(fmt)
#     fh.setFormatter(formatter)
 
#     # add handler to logger object
#     logger.addHandler(fh)
#     return logger

# def exception(function):
#     """
#     A decorator that wraps the passed in function and logs 
#     exceptions should one occur
#     """
#     @functools.wraps(function)
#     def wrapper(*args, **kwargs):
#         logger = create_logger()
#         try:
#             return function(*args, **kwargs)
#         except:
#             # log the exception
#             err = "There was an exception in  "
#             err += function.__name__
#             logger.exception(err)
 
#             # re-raise the exception
#             raise
#     return wrapper