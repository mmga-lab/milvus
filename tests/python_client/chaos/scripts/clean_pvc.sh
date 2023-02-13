
# Exit immediately for non zero status
set -e
release=${1:-"milvus-chaos"}
ns=${2:-"chaos-testing"}
kubectl delete pvc -l release=${release} -n=${ns} || echo "pvc with label release=${release} not found"
kubectl delete pvc -l app.kubernetes.io/instance=${release} -n=${ns} || echo "pvc with label app.kubernetes.io/instance=${release} not found"