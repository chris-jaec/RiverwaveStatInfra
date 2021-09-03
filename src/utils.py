from datetime import datetime

DB_TIME_FORMAT = "%d.%m.%Y %H:%M"


def get_datetime_obj_from_db_time_str(datetime_str):
    return datetime.strptime(datetime_str, DB_TIME_FORMAT)


def get_db_time_str_from_datetime_obj(datetime_obj):
    return datetime.strftime(datetime_obj, DB_TIME_FORMAT)


def transform_ebensee_time(datetime_str):
    datetime_str = datetime_str[0:19]
    format = "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(datetime_str, format)


def get_time_difference(time1, time2):
    return int((time1 - time2).total_seconds() / 60)
