

pods=("datacoord" "datanode" "indexcoord" "indexnode" "proxy" "pulsar" "querycoord" "querynode" "rootcoord")

for pod in ${pods[*]}
do
# substitute component as $pod
cat << EOF > ./chaos_objects/chaos_${pod}_network_partition.yaml  
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: test-${pod}-network-partition
  namespace: chaos-testing
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - chaos-testing
    labelSelectors:
      app.kubernetes.io/instance: chaos-testing
      app.kubernetes.io/name: milvus
  duration: 5m
  direction: both
  target:
    selector:
      namespaces:
        - chaos-testing
      labelSelectors:
        app.kubernetes.io/instance: chaos-testing
        app.kubernetes.io/name: milvus
        component: ${pod}
    mode: one
EOF
# exec chaos
cat ./chaos_objects/chaos_${pod}_network_partition.yaml|grep "component"
# pytest -s -v --host 10.96.70.171 --log-cli-level=INFO
done
