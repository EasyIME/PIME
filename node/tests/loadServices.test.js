'use strict';
// Regression tests for the input method configs the backend loads at startup.
// server.js compares the guid of every loaded service with the id of every
// request, so an ime.json that has a moduleName but no guid used to throw a
// TypeError inside that comparison and leave the request unanswered.
// Run with: npm test   (from the node/ directory)
//
// Generated with AI assistance from omp (DeepSeek V4.1 Flash).

const { test } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const NODE_DIR = path.join(__dirname, '..');
const SERVER_JS = path.join(NODE_DIR, 'server.js');
const MEOW = '{C5F37DA0-274E-4837-9B7C-9BB79FE85D9D}';
const UNKNOWN = '{00000000-0000-0000-0000-000000000000}';

// server.js reads input_methods/*/ime.json from process.cwd(), while the
// service module is required relative to the node/ directory. Reusing the
// bundled directory names therefore pairs a temporary config with the already
// vendored service module, and nothing has to be written into the product tree.
function makeImeTree(configs) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pime-ime-'));
  configs.forEach(([dir, config]) => {
    const dirPath = path.join(root, 'input_methods', dir);
    fs.mkdirSync(dirPath, { recursive: true });
    fs.writeFileSync(path.join(dirPath, 'ime.json'), JSON.stringify(config));
  });
  return root;
}

// Starts server.js the way PIMELauncher does, in cwd, and returns a helper that
// sends one raw line and resolves with the parsed JSON of the next PIME_MSG reply.
function startBackend(cwd) {
  const child = spawn(process.execPath, [SERVER_JS], { cwd, stdio: ['pipe', 'pipe', 'pipe'] });
  let buf = '';
  let waiter = null;
  let exited = false;
  let stderr = '';
  child.stdout.on('data', (chunk) => {
    buf += chunk.toString('utf8');
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (line.startsWith('PIME_MSG|') && waiter) {
        const w = waiter;
        waiter = null;
        w(JSON.parse(line.slice(line.indexOf('|', 'PIME_MSG|'.length) + 1)));
      }
    }
  });
  child.stderr.on('data', (chunk) => { stderr += chunk.toString('utf8'); });
  const exit = new Promise((resolve) => {
    child.on('exit', (code) => {
      exited = true;
      resolve(code);
      if (waiter) { const w = waiter; waiter = null; w(null); }
    });
  });
  return {
    sendLine: (line) => new Promise((resolve, reject) => {
      const timer = setTimeout(() => { waiter = null; reject(new Error(`no reply to: ${line}`)); }, 10000);
      waiter = (reply) => { clearTimeout(timer); resolve(reply); };
      child.stdin.write(line + '\n');
    }),
    send: function (clientId, msg) { return this.sendLine(`${clientId}|${JSON.stringify(msg)}`); },
    alive: () => !exited,
    stderr: () => stderr,
    exit: () => exit,
    stop: () => child.kill(),
  };
}

// Resolves with the exit code, or null when the backend is still running.
function exitWithin(backend, ms) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), ms);
    backend.exit().then((code) => { clearTimeout(timer); resolve(code); });
  });
}

const initMsg = (id, seqNum) => ({ method: 'init', id, isWindows8Above: true, isMetroApp: false, isUiLess: false, isConsole: false, seqNum });

test('an ime.json without guid does not break a sibling service', async () => {
  const root = makeImeTree([
    ['emojime', { name: 'no-guid', moduleName: 'index' }],
    ['meow', { name: '喵喵輸入法', guid: MEOW, moduleName: 'index' }],
  ]);
  const b = startBackend(root);
  try {
    // The guid-less config used to throw here, before any reply was written.
    assert.deepStrictEqual(await b.send('A', initMsg(MEOW, 0)), { success: true, seqNum: 0 });
    assert.ok(b.alive());
    // An unknown id and a request without an id are answered, not fatal.
    assert.deepStrictEqual(await b.send('B', initMsg(UNKNOWN, 1)), { success: false, seqNum: 1 });
    assert.deepStrictEqual(await b.send('C', { method: 'init', seqNum: 2 }), { success: false, seqNum: 2 });
    assert.ok(!b.stderr().includes('uncaught exception'), b.stderr());
    assert.ok(b.alive());
  } finally {
    b.stop();
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('a tree where no config has a guid exits at startup', async () => {
  const root = makeImeTree([['emojime', { name: 'no-guid', moduleName: 'index' }]]);
  const b = startBackend(root);
  try {
    assert.strictEqual(await exitWithin(b, 5000), 1, 'no usable service left, so server.js must report it');
  } finally {
    b.stop();
    fs.rmSync(root, { recursive: true, force: true });
  }
});
