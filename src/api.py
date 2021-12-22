import json
import os
from datetime import timedelta

import boto3
from boto3.dynamodb.conditions import Attr

from src.utilfuncs import replace_decimals, time_now, timestamp_now, get_timestamp_from_db_time_str

DYNAMODB = boto3.resource('dynamodb', region_name=os.getenv("region"))
TABLE_WAVE_OVERVIEW = DYNAMODB.Table(f'{os.environ["DYNAMODB_TABLE_PREFIX"]}-overview')


def get_wave_info(riverwave_name):
    wave_info = TABLE_WAVE_OVERVIEW.scan(
        Select='ALL_ATTRIBUTES',
        FilterExpression=Attr('name').contains(riverwave_name)
    )["Items"][0]

    return wave_info


def average_values(data_type, riverwave_name, min_date, max_date):
    data = get_data(data_type, riverwave_name, min_date, max_date)
    sum = 0
    for elem in data:
        sum += eval(elem["value"])
    res = sum / len(data)
    res = round(res, 1)
    return str(res)


def enabled_data(data_type, riverwave_name):
    return get_wave_info(riverwave_name)["data"][data_type]["enabled"]


def get_data(data_type, riverwave_name, min_date=None, max_date=None):
    if max_date is None:
        max_date_ts = timestamp_now()
    else:
        max_date_ts = get_timestamp_from_db_time_str(max_date)
    if min_date is None:
        min_date_ts = timestamp_now() - 60 * 60 * 24  # Subtract 1 day from timestamp
    else:
        min_date_ts = get_timestamp_from_db_time_str(min_date)

    table = DYNAMODB.Table(f'{os.environ["DYNAMODB_TABLE_PREFIX"]}-{riverwave_name}-{data_type}')

    result = table.scan(
        Select='ALL_ATTRIBUTES',
        FilterExpression=Attr('timestamp').between(min_date_ts, max_date_ts)
    )

    data = replace_decimals(result)
    data = sorted(data['Items'], key=lambda k: k['timestamp'], reverse=True)
    return data


def api_wave_info(event, context):
    riverwave_name = event["pathParameters"]["riverwave"]

    body = get_wave_info(riverwave_name)

    try:
        avg_hours = eval(event["queryStringParameters"]['time'])
    except:
        avg_hours = 4

    max_date = time_now().strftime("%d.%m.%Y %H:%M")
    datetime_min = time_now() - timedelta(hours=avg_hours)
    min_date = datetime_min.strftime("%d.%m.%Y %H:%M")

    if enabled_data("water_level", riverwave_name):
        body["data"]["water_level"]["latest"] = get_data("water-level", riverwave_name, min_date, max_date)
        body["data"]["water_level"]["average"] = average_values("water-level", riverwave_name, min_date, max_date)

    if enabled_data("water_temperature", riverwave_name):
        body["data"]["water_temperature"]["latest"] = get_data("water-temperature", riverwave_name, min_date, max_date)

    if enabled_data("water_runoff", riverwave_name):
        body["data"]["water_runoff"]["latest"] = get_data("water-runoff", riverwave_name, min_date, max_date)
        body["data"]["water_runoff"]["average"] = average_values("water-runoff", riverwave_name, min_date, max_date)

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
