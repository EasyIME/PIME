'use strict';

let debug = require('debug')('nime:emojime:reducer');

let compositionMode = require('./compositionMode');
let candidateMode   = require('./candidateMode');

function reduceOnKeyDown(request, preState) {

  let {keyCode, charCode} = request;

  let {
    compositionString,
    showCandidates
  } = preState;

  // Start input
  if (compositionString === '' && charCode === ':'.charCodeAt(0)) {
    return Object.assign({}, preState, {
      action: 'UPDATE_STRING',
      compositionString: ':',
      compositionCursor: 1
    });
  }

  if (compositionString !== '') {

    if(showCandidates) {
      return candidateMode(request, preState);
    }

    if (!showCandidates) {
      return compositionMode(request, preState);
    }
  }

  return preState;
}

function reduceOnCompositionTerminated(request, preState) {
  return Object.assign({}, preState, {
    commitString: '',
    compositionString: '',
    compositionCursor: 0,
    candidateList: [],
    candidateCursor: 0
  });
}

module.exports = {
  reduceOnKeyDown,
  reduceOnCompositionTerminated
};
