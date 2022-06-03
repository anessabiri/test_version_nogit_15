FROM python:3.6
ENV TZ Europe/Paris 
RUN cp /usr/share/zoneinfo/Europe/Paris /etc/localtime



WORKDIR /workspace
COPY . /workspace/dvc_server/
COPY cli /workspace/cli

RUN  apt update -y &&  apt upgrade -y

RUN apt install wget -y

ARG USERNAME=dvc_server
ARG USER_UID=1000
ARG USER_GID=$USER_UID


RUN  wget \
       https://dvc.org/deb/dvc.list \
       -O /etc/apt/sources.list.d/dvc.list \
        && wget -qO - https://dvc.org/deb/iterative.asc |  apt-key add - \
        && apt update -y &&  apt install dvc

RUN python -m pip install --upgrade pip
RUN pip install -r dvc_server/requirements.txt

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# ********************************************************
# * Anything else you want to do like clean up goes here *
# ********************************************************

# [Optional] Set the default user. Omit if you want to keep the default as root.
USER $USERNAME

CMD cd dvc_server && python3 run_server.py
# CMD /root/.local/bin/gunicorn --access-logfile=/etc/logs/gunicorn-access.log --error-logfile=/etc/logs/gunicorn-error.log --log-level=info --worker-tmp-dir=/dev/shm --bind 0.0.0.0:4000 run_server:app

# --workers=2 --threads=4 --worker-class=gthread
#https://docs.gunicorn.org/en/stable/settings.html

EXPOSE 4000
