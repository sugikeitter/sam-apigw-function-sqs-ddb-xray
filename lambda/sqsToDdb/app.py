from datetime import datetime, timedelta, timezone
import json
import os

import boto3

ddb_resource = boto3.resource("dynamodb")
table = ddb_resource.Table(os.environ['DDB_TABLE_NAME'])

"""
SQSキューのイベントからDynamoDBテーブルへItemをputする
"""
def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventSource'] == 'aws:sqs':
            # print('record')
            # print(record)
            payload = json.loads(record["body"])
            # print('payload')
            # print(payload)
            JST = timezone(timedelta(hours=+9), 'JST')
            processedTime = datetime.now(JST).isoformat()[0:23] # 日本時間のミリ秒3桁までの文字列
            # TODO テーブル設計でsortKeyがTimestampになるように検討が必要
            res = table.put_item(
                Item={
                    'id': payload.get("recieveTime", "YYYY-MM-DD")[0:10],
                    'recieveTime': payload.get("recieveTime", ""),
                    'recieveId': payload.get("recieveId", "NO_ID"),
                    'name': payload.get("name", "NO_NAME"),
                    'processedTime': processedTime,
                })
            
            print("--PutItem Response: " + payload.get("recieveId", "NO_ID"))
            print(res)
    
    # SQS連携の場合、何を返す？

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
