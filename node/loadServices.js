'use strict';

let fs   = require('fs');
let path = require('path');

function getImeBaseDir() {
  return path.join(process.cwd(), 'input_methods');
}

// Lists the language profile manifests of an input method module:
// ime.json, followed by ime_profiles/*/ime.json. The files may not exist.
function imeJsonPaths(dir) {
  let dirPath = path.join(getImeBaseDir(), dir);
  let paths = [path.join(dirPath, 'ime.json')];
  let profilesDir = path.join(dirPath, 'ime_profiles');
  try {
    fs.readdirSync(profilesDir).sort().forEach((profile) => {
      paths.push(path.join(profilesDir, profile, 'ime.json'));
    });
  } catch (e) {
    // no ime_profiles dir
  }
  return paths;
}

function parseImeConfig(configPath) {
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

// Returns [dir, config] pairs of all language profiles. The first manifest of a guid wins.
function loadImeConfigs() {
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

  let configs = [];
  let guids = new Set();
  imeDir.forEach((dir) => {
    imeJsonPaths(dir).forEach((configPath) => {
      let config = parseImeConfig(configPath);
      // A request id is matched against guid, so a config without one can never
      // be selected; skip it instead of loading a module nothing can reach.
      if (!config || !config.guid || !config.moduleName) {
        return;
      }
      let guid = String(config.guid).toLowerCase();
      if (guids.has(guid)) {
        console.warn(`[Node PIME] Duplicate guid ${guid} in ${configPath} ignored`);
        return;
      }
      guids.add(guid);
      configs.push([dir, config]);
    });
  });
  return configs;
}

function loadServices() {
  let services = [];
  loadImeConfigs().forEach(([dir, config]) => {
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

  let service = null;
  let targetId = String(id).toLowerCase();

  for (let [dir, config] of loadImeConfigs()) {
    if (!config.guid) {
      continue;
    }

    if (String(config.guid).toLowerCase() === targetId) {
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
