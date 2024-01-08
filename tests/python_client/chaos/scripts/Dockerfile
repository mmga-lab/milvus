# 使用 Python 3.8 的基础镜像
FROM python:3.8-slim
RUN apt-get update && apt-get install -y git
# 设置工作目录
WORKDIR /app

COPY requirements.txt /app/
# 安装依赖
RUN pip install -r requirements.txt
RUN pip install pytest
# 将项目文件复制到容器中
COPY . /app


# 设置入口点为 pytest
ENTRYPOINT ["sh", "-c", "while true; do sleep 30; done"]
