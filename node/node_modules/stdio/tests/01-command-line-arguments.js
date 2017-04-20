/*global describe, it, expect */

'use strict';

var stdio = require('../lib/getopt.js');

describe('preProcessArguments()', function () {

	var testsCases = [{
		inputArguments: [],
		expected: []
	}, {
		inputArguments: ['a'],
		expected: ['a']
	}, {
		inputArguments: ['a', '-bcd', 'e'],
		expected: ['a', '-b', '-c', '-d', 'e']
	}, {
		inputArguments: ['a', 'b=c'],
		expected: ['a', 'b=c']
	}, {
		inputArguments: ['a', '-b=c'],
		expected: ['a', '-b', 'c']
	}, {
		inputArguments: ['a', '-b=c', '-333', '444'],
		expected: ['a', '-b', 'c', '-333', '444']
	}, {
		inputArguments: ['a', '--something=hello'],
		expected: ['a', '--something', 'hello']
	}];

	testsCases.forEach(function (test, index) {

		it('Test case #' + index, function () {
			var args = stdio.preProcessArguments(test.inputArguments);
			var expected = test.expected;
			expect(JSON.stringify(args)).toBe(JSON.stringify(expected));
		});
	});
});

describe('getopt()', function () {

	var testCases = [{
		getoptConfig: {},
		argv: ['node', 'program.js'],
		expected: {}
	}, {
		getoptConfig: {},
		argv: ['node', 'program.js', 'arg1', 'arg2'],
		expected: {
			'args': ['arg1', 'arg2']
		}
	}, {
		getoptConfig: {
			'test': {}
		},
		argv: ['node', 'program.js', '--test'],
		expected: {'test': true}
	}, {
		getoptConfig: {
			'test': {key: 't'},
			'other': {key: 'o'}
		},
		argv: ['node', 'program.js', '-o'],
		expected: {'other': true}
	}, {
		getoptConfig: {
			'test': {key: 't', args: 2},
			'other': {key: 'o'}
		},
		argv: ['node', 'program.js', '-t', 'uno', '237', '--other'],
		expected: {'test': ['uno', '237'], 'other': true}
	}, {
		getoptConfig: {
			'test': {key: 't', args: 2},
			'other': {key: 'o'}
		},
		argv: ['node', 'program.js', '-t', 'uno', '237', '--other', 'extra1', 'extra2'],
		expected: {'test': ['uno', '237'], 'other': true, 'args': ['extra1', 'extra2']}
	}, {
		getoptConfig: {
			'test': {key: 't', args: 2},
			'other': {key: 'o'},
			'last': {args: 1}
		},
		argv: ['node', 'program.js', '-t', 'uno', '237', '--other', 'extra1', 'extra2', '--last', '34', 'extra3'],
		expected: {'test': ['uno', '237'], 'other': true, 'args': ['extra1', 'extra2', 'extra3'], 'last': '34'}
	}, {
		getoptConfig: {
			'joint1': {key: 'a'},
			'joint2': {key: 'b'},
			'joint3': {key: 'c'}
		},
		argv: ['node', 'program.js', '-abc'],
		expected: {joint1: true, joint2: true, joint3: true}
	}, {
		getoptConfig: {
			'joint1': {key: 'a'},
			'joint2': {key: 'b'},
			'joint3': {key: 'c'}
		},
		argv: ['node', 'program.js', '-ac'],
		expected: {joint1: true, joint3: true}
	}, {
		getoptConfig: {
			'joint1': {key: 'a'},
			'joint2': {key: 'b'},
			'joint3': {key: 'c'}
		},
		argv: ['node', 'program.js', '-b'],
		expected: {joint2: true}
	}, {
		getoptConfig: {
			'number': {key: 'n', args: 2},
			'other': {key: 'o'}
		},
		argv: ['node', 'program.js', '-n', '-33', '-237', '--other'],
		expected: {'number': ['-33', '-237'], 'other': true}
	}, {
		getoptConfig: {
			'number': {key: 'n', args: 2},
			'other': {key: 'o'}
		},
		argv: ['node', 'program.js', '-n', '33', '-237'],
		expected: {'number': ['33', '-237']}
	}, {
		getoptConfig: {
			'number': {key: 'n', args: 1},
			'other': {key: 'o'},
			'pepe': {args: 3}
		},
		argv: ['node', 'program.js', '--number=88', '--pepe', '22', '33', 'jose=3'],
		expected: {'number': '88', 'pepe': ['22', '33', 'jose=3']}
	}, {
		getoptConfig: {
			url: {key: 'u', args: 1}
		},
		argv: ['node', 'program.js', '--url', '"http://www.example.com/?b=1"'],
		expected: {url: '"http://www.example.com/?b=1"' }
	}, {
		getoptConfig: {
			meta: {key: 'm', args: 1}
		},
		argv: ['node', 'program.js', '-m', 'loc.ark+=13960=t0000693r.meta.json'],
		expected: {meta: 'loc.ark+=13960=t0000693r.meta.json' }
	}, {
		getoptConfig: {
			'number': {key: 'n', args: 2, mandatory: true},
			'other': {key: 'o'}
		},
		argv: ['node', 'program.js', '-237'],
		expected: null
	}, {
		getoptConfig: {
			meta: {key: 'm', multiple: true}
		},
		argv: ['node', 'program.js', '-m', '1', '-m', '2', '-m', '3', 'a', 'b'],
		expected: {meta: ['1', '2', '3'], args: ['a', 'b']}
	}, {
		getoptConfig: {
			meta: {args: '*'},
			other: {key: 'o'}
		},
		argv: ['node', 'program.js', '--meta', '3', '4', '5', '6', '-o', '3'],
		expected: {meta: ['3', '4', '5', '6'], other: true, args: ['3']}
	}, {
		getoptConfig: {
			meta: {key: 'm', 'default': 'foo'},
			other: true
		},
		argv: ['node', 'program.js', '--other'],
		expected: {other: true, meta: 'foo'}
	}, {
		getoptConfig: {
			meta: {key: 'm', args: 2, 'default': ['1', '2']},
			other: {'default': false}
		},
		argv: ['node', 'program.js'],
		expected: {meta: ['1', '2'], other: false}
	}, {
		getoptConfig: {
			meta: {key: 'm', args: 2, 'default': ['1', '2']},
			other: {'default': false}
		},
		argv: ['node', 'program.js', '-m', 'a', 'b'],
		expected: {meta: ['a', 'b'], other: false}
	}, {
		getoptConfig: {
			check: {key: 'c', args: 1},
			number: {key: 'n', args: 1},
			header: {key: 'H', args: 1}
		},
		argv: ['node', 'program.js', 'http://localhost:80/', '-c', '2', '-n', '1', '-H', 'Cookie:SPRING_SECURITY_CONTEXT=ZmYzYjZmYjItZThjOS00ZmZhLTkyOWQtZDRjYzE3NmRmZWIy'],
		expected: {args: ['http://localhost:80/'], check: '2', number: '1', header: 'Cookie:SPRING_SECURITY_CONTEXT=ZmYzYjZmYjItZThjOS00ZmZhLTkyOWQtZDRjYzE3NmRmZWIy'}
	}];

	testCases.forEach(function (test, index) {

		it('Test case #' + index, function () {
			var ops = stdio.getopt(test.getoptConfig, null, test.argv, true);
			var expected = test.expected;
			expect(JSON.stringify(ops)).toBe(JSON.stringify(expected));
		});
	});
});

