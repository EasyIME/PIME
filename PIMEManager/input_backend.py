import os
import glob
import json
import logging

import pyuv

logger = logging.getLogger(__name__)
cur_dir = os.path.dirname(__file__)
top_dir = os.path.dirname(cur_dir)

logger.setLevel(logging.DEBUG)


class InputBackend(object):
    def __init__(self, name, command, working_dir, params):
        self.name = name
        self.command = command
        self.working_dir = working_dir
        self.params = params
        self.stdout = None
        self.stdin = None
        self.stderr = None
        self.process = None
        self.output_buffer = b''
        self.input_methods = {}
        self.init_input_methods()

        self._restarting = False
        self._response_callbacks = []

    def init_input_methods(self):
        """Find all ime.json definition files for input method modules"""
        input_methods_dir = os.path.join(top_dir, self.name, 'input_methods')
        ime_files = glob.glob(input_methods_dir + '/*/ime.json', recursive=True)
        # load the ime.json file
        for file_name in ime_files:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    ime_info = json.load(f)
                    guid = ime_info['guid'].lower()
                    self.input_methods[guid] = ime_info
            except Exception as e:
                logger.exception('fail to load ime info: %s', e)
        print(self.input_methods)

    def start(self):
        if self.process:
            logger.error('backend is already started')
            return
        loop = pyuv.Loop.default_loop()
        if os.path.isabs(self.command):
            command_path = self.command
        else:
            command_path = os.path.join(top_dir, self.command)

        args = [
            command_path,
            # os.path.join(self.working_dir, self.params)
            self.params
        ]
        work_dir = self.working_dir
        if not os.path.isabs(work_dir):
            work_dir = os.path.join(top_dir, work_dir)

        logger.info('argv: %s', args)
        self.stdin = pyuv.Pipe(loop)
        self.stdout = pyuv.Pipe(loop)
        self.stderr = pyuv.Pipe(loop)
        stdio = [
            pyuv.StdIO(self.stdin, flags=pyuv.UV_CREATE_PIPE | pyuv.UV_READABLE_PIPE | pyuv.UV_WRITABLE_PIPE),
            pyuv.StdIO(self.stdout, flags=pyuv.UV_CREATE_PIPE | pyuv.UV_READABLE_PIPE | pyuv.UV_WRITABLE_PIPE),
            pyuv.StdIO(self.stderr, flags=pyuv.UV_CREATE_PIPE | pyuv.UV_READABLE_PIPE | pyuv.UV_WRITABLE_PIPE),
        ]

        process = pyuv.Process.spawn(loop=loop,
                                     args=args,
                                     executable=args[0],
                                     # force python stdio to use UTF-8 rather than system locale
                                     env={'PYTHONIOENCODING': 'utf-8:ignore'},
                                     cwd=work_dir,
                                     uid=pyuv.UV_PROCESS_SETUID,
                                     gid=pyuv.UV_PROCESS_SETUID,
                                     flags=pyuv.UV_PROCESS_WINDOWS_HIDE,
                                     stdio=stdio,
                                     exit_callback=self.on_exit)
        self.process = process
        self.stdout.start_read(self.on_stdout_data_received)
        self.stderr.start_read(self.on_stderr_data_received)

    def add_response_callback(self, callback):
        self._response_callbacks.append(callback)

    def remove_response_callback(self, callback):
        self._response_callbacks.remove(callback)

    def on_stdout_data_received(self, pipe_handle, data, error):
        """Receive data from stdout of the backend process"""
        if error:
            logger.error('backend error: %s', error)
        elif data:
            self.output_buffer += data
            start_pos = 0
            while start_pos < len(self.output_buffer):
                end_pos = self.output_buffer.find(b'\n', start_pos)
                if end_pos == -1:  # the last line is not complete, wait for more data
                    break
                line = self.output_buffer[start_pos: end_pos].strip()
                if line.startswith(b'PIME_MSG'):
                    try:
                        self.parse_backend_response_line(line)
                    except Exception as e:
                        logger.exception('fail to handle backend response: %s', e)
                start_pos = end_pos + 1
            self.output_buffer = self.output_buffer[start_pos:]

    def on_stderr_data_received(self, pipe_handle, data, error):
        if not error and data:
            logger.error('backend error: %s, %s', data, error)

    def handle_client_request(self, client_id: str, msg: dict):
        data = client_id + '|' + json.dumps(msg) + '\n'
        self.stdin.write(data.encode('utf8'))

    def parse_backend_response_line(self, line):
        line = line.decode('utf8')
        prefix, client_id, msg_text = line.split('|', 2)
        msg = json.loads(msg_text)
        self.handle_backend_response(client_id, msg)

    def handle_backend_response(self, client_id: str, msg: dict):
        logger.debug('MESSAGE: %s', msg)
        for callback in self._response_callbacks:
            callback(client_id, msg)

    def on_data_sent(self, pipe_handle, error):
        logger.debug('sent: %s', error)

    def on_exit(self, process_handle, exit_status, term_signal):
        logger.info('process exit: %s, %s, %s', process_handle, exit_status, term_signal)
        self.process = None
        if self._restarting:
            self._restarting = False
            self.start()

    def restart(self):
        if not self._restarting:
            self._restarting = True
            self.terminate()

    def terminate(self):
        try:
            if self.process:
                self.process.kill()
        finally:
            self.process = None
