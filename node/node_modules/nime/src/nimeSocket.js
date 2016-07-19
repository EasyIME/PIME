'use strict';

let debugGenerator = require('debug');

const SUCCESS          = 0;
const ERROR_MORE_DATA  = 234;
const ERROR_IO_PENDING = 997;

const NO_ACTION    = 0;
const NEXT_READ    = 1;
const NEXT_WRITE   = 2;
const CLOSE_SOCKET = 3;


function createSocket(ref, pipe, {services, id}, callback) {

  let readData = '';
  let message  = {};
  let service  = null;
  let open     = false;
  let state    = {'env': {}};
  let debug    = debugGenerator(`nime:socket:${id}`);

  function _handleRequest(request) {
    let response = {success: false, seqNum: request['seqNum']};

    if (request['method'] === 'init') {

      if (typeof services === 'function') {
        // Let user handle services
        service = services(request);
        if (service) {
          open = true;
        }
      } else {
        // Search the service
        services.forEach((tmpService) => {
          if (tmpService['guid'].toLowerCase() === request['id'].toLowerCase()) {
            service = tmpService['textService'];
            open    = true;
          }
        });
      }


      // Store environment
      state.env['id']              = request['id'];
      state.env['isWindows8Above'] = request['isWindows8Above'];
      state.env['isMetroApp']      = request['isMetroApp'];
      state.env['isUiLess']        = request['isUiLess'];
      state.env['isConsole']       = request['isConsole'];

    } else if (request['method'] === 'onActivate' && open === true) {
      state.env['isKeyboardOpen'] = request['isKeyboardOpen'];
    }

    if (service !== null && open === true) {
      // Use the text reducer to change state
      state    = service.textReducer(request, state);
      // Handle response
      response = service.response(request, state);
    } else {
      state    = {};
      response = {success: false, seqNum: request['seqNum']};
    }
    return [NEXT_WRITE, response];
  }

  function _handleMessage(msg) {

    // For client, check server exist or not.
    if (msg === 'ping') {
      return [NEXT_WRITE, 'pong'];
    }

    // For client, quit the server.
    if (msg === 'quit') {
      return [CLOSE_SOCKET, ''];
    }

    // Handle the normal message
    return _handleRequest(msg);
  };

  function _handleData(err, data) {

    if (err === SUCCESS) {
      readData += data;

      debug('Get Data: ' + readData);
      try {
        message = JSON.parse(readData);
      } catch (e) {
        message = readData;
      }

      readData = "";

      return _handleMessage(message);
    }

    if (err === ERROR_MORE_DATA) {
      readData += data;
      return [NEXT_READ, ''];
    }

    if (err === ERROR_IO_PENDING) {
      return [NEXT_READ, ''];
    }

    debug('Socket broken');
    return [CLOSE_SOCKET, ''];
  }

  function read() {

    pipe.read(ref, (err, data) => {

      let [result, response] = _handleData(err, data);

      if (result === NEXT_READ) {
        read();
      } else if(result === CLOSE_SOCKET){
        close();
      } else if (result === NEXT_WRITE) {
        write(response);
      }
    });
  }

  function write(response) {

    let data = '';

    try {
      data = JSON.stringify(response);
    } catch (e) {
      data = response;
    }

    pipe.write(ref, data, (err, len) => {

      if (err) {
        debug('Write Failed');
        close();
      }

      debug(`Write Len: ${len} Data: ${data}`);
      read();
    });
  }

  function close() {
    pipe.close(ref, (err) => {
      callback({
        type: 'SOCKET_CLOSE',
        id
      });
    });
  }

  return {
    read,
    write,
    close,
    _handleData
  };
}

module.exports = {
  createSocket
};
