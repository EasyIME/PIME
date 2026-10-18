'use strict';

let debug = require('debug')('nime:server');
let NIME  = require('nime');

let {loadServices, loadServiceById} = require('./loadServices');

let services = loadServices();

if (services.length == 0) {
  debug('Text services not found');
  process.exit(1);
}

// Stands in when a GUID resolves to no service, e.g. an init naming a service
// that is not registered or whose module failed to load. nime dereferences the
// service on the next request, so returning null here kills the backend
// (EasyIME/PIME#937). Reply with {success: false, seqNum} for every method
// instead, the same payload shape python/server.py sends for a missing service.
// Note: a request from a client that never sent init is still handled inside
// nime and remains unprotected; the TSF client always sends init first.
const NULL_SERVICE = {
  textReducer(request, state) {
    return state;
  },
  response(request) {
    return {success: false, seqNum: request['seqNum']};
  }
};

function resolveService(request) {
  let id = (request['id'] || '').toLowerCase();
  let service = null;

  services.forEach((tmpService) => {
    if (tmpService['guid'].toLowerCase() === id) {
      service = tmpService['textService'];
    }
  });

  if (service == null && id !== '') {
    debug('Try to dynamic load service:', id);
    // Dynamic load service without exit nodejs
    service = loadServiceById(id);
  }

  if (service == null) {
    debug('No service for id:', id);
  }

  return service || NULL_SERVICE;
}

let server = NIME.createServer(resolveService);

server.listen();
