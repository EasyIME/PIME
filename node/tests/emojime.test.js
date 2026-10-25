'use strict';
// Unit tests for emojime candidateMode reducer bounds checking.
// Run with: ..\node.exe tests/emojime.test.js (from node/ directory)

const { test } = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const candidateMode = require('../input_methods/emojime/src/reducer/candidateMode');
const KEYCODE = require('nime/lib/keyCodes');

test('candidateMode handles empty or null candidateList gracefully', () => {
  const preState = {
    candidateCursor: 0,
    candidateList: []
  };
  const resultDown = candidateMode({ keyCode: KEYCODE.VK_DOWN }, preState);
  assert.strictEqual(resultDown.action, '');

  const resultNull = candidateMode({ keyCode: KEYCODE.VK_DOWN }, { candidateCursor: 0, candidateList: null });
  assert.strictEqual(resultNull.action, '');
});

test('candidateMode clamps out-of-bound candidateCursor', () => {
  const preState = {
    candidateCursor: 10,
    candidateList: ['😃 :smiley:', '😄 :smile:']
  };
  // 10 is clamped to 0, then VK_DOWN (+3) % 2 => 1
  const result = candidateMode({ keyCode: KEYCODE.VK_DOWN }, preState);
  assert.strictEqual(result.candidateCursor, 1);
});

test('candidateMode selects candidate by number key safely within bounds', () => {
  const preState = {
    candidateCursor: 0,
    candidateList: ['😃 :smiley:', '😄 :smile:']
  };
  // '2' selects second candidate
  const result = candidateMode({ keyCode: '2'.charCodeAt(0) }, preState);
  assert.strictEqual(result.action, 'COMMIT_STRING');
  assert.strictEqual(result.commitString, '😄');

  // '5' is beyond candidateList length; should not commit
  const outOfBounds = candidateMode({ keyCode: '5'.charCodeAt(0) }, preState);
  assert.strictEqual(outOfBounds.action, '');
});
