import kaleido


def test_open_close():
    kaleido.start_sync_server()
    kaleido.stop_sync_server()
