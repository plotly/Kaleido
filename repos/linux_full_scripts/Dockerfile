# CLion remote docker environment (How to build docker container, run and stop it)
#
# Build and run:
#   docker build -t jonmmease/kaleido-builder:0.6 -f Dockerfile .

FROM jonmmease/chromium-builder:0.8

# Update depot_tools in case there are changes in how to fetch code
RUN cd /depot_tools && git pull

# Fetch chromium source tree
RUN \
    cd / \
    && fetch --nohooks chromium

COPY ./repos/linux_scripts/gclient /.gclient

# Checkout chromium revision
RUN \
    cd /src \
    && git checkout tags/$CHROMIUM_TAG \
    && gclient sync -D --force --reset
    
RUN gclient runhooks
    
# Remove .git directory to save space
RUN rm -r /src/.git

# TODO: remove .git directories from third-party dependencies under src/third_party

# Build create x64 linux out directory
RUN mkdir -p /src/out/Kaleido_linux_x64/
COPY ./repos/linux_scripts/args_x64.gn /src/out/Kaleido_linux_x64/args.gn

# Add Kaleido executable
RUN echo ' \
executable("kaleido") { \
  sources = [ "app/kaleido.cc" ]  \
  deps = [  \
    ":headless_shell_lib",  \
    "//skia", \
  ]  \
} \
' >> /src/headless/BUILD.gn

    
# Perform build using headless_example. This will make sure we have all of the 
# dependencies that Kaleido needs precompiled.
RUN \
    cd /src \
    && gn gen out/Kaleido_linux_x64 \
    && ninja -C out/Kaleido_linux_x64 -j 20 headless_example
    

# Initialize project directories for other architectures, but don't precompile
RUN mkdir -p /src/out/Kaleido_linux_arm64/
COPY ./repos/linux_scripts/args_arm64.gn /src/out/Kaleido_linux_arm64/args.gn
RUN cd /src && gn gen out/Kaleido_linux_arm64
