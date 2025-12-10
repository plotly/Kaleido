import time

import kaleido

kaleido.start_sync_server()
time.sleep(0.5)
kaleido.stop_sync_server()
time.sleep(0.5)
