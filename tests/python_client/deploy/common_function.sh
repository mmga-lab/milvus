
function replace_image_tag {
    image_repo=$1
    image_tag=$2
    if [ "$platform" == "Mac" ];
    then
        # for mac os
        sed -i "" "s/milvusdb\/milvus.*/${image_repo}\:${image_tag}/g" docker-compose.yml   
    else
        #for linux os 
        sed -i "s/milvusdb\/milvus.*/${image_repo}\:${image_tag}/g" docker-compose.yml
    fi

}

#to check containers all running and minio is healthy
function check_healthy {
    cnt=$(docker-compose ps | grep -E "running|Running|Up|up" | wc -l)
    healthy=$(docker-compose ps | grep "healthy" | wc -l)
    time_cnt=0
    echo "running num $cnt expect num $Expect"
    echo "healthy num $healthy expect num $Expect_health"
    while [[ $cnt -ne $Expect || $healthy -ne 1 ]];
    do
    printf "waiting all containers get running\n"
    sleep 5
    let time_cnt+=5
    # if time is greater than 300s, the condition still not satisfied, we regard it as a failure
    if [ $time_cnt -gt 300 ];
    then
        printf "timeout,there are some issue with deployment!"
        error_exit
    fi
    cnt=$(docker-compose ps | grep -E "running|Running|Up|up" | wc -l)
    healthy=$(docker-compose ps | grep "healthy" | wc -l)
    echo "running num $cnt expect num $Expect"
    echo "healthy num $healthy expect num $Expect_health"
    done
}