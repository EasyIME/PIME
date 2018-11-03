import os
import json
import logging

import pyuv

from win_utils import *
from input_backend import InputBackend

WINDOW_CLASS_NAME = 'PIME_Manager'

INPUT_CLIPBOARD_FORMAT_NAME = 'PIME::Input'
INPUT_CLIPBOARD_FORMAT = 0

OUTPUT_CLIPBOARD_FORMAT_NAME = 'PIME::Output'
OUTPUT_CLIPBOARD_FORMAT = 0

main_window = None
all_backends = {}
text_service_to_backend_map = {}
all_clients = {}

top_dir = os.path.dirname(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


class ClientInfo(object):
    def __init__(self, client_id, text_service_id):
        self.client_id = client_id
        self.text_service_id = text_service_id

    def get_backend(self):
        return text_service_to_backend_map[self.text_service_id]


def handle_client_request(client_id, msg):
    # print('REQ:\n', client_id, msg)
    # client_id = msg['clientId']
    if client_id not in all_clients:
        method = msg.get('method')
        if method == 'init':
            client = ClientInfo(client_id=client_id, text_service_id=msg['id'])
            all_clients[client_id] = client
        else:
            raise KeyError('not a init event')
    else:
        client = all_clients[client_id]

    backend = client.get_backend()
    backend.handle_client_request(client_id, msg)


def handle_backend_response(client_id, msg):
    # add the current response to the output queue
    # print('RESP:\n', client_id, msg)
    with open_clipboard(main_window):
        data = get_clipboard_data(OUTPUT_CLIPBOARD_FORMAT)
        if data is None:
            data = b''
        line = '{client_id}\t{msg}\n'.format(
            client_id=client_id,
            msg=json.dumps(msg)
        )
        data += line.encode('utf-8')
        set_clipboard_data(OUTPUT_CLIPBOARD_FORMAT, data)


def process_pending_client_requests(hwnd):
    # process incoming client requests from the input queue
    with open_clipboard(hwnd):
        data = get_clipboard_data(INPUT_CLIPBOARD_FORMAT)
        # print('CLIPBOARD:', data)
        if data:
            set_clipboard_data(INPUT_CLIPBOARD_FORMAT, b'')  # clear the input queue
            for line in data.splitlines():
                # print('INPUT:', line)
                try:
                    line = line.strip().decode('utf-8')
                    if not line:
                        continue
                    client_id, msg = line.split('\t', maxsplit=1)
                    msg = json.loads(msg)
                    handle_client_request(client_id, msg)
                except (UnicodeDecodeError, ValueError, TypeError) as e:
                    logger.exception('unable to parse input message: %s', e)
                except Exception as e:
                    logger.exception('fail to handle client request: %s', e)


def window_proc(hwnd, msg, wparam, lparam):
    if msg == WM_CLIPBOARDUPDATE:
        # print('clipboard changed:', windll.user32.GetClipboardSequenceNumber())
        process_pending_client_requests(hwnd)
    return windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

window_proc_ptr = None

def init_clipboard_monitor():
    # register clipboard format
    global INPUT_CLIPBOARD_FORMAT, OUTPUT_CLIPBOARD_FORMAT
    INPUT_CLIPBOARD_FORMAT = windll.user32.RegisterClipboardFormatW(INPUT_CLIPBOARD_FORMAT_NAME)
    OUTPUT_CLIPBOARD_FORMAT = windll.user32.RegisterClipboardFormatW(OUTPUT_CLIPBOARD_FORMAT_NAME)

    # create main window
    global wnd_proc_ptr
    # this variable needs to be global to keep its alive outside this function.
    # otherwise the C pointer will become invalid.
    wnd_proc_ptr = WNDPROC(window_proc)
    register_window_class(WINDOW_CLASS_NAME, wnd_proc_ptr)

    global main_window
    main_window = create_window(WINDOW_CLASS_NAME)

    # register a clipboard change listener
    with open_clipboard(main_window):
        windll.user32.AddClipboardFormatListener(main_window)


def run_clipboard_monitor():
    init_clipboard_monitor()
    process_pending_client_requests(main_window)
    run_windows_message_loop()


def init_backends():
    backend_file = os.path.join(top_dir, 'backends.json')
    with open(backend_file) as f:
        data = json.load(f)
        for backend_info in data:
            name = backend_info['name']
            backend = InputBackend(name=name,
                                   command=backend_info['command'],
                                   params=backend_info['params'],
                                   working_dir=backend_info['workingDir'])
            all_backends[name] = backend
            # map text service guid to backend
            for text_service_id in backend.input_methods:
                text_service_to_backend_map[text_service_id] = backend

            backend.add_response_callback(handle_backend_response)


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    init_backends()
    for tid, value in text_service_to_backend_map.items():
        print(tid, value)

    loop = pyuv.Loop.default_loop()
    # threading.Thread(target=run_clipboard_monitor)

    # run Windows message loop (this never returns)
    loop.queue_work(run_clipboard_monitor)

    for backend in all_backends.values():
        backend.start()

    loop.run()


if __name__ == '__main__':
    main()
