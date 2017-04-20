Module for standard input/output management with nodejs.

[![Build Status](https://secure.travis-ci.org/sgmonda/stdio.png)](http://travis-ci.org/sgmonda/stdio)

[![NPM](https://nodei.co/npm/stdio.png)](https://nodei.co/npm/stdio/)

## 1. Installation

To install the most recent release from npm, run:

    npm install stdio

## 2. Usage

You can do many things with this module:
* Parse UNIX-like command line options
* Read standard input, at once or line by line.
* Make command-line questions

### 2.1. Parse Unix-like command line options

```javascript
var stdio = require('stdio');
var ops = stdio.getopt({
    'check': {key: 'c', args: 2, description: 'What this option means'},
    'map': {key: 'm', description: 'Another description', mandatory: true},
    'kaka': {key: 'k', args: 2, mandatory: true},
    'ooo': {key: 'o'}
});
console.log(ops);
```

If you run the previous example with the command

    node pruebas.js -c 23 45 88 --map -k 23 44 cosa

Program output will be:

    { check: [ '23', '45' ],
      args: [ '88', 'cosa' ],
      map: true,
      kaka: [ '23', '44' ] }

So you can check options:

```javascript
if(ops.map){
    // Your action
}
if(ops.kaka){
    // Your action, using ops.kaka[0] or ops.kaka[1] or...
}
```

As you can see, every option in `ops` object can have one of the following 3 types of values:

* The boolean value `true` if it has been specified without an `args` attribute.
* A single `string` if it has been specified with `args: 1`.
* A `string` array, if it has been specified with `args` > 1.

Options can have the `multiple` flag, in which case they can appear multiple times (with one argument each time). The value of that option will be an array with all provided arguments:

```javascript
var ops = stdio.getopt({
    'check': {key: 'c', description: 'What this option means', multiple: true}
});
```
```
node program.js -c 1 -c 2 -c 3
```
```
{ check: ['1', '2', '3'] }

```

When specifying an option, "args" can be the string "*" instead of a number, in which case all the following arguments when calling the program will be associated to that option (until the next one):

```
var ops = stdio.getopt({
    'check': {args: '*'},
	'meta': {key: 'm'}
});
console.log(ops);
```
```
node program.js --check 1 2 3 4 5 6 -m 44 2
```
```
{ check: ['1', '2', '3', '4', '5', '6'], meta: true, args: ['44', '2'] }
```

Default values can be specified using "default" attribute when specifying options. Of course, default value length has to match the specified args count (if it is not '*'):

```
var ops = stdio.getopt({
	something: {args: 2, default: ['a', 'b']}
});
```

#### Mandatory positional arguments

If your program has to receive some mandatory positional arguments (extra arguments without an option flag), you can specify it when calling `getopt()`:

```
var ops = stdio.getopt({
	_meta_: {args: 2}
});
```

```
var ops = stdio.getopt({
	_meta_: {minArgs: 1}
});
```

```
var ops = stdio.getopt({
	_meta_: {maxArgs: 5}
});
```

#### Print usage

This module generates a descriptive usage message automatically. You'll see it when your program is called with `--help` option, which is automatically supported. The following code:

```javascript
var stdio = require('stdio');

var ops = exports.getopt({
	una: {description: 'Sets something to some value', args: 2, mandatory: true},
	otra_muy_larga: {description: 'A boolean flag', key: 'o', mandatory: true},
	una_sin_desc: {description: 'Another boolean flag'},
	ultima: {description: 'A description', key: 'u', args: 1}
});
```

will produce the following output (if it is called with `--help` flag):

```
USAGE: node main.js [OPTION1] [OPTION2]... arg1 arg2...
  --una <ARG1> <ARG2>  	Sets something to some value (mandatory)
  -o, --otra_muy_larga 	A boolean flag (mandatory)
  --una_sin_desc       	Another boolean flag
  -u, --ultima <ARG1>  	A description
```

If a non-expected option is given or a mandatory option isn't, then an error will be shown, suggesting to use `--help` option to know how to use your program and finishing it automatically. In case the unknown option is similar to a known one, then a suggestion to use it will be shown.

```
Missing "una" argument.
Try "--help" for more information.
```

You can print the help message manually if you want, executing `ops.printHelp()`.

### 2.2. Read standard input at once

The following code will read the whole standard input at once and put it into `text` variable.

```javascript
var stdio = require('stdio');
stdio.read(function(text){
    console.log(text);
});
```

Obviously it is recommended only for small input streams, for instance a small file:

```
node myprogram.js < input-file.txt
```

### 2.3. Read standard input line by line

The following code will execute dynamically a function over every line, when it is read from the standard input:

```javascript
var stdio = require('stdio');
stdio.readByLines(function lineHandler(line, index) {
    // You can do whatever you want with every line
    console.log('Line %d:', index, line);
}, function (err) {
    console.log('Finished');
});
```

The previous code will apply `lineHandler()` to every line while they are read, without waiting the whole input to end or buffering it, so it is very useful for large text streams. For instance a continuous log:

```
tail -f /var/log/system.log | node myprogram.js
```

### 2.4. Show prompt questions and wait user's answer

The following code will ask the user for some info and then print it.

```javascript
stdio.question('What is your name?', function (err, name) {
    stdio.question('How old are you?', function (err, age) {
        stdio.question('Are you male or female?', ['male', 'female'], function (err, sex) {
            console.log('Your name is "%s". You are a "%s" "%s" years old.', name, sex, age);
        });
    });
});
```

By default `stdio.question()` offers some retries when allowed answers are restricted (see the male/female question above). If no possible answers are specified, then the user can answer whatever he wants to the question.

### 2.5. Show a progress bar

The following code will create a progress bar of 100 pieces and increments of 10. These values do not affect how the progress bar is shown, so a progress bar with 100 steps will be equals to a progress bar with 4 steps. Every call to `tick()` increments the bar value. Remaining time is estimated dynamically:

```javascript
var stdio = require('./main.js');

var pbar = stdio.progressBar(100, 10);
var i = setInterval(function () {
	pbar.tick();
}, 1000);
pbar.onFinish(function () {
	console.log('finish');
	clearInterval(i);
});
```

The progress bar is updated in real-time:
```
00:00:03 25% [###############························] ETA 00:00:09
```
Instead of calling `tick()` it is possible to force the progress bar value at any time:

```javascript
pbar.setValue(31);
```

## 3. Testing

To run tests, use the following command from module's root:

````
npm test
````
