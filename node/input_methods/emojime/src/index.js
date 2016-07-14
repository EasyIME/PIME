
'use strict';

let emojione = require('emojione');
let debug    = require('debug')('nime:emojime');

let {
  reduceOnKeyDown,
  reduceOnCompositionTerminated
} = require('./reducer');

let {
  respOnKeyDown,
  respOnFilterKeyDown
} = require('./response');


module.exports = {
  textReducer(request, preState) {

    if (request['method'] === 'init') {
      return Object.assign({}, preState, {
        action: '',
        compositionString: '',
        compositionCursor: 0,
        showCandidates: false,
        candidateList: [],
        candidateCursor: 0
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
}
