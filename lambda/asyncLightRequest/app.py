from datetime import datetime, timedelta, timezone
import base64
import json
import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key

sqs_resource = boto3.resource("sqs")
queue = sqs_resource.get_queue_by_name(
    QueueName=os.environ['SQS_QUEUE_NAME']
)

ddb_resource = boto3.resource("dynamodb")
table = ddb_resource.Table(os.environ['DDB_TABLE_NAME'])

html = """
<!DOCTYPE html>
<html>
<head>
  <style>
    {style}
  </style>
</head>
<body>
  {TopMsg}
  <a href="/">トップへ</a>
  {RecieveIds}
</body>
</html>
"""

style = """
.styled-table {
    border-collapse: collapse;
    margin: 25px 0;
    font-size: 0.9em;
    font-family: Menlo, Monaco, 'Courier New', monospace;
    min-width: 400px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}

.styled-table thead tr {
    background-color: #009879;
    color: #ffffff;
    text-align: left;
}

.styled-table th,
.styled-table td {
    padding: 12px 15px;
}

.styled-table tbody tr {
    border-bottom: 1px solid #dddddd;
}

.styled-table tbody tr:nth-of-type(even) {
    background-color: #f3f3f3;
}

.styled-table tbody tr:last-of-type {
    border-bottom: 2px solid #009879;
}

.styled-table tbody tr.active-row {
    font-weight: bold;
    color: #009879;
}
"""

"""
API Gateway(HTTP)からPOSTリクエストを受けて、現在時刻とPOSTに入ってるパラメータをSQSキューに送る
"""
def lambda_handler(event, context):
    
    # POSTのテキスト(name=XXX)を取得
    print(event)
    body = event.get('body', 'bmFtZT1OT19OQU1F') # 'bmFtZT1OT19OQU1F'をdecodeすると'name=NO_NAME'
    print(body)
    decodedBody = base64.b64decode(body).decode() # POSTのbodyがAPIGWでencodeされてるのでdecode
    print(decodedBody)
    name = decodedBody.split('=')[1][0:12] # bodyは空文字でもname=''がくる前提
    if name == "":
        name = 'NO_NAME'

    JST = timezone(timedelta(hours=+9), 'JST')
    recieveTime = datetime.now(JST).isoformat()[0:23] # 日本時間のミリ秒3桁までの文字列
    yearAndDate = recieveTime[0:10]
    recieveId = uuid.uuid4().hex # ランダムな文字列

    # SQSキューに情報を渡す
    msg = {
        "recieveTime": recieveTime,
        "recieveId": recieveId,
        "name": name,
    }
    res = queue.send_message(
        MessageBody=json.dumps(msg),
    )

    # DynamoDBにprocessedTime以外をput
    res = table.put_item(
                Item={
                    'id': yearAndDate,
                    'recieveTime': recieveTime, # TODO uuidと合わせて排他制御が必要
                    'recieveId': recieveId,
                    'name': name,
                })
    
    # DynamoDBの直近数件をQuery
    JST = timezone(timedelta(hours=+9), 'JST')
    timestamp = datetime.now(JST).isoformat()[0:23] # 日本時間のミリ秒3桁までの文字列
    res = table.query(
        KeyConditionExpression=Key('id').eq(yearAndDate),
        ScanIndexForward=False,
        Limit=10,
    )
    print('query timestamp: ' + timestamp)
    recieveIdsHtml = """
    <table class="styled-table">
    <tr>
      <th>受付ID</th><th>名前</th><th>受付時間</th><th>処理時間</th>
    </tr>
    """
    for ddbItems in res.get('Items', []):
        recieveIdsHtml += "<tr><th>{}</th><th>{}</th><th>{}</th><th>{}</th></tr>".format(
            ddbItems.get("recieveId", ""),
            ddbItems.get("name", "NO_NEME"),
            ddbItems.get("recieveTime", ""),
            ddbItems.get("processedTime", "")
        )
    
    recieveIdsHtml += "</table>"
    
    

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {
            "content-type": "text/html; charset=utf-8"
        },
        "body": html.format(style=style, TopMsg="<p>受付番号: "+recieveId+"</p>", RecieveIds=recieveIdsHtml),
    }
