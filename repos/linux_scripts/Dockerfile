# CLion remote docker environment (How to build docker container, run and stop it)
#
# Build and run:
#   docker build -t jonmmease/chromium-builder:0.6 -f Dockerfile .

FROM ubuntu:16.04

# Find stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update
# Look up date of tag in GitHub at https://github.com/chromium/chromium/
# Stable chrome version tag on 05/19/2020: 83.0.4103.61

# depot_tools commitlog: https://chromium.googlesource.com/chromium/tools/depot_tools/+log
# depot_tools commit hash from 05/19/2020: e67e41a
ENV DEPOT_TOOLS_COMMIT=e67e41a CHROMIUM_TAG="83.0.4103.61"

ENV DEPOT_TOOLS_UPDATE=0

# Reference: https://github.com/chromedp/docker-chromium-builder/blob/master/Dockerfile
RUN apt-get update

RUN \
    apt-get update && apt-get install -y ssh git curl wget lsb-base lsb-release sudo python2.7 python3-pip

RUN python3 -m pip install -U wheel setuptools

# Add npm 
RUN \
    curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash - \
    && apt-get install -y nodejs

# Set default Python to 2.7 for gclient
RUN \
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 10 \
    && python --version

# Force gclient to use Python 2
ENV GCLIENT_PY3=0

RUN \
    cd / \
    && git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git \ 
    && cd depot_tools \
    && git reset --hard $DEPOT_TOOLS_COMMIT
    
# timezone config
RUN \
    echo Etc/UTC > /etc/timezone

RUN \
    echo tzdata tzdata/Areas select Etc | debconf-set-selections

RUN \
    echo tzdata tzdata/Zones/Etc UTC | debconf-set-selections

ENV PATH=/depot_tools:$PATH

RUN \
    curl -s https://chromium.googlesource.com/chromium/src/+/$CHROMIUM_TAG/build/install-build-deps.sh?format=TEXT \
    | base64 -d > install-build-deps.sh && chmod +x ./install-build-deps.sh && \
    ./install-build-deps.sh --no-syms --no-arm --no-chromeos-fonts --no-nacl --no-prompt
