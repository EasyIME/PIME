
'use strict';

const fs = require('fs');
const path = require('path');

const distPath = path.join(__dirname, 'dist', 'index.js');
if (fs.existsSync(distPath)) {
  module.exports = require(distPath);
} else {
  module.exports = require('./src');
}
