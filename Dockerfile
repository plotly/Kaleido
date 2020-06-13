# CLion remote docker environment (How to build docker container, run and stop it)
#
# Build and run:
#   docker build -t jonmmease/chromium-builder:0.5 -f Dockerfile .
#   docker run -d --cap-add sys_ptrace -p127.0.0.1:2222:22 --name orca-next jonmmease/orca-next:0.5
#   ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[localhost]:2222"
#
# stop:
#   docker stop orca-next
# 
# ssh credentials (test user):
#   user@password

FROM ubuntu:16.04

# Find stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update
# Look up date of tag in GitHub at https://github.com/chromium/chromium/
# Stable chrome version tag on 05/19/2020: 83.0.4103.61

# depot_tools commitlog: https://chromium.googlesource.com/chromium/tools/depot_tools/+log
# depot_tools commit hash from 05/19/2020: e67e41a
ENV DEPOT_TOOLS_COMMIT=e67e41a CHROMIUM_TAG="83.0.4103.61"
ENV WIN_TOOLCHAIN_HASH=7ebbede533b63df2394fe770745668433aab2c20


# Reference: https://github.com/chromedp/docker-chromium-builder/blob/master/Dockerfile
RUN apt-get update

RUN \
    apt-get update && apt-get install -y ssh git curl wget lsb-base lsb-release sudo python2.7
        
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

# Add windows toolchain to image
COPY win_toolchain/ /win_toolchain/

# Set windows toolchain environment variables
ENV \
    DEPOT_TOOLS_WIN_TOOLCHAIN_BASE_URL=/win_toolchain/ \
    GYP_MSVS_HASH_9ff60e43ba91947baca460d0ca3b1b980c3a2c23=%WIN_TOOLCHAIN_HASH%

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
    
# Pre accept msttcorefonts EULA
RUN \
    echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections
    
ENV PATH=/depot_tools:$PATH

RUN \
    curl -s https://chromium.googlesource.com/chromium/src/+/$CHROMIUM_TAG/build/install-build-deps.sh?format=TEXT \
    | base64 -d > install-build-deps.sh && chmod +x ./install-build-deps.sh && \
    ./install-build-deps.sh --no-syms --no-arm --no-chromeos-fonts --no-nacl --no-prompt


# Add SSH support
RUN ( \
    echo 'LogLevel DEBUG2'; \
    echo 'PermitRootLogin yes'; \
    echo 'PasswordAuthentication yes'; \
    echo 'Subsystem sftp /usr/lib/openssh/sftp-server'; \
  ) > /etc/ssh/sshd_config_test_clion \
  && rm -r /run/sshd && mkdir /run/sshd

RUN useradd -m user \
  && yes password | passwd user

CMD ["/usr/sbin/sshd", "-D", "-e", "-f", "/etc/ssh/sshd_config_test_clion"]
