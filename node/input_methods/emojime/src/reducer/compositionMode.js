'use strict';

let emojione = require('emojione');
let debug    = require('debug')('nime:emojime:composition');
let KEYCODE  = require('nime/lib/keyCodes');

function compositionMode(request, preState) {

  let {keyCode, charCode} = request;

  let {
    compositionString,
    compositionCursor,
    showCandidates
  } = preState;

  // Show candidate list
  if (keyCode === KEYCODE.VK_DOWN) {

    // Must larger ':'.length
    if (compositionString.length > 1) {

      let candidateList = [];

      emojione.mapEmojioneList((unicode, shortname) => {
        if (shortname.indexOf(compositionString.slice(1)) >= 0 && candidateList.length < 9) {
          candidateList.push(`${emojione.convert(unicode)} ${shortname}`);
        }
      });

      if (candidateList.length > 0) {
        return Object.assign({}, preState, {
          action: 'SHOW_CANDIDATES',
          showCandidates: true,
          candidateList
        });
      }
    }
  }

  // Move cursor left
  if (keyCode === KEYCODE.VK_LEFT) {
    if (compositionCursor > 0) {
      return Object.assign({}, preState, {
        action: 'UPDATE_STRING',
        compositionCursor: compositionCursor - 1
      });
    }
    return Object.assign({}, preState, {action: ''});
  }

  // Move cursor right
  if (keyCode === KEYCODE.VK_RIGHT) {
    if (compositionCursor < compositionString.length) {
      return Object.assign({}, preState, {
        action: 'UPDATE_STRING',
        compositionCursor: compositionCursor + 1
      });
    }
    return Object.assign({}, preState, {action: ''});
  }

  // Exist composition mode
  if (keyCode === KEYCODE.VK_ESCAPE) {
    return Object.assign({}, preState, {
      action: 'UPDATE_STRING',
      compositionString: '',
      compositionCursor: 0
    });
  }

  // Delete compositionString
  if (keyCode === KEYCODE.VK_BACK) {
    if (compositionString === '') {
      return Object.assign({}, preState, {action: ''});
    }
    let cursor = compositionCursor;
    compositionCursor -= 1;
    compositionString = compositionString.slice(0, compositionCursor) + compositionString.slice(cursor);

    return Object.assign({}, preState, {
      action: 'UPDATE_STRING',
      compositionString,
      compositionCursor
    });
  }

  if (charCode === ':'.charCodeAt(0)) {
    let emojikey = compositionString + ':';

    debug('Get emoji short name');
    debug(emojikey);
    debug(emojione.shortnameToUnicode(emojikey));
    return Object.assign({}, preState, {
      action: 'COMMIT_STRING',
      commitString: emojione.shortnameToUnicode(emojikey),
      compositionString: '',
      compositionCursor: 0
    });

  }

  if (
    (charCode >= 'a'.charCodeAt(0) && charCode <= 'z'.charCodeAt(0)) ||
    (charCode >= 'A'.charCodeAt(0) && charCode <= 'Z'.charCodeAt(0))) {

    return Object.assign({}, preState, {
      action: 'UPDATE_STRING',
      compositionString: compositionString + String.fromCharCode(charCode),
      compositionCursor: compositionCursor + 1
    });
  }

  return preState;
}

module.exports = compositionMode;
