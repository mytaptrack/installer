FROM --platform=linux/amd64 python:3.9-slim

RUN apt-get update
RUN apt-get -y install npm gnupg
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
RUN npm i aws-cdk esbuild -g
ENV PATH="$PATH:/bin/python/executable/"

COPY ./cicd ./cicd
COPY ./config_storage.py .
COPY ./deployment.py .
COPY ./encryption.py .
COPY ./html_resources.py .
COPY ./license.py .
COPY ./mytaptrack_installer.py .
COPY ./requirements.txt .
copy ./utils.py .

RUN pip install -r ./requirements.txt

expose 8501

CMD ["streamlit", "run", "mytaptrack_installer.py"]
