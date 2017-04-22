'use strict';

const debug = require('debug')('nime:server');
const stdio = require('stdio');

const {
  initService,
  handleRequest
} = require('./requestHandler');

function createServer(services = []) {

  const connections = {};

  // handle client requests
  function handleClientRequest(clientId, request) {

    debug(clientId);
    debug(request);

    if (!connections.hasOwnProperty(clientId)) {
      debug(`Connection not found ${clientId}`);
      return {};
    }

    if (request['method'] === 'init') {

      let {service, state, response} = initService(request, services);
      connections[clientId] = {service, state}
      debug(response);
      return response;

    } else {

      let {state, response} = handleRequest(request, connections[clientId]);
      connections[clientId].state = state;
      debug(response);
      return response;
    }

    return {};
  }

  // Delete client, http url: /clientId
  function removeClient(clientId) {

    debug(clientId);

    if (clientId === '') {
      // Exit the IME server
      process.exit();
    }

    if (!connections.hasOwnProperty(clientId)) {
      debug(`Connection not found ${clientId}`);
      return;
    }

    delete connections[clientId];
  };

  function listen() {

    stdio.readByLines(function lineHandler(line) {
      line = line.trim();
      const parts = line.split('|', 2);

      if (parts.length == 2) {
        const clientId = parts[0];
        const msgText = parts[1];
        const msg = JSON.parse(msgText);
        let client;

        if (!connections.hasOwnProperty(clientId)) {
          client = {service: null, state: null};
          connections[clientId] = client;
          debug("new client", clientId);
        }

        if (msg['method'] === "close") { // special handling for closing a client
          removeClient(clientId);
          debug("client disconnected:", clientId + "\n");
        } else {
          const ret = handleClientRequest(clientId, msg)
          // Send the response to the client via stdout
          // one response per line in the format "PIME_MSG|<client_id>|<json reply>"
          const reply_line = "PIME_MSG|" + clientId + "|" + JSON.stringify(ret) + "\n";
          process.stdout.write(reply_line);
        }
      }
    }, function (err) {
        console.log('Finished');
    });
  }
  return {listen};
}

module.exports = {
  createServer
};
