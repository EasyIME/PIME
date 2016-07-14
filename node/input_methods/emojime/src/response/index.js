
'use strict';

function respOnFilterKeyDown(request, state) {

  let {charCode, seqNum} = request;
  let {compositionString} = state;

  let response = {
    return: false,
    success: true,
    seqNum
  };

  if (compositionString !== '' || charCode === ':'.charCodeAt(0)) {
    response['return'] = true;
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
      response['candidateList'] = state['candidateList'];
    }
    response['showCandidates'] = state['showCandidates'];
    return response;
  }

  if (state['action'] === 'UPDATE_CANDIDATE') {
    response['candidateCursor'] = state['candidateCursor'];
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
    response['showCandidates']    = state['showCandidates'];
    response['commitString']      = state['commitString'];
    response['compositionString'] = state['compositionString'];
    return response;
  }

  return response;
}

module.exports = {
  respOnKeyDown,
  respOnFilterKeyDown
};
