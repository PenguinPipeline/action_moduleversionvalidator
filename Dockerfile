FROM golang:latest

WORKDIR /app

COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt
COPY test_files/vm.json /app/test.json
COPY clitools/terraform-config-inspect /clitools/terraform-config-inspect

RUN apt-get update
RUN apt-get upgrade -y

RUN apt install python3
RUN apt install python3-pip -y

RUN pip3 install -r requirements.txt
RUN chmod +x /app/main.py
RUN chmod +x /clitools/terraform-config-inspect

ENV GOBIN /go/bin

RUN go get github.com/hashicorp/terraform-config-inspect

ENTRYPOINT ["/app/main.py"]