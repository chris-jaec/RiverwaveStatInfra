import json
import os
import boto3

dynamodb = boto3.resource('dynamodb', region_name=os.getenv("region"))


def get_latest(event, context):
    riverwave_name = event["pathParameters"]["riverwave"]
    table = dynamodb.Table(
        f'{os.environ["DYNAMODB_TABLE_PREFIX"]}-{riverwave_name}')

    result = table.scan()

    data = sorted(result['Items'], key=lambda k: k['datetime'], reverse=True)

    # If some data is None, then retrieve previous data value
    for key, val in data[0].items():
        if val == "None":
            data[0][key] = data[1][key]

    print(json.dumps(data))

    # create a response
    response = {
        "statusCode": 200,
        "body": json.dumps(data[0])
    }

    return response