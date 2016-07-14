Emoji Input Method Editor
=============
The 'real' input method editor of Emoji on windows. Implement by [emojione](http://emojione.com/), [PIME](https://github.com/EasyIME/PIME), [NIME](https://github.com/EasyIME/NIME).


#### Node

- Node v4.x 32 bit (Must be 32 bit.)
- Install [node-gyp](https://github.com/nodejs/node-gyp) dependecise for c binding through [node-ffi](https://github.com/node-ffi/node-ffi). Please see [node-gyp document](https://github.com/nodejs/node-gyp#installation) to setup your environment.


#### Development

Now NIME doesn't has it own installation, so we use PIME for development `emojime`.

- Prepare Node v6.x environment.
- Install [PIME](https://github.com/EasyIME/PIME/releases) v0.14.x
- Create `emojime` folder into `C:\Program Files (x86)\PIME\server\input_methods\`
- Copy `ime.json` and `icon.ico` into `C:\Program Files (x86)\PIME\server\input_methods\emojime\`
- `regsvr32 "C:\Program Files (X86)\PIME\x86\PIMETextService.dll" (run as administrator)`
- `regsvr32 "C:\Program Files (X86)\PIME\x64\PIMETextService.dll" (run as administrator)`
- `npm i`
- `npm start`


#### Input method rule

It is following [emojione codes](http://emoji.codes/).

- `:rocket:` => 🚀
- `:heart:` => ❤️
- `:relaxed:` => ☺️


## Reference

- [PIME](https://github.com/EasyIME/PIME)
- [Virtual-Key Codes](https://msdn.microsoft.com/zh-tw/library/windows/desktop/dd375731%28v=vs.85%29.aspx)
- [NIME](https://github.com/EasyIME/NIME)
- [emojione](http://emojione.com/)


## License

The MIT License (MIT)

Copyright (c) 2016 Lee  < jessy1092@gmail.com >

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
