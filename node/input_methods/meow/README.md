喵喵輸入法
=============
This is reimplement of [PIME's 喵喵輸入法](https://github.com/EasyIME/PIME/tree/master/server/input_methods/meow) by using NIME.

The `chi.ico`, `icon.ico` and `ime.json` are copied from [PIME's 喵喵輸入法](https://github.com/EasyIME/PIME/tree/master/server/input_methods/meow). These are under LGPL 2.0 License.

NIME is under MIT License.


## Requirement

- [nodejs 6.x 32bit](https://nodejs.org/en/)
- Install [node-gyp](https://github.com/nodejs/node-gyp) dependecise for c binding through [node-ffi](https://github.com/node-ffi/node-ffi). Please see [node-gyp document](https://github.com/nodejs/node-gyp#installation) to setup your environment.


## Run

- `node index.js`


## Implement

It is the reduce-based implement. It uses the `textReducer` and `response` function to handle text and request.

```js
'use strict';

let NIME = require('nime');

// It would pass the client request and previous state that you define.
// The default state is
// { env:
//   { id: '{c5f37da0-274e-4837-9b7c-9bb79fe85d9d}',
//     isWindows8Above: false,
//     isMetroApp: false,
//     isUiLess: false,
//     isConsole: false,
//     isKeyboardOpen: true
//   }
// }
function textReducer(request, preState) {
  return preState;
}

// You can define your response information.
function response(request, state) {
  return {success: true, seqNum: request['seqNum']};
}

let server = NIME.createServer([{
  'guid': '123', // Your ime's guid, it also write in the ime.json
  'textService': {
    textReducer,
    response
  }
}]);

server.listen();
```
