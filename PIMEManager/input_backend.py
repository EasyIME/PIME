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

        self.response_callbacks = []

    def init_input_methods(self):
        """Find all ime.json definition files for input method modules"""
        input_methods_dir = os.path.join(top_dir, self.name, 'input_methods')
        ime_files = glob.glob(input_methods_dir + '/*/ime.json', recursive=True)
        # load the ime.json file
        for file_name in ime_files:
            with open(file_name, 'r', encoding='utf-8') as f:
                ime_info = json.load(f)
                guid = ime_info['guid']
                self.input_methods[guid] = ime_info
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
            # self.params
            os.path.join(cur_dir, 'test.py')
        ]
        work_dir = top_dir
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
                                     env={},
                                     cwd=work_dir,
                                     uid=pyuv.UV_PROCESS_SETUID,
                                     gid=pyuv.UV_PROCESS_SETUID,
                                     flags=pyuv.UV_PROCESS_WINDOWS_HIDE,
                                     stdio=stdio,
                                     exit_callback=self.on_exit)
        self.process = process
        self.stdout.start_read(self.on_stdout_data_received)
        self.stderr.start_read(self.on_stderr_data_received)
        logger.debug('%s, %s', self.stdout, process.pid)
        self.stdin.write(b'xxxxx\n', self.on_data_sent)
        self.stdin.write(b'xxxxx2\n', self.on_data_sent)

    def add_response_callback(self, callback):
        self.response_callbacks.append(callback)

    def remove_response_callback(self, callback):
        self.response_callbacks.remove(callback)

    def on_stdout_data_received(self, pipe_handle, data, error):
        """Receive data from stdout of the backend process"""
        if error:
            logger.error('backend error: %s', error)
        elif data:
            self.output_buffer += data
            start_pos = 0
            while start_pos < len(self.output_buffer):
                end_pos = self.output_buffer.find(b'\n', start_pos)
                if end_pos == -1:  # the last line is not complete
                    break
                line = self.output_buffer[start_pos: end_pos].strip()
                try:
                    msg = json.loads(line)
                    self.handle_backend_response(msg)
                except Exception as e:
                    logger.exception('fail to handle backend response')
                start_pos = end_pos + 1
            self.output_buffer = self.output_buffer[start_pos:]

    def on_stderr_data_received(self, pipe_handle, data, error):
        if not error and data:
            logger.error('backend error: %s, %s', data, error)

    def handle_client_request(self, msg: dict):
        data = json.dumps(msg)
        self.stdin.write(data.encode('utf8'))

    def handle_backend_response(self, msg: dict):
        logger.info('MESSAGE: %s', msg)
        for callback in self.response_callbacks:
            callback(msg)

    def on_data_sent(self, pipe_handle, error):
        logger.debug('sent: %s', error)

    def on_exit(self, process_handle, exit_status, term_signal):
        logger.info('process exit: %s, %s, %s', process_handle, exit_status, term_signal)
        self.process = None

    def restart(self):
        self.terminate()
        self.start()

    def terminate(self):
        try:
            if self.process:
                self.process.kill()
        finally:
            self.process = None
