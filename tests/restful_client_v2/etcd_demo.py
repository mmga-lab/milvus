from etcd import Client

# 创建etcd客户端
client = Client(host='10.104.19.56', port=2379)

# 获取所有键
response = client.get_prefix('/')
keys = [node.key for node in response.etcd_index.nodes]

# 打印所有键
for key in keys:
    print(key)
