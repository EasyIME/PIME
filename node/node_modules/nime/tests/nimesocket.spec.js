'use strict';

let textService = require('../src/textService');
let nimeSocket  = require('../src/nimeSocket');
let sinon       = require('sinon');

const FAKE_REF = 0;

const SUCCESS          = 0;
const ERROR_MORE_DATA  = 234;
const ERROR_IO_PENDING = 997;

const NO_ACTION    = 0;
const NEXT_READ    = 1;
const CLOSE_SOCKET = 2;

describe('Socket', () => {

  describe('#initialize', () => {

    let fakePipe;
    let fakeServer;
    let fakeService;

    beforeEach(() => {
      fakePipe = {
        connect: sinon.spy(),
        read: sinon.spy(),
        write: sinon.spy(),
        close: sinon.spy()
      };
      fakeServer = {
        deleteConnection: sinon.spy()
      };
      fakeService = {
        guid: '123',
        textService: {
          textReducer: textService.textReducer,
          response: sinon.spy()
        }
      };
    });

    it('should response pong when request ping', () => {

      let socket = nimeSocket.createSocket(FAKE_REF, fakePipe, fakeServer, textService, 0);
      let fakeData = "ping";

      socket.write = sinon.spy();

      socket._handleData(SUCCESS, fakeData);

      assert.equal('pong', socket.write.getCall(0).args[0]);
    });

    it('should close when request quit', () => {

      let socket = nimeSocket.createSocket(FAKE_REF, fakePipe, fakeServer, textService, 0);
      let fakeData = "quit";

      let result = socket._handleData(SUCCESS, fakeData);

      assert.equal(CLOSE_SOCKET, result);
    });

    it('should initialize state env when request init', () => {
      let socket = nimeSocket.createSocket(FAKE_REF, fakePipe, fakeServer, [fakeService], 0);
      let fakeData = '{"id":"123","isConsole":false,"isMetroApp":false,"isUiLess":false,"isWindows8Above":false,"method":"init","seqNum":233}';

      socket.write = sinon.spy();

      socket._handleData(SUCCESS, fakeData);

      let testRequest = {
        id: '123',
        isConsole: false,
        isMetroApp: false,
        isUiLess: false,
        isWindows8Above: false,
        method: 'init',
        seqNum: 233
      };

      let testState = {
        env: {
          id: '123',
          isWindows8Above: false,
          isMetroApp: false,
          isUiLess: false,
          isConsole: false
        }
      };

      assert.deepEqual(testRequest, fakeService.textService.response.getCall(0).args[0]);
      assert.deepEqual(testState, fakeService.textService.response.getCall(0).args[1]);
    });

    it('should onActivate state env when request onActivate after init', () => {
      let socket = nimeSocket.createSocket(FAKE_REF, fakePipe, fakeServer, [fakeService], 0);
      let fakeData = '{"id":"123","isConsole":false,"isMetroApp":false,"isUiLess":false,"isWindows8Above":false,"method":"init","seqNum":233}';
      let fakeData2 = '{"isKeyboardOpen":true,"method":"onActivate","seqNum":0}';

      socket.write = sinon.spy();

      socket._handleData(SUCCESS, fakeData);
      socket._handleData(SUCCESS, fakeData2);

      let testRequest = {
        isKeyboardOpen: true,
        method: 'onActivate',
        seqNum: 0
      };

      let testState = {
        env: {
          id: '123',
          isWindows8Above: false,
          isMetroApp: false,
          isUiLess: false,
          isKeyboardOpen: true,
          isConsole: false
        }
      };

      assert.deepEqual(testRequest, fakeService.textService.response.getCall(1).args[0]);
      assert.deepEqual(testState, fakeService.textService.response.getCall(1).args[1]);
    });

    it('should write failed when not find the text service', () => {
      let socket = nimeSocket.createSocket(FAKE_REF, fakePipe, fakeServer, [fakeService], 0);
      let fakeData = '{"id":"321","isConsole":false,"isMetroApp":false,"isUiLess":false,"isWindows8Above":false,"method":"init","seqNum":233}';

      socket.write = sinon.spy();

      socket._handleData(SUCCESS, fakeData);

      let testResponse = {
        success: false, seqNum: 233
      };

      assert.deepEqual(testResponse, socket.write.getCall(0).args[0]);
    });
  });
});
