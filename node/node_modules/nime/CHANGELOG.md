<a name="0.4.1"></a>
## [0.4.1](https://github.com/jessy1092/NIME/compare/v0.4.0...v0.4.1) (2016-11-21)


### Bug Fixes

* Prevent publish the unnecessary package([85ca918](https://github.com/jessy1092/NIME/commit/85ca918))



<a name="0.4.0"></a>
# [0.4.0](https://github.com/jessy1092/NIME/compare/v0.3.0...v0.4.0) (2016-11-20)


### Features

* Modify createServer api, there no need dllPath([4524c59](https://github.com/jessy1092/NIME/commit/4524c59))
* Support delete the client id when client terminate connection(http delete)([5db699d](https://github.com/jessy1092/NIME/commit/5db699d))
* Support random port([b57a0c9](https://github.com/jessy1092/NIME/commit/b57a0c9))
* Support the IME http server, the new IPC architecture([3ce13f7](https://github.com/jessy1092/NIME/commit/3ce13f7))



<a name="0.3.0"></a>
# [0.3.0](https://github.com/jessy1092/NIME/compare/v0.2.1...v0.3.0) (2016-07-19)


### Bug Fixes

* Increase `UV_THREADPOOL_SIZE`=32 to service more client([5eb09dd](https://github.com/jessy1092/NIME/commit/5eb09dd))


### Features

* Let user can customize search services method([28c64e4](https://github.com/jessy1092/NIME/commit/28c64e4))



<a name="0.2.1"></a>
## [0.2.1](https://github.com/jessy1092/NIME/compare/v0.2.0...v0.2.1) (2016-07-12)


### Bug Fixes

* **pipe:** pipe.write response parameter should be string([493e1e3](https://github.com/jessy1092/NIME/commit/493e1e3))



<a name="0.2.0"></a>
# [0.2.0](https://github.com/jessy1092/NIME/compare/v0.1.0...v0.2.0) (2016-07-09)


### Features

* Setup mocha, chai, sinon library for testing([ed6fd08](https://github.com/jessy1092/NIME/commit/ed6fd08))
* **libpipe:** Update libpipe to 0.13.1([900cf19](https://github.com/jessy1092/NIME/commit/900cf19))
* **LOG:** Customize logger([a0119f2](https://github.com/jessy1092/NIME/commit/a0119f2))
* **nime:** Support Node server([7c3ad4d](https://github.com/jessy1092/NIME/commit/7c3ad4d))
* Use nodejs v6 for development. close #3([3e5a05c](https://github.com/jessy1092/NIME/commit/3e5a05c)), closes [#3](https://github.com/jessy1092/NIME/issues/3)
* **pipe:** Can specific libpipe.dll path([203b327](https://github.com/jessy1092/NIME/commit/203b327))
* **textService:** Export textService for define own textService([9326e9d](https://github.com/jessy1092/NIME/commit/9326e9d))



<a name="0.1.0"></a>
# 0.1.0 (2016-02-18)


### Bug Fixes

* **event:** let service not open when guid not match 97143d3
* **pipe:** Convert js object to JSON format 94024f5
* **TextService:** Correct the response format a547274
* npm start script and remove unnecessary file 6be00ac

### Features

* **async:** Change connect_pipe, read_pipe, close_pipe to non-blocking call 1aa4596
* **init:** Handle initialize service and check the guid ec452b1
* **keycode:** Add keycode mapping. 9dbdc81
* **KeyHandler:** Add KeyHandler class to handle normal key event dbf02bb
* **lib:** Initial binding libpipe.dll e4a0d6b
* **pipe:** Support write_pipe and can response the dummy message 8059f16
* **socket:** Use socket and server architecture to handle connection 9fb8211
* **TextService:** Support TextService for key event f9e37b7
