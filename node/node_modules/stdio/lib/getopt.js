'use strict';

var util = require('./util.js');

/**
 * Check if an argument seems to be a number
 **/
function isNumericalArgument(arg) {
	return (/^[\d\-.,]+$/).test(arg);
}

/**
 * Check if an arguments item is an option or an option's argument
 **/
function isAnOption(arg) {
	return arg[0] === '-' && !isNumericalArgument(arg);
}

/**
 * Process an arguments list and refactorizes it replacing each -a=b element for two new elements: -a and b
 **/
function preProcessArguments (argv) {

	var processedArgs = [];
	argv.forEach(function (arg) {

		// If the argument is not an option, do not touch it
		if (arg[0] !== '-' || isNumericalArgument(arg)) {
			processedArgs.push(arg);
			return;
		}

		// For collapsed options, like "-abc" instead of "-a -b -c"
		if (arg[0] === '-' && arg[1] !== '-' && arg.length > 2 && arg.indexOf('=') === -1) {
			processedArgs = processedArgs.concat(arg.slice(1).split('').map(function (x) {
				return '-' + x;
			}));
			return;
		}

		// The general case, without collapsed options or assignments
		if (arg[0] !== '-' || arg.indexOf('=') === -1) {
			processedArgs.push(arg);
			return;
		}

		// For assignment options, like "-b=2" instead of "-b 2"
		arg = arg.match(/(.*?)=(.*)/);
		processedArgs.push(arg[1]);
		processedArgs.push(arg[2]);
	});
	return processedArgs;
}

/**
 * Builds an arguments map from a processed arguments list and a getopt() options object
 **/
function extractArgumentsMap (argv, config) {

	/**
	 * Find the nearest option of a provided one
	 **/
	function getNearestOption(option) {
		var options = Object.keys(config);
		var minDistance = Infinity;
		var nearestWord = null;
		options.forEach(function (o) {
			var d = util.textDistance(o, option);
			if (d < minDistance) {
				minDistance = d;
				nearestWord = o;
			}
		});
		if (minDistance < 3) {
			return nearestWord;
		}
		return null;
	}

	/**
	 * Find the option name of an argument key
	 **/
	function getOptionNameFromArgument (key) {

		// If key is a large form, then it is the option name itself
		if (key.indexOf('--') === 0) {
			return key.slice(2);
		}

		// If key is a short form, then we have to find the option name
		key = key.slice(1);
		for (var option in config) {
			if (config[option].key === key) {
				return option;
			}
		}

		// If no name is found, throw an error
		console.log('Unknown option: "-' + key + '".');
		console.log('Try "--help" for more information.');
		process.exit(-1);
	}

	/**
	 * Check if all arguments have been already specified for an option
	 **/
	function isOptionCompleted (option) {

		// args option is never fully specified, so any free argument is always a part of it
		if (option === 'args') {
			return false;
		}

		// Multiple arguments are not fully specified. They can be repeated many times
		if (config[option].multiple) {
			return false;
		}

		// Variable arguments count
		if (config[option].args === '*') {
			return false;
		}

		// Get the expected arguments count
		var expected = config[option].args;
		if (expected && typeof expected !== 'number') {
			throw new Error('"args" attribute has to be a number or the string "*" when specifying getopt() settings');
		}

		// Compute how many arguments have been already specified and how many ones are expected
		var argsCount = 0;
		if (config[option]) {
			if (Array.isArray(options[option])) {
				argsCount = options[option].length;
			} else if (options[option] !== true){
				argsCount = 1;
			} else {
				argsCount = 0;
			}
		}

		return !expected || (argsCount === expected);
	}

	// Remove "node" and "program.js", then preprocess arguments array
	argv = argv.slice(2);
	argv = preProcessArguments(argv);

	var options = {};
	var lastArgument;

	for (var i = 0, len = argv.length; i < len; i++) {

		// Not allowed arguments
		if (argv[i] === '-' || argv[i] == '--') {
			console.log('Wrong argument provided: "%s".\nTry "--help" for more information.', argv[i]);
			process.exit(-1);
		}

		if (isAnOption(argv[i])) {

			// It is an option name (not an argument for an option)

			lastArgument = getOptionNameFromArgument(argv[i]);
			if (!config[lastArgument]) {
				var strError = 'Unknown option "--' + lastArgument + '".';
				var suggestion = getNearestOption(lastArgument);
				if (suggestion) {
					strError += ' Did you mean "--' + suggestion + '"?';
				}
				strError += '\nTry "--help" for more information.';
				console.log(strError);
				process.exit(-1);
			}
			options[lastArgument] = options[lastArgument] || true;

		} else {

			// It is an argument for an option

			if (!lastArgument || isOptionCompleted(lastArgument)) {
				lastArgument = 'args';
			} else if ((config[lastArgument] || {}).multiple && i > 0 && !isAnOption(argv[i - 1])) {
				lastArgument = 'args';
			}

			if (options[lastArgument] === true) {
				options[lastArgument] = argv[i];
			} else if (Array.isArray(options[lastArgument])) {
				options[lastArgument].push(argv[i]);
			} else if (lastArgument === 'args') {
				options[lastArgument] = [argv[i]];
			} else {
				options[lastArgument] = [options[lastArgument]];
				options[lastArgument].push(argv[i]);
			}
		}
	}

	return options;
}

/**
 * Core getopt function
 **/
function getopt (config, helpTail, argv, testing) {

	argv = argv || process.argv;
	config = config || {};
	var programName = argv[1].split('/').pop();

	// Help option cannot be overrided
	if (config.help) {
		throw new Error('"--help" option is reserved for the automatic help message. You cannot override it when calling getopt().');
	}

	var usedKeys = {};
	var key, option;
	for (option in config) {

		key = config[option].key;

		if (!key) {
			continue;
		}

		// Short options name has to be unique
		if (usedKeys[key]) {
			throw new Error('Short key "' + key + '" is repeated in getopt() config. You cannot use the same key for two options.');
		}

		// Multiple option is not compatible with args count
		if (config[option].multiple && ('args' in config[option])) {
			throw new Error('"args" count cannot be specified for options marked with "multiple" flag.');
		}
		usedKeys[key] = true;
	}

	// Print help message when executing with --help or -h
	if (argv.indexOf('--help') !== -1) {
		printHelpMessage(config, helpTail, programName);
		process.exit(0);
	}

	// Build de options/arguments map
	var cmdOptions = extractArgumentsMap(argv, config);

	// Check every mandatory option is specified
	for (option in config) {
		if (option === '_meta_') {
			continue;
		}
		if (config[option].mandatory && !(option in cmdOptions)) {
			if (testing) {
				return null;
			}
			console.log('Missing "%s" argument.\nTry "--help" for more information.', option);
			process.exit(-1);
		}
		if (!(option in cmdOptions)) {
			continue;
		}

		// Check all required arguments have been specified for each option
		var requiredArgumentsCount = config[option].args;
		var providedArgumentsCount = cmdOptions[option] === true ? 0 : (Array.isArray(cmdOptions[option]) ? cmdOptions[option].length : 1);
		if (requiredArgumentsCount > 1 && providedArgumentsCount !== requiredArgumentsCount) {
			if (testing) {
				return null;
			}
			console.log('Option "--%s" requires %d arguments, but %d were provided. Try "--help" for more information.', option, requiredArgumentsCount, providedArgumentsCount);
			printHelpMessage(config, helpTail, programName);
			process.exit(-1);
		}
	}

	// Check expected positional arguments are provided
	var providedArgs = 0;
	if (Array.isArray(cmdOptions.args) && cmdOptions.args.length > 0) {
		providedArgs = cmdOptions.args.length;
	}
	if (config._meta_ && config._meta_.args && providedArgs !== config._meta_.args) {
		console.log('%d positional arguments (without option flag) are required, but %d have been provided.', config._meta_.args, providedArgs);
		printHelpMessage(config, helpTail, programName);
		process.exit(-1);
	}
	if (config._meta_ && config._meta_.minArgs && providedArgs < config._meta_.minArgs) {
		console.log('At least %d positional arguments (without option flag) are required, but %d have been provided.', config._meta_.minArgs, providedArgs);
		printHelpMessage(config, helpTail, programName);
		process.exit(-1);
	}
	if (config._meta_ && config._meta_.maxArgs && providedArgs > config._meta_.maxArgs) {
		console.log('Too many positional arguments (without option flag) provided. The maximum allowed is %d, but %d have been provided.', config._meta_.maxArgs, providedArgs);
		printHelpMessage(config, helpTail, programName);
		process.exit(-1);
	}

	// Apply default values
	for (option in config) {
		if (typeof config[option] === 'object' && 'default' in config[option]) {
			if ((!Array.isArray(config[option]['default']) && parseInt(config[option].args, 10) > 1) ||
				(Array.isArray(config[option]['default']) && config[option]['default'].length !== parseInt(config[option].args, 10))) {
				throw new Error('Default value of an option must have the same length as specified by its "args" attribute');
			}
			cmdOptions[option] = cmdOptions[option] || config[option]['default'];
		}

	}

	// A function to print help message manually
	cmdOptions.printHelp = function () {
		printHelpMessage(config, helpTail, programName);
	};

	return cmdOptions;
}

/**
 * Prints the help (--help, -h)
 **/
function printHelpMessage(options, helpTail, programName) {

	helpTail = helpTail || 'node ' + programName + ' [OPTION1] [OPTION2]... arg1 arg2...';
	console.log('USAGE:', helpTail);
	console.log('The following options are supported:');

	var o = null, lines = [], maxLength;

	for (o in options) {
		if (o === '_meta_') {
			continue;
		}
		if (options.hasOwnProperty(o)) {
			var ops = ' ', i;
			if (options[o].multiple) {
				options[o].args = 1;
			}
			for (i = 0; i < options[o].args; i++) {
				ops += '<ARG' + (i + 1) + '> ';
			}
			if (options[o].args === '*') {
				ops += '<ARG1>...<ARGN>';
			}
			lines.push(['  ' + (options[o].key ? '-' + options[o].key + ', --' : '--') + o + ops, (options[o].description || '') + (options[o].mandatory ? ' (mandatory)' : '') + (options[o].multiple ? ' (multiple)' : '' + (options[o]['default'] ? ' ("' + options[o]['default'] + '" by default)' : ''))]);
		}
	}

	maxLength = lines.reduce(function (prev, curr) {
		var aux = curr[0].length;
		if (aux > prev) {
			return aux;
		}
		return prev;
	}, 0);

	lines = lines.map(function (l) {
		return l[0] + (new Array(maxLength - l[0].length + 1)).join(' ') + '\t' + l[1];
	});

	console.log(lines.join('\n'));

}

// Exports
module.exports.getopt = getopt;
module.exports.preProcessArguments = preProcessArguments;
