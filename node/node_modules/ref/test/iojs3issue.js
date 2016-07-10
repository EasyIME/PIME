var assert = require('assert')
var ref = require('../')

// This will check if the new Buffer implementation behaves like the pre io.js 3.0 one did:
describe('iojs3issue', function () {
    it('should not crash', function() {
        for (var i = 0; i < 10; i++) {
            gc()
            var buf = new Buffer(8)
            buf.fill(0)
            var buf2 = ref.ref(buf)
            var buf3 = ref.deref(buf2)
        }
    })
    it('should not crash too', function() {
        for (var i = 0; i < 10; i++) {
            gc()
            var buf = new Buffer(7)
            buf.fill(0)
            var buf2 = ref.ref(buf)
            var buf3 = ref.deref(buf2)
        }
    })
})