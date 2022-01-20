
release=${1:-"milvs-chaos"}
ns=${2:-"chaos-testing"}
bash uninstall_milvus.sh ${release} ${ns}|| true

helm repo add milvus https://milvus-io.github.io/milvus-helm/
helm repo update
helm install --wait --timeout 720s ${release} milvus/milvus \
                    --set metrics.serviceMonitor.enabled=true \  
                    --set pulsar.broker.podMonitor.enabled=true \
                    --set pulsar.proxy.podMonitor.enabled=true \                    
                    -f ../cluster-values.yaml -n=${ns}
