import time
import json

from win_utils import *

INPUT_CLIPBOARD_FORMAT_NAME = 'PIME::Input'
OUTPUT_CLIPBOARD_FORMAT_NAME = 'PIME::Output'

INPUT_CLIPBOARD_FORMAT = windll.user32.RegisterClipboardFormatW(INPUT_CLIPBOARD_FORMAT_NAME)
OUTPUT_CLIPBOARD_FORMAT = windll.user32.RegisterClipboardFormatW(OUTPUT_CLIPBOARD_FORMAT_NAME)


def send_request(client_id, message):
    with open_clipboard(hwnd=0):
        data = get_clipboard_data(INPUT_CLIPBOARD_FORMAT) or b''
        line = client_id + '\t' + json.dumps(message)
        data += line.encode('utf-8')
        ret = set_clipboard_data(INPUT_CLIPBOARD_FORMAT, data)
        print('SET:', ret, data)


def wait_response(client_id):
    responses = []
    while True:
        with open_clipboard(hwnd=0):
            data = get_clipboard_data(OUTPUT_CLIPBOARD_FORMAT)
            if not data:
                continue
            print('GET:', data)
            data = data.decode('utf-8')
            remain_lines = []
            for line in data.splitlines():
                print('    LINE:', line)
                if line.startswith(client_id):
                    _, msg_text = line.split('|', 1)
                    responses.append(json.loads(msg_text))
                else:
                    remain_lines.append(line)
            if responses:
                data = remain_lines.join('\n')
                set_clipboard_data(OUTPUT_CLIPBOARD_FORMAT, data)
                break
            else:
                time.sleep(0.01)
    return responses


test_client_id = 'test_client_id'
test_msg = {
    'method': 'init',
    'id': '{263DC448-FD3B-497C-AAC3-E915DC280D92}',
    'isWindows8Above': True,
    'isMetroApp': False,
    'isUiLess': False,
    'isConsole': False
}

send_request(test_client_id, test_msg)
resps = wait_response(test_client_id)
print(resps)
