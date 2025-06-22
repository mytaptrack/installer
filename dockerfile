FROM --platform=linux/amd64 python:3.9-slim

RUN apt-get update
RUN apt-get -y install npm gnupg curl unzip
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
RUN npm i aws-cdk esbuild -g
ENV PATH="$PATH:/bin/python/executable/"

COPY ./cicd ./cicd
COPY ./mytaptrack_installer.py .
COPY ./requirements.txt .
COPY ./components ./components
COPY ./pages ./pages
COPY ./sm-text-logo.gif .
COPY ./styles.css .
COPY ./LICENSE .
COPY ./favicon.ico .


RUN pip install -r ./requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "mytaptrack_installer.py"]
