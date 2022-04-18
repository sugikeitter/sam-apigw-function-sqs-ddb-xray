from datetime import datetime, timedelta, timezone
import json
import os

import boto3
from boto3.dynamodb.conditions import Key

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
  <form action="./asyncLightRequest" method="POST">
    <div>
      <label for="name">Let's submit some name</label>
      <input id="name" type="text" name="name" maxlength="12">
    </div>
    <div>
      <input type="submit" value="Send">
    </div>
  </form>
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
トップページとして、受付IDの一覧を返す
"""
def lambda_handler(event, context):
    JST = timezone(timedelta(hours=+9), 'JST')
    timestamp = datetime.now(JST).isoformat()[0:23] # 日本時間のミリ秒3桁までの文字列
    res = table.query(
        KeyConditionExpression=Key('id').eq(timestamp[0:10]),
        ScanIndexForward=False,
        Limit=50,
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
        "body": html.format(style=style, RecieveIds=recieveIdsHtml),
    }
