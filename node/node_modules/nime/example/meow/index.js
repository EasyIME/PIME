'use strict';

let KEYCODE = require('../../lib/keyCodes');

const candidateList = ['喵', '描', '秒', '妙'];


function respOnFilterKeyDown(request, state) {

  let {keyCode, seqNum} = request;

  let response = {
    success: true,
    return: true,
    seqNum
  };

  if (state['compositionString'] === '' && (
      keyCode === KEYCODE.VK_RETURN || keyCode === KEYCODE.VK_BACK ||
      keyCode === KEYCODE.VK_LEFT || keyCode === KEYCODE.VK_UP ||
      keyCode === KEYCODE.VK_DOWN || keyCode === KEYCODE.VK_RIGHT)) {
    response['return'] = false;
  }

  return response;
}

function respOnKeyDown(request, state) {

  let {keyCode, seqNum} = request;

  let response = {
    success: true,
    return: true,
    seqNum
  };

  if (state['action'] === 'SHOW_CANDIDATES') {
    if (state['showCandidates']) {
      response['candidateList'] = candidateList;
    }
    response['showCandidates'] = state['showCandidates'];
    return response;
  }

  if (state['action'] === 'SELECT_CANDIDATE') {
    response['compositionString'] = state['compositionString'];
    response['showCandidates']    = state['showCandidates'];
    return response;
  }

  if (state['action'] === 'UPDATE_STRING') {
    response['compositionString'] = state['compositionString'];
    response['compositionCursor'] = state['compositionCursor'];
    return response;
  }

  if (state['action'] === 'COMMIT_STRING') {
    response['commitString']      = state['commitString'];
    response['compositionString'] = state['compositionString'];
    return response;
  }

  return response;
}

function reduceOnKeyDown(request, preState) {

  let {
    action = '',
    compositionString = '',
    compositionCursor = 0,
    showCandidates = false
  } = preState;

  let {keyCode} = request;

  if (showCandidates) {

    if (keyCode === KEYCODE.VK_UP || keyCode === KEYCODE.VK_ESCAPE) {
      return Object.assign({}, preState, {
        action: 'SHOW_CANDIDATES',
        showCandidates: false
      });

    } else if (keyCode >= '1'.charCodeAt(0) && keyCode <= '4'.charCodeAt(0)) {

      let selectCandidate = candidateList[keyCode - '1'.charCodeAt(0)];
      let cursor = compositionCursor - 1;

      if (cursor < 0) {
        cursor = 0;
      }

      compositionString = compositionString.substring(0, cursor) + selectCandidate + compositionString.substring(cursor + 1);

      return Object.assign({}, preState, {
        action: 'SELECT_CANDIDATE',
        showCandidates: false,
        compositionString
      });
    }

    return Object.assign({}, preState, {action: ''});

  } else {

    if (keyCode === KEYCODE.VK_DOWN) { // Show Candidate List
      return Object.assign({}, preState, {
        action: 'SHOW_CANDIDATES',
        showCandidates: true
      });
    }

    if (keyCode === KEYCODE.VK_RETURN) { // Comfirm String
      return Object.assign({}, preState, {
        action: 'COMMIT_STRING',
        commitString: compositionString,
        compositionString: '',
        compositionCursor: 0
      });
    }

    if (keyCode === KEYCODE.VK_BACK) { // Delete compositionString
      if (compositionString === '') {
        return Object.assign({}, preState, {action: ''});
      }
      let cursor = compositionCursor;
      compositionCursor -= 1;
      compositionString = compositionString.substring(0, compositionCursor) + compositionString.substring(cursor);

      return Object.assign({}, preState, {
        action: 'UPDATE_STRING',
        compositionString,
        compositionCursor
      });
    }

    if (keyCode === KEYCODE.VK_LEFT) { // Move cursor left
      if (compositionCursor > 0) {
        return Object.assign({}, preState, {
          action: 'UPDATE_STRING',
          compositionCursor: compositionCursor - 1
        });
      }
      return Object.assign({}, preState, {action: ''});
    }

    if (keyCode === KEYCODE.VK_RIGHT) { // Move cursor right
      if (compositionCursor < compositionString.length) {
        return Object.assign({}, preState, {
          action: 'UPDATE_STRING',
          compositionCursor: compositionCursor + 1
        });
      }
      return Object.assign({}, preState, {action: ''});
    }

    compositionString = compositionString.substring(0, compositionCursor) + '喵' + compositionString.substring(compositionCursor);

    return Object.assign({}, preState, {
      action: 'UPDATE_STRING',
      compositionCursor: compositionCursor + 1,
      compositionString
    });
  }
}

function reduceOnCompositionTerminated(request, preState) {
  return Object.assign({}, preState, {
    compositionString: '',
    compositionCursor: 0
  });
}

module.exports = {
  textReducer(request, preState) {

    if (request['method'] === 'init') {
      return Object.assign({}, preState, {
        action: '',
        compositionString: '',
        compositionCursor: 0,
        showCandidates: false
      });
    }

    if (request['method'] === 'onKeyDown') {
      return reduceOnKeyDown(request, preState);
    }

    if (request['method'] === 'onCompositionTerminated') {
      return reduceOnCompositionTerminated(request, preState);
    }
    return preState;
  },

  response(request, state) {
    if (request['method'] === 'filterKeyDown') {
      return respOnFilterKeyDown(request, state);

    } else if (request['method'] === 'onKeyDown') {
      return respOnKeyDown(request, state);
    }
    return {success: true, seqNum: request['seqNum']};
  }
};
