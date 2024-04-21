You'll see some different cc folders.

The cc folder that works with a particular chromium build is marked in [BUILD_AND_RELEASE.md](../../BUILD_AND_RELEASE.md).


Chromium had two APIs for headless integration, they axed the one we were using after letting it degrade.

We also used Chromium's `base::` namespace for JSON and Key-Value dictionary utilities, but they [mention](https://chromium.googlesource.com/chromium/src/+/refs/tags/88.0.4324.150/base/README.md) not to do that. They also claim that `base::` is "very mature". IMO, YMMV.

A true version 2.x.x of the C++ portion of Kaleido probably looks like: No reliance on `base::`, and full adoption of the only headless API left.
