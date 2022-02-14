# test-pod-kill-chaos (standalone) success: 29, failure: 0, failure_reason: []
# test-pod-kill-chaos (datacoord) success: 28, failure: 1, failure_reason: ['Milvus E2E Test']
# test-pod-kill-chaos (datanode) success: 28, failure: 1, failure_reason: ['Deploy Milvus']
# test-pod-kill-chaos (indexcoord) success: 28, failure: 1, failure_reason: ['Deploy Milvus']
# test-pod-kill-chaos (indexnode) success: 28, failure: 1, failure_reason: ['Deploy Milvus']
# test-pod-kill-chaos (proxy) success: 28, failure: 1, failure_reason: ['Milvus E2E Test']
# test-pod-kill-chaos (pulsar) success: 20, failure: 9, failure_reason: ['Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test', 'Milvus E2E Test']
# test-pod-kill-chaos (querycoord) success: 28, failure: 1, failure_reason: ['Deploy Milvus']
# test-pod-kill-chaos (querynode) success: 27, failure: 2, failure_reason: ['Milvus E2E Test', 'Milvus E2E Test']
# test-pod-kill-chaos (rootcoord) success: 27, failure: 2, failure_reason: ['Milvus E2E Test', 'Milvus E2E Test']
# test-pod-kill-chaos (etcd) success: 28, failure: 1, failure_reason: ['Milvus E2E Test']
# test-pod-kill-chaos (minio) success: 28, failure: 1, failure_reason: ['Milvus E2E Test']


import numpy as np
import matplotlib.pyplot as plt


component_list = ["standalone", "datacoord", "datanode", "indexcoord", "indexnode", "proxy", "pulsar", "querycoord", "querynode", "rootcoord", "etcd", "minio"]
success_cnt = [29, 28, 28, 28, 28, 28, 20, 28, 27, 27, 28, 28]
failure_cnt = [0, 1, 1, 1, 1, 1, 9, 1, 2, 2, 1, 1]


x = np.arange(len(component_list))

plt.xticks([index for index in x], component_list)
plt.xlabel("Component")
plt.bar(x, success_cnt, label='success', color='g')
plt.bar(x, failure_cnt, bottom=success_cnt, label='failure', color='r')
plt.legend()
plt.show()