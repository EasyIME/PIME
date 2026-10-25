'use strict';
// Tests for the stdin/stdout line protocol of the Node.js backend (nime).
// Run with: node --test tests/nimeServer.test.js   (from the node/ directory)
//
// This file was generated with assistance from Claude Code (Claude Fable 5.1).

const { test } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const path = require('node:path');

const NODE_DIR = path.join(__dirname, '..');
const MEOW = '{C5F37DA0-274E-4837-9B7C-9BB79FE85D9D}';
const UNKNOWN = '{00000000-0000-0000-0000-000000000000}';

// Starts server.js the way PIMELauncher does and returns a helper that sends
// one raw line and resolves with the parsed JSON of the next PIME_MSG reply.
function startBackend() {
  const child = spawn(process.execPath, ['server.js'], { cwd: NODE_DIR, stdio: ['pipe', 'pipe', 'ignore'] });
  let buf = '';
  let waiter = null;
  let exited = false;
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
  child.on('exit', () => { exited = true; if (waiter) { const w = waiter; waiter = null; w(null); } });
  return {
    sendLine: (line) => new Promise((resolve, reject) => {
      const timer = setTimeout(() => { waiter = null; reject(new Error(`no reply to: ${line}`)); }, 10000);
      waiter = (reply) => { clearTimeout(timer); resolve(reply); };
      child.stdin.write(line + '\n');
    }),
    send: function (clientId, msg) { return this.sendLine(`${clientId}|${JSON.stringify(msg)}`); },
    alive: () => !exited,
    stop: () => child.kill(),
  };
}

const initMsg = (id, seqNum) => ({ method: 'init', id, isWindows8Above: true, isMetroApp: false, isUiLess: false, isConsole: false, seqNum });

test('init and onActivate of a bundled input method succeed', async () => {
  const b = startBackend();
  try {
    assert.deepStrictEqual(await b.send('A', initMsg(MEOW, 0)), { success: true, seqNum: 0 });
    assert.deepStrictEqual(await b.send('A', { method: 'onActivate', isKeyboardOpen: true, seqNum: 1 }), { success: true, seqNum: 1 });
  } finally { b.stop(); }
});

test('a request from a client that never sent init is answered, not fatal (#937)', async () => {
  const b = startBackend();
  try {
    assert.deepStrictEqual(await b.send('A', { method: 'onActivate', isKeyboardOpen: true, seqNum: 5 }), { success: false, seqNum: 5 });
    assert.ok(b.alive());
    assert.deepStrictEqual(await b.send('B', initMsg(MEOW, 0)), { success: true, seqNum: 0 });
  } finally { b.stop(); }
});

test('a request after an init with an unknown GUID is answered, not fatal (#937)', async () => {
  const b = startBackend();
  try {
    assert.deepStrictEqual(await b.send('A', initMsg(UNKNOWN, 0)), { success: false, seqNum: 0 });
    assert.deepStrictEqual(await b.send('A', { method: 'onActivate', isKeyboardOpen: true, seqNum: 1 }), { success: false, seqNum: 1 });
    assert.ok(b.alive());
  } finally { b.stop(); }
});

test('a malformed request line is answered, not fatal (#936)', async () => {
  const b = startBackend();
  try {
    assert.deepStrictEqual(await b.sendLine('A|{not json'), { success: false });
    assert.ok(b.alive());
    assert.deepStrictEqual(await b.send('B', initMsg(MEOW, 0)), { success: true, seqNum: 0 });
  } finally { b.stop(); }
});

test('a payload containing "|" is parsed as a whole', async () => {
  const b = startBackend();
  try {
    await b.send('A', initMsg(MEOW, 0));
    const reply = await b.send('A', { method: 'onCommand', id: 'x|y', seqNum: 1 });
    assert.strictEqual(reply.seqNum, 1);
    assert.ok(b.alive());
  } finally { b.stop(); }
});
