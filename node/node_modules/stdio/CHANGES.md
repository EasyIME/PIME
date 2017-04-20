# Changes

## 0.2.7

* Positional arguments constraints support added, by mean of `_meta_` argument settings.

## 0.2.5

* Progress bar feature added

## 0.2.3

* `printHelp()` function is available again into `getopt()` response object.
* `-h` is not a reserved key any more. You can use it in your options.

## 0.2.2

* Bug fixes

## 0.2.1

* The "args" attribute when specifying an option now can be the string "*" instead of a number. This means that option supports a variable arguments count.
* New cool feature! `getopt()` now makes suggestions if you write an unknown option that is similar to a known one.
* Default value per option support added.

## 0.2.0

* The whole project has been rewritten. The code is now more readable and follows JSHint. Many tests have been added, now using Jasmine.
* Options with "=" character now don't need to be escaped. This adds a backwards incompatibility, so be careful updating to this version if you use escaped arguments.

## 0.1.7

* Support for multiple options added by mean of `multiple: true` flag:
````
node program.js -c 1 -c 2 -c 3
````

## 0.1.6

* Arguments now can have "=" sign escaped: `node program.js -m loc.ark+\\=13960\\=t0000693r.meta.json` will give the following:
````
{
  createHelp: [Function],
  printHelp: [Function],
  meta: 'loc.ark+=13960=t0000693r.meta.json'
}
````

## 0.1.5

* Added support for prompt questions without options

## 0.1.4

* New fancy feature! Now you can show simple prompts to interact with users by mean of a question.
* Old printf-like feature has been removed.

## 0.1.3

* Support for extended large options added. Now it is possible to write `--anoption=44` instead of `--anoption 44`. This works only for options with a single parameter.

## 0.1.2

* Bug fix: Negative numbers as parameters caused wrong errors.

## 0.1.1

* Grouped short options support added (for boolean flags). Now you can write `-abc` instead of `-a -b -c`.
* Usage message has been simplified. Extra arguments description is supported now.

## 0.1.0

* If an option is specified with less arguments than the specified, an error (and the help message) is shown and program finishes.
* Captured options now has 3 possible values: `true`, a single `string` or an array of `strings`. Much easier to use than in previous releases (but incompatible with them, so be careful updating).
