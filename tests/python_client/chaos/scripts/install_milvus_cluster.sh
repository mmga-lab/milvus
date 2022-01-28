#!/bin/bash
set -e

release=${1:-"milvs-chaos"}
ns=${2:-"chaos-testing"}
pod=${3:-"querynode"}
node_num=${4:-1}
bash uninstall_milvus.sh ${release} ${ns}|| true

declare -A pod_map=(["querynode"]="queryNode" ["indexnode"]="indexNode" ["datanode"]="dataNode" ["proxy"]="proxy")
echo "insatll cluster"
helm install --wait --version==${HELM_MILVUS_VERSION:-"3.0.0"}  --timeout 720s ${RELEASE_NAME:-$release} milvus-dev/milvus \
                    --set cluster.enabled=true \
                    --set image.all.repository=${REPOSITORY:-"milvusdb/milvus-dev"} \
                    --set image.all.tag=${IMAGE_TAG:-"master-latest"} \
                    --set ${pod_map[${pod}]}.replicas=$node_num \
                    --set metrics.serviceMonitor.enabled=true \
                    --set pulsar.broker.podMonitor.enabled=true \
                    --set pulsar.proxy.podMonitor.enabled=true \
                    -f ../cluster-values.yaml -n=${ns}