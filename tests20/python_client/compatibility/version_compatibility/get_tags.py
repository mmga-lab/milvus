import requests
import json
# get milvus rc tags
url = "https://registry.hub.docker.com/v2/repositories/milvusdb/milvus-dev/tags?ordering=last_updated&name=rc"

response = requests.get(url)
r = response.json()

tags = [x["name"] for x in r["results"] if "latest" in x["name"] ]
print(tags)
latest_rc = tags[0]

print(f"latest_rc tag: {latest_rc}")


url = "https://registry.hub.docker.com/v2/repositories/milvusdb/milvus-dev/tags?ordering=last_updated"

response = requests.get(url)
r = response.json()

tags = [x["name"] for x in r["results"]]
print(tags)
latest = tags[1]
print(f"latest tag: {latest}")

info = {
    "latest_tag":latest,
    "latest_rc_tag":latest_rc
}
with open("tags_info.json","w+") as f:
    json.dump(info,f)

