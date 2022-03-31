pipeline {
    options {
        timestamps()
    }
    agent {
        kubernetes {
            label "milvus-chaos-test"
            defaultContainer 'main'
            yamlFile "build/ci/jenkins/pod/chaos-test.yaml"
            customWorkspace '/home/jenkins/agent/workspace'
            // idle 5 minutes to wait clean up tasks
            idleMinutes 5
        }
    }
    parameters{
        choice(
            description: 'Choose tools to deploy Milvus',
            name: 'deploy_tool',
            choices: ['docker-compose']
        )
        choice(
            description: 'Milvus Mode',
            name: 'milvus_mode',
            choices: ["standalone", "cluster"]
        )
        choice(
            description: 'Deploy Test Task',
            name: 'deploy_task',
            choices: ['reinstall', 'upgrade']
        )
        string(
            description: 'Release Version',
            name: 'release_version',
            defaultValue: 'v2.0.1'
        )        
        string(
            description: 'Old Image Repository',
            name: 'old_image_repository',
            defaultValue: 'milvusdb/milvus'
        )
        string(
            description: 'Old Version Image Tag',
            name: 'old_image_tag',
            defaultValue: 'latest'
        )
        string(
            description: 'New Image Repository',
            name: 'new_image_repository',
            defaultValue: 'milvusdb/milvus-dev'
        )
        string(
            description: 'New Version Image Tag',
            name: 'new_image_tag',
            defaultValue: 'master-latest'
        )
        string(
            description: 'Data Size',
            name: 'data_size',
            defaultValue: '3000'
        )
        string(
            description: 'Idle Time in Minutes',
            name: 'idel_time',
            defaultValue: '1'
        )
        booleanParam(
            description: 'Keep Env',
            name: 'keep_env',
            defaultValue: 'false'
        )
    }
    
    environment {
        ARTIFACTS = "${env.WORKSPACE}/_artifacts"
        RELEASE_NAME = "${params.milvus_mode}-${params.deploy_task}-${env.BUILD_ID}"
        NAMESPACE = "chaos-testing"
        new_image_tag_modified = ""
    }

    stages {
        stage ('Install Dependency') {
            steps {
                container('main') {
                    dir ('tests/python_client') {
                        script {
                        sh "pip install -r requirements.txt --trusted-host https://test.pypi.org" 
                        }
                    }
                }
            }
        }
        stage ('First Milvus Deployment') {
            options {
              timeout(time: 100, unit: 'MINUTES')   // timeout on this stage
            }
            steps {
                container('main') {
                    dir ("tests/python_client/deploy/${params.milvus_mode}") {
                        script {
                            def old_image_tag_modified = ""
                            def new_image_tag_modified = ""

                            def old_image_repository_modified = ""
                            def new_image_repository_modified = ""

                            if ("${params.old_image_tag}" == "master-latest") {
                                old_image_tag_modified = sh(returnStdout: true, script: 'bash ../../../../scripts/docker_image_find_tag.sh -n milvusdb/milvus-dev -t master-latest -f master- -F -L -q').trim()    
                            }
                            else if ("${params.old_image_tag}" == "latest") {
                                old_image_tag_modified = sh(returnStdout: true, script: 'bash ../../../../scripts/docker_image_find_tag.sh -n milvusdb/milvus -t latest -F -L -q').trim()
                            }
                            else {
                                old_image_tag_modified = "${params.old_image_tag}"
                            }

                            if ("${params.new_image_tag}" == "master-latest") {
                                new_image_tag_modified = sh(returnStdout: true, script: 'bash ../../../../scripts/docker_image_find_tag.sh -n milvusdb/milvus-dev -t master-latest -f master- -F -L -q').trim()    
                            }
                            else {
                                new_image_tag_modified = "${params.new_image_tag}"
                            }
                            sh "echo ${old_image_tag_modified}"
                            sh "echo ${new_image_tag_modified}"
                            sh "echo ${new_image_tag_modified} > new_image_tag_modified.txt"
                            stash includes: 'new_image_tag_modified.txt', name: 'new_image_tag_modified'
                            env.new_image_tag_modified = new_image_tag_modified
                            sh "docker pull ${params.old_image_repository}:${old_image_tag_modified}"
                            sh "docker pull ${params.new_image_repository}:${new_image_tag_modified}"
                            if ("${params.deploy_task}" == "reinstall"){
                                echo "reinstall Milvus with new image tag"
                                old_image_tag_modified = new_image_tag_modified
                            }
                            if ("${params.deploy_task}" == "reinstall"){
                                echo "reinstall Milvus with new image repository"
                                old_image_repository_modified = "${params.new_image_repository}"
                            }
                            else {
                                old_image_repository_modified = "${params.old_image_repository}"
                            }

                            // download docker-compose.yaml
                            if ("${params.deploy_task}" == "reinstall"){
                                echo "download docker-compose.yaml from master branch"
                                sh "wget https://raw.githubusercontent.com/milvus-io/milvus/master/deployments/docker/${params.milvus_mode}/docker-compose.yml -O docker-compose.yml"  
                            }
                            else {
                                echo "download docker-compose.yaml from release branch"
                                sh "wget https://github.com/milvus-io/milvus/releases/download/${params.release_version}/milvus-${params.milvus_mode}-docker-compose.yml -O docker-compose.yml"                                 
                            }

                            // modify docker-compose.yaml
                            sh "python3 ../scripts/modify_yaml.py --file_name 'docker-compose.yml' --suffix '${env.BUILD_ID}'"

                            // deploy milvus
                            sh"""
                            MILVUS_IMAGE="${old_image_repository_modified}:${old_image_tag_modified}" \
                            DOCKER_VOLUME_DIRECTORY="${pwd}" \
                            docker-compose up -d
                            """
                            sleep(30)
                            // wait for milvus ready
                            sh "bash ../check_healthy.sh"

                        }
                    }
                }
            }
        }
        stage ('Run first test') {
            steps {
                container('main') {
                    dir ('tests/python_client/deploy/scripts') {
                        script {
                        def host = sh(returnStdout: true, script: "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' milvus-${params.milvus_mode}-${env.BUILD_ID}").trim()    
                        // def host = docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' milvus-standalone
                        
                        if ("${params.deploy_task}" == "reinstall") {
                            sh "python3 action_before_reinstall.py --host ${host} --data_size ${params.data_size}"
                        }

                        if ("${params.deploy_task}" == "upgrade") {
                            sh "python3 action_before_upgrade.py --host ${host} --data_size ${params.data_size}"
                        }
                        }
                    }
                }
            }
            
        }

        stage ('Milvus Idle Time') {

            steps {
                container('main') {
                    dir ('tests/python_client/deploy') {
                        script {
                        echo "sleep ${params.idel_time}m"
                        sh "sleep ${params.idel_time}m"
                        }
                    }
                }
            }
        }

        stage ('Restart Milvus') {
            options {
              timeout(time: 15, unit: 'MINUTES')   // timeout on this stage
            }
            steps {
                container('main') {
                    dir ('tests/python_client/deploy${params.milvus_mode}') {
                        script {
                            sh "docker-compose restart"
                            sleep(30)
                            sh "bash ../check_healthy.sh"
                        }
                    }
                }
            }
            
        }

        stage ('Second Milvus Deployment') {
            options {
              timeout(time: 15, unit: 'MINUTES')   // timeout on this stage
            }
            steps {
                container('main') {
                    dir ("tests/python_client/deploy/${param.milvus_mode}") {                                     
                        script {

                            // in case of master-latest is different in two stages, we need use the new_image_tag_modified.txt to store the new_image_tag in first stage
                            // this case will happen when a new images is pushed to docker hub after the first stage
                            def new_image_tag_modified = ""

                            dir ("new_image_tag_modified"){
                                try{
                                    unstash 'new_image_tag_modified'
                                    new_image_tag_modified=sh(returnStdout: true, script: 'cat new_image_tag_modified.txt | tr -d \'\n\r\'')
                                }catch(e){
                                    print "No image tag info remained"
                                    exit 1
                                }
                            }
                            // if the task is upgrade, we need to download the docker-compose.yaml from master branch
                            // because the different may not only be the image tag, but also some other parameters
                            if ("${params.deploy_task}" == "upgrade"){
                                echo "download docker-compose.yaml from master branch"
                                sh "wget https://raw.githubusercontent.com/milvus-io/milvus/master/deployments/docker/${params.milvus_mode}/docker-compose.yml -O docker-compose.yml"
                                // modify docker-compose.yaml
                                sh "python3 ../scripts/modify_yaml.py --file_name 'docker-compose.yml' --suffix '${env.BUILD_ID}'"
                            }

                            // deploy milvus
                            sh"""
                            MILVUS_IMAGE="${new_image_repository_modified}:${new_image_tag_modified}" \
                            DOCKER_VOLUME_DIRECTORY="${pwd}" \
                            docker-compose up -d
                            """
                            // wait for milvus ready
                            sleep(30)
                            sh "bash ../check_healthy.sh"
                        }
                    }
                }
            }
            
        }

        stage ('Run Second Test') {
            steps {
                container('main') {
                    dir ('tests/python_client/deploy/scripts') {
                        script {
                        sh "sleep 60s" // wait loading data for the second deployment to be ready
                        def host = sh(returnStdout: true, script: "docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' milvus-${params.milvus_mode}-${env.BUILD_ID}").trim()
                        if ("${params.deploy_task}" == "reinstall") {
                            sh "python3 action_after_reinstall.py --host ${host} --data_size ${params.data_size}"
                        }

                        if ("${params.deploy_task}" == "upgrade") {
                            sh "python3 action_after_upgrade.py --host ${host} --data_size ${params.data_size}"
                        }
                        }
                    }
                }
            }
            
        }
 
    }
    post {
        always {
            echo 'upload logs'
            container('main') {
                dir ("tests/python_client/deploy/${params.milvus_mode}") {
                    script {
                        echo "get pod status"
                        sh "docker-compose ps -a || true"
                        echo "collecte logs"
                        sh "mkdir -p logs"
                        sh "docker-compose logs > ./logs/${param.milvus_mode}-${param.deploy_task}.log 2>&1 || echo 'export log failed'"
                        echo "upload logs"
                        sh "tar -zcvf artifacts-${param.milvus_mode}-${param.deploy_task}-logs.tar.gz log/ --remove-files || true"
                        archiveArtifacts artifacts: "artifacts-${param.milvus_mode}-${param.deploy_task}-logs.tar.gz", allowEmptyArchive: true
                        if ("${params.keep_env}" == "false"){
                            sh "docker-compose down || true"
                            sh "rm -rf volumes || true"
                        }
                    }
                }
            }
        }
        success {
            echo 'I succeeeded!'
            container('main') {
                dir ("tests/python_client/deploy/${params.milvus_mode}") {
                    script {
                        sh "docker-compose down || true"
                        sh "rm -rf volumes || true"
                    }
                }
            }  

        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
        }
        changed {
            echo 'Things were different before...'
        }
    }
}