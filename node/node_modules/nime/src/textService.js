'use strict';

const NOREMAL_KEY_EVENT = [
  'filterKeyDown',
  'filterKeyUp',
  'onKeyDown',
  'onKeyUp'
];

const SPECIAL_KEY_EVENT = [
  'onPreservedKey',
  'onCommand',
  'onCompartmentChanged',
  'onKeyboardStatusChanged',
  'onCompositionTerminated'
]


module.exports = {

  textReducer(request, preState = {}) {
    return preState;
  },

  response(request, state) {
    return {success: true, seqNum: request['seqNum']};
  }
};
