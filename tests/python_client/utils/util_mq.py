from confluent_kafka.admin import AdminClient
import requests
import time
from loguru import logger as log


def delete_kafka_topics(server_ip, port=9092):
    conf = {'bootstrap.servers': f'{server_ip}:{port}'}
    kadmin = AdminClient(conf)
    topics = kadmin.list_topics().topics
    topics = list(topics.keys())
    fs = kadmin.delete_topics(topics)
    for topic, f in fs.items():
        try:
            f.result()
            log.info(f"Topic {topic} deleted")
        except Exception as e:
            log.info(f"Failed to delete topic {topic} with error {e}")
    topics = kadmin.list_topics().topics
    log.info(topics)
    # check whether the topics are deleted
    log.info("check the topics status")
    start_time = time.time()
    while time.time() - start_time < 60:
        topics = kadmin.list_topics().topics
        topics = list(topics.keys())
        for topic in topics:
            log.info(f"topic: {topic}")
        log.info("##" * 20)
        log.info(f"topics num: {len(topics)}")
        time.sleep(5)


def delete_pulsar_topics(server_ip, port=80):
    url = f"http://{server_ip}:{port}/admin/v2/persistent/public/default"
    rsp = requests.get(url)
    if rsp.status_code == 200:
        topics = rsp.json()
        log.info(f"topics: {topics}")
        for topic in topics:
            topic_name = topic.split("/")[-1]
            rsp = requests.delete(f"{url}/{topic_name}", params={"force": "true"})
            if rsp.status_code == 204:  # 204 means no content in response and this is as expected
                log.info(f"Topic {topic_name} deleted")
            else:
                log.info(f"Failed to delete topics with status code {rsp.status_code}")

    else:
        log.info(f"Failed to get topics with status code {rsp.status_code}")
    # check whether the topics are deleted
    log.info("check the topics status")
    start_time = time.time()
    while time.time() - start_time < 60:
        rsp = requests.get(url)
        if rsp.status_code == 200:
            topics = rsp.json()
            for topic in topics:
                log.info(f"topic: {topic}")
            log.info("##" * 20)
            log.info(f"topics num: {len(topics)}")
        else:
            log.info(f"Failed to get topics with status code {rsp.status_code}")
        time.sleep(5)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="config for delete topics")
    parser.add_argument("--mq_type", type=str, default="pulsar", help="message queue type")
    parser.add_argument("--server_ip", type=str, default="10.101.83.120", help="server ip")
    args = parser.parse_args()
    mq_type = args.mq_type
    server_ip = args.server_ip
    if mq_type == "kafka":
        delete_kafka_topics(server_ip)
    elif mq_type == "pulsar":
        delete_pulsar_topics(server_ip)
    else:
        log.info(f"{mq_type} is not supported")
