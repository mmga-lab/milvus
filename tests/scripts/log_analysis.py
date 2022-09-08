cnt = 0
with open("/tem/ci_logs/ci_test_log.log","r") as f:

    lines = f.readlines()
    for i,line in enumerate(lines):
        if "ERROR" and "api_response" in line:
            cnt += 1
            print(f"{line}")
print(cnt)