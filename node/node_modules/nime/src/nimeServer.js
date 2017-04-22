'use strict';

const express    = require('express');
const bodyParser = require('body-parser');
const uuid       = require('uuid');
const debug      = require('debug')('nime:server');

const {
  initService,
  handleRequest
} = require('./requestHandler');

const {
  makeDir,
  writeFile,
  getRandomInt
} = require('./util');

const statusDir  = `${process.env.LOCALAPPDATA}/PIME/status`;
const statusFile = `${statusDir}/node.json`;

const minPort = 1025;
const maxPort = 65535;

function isAuthenticated(req, httpBasicAuth) {
  return req.get('Authentication') === httpBasicAuth;
}

function createServer(services = []) {

  const app = express();
  const accessToken = uuid.v4();
  const userPass = `PIME:${accessToken}`;
  const httpBasicAuth = `Basic ${new Buffer.from(userPass).toString('base64')}`;
  const connections = {};

  makeDir(`${process.env.LOCALAPPDATA}/PIME/status`);

  app.use(bodyParser.json({
    type: () => true
  }));

  // Initialize client return client id
  app.post('/', (req, res) => {
    debug("start");

    if (!isAuthenticated(req, httpBasicAuth)) {
      debug('Authenticate not match');
      res.send('');
    }

    const client_id = uuid.v4();

    connections[client_id] = {service: null, state: null};
    debug(`Connections: ${JSON.stringify(connections)}`);
    res.send(client_id);
  });

  // Handle client request, http url: /clientId  body: request
  app.post('*', (req, res) => {

    if (!isAuthenticated(req, httpBasicAuth)) {
      debug('Authenticate not match');
      res.send('');
      return;
    }

    const clientId = req.path.slice(1);
    const request  = req.body;

    debug(clientId);
    debug(request);

    if (!connections.hasOwnProperty(clientId)) {
      debug(`Connection not found ${clientId}`);
      res.send('');
      return;
    }

    if (request['method'] === 'init') {

      let {service, state, response} = initService(request, services);
      connections[clientId] = {service, state}
      debug(response);
      res.send(JSON.stringify(response));
      return;

    } else {

      let {state, response} = handleRequest(request, connections[clientId]);
      connections[clientId].state = state;
      debug(response);
      res.send(JSON.stringify(response));
      return;
    }
  });

  // Delete client, http url: /clientId
  app.delete('*', (req, res) => {
    if (!isAuthenticated(req, httpBasicAuth)) {
      debug('Authenticate not match');
      res.send('');
      return;
    }

    const clientId = req.path.slice(1);
    const request  = req.body;

    debug(clientId);
    debug(request);

    if (clientId === '') {
      // Exit the IME server
      process.exit();
    }

    if (!connections.hasOwnProperty(clientId)) {
      debug(`Connection not found ${clientId}`);
      res.send('');
      return;
    }

    delete connections[clientId];
    res.send('');
  })

  function listen() {

    let port = 3000;

    while (true) {
      port = getRandomInt(minPort, maxPort);
      try {
        app.listen(port, '127.0.0.1');
        debug(`Wait connection at 127.0.0.1:${port}`);
        break;
      } catch (err) {
        if (err) {
          debug(`Port has be uesd ${port}, error: ${err}`);
        }
      }
    }

    const info = {
      port,
      pid: process.pid,
      access_token: accessToken
    };

    writeFile(statusFile, JSON.stringify(info));
  }

  return {listen};
}

module.exports = {
  createServer
};
