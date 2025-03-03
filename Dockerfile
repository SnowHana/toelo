FROM ubuntu:latest
LABEL authors="nautilus"

ENTRYPOINT ["top", "-b"]