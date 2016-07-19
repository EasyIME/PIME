'use strict';

let pipeGen     = require('../lib/pipe');
let nimeSocket  = require('./nimeSocket');
let textService = require('./textService');
let debug       = require('debug')('nime:server');


function createServer(dllPath, services = [{guid: '123', textService}]) {

  let connections = [];
  let id = 0;
  let pipe = pipeGen.createPIPE(dllPath);

  function addConnection(socketInfo) {
    connections.push(socketInfo);
  }

  function deleteConnection(delID) {
    connections = connections.filter(({id}) => id !== delID);
  }

  function handleSocket(message) {
    if (message['type'] === 'SOCKET_CLOSE') {
      deleteConnection(message['id']);
    }
  }

  function listen() {
    debug('Wait connection');

    pipe.connect((err, ref) => {
      debug('Connected');

      // Each connection create a socket to handle.
      let socket = nimeSocket.createSocket(ref, pipe, {services, id}, handleSocket);

      addConnection({id, socket});
      id += 1;

      // Start read data
      socket.read();

      // Keep listen
      listen();
    });
  }

  return {addConnection, deleteConnection, listen};
}


module.exports = {
  createServer
};
