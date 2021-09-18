from yaml import full_load

def gen_experiment_config(yaml):
    with open(yaml) as f:
        _config = full_load(f)
        f.close()
    return _config

config = gen_experiment_config("chaos_objects/testcases.yaml")
print(config)
testcases = [x["testcase"]["name"] for x in config["Collections"]]
