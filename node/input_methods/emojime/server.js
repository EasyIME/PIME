'use strict';

let nime = require('nime');
let fs   = require('fs');
let path = require('path');

let service = require('./index');

let configFile = fs.readFileSync(path.join(process.cwd(), 'ime.json'), 'utf8');
let config = JSON.parse(configFile);

config['textService'] = service;

let server = nime.createServer(undefined, [config]);

server.listen();
