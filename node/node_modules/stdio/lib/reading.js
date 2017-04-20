'use strict';

/**
 * Reads the complete standard input
 * @param {function} callback Function to call when finished: function (wholeInputText) {...}
 */
function read(callback) {

	if (!callback) {
		throw new Error('no callback provided to readInput() call');
	}

	var inputdata = '';
	process.stdin.resume();

	var listener = function (text) {
		if (!text) {
			return;
		}
		inputdata += String(text);
	};

	process.stdin.on('data', listener);

	process.stdin.on('end', function () {
		process.stdin.removeListener('data', listener);
		callback(inputdata);
	});
}

/**
 * Reads the standard input by lines and apply a function to every line
 * @param {function} lineProcessor Function to call for every line: function (line) {...}
 * @param {function} callback      Function to call when finished: function (err) {...}
 **/
function readByLines(lineProcessor, callback) {

	var index = 0;

	var readline = require('readline');
	var rl = readline.createInterface({
		input: process.stdin,
		output: process.stdout,
		terminal: false
	});
	rl.on('line', function (line) {
		lineProcessor(line, index);
		index++;
	});
	if (callback) {
		rl.on('close', callback);
	}
}

// Exports
module.exports.read = read;
module.exports.readByLines = readByLines;
