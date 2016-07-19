'use strict';

let debug = require('debug')('nime:server');
let NIME  = require('nime');

let {loadServices, loadServiceById} = require('./loadServices');

debug(`Thread pool: ${process.env.UV_THREADPOOL_SIZE} can service ${process.env.UV_THREADPOOL_SIZE - 1} clients`);

let services = loadServices();

if (services.length == 0) {
  debug('Text services not found');
  process.exit(1);
}

let server = NIME.createServer('../libpipe.dll', (request) => {

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

  return service;
});

server.listen();
