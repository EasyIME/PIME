'use strict';

let debug = require('debug')('nime:server');
let NIME  = require('nime');

let {loadServices, loadServiceById} = require('./loadServices');

process.on('uncaughtException', (err) => {
  debug('Uncaught exception in Node.js backend:', err);
  console.error('ERROR: uncaught exception in Node.js backend:', err);
});

let services = loadServices();

if (services.length == 0) {
  debug('Text services not found');
  process.exit(1);
}

let server = NIME.createServer((request) => {

  let service = null;

  services.forEach((tmpService) => {
    if (tmpService['guid'].toLowerCase() === request['id'].toLowerCase()) {
      service = tmpService['textService'];
    }
  });

  if (service == null) {
    debug('Try to dynamic load service:', request['id']);
    // Dynamic load service without exit nodejs
    service = loadServiceById(request['id']);
  }

  if (service == null) {
    // Return fallback dummy service to prevent null pointer dereference in nime requestHandler
    return {
      textReducer: (req, state) => state || { env: {} },
      response: (req, state) => ({ success: false, seqNum: req['seqNum'] })
    };
  }

  return service;
});

server.listen();
