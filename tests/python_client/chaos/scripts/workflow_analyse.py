import requests
import json
import time
requests.packages.urllib3.disable_warnings() # noqa
url = "https://api.github.com/repos/milvus-io/milvus/actions/workflows"

payload = {}
token = "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"  # your token
headers = {
    "Authorization": f"token {token}",
}

from influxdb import InfluxDBClient
client = InfluxDBClient('10.96.13.165', 8086, 'root', 'root', 'pod_kill_chaos_test')
client.create_database('pod_kill_chaos_test')

response = requests.request("GET", url, headers=headers, verify=False)
s = requests.session()
s.keep_alive = False
requests.packages.urllib3.disable_warnings()

def analysis_workflow(workflow_name, workflow_response):
    """
    Used to count the number of successes and failures of jobs in the chaos test workflow, 
    so as to understand the robustness of different components(each job represents a component).
    """
    workflow_id = [w["id"] for w in workflow_response.json()["workflows"] if workflow_name in w["name"]][0]    
    runs_response = requests.get(f"https://api.github.com/repos/milvus-io/milvus/actions/workflows/{workflow_id}/runs", params={"per_page":100}, headers=headers, verify=False)    
    workflow_runs = [r["id"] for r in runs_response.json()["workflow_runs"] if r["status"] == "completed"]
    print(len(workflow_runs))
    raw_results = []
    results = {}
    failure_job_links = []
    workflow_dict = {}
    for run in workflow_runs:
        job_url = f"https://api.github.com/repos/milvus-io/milvus/actions/runs/{run}/jobs"
        job_response = requests.request("GET", job_url, headers=headers, data=payload, verify=False)
        workflow_dict[run] = job_response.json()
        for r in job_response.json()["jobs"]:
            # raw_result = {}
            json_body = [
            {
                "measurement": "cpu_load_short",
                "tags": {
                    "compont": r["name"]
                },
                "time": r["started_at"],
                "fields": {
                    "conclusion": r["conclusion"],
                    "failure_reason": r["failure_reason"],
                    "html_url": r["html_url"]
                }
            }
            ]
            print("json_body", json_body)
            client.write_points(json_body)
            
            # raw_result["job_name"] = r["name"]
            # raw_result["job_status"] = r["status"]
            # raw_result["conclusion"] = r["conclusion"]
            # raw_result["html_url"] = r["html_url"]
            # raw_result["failure_reason"] = ""



            # if r["name"] not in results:
            #     results[r["name"]] = {"success": 0, "failure": 0, "failure_reason": []}
            # if r["status"] == "completed" and r["conclusion"] == "success":
            #     results[r["name"]]["success"] += 1
            # elif r["status"] == "completed" and r["conclusion"] != "success":
            #     results[r["name"]]["failure"] += 1
            #     failure_job_links.append(r["html_url"])
            #     for step in r["steps"]:
            #         if step["conclusion"] != "success":
            #             raw_result["failure_reason"] = step["name"]
            #             results[r["name"]]["failure_reason"].append(step["name"]) # find first failure step
            #             break
            # raw_results.append(raw_result)
    workflow_json = json.dumps(workflow_dict, indent = 4)
    with open(f"{workflow_name}_workflows.json", "w") as outfile:
        outfile.write(workflow_json)
    print(raw_results)
    print(len(raw_results))
    return results

for workflow in ["Pod Kill"]:
    result = analysis_workflow(workflow, response)
    # print(f"{workflow}:")
    # for k, v in result.items():
    #     print(f"{k} success: {v['success']}, failure: {v['failure']}, failure_reason: {v['failure_reason']}")    
    # print("\n")
