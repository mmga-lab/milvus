

## overview
To test deployment by docker-compose(Both standalone and cluster)

* re-install milvus to check data persistence
    1. Deploy Milvus
    2. Insert data
    3. Build index 
    4. Search
    5. Stop Milvus
    6. Repeat from step #1
* upgrade milvus to check data compatibility
    1. Deploy Milvus （Previous RC)
    2. Insert data
    3. Search
    4. Stop Milvus
    5. Deploy Milvus  (Latest RC)
    6. Build index
    7. Search

## project structure
```
.
├── README.md
├── cluster # dir to deploy cluster
│   ├── logs # dir to save logs
│   └──docker-compose.yml
├── standalone # dir to deploy standalone
│   ├── logs # dir to save logs
│   └──docker-compose.yml
├── scripts
│   ├── test_after_upgrade.py
│   ├── test_before_upgrade.py
│   ├── test_reinstall.py
│   └── utils.py
├── test.sh # script to run a single task
└── run.sh # script to run all tasks
```

## usage
make sure you have installed `docker`,`docker-compose` and `pymilvus`!

for single test task

`
$ bash test.sh standalone reinstall
`

run all tasks
`
$ bash run.sh
`