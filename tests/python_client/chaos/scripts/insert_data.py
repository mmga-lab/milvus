import json
from influxdb import InfluxDBClient
client = InfluxDBClient('10.96.13.165', 8086, 'root', 'root', 'chaos_test_results')
client.create_database('chaos_test_results')


with open("/Users/zilliz/workspace/backup/milvus/Pod Kill_workflows.json", "r") as f:
    runs_response = json.load(f)


for run in runs_response:
    jobs = runs_response[run]["jobs"]
    for r in jobs:
        failure_reason = ""
        for step in r["steps"]:
            if step["conclusion"] == "failure":
                failure_reason = step["name"]
        json_body = [
        {
            "measurement": "pod_kill_chaos_test",
            "tags": {
                "compont": r["name"]
            },
            "time": r["started_at"],
            "fields": {
                "conclusion": r["conclusion"],
                "failure_reason": failure_reason,
                "html_url": r["html_url"]
            }
        }
        ]
        print("json_body", json_body)
        client.write_points(json_body)
        result = client.query('select conclusion from pod_kill_chaos_test;')
        print(f"result: {result}")

    
    
