#!/bin/bash
set -e
# set -x

ROOT_FOLDER=$(cd "$(dirname "$0")";pwd)

# to export docker-compose logs before exit
function error_exit {
    pushd ${ROOT_FOLDER}/${Deploy_Dir}
    echo "test failed"
    current=`date "+%Y-%m-%d-%H-%M-%S"`
    if [ ! -d logs  ];
    then
        mkdir logs
    fi
    docker-compose logs > ./logs/${Deploy_Dir}-${MODE}-${current}.log
    echo "log saved to `pwd`/logs/${Deploy_Dir}-${MODE}-${current}.log"
    popd
    exit 1
}
#to check containers all running and minio is healthy
function check_healthy {
    cnt=`docker-compose ps | grep -E "Running|Up" | wc -l`
    healthy=`docker-compose ps | grep "Healthy" | wc -l`
    time_cnt=0
    echo "cnt num $cnt"
    echo "healthy num $healthy"
    while [[ $cnt -ne $Expect || $healthy -ne 1 ]];
    do
    printf "waiting all containers get running\n"
    sleep 5s
    let time_cnt+=5
    # if time is greater than 300s, the condition still not satisfied, we regard it as a failure
    if [ $time_cnt -gt 300 ];
    then
        printf "timeout,there are some issue with deployment!"
        error_exit
    fi
    cnt=`docker-compose ps | grep -E "Running|Up" | wc -l`
    healthy=`docker-compose ps | grep "healthy" | wc -l`
    echo "running num $cnt"
    echo "healthy num $healthy"
    done
}

Deploy_Dir=${1:-"standalone"}
MODE=${2:-"reinstall"}
Release=${3:-"2.0.0-rc5"}
if [ ! -d ${Deploy_Dir}  ];
then
    mkdir ${Deploy_Dir}
fi
latest_tag=2.0.0-rc5-latest
latest_rc_tag=2.0.0-rc4-latest

pushd ${Deploy_Dir}
# download docker-compose.yml
wget https://github.com/milvus-io/milvus/releases/download/v${Release}/milvus-${Deploy_Dir}-docker-compose.yml -O docker-compose.yml
# clean env to deoploy a fresh milvus
docker-compose down
sleep 10s
docker-compose ps
rm -rf ./volumes

# first deployment
if [ "$MODE" == "reinstall" ];
then
    printf "start to deploy latest rc tag milvus\n"
    sed -i "" "s/milvusdb\/milvus.*/milvusdb\/milvus-dev\:${latest_tag}/g" ./docker-compose.yml
fi
if [ "$MODE" == "upgrade" ];
then
    printf "start to deploy previous rc tag milvus\n"
    sed -i "" "s/milvusdb\/milvus.*/milvusdb\/milvus-dev\:${latest_rc_tag}/g" docker-compose.yml
fi
cat docker-compose.yml|grep milvusdb
Expect=`grep "container_name" docker-compose.yml | wc -l`
docker-compose up -d
check_healthy
docker-compose ps
popd

# test for first deploymnent
printf "test for first deployment\n"
if [ "$MODE" == "reinstall" ];
then
    python scripts/test_reinstall.py || error_exit
fi
if [ "$MODE" == "upgrade" ];
then
    python scripts/test_before_upgrade.py || error_exit
fi

pushd ${Deploy_Dir}
# uninstall milvus
printf "start to uninstall milvus\n"
docker-compose down
sleep 10s
printf "check all containers removed\n"
docker-compose ps

# second deployment
if [ "$MODE" == "reinstall" ];
then
    printf "start to reinstall milvus\n"
fi
if [ "$MODE" == "upgrade" ];
then
    printf "start to upgrade milvus\n"
    sed -i "" "s/milvusdb\/milvus.*/milvusdb\/milvus-dev\:${latest_tag}/g" docker-compose.yml   

fi
cat docker-compose.yml|grep milvusdb
docker-compose up -d
check_healthy
docker-compose ps
popd

# test for second deployment
printf "test for second deployment\n"
if [ "$MODE" == "reinstall" ];
then
    python scripts/test_reinstall.py || error_exit
fi
if [ "$MODE" == "upgrade" ];
then
    python scripts/test_after_upgrade.py || error_exit
fi

pushd ${Deploy_Dir}
# clean env
docker-compose ps
docker-compose down
sleep 10s
docker-compose ps
rm -rf ./volumes
popd


