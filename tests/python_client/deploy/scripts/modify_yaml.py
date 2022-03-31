
# this function is used to modify the docker-compose.yaml file, 
# to make the container name and network are unique
import yaml
import os
def modify_yaml(file_name, suffix):
    file_name = os.path.join(os.getcwd(), file_name)
    with open(file_name, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for k in data['services'].keys():
        data['services'][k]['container_name'] = f"milvus-{k}-{suffix}"
    data['networks']['default']['name'] = f"milvus-{suffix}"
    with open(file_name, 'w') as f:
        yaml.dump(data, f)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='config for deploy test')
    parser.add_argument('--file_name', type=str, default="docker-compose.yml", help='docker-compose.yaml file name')
    parser.add_argument('--suffix', type=str, default="test", help='suffix for container name')
    args = parser.parse_args()
    file_name = args.file_name
    suffix = args.suffix
    modify_yaml(file_name, suffix)