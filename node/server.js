'use strict';

let fs    = require('fs');
let path  = require('path');
let debug = require('debug')('nime:server');

let NIME = require('nime');

let imeDir = fs.readdirSync(path.join(process.cwd(), 'input_methods'));
let services = [];

imeDir.forEach((dir) => {

  if (fs.lstatSync(path.join(process.cwd(), 'input_methods', dir)).isDirectory()) {
    let configFile = fs.readFileSync(path.join(process.cwd(), 'input_methods', dir, 'ime.json'), 'utf8');
    let config = JSON.parse(configFile);
    let textService = require(`./input_methods/${dir}/${config.moduleName}`);

    config['textService'] = textService;

    services.push(config);
  }
});

if (services.length == 0) {
  debug('Text services not found');
  process.exit(1);
}

let server = NIME.createServer('../libpipe.dll', services);

server.listen();
