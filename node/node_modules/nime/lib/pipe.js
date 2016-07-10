'use strict';

let ffi = require('ffi');
let ref = require('ref');

let charPtr = ref.refType('char');
let longPtr = ref.refType('long');

const BUFFER_LEN = 512;

function createPIPE(dllPath = `${__dirname}/libpipe.dll`) {

  let libPipe = ffi.Library(dllPath, {
    // HANDLE connect_pipe(const char* app_name)
    'connect_pipe': ['pointer', ['string']],
    // int read_pipe(HANDLE pipe, char* buf, unsigned long len, unsigned long* error)
    'read_pipe': ['int', ['pointer', charPtr, 'long', longPtr]],
    // int write_pipe(HANDLE pipe, const char* data, unsigned long len, unsigned long* error)
    'write_pipe': ['int', ['pointer', 'string', 'long', longPtr]],
    // void close_pipe(HANDLE pipe)
    'close_pipe': ['void', ['pointer']]
  });

  return {

    connect(callback) {
      libPipe.connect_pipe.async('node', callback);
    },

    read(pipe, callback) {
      let error = ref.alloc(ref.types.long);
      let buf = new Buffer(BUFFER_LEN);

      libPipe.read_pipe.async(pipe, buf, BUFFER_LEN, error, (err, len) => {
        if (err) {
          throw err;
        }

        let data = buf.toString('utf8', 0, len);
        let realError = ref.deref(error);

        callback(realError, data);
      });
    },

    write(pipe, response, callback) {

      let error = ref.alloc(ref.types.long);
      let msg = JSON.stringify(response);
      let buf = new Buffer(msg, 'utf8');
      let length = Buffer.byteLength(msg, 'utf8');

      libPipe.write_pipe.async(pipe, buf, length, error, (err, len) => {
        if (err) {
          throw err;
        }

        let realError = ref.deref(error);

        callback(realError, len);
      });
    },

    close(pipe, callback) {
      libPipe.close_pipe.async(pipe, callback);
    },
  };
}

module.exports = {
  createPIPE
};
