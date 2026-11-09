'use strict';

let fs   = require('fs');
let path = require('path');

// `baseDir` defaults to the process working directory, which is what the
// backend uses at runtime. Tests pass a fixture directory instead.
function getImeBaseDir(baseDir) {
  return path.join(baseDir || process.cwd(), 'input_methods');
}

function parseImeConfig(dir, baseDir) {
  let imeDir = getImeBaseDir(baseDir);
  let dirPath = path.join(imeDir, dir);
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

function loadServices(baseDir) {
  let imeDir = getImeBaseDir(baseDir);
  if (!fs.existsSync(imeDir)) {
    return [];
  }

  let entries;
  try {
    entries = fs.readdirSync(imeDir);
  } catch (e) {
    console.warn(`[Node PIME] Failed to read ${imeDir}:`, e.message);
    return [];
  }

  let services = [];
  entries.forEach((dir) => {
    let config = parseImeConfig(dir, baseDir);
    if (!config || !config.moduleName) {
      return;
    }

    try {
      let textService = require(path.join(imeDir, dir, config.moduleName));
      config['textService'] = textService;
      services.push(config);
    } catch (e) {
      console.warn(`[Node PIME] Failed to require service for ${dir}:`, e.message);
    }
  });

  return services;
}

function loadServiceById(id, baseDir) {
  if (!id) {
    return null;
  }

  let imeDir = getImeBaseDir(baseDir);
  if (!fs.existsSync(imeDir)) {
    return null;
  }

  let entries;
  try {
    entries = fs.readdirSync(imeDir);
  } catch (e) {
    console.warn(`[Node PIME] Failed to read ${imeDir}:`, e.message);
    return null;
  }

  let service = null;
  let targetId = id.toLowerCase();

  for (let dir of entries) {
    let config = parseImeConfig(dir, baseDir);
    if (!config || !config.guid || !config.moduleName) {
      continue;
    }

    let matches = String(config.guid).toLowerCase() === targetId;
    // 同一個 service 也可由額外語言檔（additionalProfiles）的 GUID 啟動。
    if (!matches && Array.isArray(config.additionalProfiles)) {
      matches = config.additionalProfiles.some(
        (profile) => profile && typeof profile.guid === 'string' &&
          profile.guid.toLowerCase() === targetId);
    }
    if (matches) {
      try {
        service = require(path.join(imeDir, dir, config.moduleName));
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
