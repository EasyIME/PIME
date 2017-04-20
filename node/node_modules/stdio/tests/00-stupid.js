/*global describe, it, expect, jasmine*/

'use strict';

describe('Stupid tests', function () {

	it('Basic synchronous true', function () {
		expect(true).toBe(true);
	});

	it('Basic asynchronous true', function (done) {
		expect(true).toBe(true);
		done();
	});
});
