# !/bin/sh
set -e 

CUR_FOLDER=$(dirname $(greadlink -f "$0"))

pushd $CUR_FOLDER

DEPLOY_MODE=$1
# get tags info
python get_tags.py

latest_rc_tag=$(jq -r .latest_rc_tag tags_info.json)
latest_tag=$(jq -r .latest_tag tags_info.json)
echo $latest_rc_tag
echo $latest_tag
# deploy old version milvus
pushd ./milvus/$DEPLOY_MODE
# docker-compose ps
# docker-compose down
rm -rf ./volumes
echo $latest_rc_tag
sed -i "" "s/milvusdb\/milvus\:.*/milvusdb\/milvus-dev\:$latest_rc_tag/g" docker-compose.yml
sed -i "" "s/milvusdb\/milvus-dev\:.*/milvusdb\/milvus-dev\:$latest_rc_tag/g" docker-compose.yml

docker-compose up -d

sleep 1m


popd

# need to wait all containers are healthy


# insert data into milvus and creat index

python insert_data.py

# search data
python search_data.py


# update milvu
pushd ./milvus/DEPLOY_MODE
docker-compose down
sed -i "" "s/milvusdb\/milvus\:.*/milvusdb\/milvus-dev\:$latest_tag/g" docker-compose.yml
sed -i "" "s/milvusdb\/milvus-dev\:.*/milvusdb\/milvus-dev\:$latest_tag/g" docker-compose.yml

docker-compose up -d

popd
# search data

python search_data.py



# stop milvus and remove volumes
pushd ./milvus/DEPLOY_MODE
# docker-compose ps
docker-compose down
rm -rf ./volumes
popd

popd
