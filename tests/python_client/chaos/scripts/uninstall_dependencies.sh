
# Exit immediately for non zero status
set -e
release=${1:-"milvus-chaos"}
ns=${2:-"chaos-testing"}
dependences=('etcd', 'minio', 'pulsar', 'kafka')
for d in ${dependences[@]}; do
    helm uninstall ${release}-${d} -n=${ns} || echo "helm release ${release}-${d} not found"
done

helm uninstall ${release}- -n=${ns} || echo "helm release ${release} not found"
kubectl delete pvc -l release=${release} -n=${ns} || echo "pvc with label release=${release} not found"
kubectl delete pvc -l app.kubernetes.io/instance=${release} -n=${ns} || echo "pvc with label app.kubernetes.io/instance=${release} not found"