# docker build --network host -t ran .
# docker run -it --network host --name ran1 -v /mnt/e/work/ransomware:/home/ransomwatch ran

FROM debian:12

RUN apt-get update -y
#RUN apt-get upgrade -yy
# 安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    gcc  libxml2-dev \
    libxslt-dev \
    libffi-dev \
    make curl unzip \
    python3  pip \
    wget  libxi6 \
    libgconf-2-4  pkg-config \
    build-essential \
    python3-dev \
    default-libmysqlclient-dev \
	libmariadb-dev-compat \
	libmariadb-dev \
	apt-transport-https lsb-release ca-certificates

# 添加chrome
run wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-archive-keyring.gpg

run echo "deb [signed-by=/usr/share/keyrings/google-archive-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y \
	google-chrome-stable

COPY requirements.txt /home/requirements.txt

RUN pip3 install -r /home/requirements.txt \
	--break-system-packages

# playwright 安装
# RUN playwright install
# RUN playwright install-deps

