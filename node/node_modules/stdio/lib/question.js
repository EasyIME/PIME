'use strict';

var MAX_PROMPT_TRIES = 3;

/**
 * Shows a prompt question, letting the user to answer it.
 * @param {string}   question Question text
 * @param {array}    options  Possible answers (optional)
 * @param {function} callback Function to call with the results: function (err, responseText) {...}
 **/
function askQuestion(question, options, callback) {

	// Options can be omited
	if (typeof options === 'function') {
		callback = options;
		options = null;
	}

	// Throw possible errors
	if (!question) {
		throw new Error('Stdio prompt question is malformed. It must include at least a question text.');
	}
	if (options && (!Array.isArray(options) || options.length < 2)) {
		throw new Error('Stdio prompt question is malformed. Provided options must be an array with two options at least.');
	}

	/**
	 * Prints the question
	 **/
	var performQuestion = function () {
		var str = question;
		if (options) {
			str += ' [' + options.join('/') + ']';
		}
		str += ': ';
		process.stdout.write(str);
	};

	var tries = MAX_PROMPT_TRIES;

	process.stdin.resume();

	var listener = function (data) {

		var response = data.toString().toLowerCase().trim();

		if (options && options.indexOf(response) === -1) {
			console.log('Unexpected answer. %d retries left.', tries - 1);
			tries--;
			if (tries === 0) {
				process.stdin.removeListener('data', listener);
				process.stdin.pause();
				callback('Retries spent');
			} else {
				performQuestion();
			}
			return;
		}
		process.stdin.removeListener('data', listener);
		process.stdin.pause();
		callback(false, response);
	};

	process.stdin.addListener('data', listener);
	performQuestion();
}

// Exports
module.exports.question = askQuestion;
