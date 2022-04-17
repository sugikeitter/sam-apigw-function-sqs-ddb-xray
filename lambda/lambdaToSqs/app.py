from datetime import datetime, timedelta, timezone
import json
import os
import uuid

import boto3

sqs_resource = boto3.resource("sqs")
queue = sqs_resource.get_queue_by_name(
    QueueName=os.environ['SQS_QUEUE_NAME']
)

html = """
<!DOCTYPE html>
<html>
<body>
受付ID: {RecieveId}
</body>
</html>
"""

"""
API Gateway(HTTP)からPOSTリクエストを受けて、現在時刻とPOSTに入ってるパラメータをSQSキューに送る
"""
def lambda_handler(event, context):
    
    print(event)
    JST = timezone(timedelta(hours=+9), 'JST')
    recieveTime = datetime.now(JST).isoformat()[0:23] # 日本時間のミリ秒3桁までの文字列
    recieveId = uuid.uuid4().hex # ランダムな文字列
    # TODO DynamoDBに入れる他の要素作成
    body = json.loads(event.get('body', {}))
    name = body.get('name', recieveId[3:9])
    msg = {
        "recieveTime": recieveTime,
        "recieveId": recieveId,
        "name": name[0:12],
    }
    
    res = queue.send_message(
        MessageBody=json.dumps(msg),
    )

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {
            "content-type": "text/html; charset=utf-8"
        },
        "body": html.format(RecieveId=recieveId),
    }
