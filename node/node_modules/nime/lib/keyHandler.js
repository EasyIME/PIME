'use strict';

function createKeyHandler(msg) {

  let {
    charCode, keyCode, repeatCount, scanCode, isExtended, keyStates
  } = msg;

  function isKeyDown(code) {
    return keyStates ? (keyStates[code] & 0x80) !== 0 : false;
  }

  function isKeyToggled(code) {
    return keyStates ? (keyStates[code] & 1) !== 0 : false;
  }

  function isChar() {
    return charCode ? (charCode !== 0) : false;
  }

  return {isKeyDown, isKeyToggled, isChar};
}

module.exports = {
  createKeyHandler
};
