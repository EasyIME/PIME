'use strict';

let fs   = require('fs');
let path = require('path');

function getImeBaseDir() {
  return path.join(process.cwd(), 'input_methods');
}

function parseImeConfig(dir) {
  let baseDir = getImeBaseDir();
  let dirPath = path.join(baseDir, dir);
  try {
    if (!fs.lstatSync(dirPath).isDirectory()) {
      return null;
    }
  } catch (e) {
    return null;
  }

  let configPath = path.join(dirPath, 'ime.json');
  if (!fs.existsSync(configPath)) {
    return null;
  }

  try {
    let configFile = fs.readFileSync(configPath, 'utf8');
    return JSON.parse(configFile);
  } catch (e) {
    console.warn(`[Node PIME] Failed to parse ${configPath}:`, e.message);
    return null;
  }
}

function loadServices() {
  let baseDir = getImeBaseDir();
  if (!fs.existsSync(baseDir)) {
    return [];
  }

  let imeDir;
  try {
    imeDir = fs.readdirSync(baseDir);
  } catch (e) {
    console.warn(`[Node PIME] Failed to read ${baseDir}:`, e.message);
    return [];
  }

  let services = [];
  imeDir.forEach((dir) => {
    let config = parseImeConfig(dir);
    if (!config || !config.moduleName) {
      return;
    }

    try {
      let textService = require(`./input_methods/${dir}/${config.moduleName}`);
      config['textService'] = textService;
      services.push(config);
    } catch (e) {
      console.warn(`[Node PIME] Failed to require service for ${dir}:`, e.message);
    }
  });

  return services;
}

function loadServiceById(id) {
  if (!id) {
    return null;
  }

  let baseDir = getImeBaseDir();
  if (!fs.existsSync(baseDir)) {
    return null;
  }

  let imeDir;
  try {
    imeDir = fs.readdirSync(baseDir);
  } catch (e) {
    console.warn(`[Node PIME] Failed to read ${baseDir}:`, e.message);
    return null;
  }

  let service = null;
  let targetId = id.toLowerCase();

  for (let dir of imeDir) {
    let config = parseImeConfig(dir);
    if (!config || !config.guid || !config.moduleName) {
      continue;
    }

    if (config.guid.toLowerCase() === targetId) {
      try {
        service = require(`./input_methods/${dir}/${config.moduleName}`);
        break;
      } catch (e) {
        console.warn(`[Node PIME] Failed to require service for ${dir}:`, e.message);
      }
    }
  }

  return service;
}

module.exports = {
  loadServices,
  loadServiceById
};
