'use strict';

let fs   = require('fs');
let path = require('path');


function loadServices() {
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

  return services;
}

function loadServiceById(id) {
  let imeDir = fs.readdirSync(path.join(process.cwd(), 'input_methods'));
  let service = null;

  imeDir.forEach((dir) => {

    if (fs.lstatSync(path.join(process.cwd(), 'input_methods', dir)).isDirectory()) {
      let configFile = fs.readFileSync(path.join(process.cwd(), 'input_methods', dir, 'ime.json'), 'utf8');
      let config = JSON.parse(configFile);

      if (config['guid'].toLowerCase() === id.toLowerCase()) {
        service = require(`./input_methods/${dir}/${config.moduleName}`);
      }
    }
  });

  return service;
}

module.exports = {
  loadServices,
  loadServiceById
};
