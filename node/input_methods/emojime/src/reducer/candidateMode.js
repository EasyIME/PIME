'use strict';

let debug    = require('debug')('nime:emojime:composition');
let KEYCODE  = require('nime/lib/keyCodes');

function candidateMode(request, preState) {

  let {keyCode} = request;

  let {
    candidateCursor,
    candidateList
  } = preState;

  if (!candidateList || candidateList.length === 0) {
    return Object.assign({}, preState, {action: ''});
  }
  if (candidateCursor >= candidateList.length || candidateCursor < 0) {
    candidateCursor = 0;
  }

  // Close candidate
  if (keyCode === KEYCODE.VK_ESCAPE) {
    return Object.assign({}, preState, {
      action: 'SHOW_CANDIDATES',
      showCandidates: false,
      candidateList: [],
      candidateCursor: 0
    });
  }

  if (keyCode === KEYCODE.VK_DOWN) {
    candidateCursor = (candidateCursor + 3) % candidateList.length;
    return Object.assign({}, preState, {
      action: 'UPDATE_CANDIDATE',
      candidateCursor
    });
  }

  if (keyCode === KEYCODE.VK_UP) {
    candidateCursor = candidateCursor < 3 ? 0 : candidateCursor - 3;
    return Object.assign({}, preState, {
      action: 'UPDATE_CANDIDATE',
      candidateCursor
    });
  }

  if (keyCode === KEYCODE.VK_RIGHT) {
    candidateCursor = (candidateCursor + 1) % candidateList.length;
    return Object.assign({}, preState, {
      action: 'UPDATE_CANDIDATE',
      candidateCursor
    });
  }

  if (keyCode === KEYCODE.VK_LEFT) {
    candidateCursor = candidateCursor == 0 ? 0 : candidateCursor - 1;
    return Object.assign({}, preState, {
      action: 'UPDATE_CANDIDATE',
      candidateCursor
    });
  }

  if (keyCode >= '1'.charCodeAt(0) && keyCode <= '9'.charCodeAt(0)) {
    let index = keyCode - '1'.charCodeAt(0);
    if (index < candidateList.length) {
      let selectCandidate = candidateList[index];

      return Object.assign({}, preState, {
        action: 'COMMIT_STRING',
        showCandidates: false,
        compositionString: '',
        commitString: selectCandidate.split(' ')[0]
      });
    }
  }

  if (keyCode === KEYCODE.VK_RETURN) {

    let selectCandidate = candidateList[candidateCursor];

    return Object.assign({}, preState, {
      action: 'COMMIT_STRING',
      showCandidates: false,
      compositionString: '',
      commitString: selectCandidate.split(' ')[0]
    });
  }

  return Object.assign({}, preState, {action: ''});
}

module.exports = candidateMode;
