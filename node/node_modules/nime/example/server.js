'use strict';

let fs   = require('fs');
let path = require('path');

let NIME = require('../index');

let imeDir = fs.readdirSync(process.cwd());
let services = [];

imeDir.forEach((dir) => {

  if (fs.lstatSync(path.join(process.cwd(), dir)).isDirectory()) {
    let configFile = fs.readFileSync(path.join(process.cwd(), dir, 'ime.json'), 'utf8');
    let config = JSON.parse(configFile);
    let textService = require(`./${dir}/${config.moduleName}`);

    config['textService'] = textService;

    services.push(config);
  }
});

let server = NIME.createServer('../lib/libpipe.dll', services);

server.listen();
