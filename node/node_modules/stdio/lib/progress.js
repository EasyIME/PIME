'use strict';

/**
 * Progress bar class
 **/
function ProgressBar(maxValue, incrementValue) {

	var self = this;
	self.value = 0;
	self.incrementValue = incrementValue || 1;
	self.MAX_VALUE = maxValue || 100;
	self.startTime = Date.now();

	/**
	 * Transforms a number of seconds into an string representing the
	 * hours, minutes and seconds in format HH:MM:SS
	 **/
	function secondsToTimeString(seconds) {
		var minutes = 0, hours = 0;
		if (seconds / 60 > 0) {
			minutes = parseInt(seconds / 60, 10);
			seconds = seconds % 60;
		}
		if (minutes / 60 > 0) {
			hours = parseInt(minutes / 60, 10);
			minutes = minutes % 60;
		}
		return ('0' + hours).slice(-2) + ':' + ('0' + minutes).slice(-2) + ':' + ('0' + seconds).slice(-2);
	}

	/**
	 * Computes the amount of seconds from the begining of the progress
	 **/
	self.getEllapsedTime = function () {
		return parseInt((Date.now() - self.startTime) / 1000, 10);
	};

	/**
	 * Computes the estimated remaining time in seconds
	 **/
	self.getRemainingTime = (function () {
		var lastRemainingTimes = [];
		return function () {
			var secondsPerTick = self.getEllapsedTime() / self.value;
			var remaining = parseInt((self.MAX_VALUE - self.value) * secondsPerTick, 10);
			lastRemainingTimes.push(remaining);
			if (lastRemainingTimes.length > 5) {
				lastRemainingTimes.shift();
			}
			return parseInt(lastRemainingTimes.reduce(function (acum, item) {
				return acum + item;
			}, 0) / lastRemainingTimes.length, 10);
		};
	}());

	/**
	 * Sets the current value of the progress bar.
	 * It must be a number between 0 and the MAX_VALUE of the bar
	 **/
	self.setValue = function (value) {
		self.value = value;
		if (self.value > self.MAX_VALUE) {
			self.value = self.MAX_VALUE;
		}
		self.print();
		if (self.value === self.MAX_VALUE && self.finishedCallback) {
			process.stdout.write('\n');
			self.finishedCallback();
			self.finishedCallback = null;
		}
	};

	/**
	 * Increment the current value by the specified increment
	 **/
	self.tick = function () {
		self.value += self.incrementValue;
		if (self.value > self.MAX_VALUE) {
			self.value = self.MAX_VALUE;
		}
		self.print();
		if (self.value === self.MAX_VALUE) {
			process.stdout.write('\n');
			if (self.finishedCallback) {
				self.finishedCallback();
				self.finishedCallback = null;
			}
		}
	};

	/**
	 * Replaces the previous bar print with the current one, updating the status
	 **/
	self.print = function () {

		var ellapsedTime = secondsToTimeString(self.getEllapsedTime());
		var percent = parseInt(self.value * 100 / self.MAX_VALUE, 10);
		var prefix = ellapsedTime + ' ' + percent + '%';

		var eta = secondsToTimeString(self.getRemainingTime());
		var sufix = 'ETA ' + eta;

		process.stdout.write('\r');
		var TERMINAL_WIDTH = process.stdout.width || 70;
		var ticks = [];

		for (var i = 0, len = (TERMINAL_WIDTH - ellapsedTime.length - 3); i < len; i++) {
			if ((i * 100 / len) <= percent) {
				ticks.push('#');
			} else {
				ticks.push('·');
			}
		}

		process.stdout.write(prefix + ' [' + ticks.join('') + '] ' + sufix);
	};

	/**
	 * Receives a function to call when progress finishes
	 **/
	self.onFinish = function (callback) {
		self.finishedCallback = callback;
	};

}

// Exports

exports.progressBar = function (max, increment) {
	var p = new ProgressBar(max, increment);
	return p;
};
