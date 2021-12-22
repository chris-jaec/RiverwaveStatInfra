import re
from datetime import datetime
from decimal import Decimal

DB_TIME_FORMAT = "%d.%m.%Y %H:%M"


def get_datetime_obj_from_db_time_str(datetime_str):
    return datetime.strptime(datetime_str, DB_TIME_FORMAT)


def time_now():
    return datetime.now()


def timestamp_now():
    return int(time_now().timestamp())


def get_db_time_str_from_datetime_obj(datetime_obj):
    return datetime.strftime(datetime_obj, DB_TIME_FORMAT)


def get_timestamp_from_db_time_str(datetime_str):
    return int(datetime.strptime(datetime_str, DB_TIME_FORMAT).timestamp())


def transform_theriverwave_time(datetime_str):
    datetime_str = datetime_str[0:19]
    format = "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(datetime_str, format)


def tranform_values(value):
    if not isinstance(value, str):
        return str(value)

    pattern = "[0-9]+,[0-9]+"
    if re.search(pattern, value):
        return value.replace(",", ".")

    return value


def get_time_difference(time1, time2):
    return int((time1 - time2).total_seconds() / 60)


def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj
