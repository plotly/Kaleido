(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.kaleido_scopes = f()}})(function(){var define,module,exports;return (function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
/**
 * inspired by is-number <https://github.com/jonschlinkert/is-number>
 * but significantly simplified and sped up by ignoring number and string constructors
 * ie these return false:
 *   new Number(1)
 *   new String('1')
 */

'use strict';

var allBlankCharCodes = require('is-string-blank');

module.exports = function(n) {
    var type = typeof n;
    if(type === 'string') {
        var original = n;
        n = +n;
        // whitespace strings cast to zero - filter them out
        if(n===0 && allBlankCharCodes(original)) return false;
    }
    else if(type !== 'number') return false;

    return n - n < 1;
};

},{"is-string-blank":3}],2:[function(require,module,exports){
'use strict';

module.exports = value => {
	if (Object.prototype.toString.call(value) !== '[object Object]') {
		return false;
	}

	const prototype = Object.getPrototypeOf(value);
	return prototype === null || prototype === Object.prototype;
};

},{}],3:[function(require,module,exports){
'use strict';

/**
 * Is this string all whitespace?
 * This solution kind of makes my brain hurt, but it's significantly faster
 * than !str.trim() or any other solution I could find.
 *
 * whitespace codes from: http://en.wikipedia.org/wiki/Whitespace_character
 * and verified with:
 *
 *  for(var i = 0; i < 65536; i++) {
 *      var s = String.fromCharCode(i);
 *      if(+s===0 && !s.trim()) console.log(i, s);
 *  }
 *
 * which counts a couple of these as *not* whitespace, but finds nothing else
 * that *is* whitespace. Note that charCodeAt stops at 16 bits, but it appears
 * that there are no whitespace characters above this, and code points above
 * this do not map onto white space characters.
 */

module.exports = function(str){
    var l = str.length,
        a;
    for(var i = 0; i < l; i++) {
        a = str.charCodeAt(i);
        if((a < 9 || a > 13) && (a !== 32) && (a !== 133) && (a !== 160) &&
            (a !== 5760) && (a !== 6158) && (a < 8192 || a > 8205) &&
            (a !== 8232) && (a !== 8233) && (a !== 8239) && (a !== 8287) &&
            (a !== 8288) && (a !== 12288) && (a !== 65279)) {
                return false;
        }
    }
    return true;
}

},{}],4:[function(require,module,exports){
// shim for using process in browser
var process = module.exports = {};

// cached from whatever global is present so that test runners that stub it
// don't break things.  But we need to wrap it in a try catch in case it is
// wrapped in strict mode code which doesn't define any globals.  It's inside a
// function because try/catches deoptimize in certain engines.

var cachedSetTimeout;
var cachedClearTimeout;

function defaultSetTimout() {
    throw new Error('setTimeout has not been defined');
}
function defaultClearTimeout () {
    throw new Error('clearTimeout has not been defined');
}
(function () {
    try {
        if (typeof setTimeout === 'function') {
            cachedSetTimeout = setTimeout;
        } else {
            cachedSetTimeout = defaultSetTimout;
        }
    } catch (e) {
        cachedSetTimeout = defaultSetTimout;
    }
    try {
        if (typeof clearTimeout === 'function') {
            cachedClearTimeout = clearTimeout;
        } else {
            cachedClearTimeout = defaultClearTimeout;
        }
    } catch (e) {
        cachedClearTimeout = defaultClearTimeout;
    }
} ())
function runTimeout(fun) {
    if (cachedSetTimeout === setTimeout) {
        //normal enviroments in sane situations
        return setTimeout(fun, 0);
    }
    // if setTimeout wasn't available but was latter defined
    if ((cachedSetTimeout === defaultSetTimout || !cachedSetTimeout) && setTimeout) {
        cachedSetTimeout = setTimeout;
        return setTimeout(fun, 0);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedSetTimeout(fun, 0);
    } catch(e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't trust the global object when called normally
            return cachedSetTimeout.call(null, fun, 0);
        } catch(e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error
            return cachedSetTimeout.call(this, fun, 0);
        }
    }


}
function runClearTimeout(marker) {
    if (cachedClearTimeout === clearTimeout) {
        //normal enviroments in sane situations
        return clearTimeout(marker);
    }
    // if clearTimeout wasn't available but was latter defined
    if ((cachedClearTimeout === defaultClearTimeout || !cachedClearTimeout) && clearTimeout) {
        cachedClearTimeout = clearTimeout;
        return clearTimeout(marker);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedClearTimeout(marker);
    } catch (e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't  trust the global object when called normally
            return cachedClearTimeout.call(null, marker);
        } catch (e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error.
            // Some versions of I.E. have different rules for clearTimeout vs setTimeout
            return cachedClearTimeout.call(this, marker);
        }
    }



}
var queue = [];
var draining = false;
var currentQueue;
var queueIndex = -1;

function cleanUpNextTick() {
    if (!draining || !currentQueue) {
        return;
    }
    draining = false;
    if (currentQueue.length) {
        queue = currentQueue.concat(queue);
    } else {
        queueIndex = -1;
    }
    if (queue.length) {
        drainQueue();
    }
}

function drainQueue() {
    if (draining) {
        return;
    }
    var timeout = runTimeout(cleanUpNextTick);
    draining = true;

    var len = queue.length;
    while(len) {
        currentQueue = queue;
        queue = [];
        while (++queueIndex < len) {
            if (currentQueue) {
                currentQueue[queueIndex].run();
            }
        }
        queueIndex = -1;
        len = queue.length;
    }
    currentQueue = null;
    draining = false;
    runClearTimeout(timeout);
}

process.nextTick = function (fun) {
    var args = new Array(arguments.length - 1);
    if (arguments.length > 1) {
        for (var i = 1; i < arguments.length; i++) {
            args[i - 1] = arguments[i];
        }
    }
    queue.push(new Item(fun, args));
    if (queue.length === 1 && !draining) {
        runTimeout(drainQueue);
    }
};

// v8 likes predictible objects
function Item(fun, array) {
    this.fun = fun;
    this.array = array;
}
Item.prototype.run = function () {
    this.fun.apply(null, this.array);
};
process.title = 'browser';
process.browser = true;
process.env = {};
process.argv = [];
process.version = ''; // empty string to avoid regexp issues
process.versions = {};

function noop() {}

process.on = noop;
process.addListener = noop;
process.once = noop;
process.off = noop;
process.removeListener = noop;
process.removeAllListeners = noop;
process.emit = noop;
process.prependListener = noop;
process.prependOnceListener = noop;

process.listeners = function (name) { return [] }

process.binding = function (name) {
    throw new Error('process.binding is not supported');
};

process.cwd = function () { return '/' };
process.chdir = function (dir) {
    throw new Error('process.chdir is not supported');
};
process.umask = function() { return 0; };

},{}],5:[function(require,module,exports){
const ANY = Symbol('SemVer ANY')
// hoisted class for cyclic dependency
class Comparator {
  static get ANY () {
    return ANY
  }
  constructor (comp, options) {
    if (!options || typeof options !== 'object') {
      options = {
        loose: !!options,
        includePrerelease: false
      }
    }

    if (comp instanceof Comparator) {
      if (comp.loose === !!options.loose) {
        return comp
      } else {
        comp = comp.value
      }
    }

    debug('comparator', comp, options)
    this.options = options
    this.loose = !!options.loose
    this.parse(comp)

    if (this.semver === ANY) {
      this.value = ''
    } else {
      this.value = this.operator + this.semver.version
    }

    debug('comp', this)
  }

  parse (comp) {
    const r = this.options.loose ? re[t.COMPARATORLOOSE] : re[t.COMPARATOR]
    const m = comp.match(r)

    if (!m) {
      throw new TypeError(`Invalid comparator: ${comp}`)
    }

    this.operator = m[1] !== undefined ? m[1] : ''
    if (this.operator === '=') {
      this.operator = ''
    }

    // if it literally is just '>' or '' then allow anything.
    if (!m[2]) {
      this.semver = ANY
    } else {
      this.semver = new SemVer(m[2], this.options.loose)
    }
  }

  toString () {
    return this.value
  }

  test (version) {
    debug('Comparator.test', version, this.options.loose)

    if (this.semver === ANY || version === ANY) {
      return true
    }

    if (typeof version === 'string') {
      try {
        version = new SemVer(version, this.options)
      } catch (er) {
        return false
      }
    }

    return cmp(version, this.operator, this.semver, this.options)
  }

  intersects (comp, options) {
    if (!(comp instanceof Comparator)) {
      throw new TypeError('a Comparator is required')
    }

    if (!options || typeof options !== 'object') {
      options = {
        loose: !!options,
        includePrerelease: false
      }
    }

    if (this.operator === '') {
      if (this.value === '') {
        return true
      }
      return new Range(comp.value, options).test(this.value)
    } else if (comp.operator === '') {
      if (comp.value === '') {
        return true
      }
      return new Range(this.value, options).test(comp.semver)
    }

    const sameDirectionIncreasing =
      (this.operator === '>=' || this.operator === '>') &&
      (comp.operator === '>=' || comp.operator === '>')
    const sameDirectionDecreasing =
      (this.operator === '<=' || this.operator === '<') &&
      (comp.operator === '<=' || comp.operator === '<')
    const sameSemVer = this.semver.version === comp.semver.version
    const differentDirectionsInclusive =
      (this.operator === '>=' || this.operator === '<=') &&
      (comp.operator === '>=' || comp.operator === '<=')
    const oppositeDirectionsLessThan =
      cmp(this.semver, '<', comp.semver, options) &&
      (this.operator === '>=' || this.operator === '>') &&
        (comp.operator === '<=' || comp.operator === '<')
    const oppositeDirectionsGreaterThan =
      cmp(this.semver, '>', comp.semver, options) &&
      (this.operator === '<=' || this.operator === '<') &&
        (comp.operator === '>=' || comp.operator === '>')

    return (
      sameDirectionIncreasing ||
      sameDirectionDecreasing ||
      (sameSemVer && differentDirectionsInclusive) ||
      oppositeDirectionsLessThan ||
      oppositeDirectionsGreaterThan
    )
  }
}

module.exports = Comparator

const {re, t} = require('../internal/re')
const cmp = require('../functions/cmp')
const debug = require('../internal/debug')
const SemVer = require('./semver')
const Range = require('./range')

},{"../functions/cmp":9,"../internal/debug":34,"../internal/re":36,"./range":6,"./semver":7}],6:[function(require,module,exports){
// hoisted class for cyclic dependency
class Range {
  constructor (range, options) {
    if (!options || typeof options !== 'object') {
      options = {
        loose: !!options,
        includePrerelease: false
      }
    }

    if (range instanceof Range) {
      if (
        range.loose === !!options.loose &&
        range.includePrerelease === !!options.includePrerelease
      ) {
        return range
      } else {
        return new Range(range.raw, options)
      }
    }

    if (range instanceof Comparator) {
      // just put it in the set and return
      this.raw = range.value
      this.set = [[range]]
      this.format()
      return this
    }

    this.options = options
    this.loose = !!options.loose
    this.includePrerelease = !!options.includePrerelease

    // First, split based on boolean or ||
    this.raw = range
    this.set = range
      .split(/\s*\|\|\s*/)
      // map the range to a 2d array of comparators
      .map(range => this.parseRange(range.trim()))
      // throw out any comparator lists that are empty
      // this generally means that it was not a valid range, which is allowed
      // in loose mode, but will still throw if the WHOLE range is invalid.
      .filter(c => c.length)

    if (!this.set.length) {
      throw new TypeError(`Invalid SemVer Range: ${range}`)
    }

    this.format()
  }

  format () {
    this.range = this.set
      .map((comps) => {
        return comps.join(' ').trim()
      })
      .join('||')
      .trim()
    return this.range
  }

  toString () {
    return this.range
  }

  parseRange (range) {
    const loose = this.options.loose
    range = range.trim()
    // `1.2.3 - 1.2.4` => `>=1.2.3 <=1.2.4`
    const hr = loose ? re[t.HYPHENRANGELOOSE] : re[t.HYPHENRANGE]
    range = range.replace(hr, hyphenReplace(this.options.includePrerelease))
    debug('hyphen replace', range)
    // `> 1.2.3 < 1.2.5` => `>1.2.3 <1.2.5`
    range = range.replace(re[t.COMPARATORTRIM], comparatorTrimReplace)
    debug('comparator trim', range, re[t.COMPARATORTRIM])

    // `~ 1.2.3` => `~1.2.3`
    range = range.replace(re[t.TILDETRIM], tildeTrimReplace)

    // `^ 1.2.3` => `^1.2.3`
    range = range.replace(re[t.CARETTRIM], caretTrimReplace)

    // normalize spaces
    range = range.split(/\s+/).join(' ')

    // At this point, the range is completely trimmed and
    // ready to be split into comparators.

    const compRe = loose ? re[t.COMPARATORLOOSE] : re[t.COMPARATOR]
    return range
      .split(' ')
      .map(comp => parseComparator(comp, this.options))
      .join(' ')
      .split(/\s+/)
      .map(comp => replaceGTE0(comp, this.options))
      // in loose mode, throw out any that are not valid comparators
      .filter(this.options.loose ? comp => !!comp.match(compRe) : () => true)
      .map(comp => new Comparator(comp, this.options))
  }

  intersects (range, options) {
    if (!(range instanceof Range)) {
      throw new TypeError('a Range is required')
    }

    return this.set.some((thisComparators) => {
      return (
        isSatisfiable(thisComparators, options) &&
        range.set.some((rangeComparators) => {
          return (
            isSatisfiable(rangeComparators, options) &&
            thisComparators.every((thisComparator) => {
              return rangeComparators.every((rangeComparator) => {
                return thisComparator.intersects(rangeComparator, options)
              })
            })
          )
        })
      )
    })
  }

  // if ANY of the sets match ALL of its comparators, then pass
  test (version) {
    if (!version) {
      return false
    }

    if (typeof version === 'string') {
      try {
        version = new SemVer(version, this.options)
      } catch (er) {
        return false
      }
    }

    for (let i = 0; i < this.set.length; i++) {
      if (testSet(this.set[i], version, this.options)) {
        return true
      }
    }
    return false
  }
}
module.exports = Range

const Comparator = require('./comparator')
const debug = require('../internal/debug')
const SemVer = require('./semver')
const {
  re,
  t,
  comparatorTrimReplace,
  tildeTrimReplace,
  caretTrimReplace
} = require('../internal/re')

// take a set of comparators and determine whether there
// exists a version which can satisfy it
const isSatisfiable = (comparators, options) => {
  let result = true
  const remainingComparators = comparators.slice()
  let testComparator = remainingComparators.pop()

  while (result && remainingComparators.length) {
    result = remainingComparators.every((otherComparator) => {
      return testComparator.intersects(otherComparator, options)
    })

    testComparator = remainingComparators.pop()
  }

  return result
}

// comprised of xranges, tildes, stars, and gtlt's at this point.
// already replaced the hyphen ranges
// turn into a set of JUST comparators.
const parseComparator = (comp, options) => {
  debug('comp', comp, options)
  comp = replaceCarets(comp, options)
  debug('caret', comp)
  comp = replaceTildes(comp, options)
  debug('tildes', comp)
  comp = replaceXRanges(comp, options)
  debug('xrange', comp)
  comp = replaceStars(comp, options)
  debug('stars', comp)
  return comp
}

const isX = id => !id || id.toLowerCase() === 'x' || id === '*'

// ~, ~> --> * (any, kinda silly)
// ~2, ~2.x, ~2.x.x, ~>2, ~>2.x ~>2.x.x --> >=2.0.0 <3.0.0-0
// ~2.0, ~2.0.x, ~>2.0, ~>2.0.x --> >=2.0.0 <2.1.0-0
// ~1.2, ~1.2.x, ~>1.2, ~>1.2.x --> >=1.2.0 <1.3.0-0
// ~1.2.3, ~>1.2.3 --> >=1.2.3 <1.3.0-0
// ~1.2.0, ~>1.2.0 --> >=1.2.0 <1.3.0-0
const replaceTildes = (comp, options) =>
  comp.trim().split(/\s+/).map((comp) => {
    return replaceTilde(comp, options)
  }).join(' ')

const replaceTilde = (comp, options) => {
  const r = options.loose ? re[t.TILDELOOSE] : re[t.TILDE]
  return comp.replace(r, (_, M, m, p, pr) => {
    debug('tilde', comp, _, M, m, p, pr)
    let ret

    if (isX(M)) {
      ret = ''
    } else if (isX(m)) {
      ret = `>=${M}.0.0 <${+M + 1}.0.0-0`
    } else if (isX(p)) {
      // ~1.2 == >=1.2.0 <1.3.0-0
      ret = `>=${M}.${m}.0 <${M}.${+m + 1}.0-0`
    } else if (pr) {
      debug('replaceTilde pr', pr)
      ret = `>=${M}.${m}.${p}-${pr
      } <${M}.${+m + 1}.0-0`
    } else {
      // ~1.2.3 == >=1.2.3 <1.3.0-0
      ret = `>=${M}.${m}.${p
      } <${M}.${+m + 1}.0-0`
    }

    debug('tilde return', ret)
    return ret
  })
}

// ^ --> * (any, kinda silly)
// ^2, ^2.x, ^2.x.x --> >=2.0.0 <3.0.0-0
// ^2.0, ^2.0.x --> >=2.0.0 <3.0.0-0
// ^1.2, ^1.2.x --> >=1.2.0 <2.0.0-0
// ^1.2.3 --> >=1.2.3 <2.0.0-0
// ^1.2.0 --> >=1.2.0 <2.0.0-0
const replaceCarets = (comp, options) =>
  comp.trim().split(/\s+/).map((comp) => {
    return replaceCaret(comp, options)
  }).join(' ')

const replaceCaret = (comp, options) => {
  debug('caret', comp, options)
  const r = options.loose ? re[t.CARETLOOSE] : re[t.CARET]
  const z = options.includePrerelease ? '-0' : ''
  return comp.replace(r, (_, M, m, p, pr) => {
    debug('caret', comp, _, M, m, p, pr)
    let ret

    if (isX(M)) {
      ret = ''
    } else if (isX(m)) {
      ret = `>=${M}.0.0${z} <${+M + 1}.0.0-0`
    } else if (isX(p)) {
      if (M === '0') {
        ret = `>=${M}.${m}.0${z} <${M}.${+m + 1}.0-0`
      } else {
        ret = `>=${M}.${m}.0${z} <${+M + 1}.0.0-0`
      }
    } else if (pr) {
      debug('replaceCaret pr', pr)
      if (M === '0') {
        if (m === '0') {
          ret = `>=${M}.${m}.${p}-${pr
          } <${M}.${m}.${+p + 1}-0`
        } else {
          ret = `>=${M}.${m}.${p}-${pr
          } <${M}.${+m + 1}.0-0`
        }
      } else {
        ret = `>=${M}.${m}.${p}-${pr
        } <${+M + 1}.0.0-0`
      }
    } else {
      debug('no pr')
      if (M === '0') {
        if (m === '0') {
          ret = `>=${M}.${m}.${p
          }${z} <${M}.${m}.${+p + 1}-0`
        } else {
          ret = `>=${M}.${m}.${p
          }${z} <${M}.${+m + 1}.0-0`
        }
      } else {
        ret = `>=${M}.${m}.${p
        } <${+M + 1}.0.0-0`
      }
    }

    debug('caret return', ret)
    return ret
  })
}

const replaceXRanges = (comp, options) => {
  debug('replaceXRanges', comp, options)
  return comp.split(/\s+/).map((comp) => {
    return replaceXRange(comp, options)
  }).join(' ')
}

const replaceXRange = (comp, options) => {
  comp = comp.trim()
  const r = options.loose ? re[t.XRANGELOOSE] : re[t.XRANGE]
  return comp.replace(r, (ret, gtlt, M, m, p, pr) => {
    debug('xRange', comp, ret, gtlt, M, m, p, pr)
    const xM = isX(M)
    const xm = xM || isX(m)
    const xp = xm || isX(p)
    const anyX = xp

    if (gtlt === '=' && anyX) {
      gtlt = ''
    }

    // if we're including prereleases in the match, then we need
    // to fix this to -0, the lowest possible prerelease value
    pr = options.includePrerelease ? '-0' : ''

    if (xM) {
      if (gtlt === '>' || gtlt === '<') {
        // nothing is allowed
        ret = '<0.0.0-0'
      } else {
        // nothing is forbidden
        ret = '*'
      }
    } else if (gtlt && anyX) {
      // we know patch is an x, because we have any x at all.
      // replace X with 0
      if (xm) {
        m = 0
      }
      p = 0

      if (gtlt === '>') {
        // >1 => >=2.0.0
        // >1.2 => >=1.3.0
        gtlt = '>='
        if (xm) {
          M = +M + 1
          m = 0
          p = 0
        } else {
          m = +m + 1
          p = 0
        }
      } else if (gtlt === '<=') {
        // <=0.7.x is actually <0.8.0, since any 0.7.x should
        // pass.  Similarly, <=7.x is actually <8.0.0, etc.
        gtlt = '<'
        if (xm) {
          M = +M + 1
        } else {
          m = +m + 1
        }
      }

      if (gtlt === '<')
        pr = '-0'

      ret = `${gtlt + M}.${m}.${p}${pr}`
    } else if (xm) {
      ret = `>=${M}.0.0${pr} <${+M + 1}.0.0-0`
    } else if (xp) {
      ret = `>=${M}.${m}.0${pr
      } <${M}.${+m + 1}.0-0`
    }

    debug('xRange return', ret)

    return ret
  })
}

// Because * is AND-ed with everything else in the comparator,
// and '' means "any version", just remove the *s entirely.
const replaceStars = (comp, options) => {
  debug('replaceStars', comp, options)
  // Looseness is ignored here.  star is always as loose as it gets!
  return comp.trim().replace(re[t.STAR], '')
}

const replaceGTE0 = (comp, options) => {
  debug('replaceGTE0', comp, options)
  return comp.trim()
    .replace(re[options.includePrerelease ? t.GTE0PRE : t.GTE0], '')
}

// This function is passed to string.replace(re[t.HYPHENRANGE])
// M, m, patch, prerelease, build
// 1.2 - 3.4.5 => >=1.2.0 <=3.4.5
// 1.2.3 - 3.4 => >=1.2.0 <3.5.0-0 Any 3.4.x will do
// 1.2 - 3.4 => >=1.2.0 <3.5.0-0
const hyphenReplace = incPr => ($0,
  from, fM, fm, fp, fpr, fb,
  to, tM, tm, tp, tpr, tb) => {
  if (isX(fM)) {
    from = ''
  } else if (isX(fm)) {
    from = `>=${fM}.0.0${incPr ? '-0' : ''}`
  } else if (isX(fp)) {
    from = `>=${fM}.${fm}.0${incPr ? '-0' : ''}`
  } else if (fpr) {
    from = `>=${from}`
  } else {
    from = `>=${from}${incPr ? '-0' : ''}`
  }

  if (isX(tM)) {
    to = ''
  } else if (isX(tm)) {
    to = `<${+tM + 1}.0.0-0`
  } else if (isX(tp)) {
    to = `<${tM}.${+tm + 1}.0-0`
  } else if (tpr) {
    to = `<=${tM}.${tm}.${tp}-${tpr}`
  } else if (incPr) {
    to = `<${tM}.${tm}.${+tp + 1}-0`
  } else {
    to = `<=${to}`
  }

  return (`${from} ${to}`).trim()
}

const testSet = (set, version, options) => {
  for (let i = 0; i < set.length; i++) {
    if (!set[i].test(version)) {
      return false
    }
  }

  if (version.prerelease.length && !options.includePrerelease) {
    // Find the set of versions that are allowed to have prereleases
    // For example, ^1.2.3-pr.1 desugars to >=1.2.3-pr.1 <2.0.0
    // That should allow `1.2.3-pr.2` to pass.
    // However, `1.2.4-alpha.notready` should NOT be allowed,
    // even though it's within the range set by the comparators.
    for (let i = 0; i < set.length; i++) {
      debug(set[i].semver)
      if (set[i].semver === Comparator.ANY) {
        continue
      }

      if (set[i].semver.prerelease.length > 0) {
        const allowed = set[i].semver
        if (allowed.major === version.major &&
            allowed.minor === version.minor &&
            allowed.patch === version.patch) {
          return true
        }
      }
    }

    // Version has a -pre, but it's not one of the ones we like.
    return false
  }

  return true
}

},{"../internal/debug":34,"../internal/re":36,"./comparator":5,"./semver":7}],7:[function(require,module,exports){
const debug = require('../internal/debug')
const { MAX_LENGTH, MAX_SAFE_INTEGER } = require('../internal/constants')
const { re, t } = require('../internal/re')

const { compareIdentifiers } = require('../internal/identifiers')
class SemVer {
  constructor (version, options) {
    if (!options || typeof options !== 'object') {
      options = {
        loose: !!options,
        includePrerelease: false
      }
    }
    if (version instanceof SemVer) {
      if (version.loose === !!options.loose &&
          version.includePrerelease === !!options.includePrerelease) {
        return version
      } else {
        version = version.version
      }
    } else if (typeof version !== 'string') {
      throw new TypeError(`Invalid Version: ${version}`)
    }

    if (version.length > MAX_LENGTH) {
      throw new TypeError(
        `version is longer than ${MAX_LENGTH} characters`
      )
    }

    debug('SemVer', version, options)
    this.options = options
    this.loose = !!options.loose
    // this isn't actually relevant for versions, but keep it so that we
    // don't run into trouble passing this.options around.
    this.includePrerelease = !!options.includePrerelease

    const m = version.trim().match(options.loose ? re[t.LOOSE] : re[t.FULL])

    if (!m) {
      throw new TypeError(`Invalid Version: ${version}`)
    }

    this.raw = version

    // these are actually numbers
    this.major = +m[1]
    this.minor = +m[2]
    this.patch = +m[3]

    if (this.major > MAX_SAFE_INTEGER || this.major < 0) {
      throw new TypeError('Invalid major version')
    }

    if (this.minor > MAX_SAFE_INTEGER || this.minor < 0) {
      throw new TypeError('Invalid minor version')
    }

    if (this.patch > MAX_SAFE_INTEGER || this.patch < 0) {
      throw new TypeError('Invalid patch version')
    }

    // numberify any prerelease numeric ids
    if (!m[4]) {
      this.prerelease = []
    } else {
      this.prerelease = m[4].split('.').map((id) => {
        if (/^[0-9]+$/.test(id)) {
          const num = +id
          if (num >= 0 && num < MAX_SAFE_INTEGER) {
            return num
          }
        }
        return id
      })
    }

    this.build = m[5] ? m[5].split('.') : []
    this.format()
  }

  format () {
    this.version = `${this.major}.${this.minor}.${this.patch}`
    if (this.prerelease.length) {
      this.version += `-${this.prerelease.join('.')}`
    }
    return this.version
  }

  toString () {
    return this.version
  }

  compare (other) {
    debug('SemVer.compare', this.version, this.options, other)
    if (!(other instanceof SemVer)) {
      if (typeof other === 'string' && other === this.version) {
        return 0
      }
      other = new SemVer(other, this.options)
    }

    if (other.version === this.version) {
      return 0
    }

    return this.compareMain(other) || this.comparePre(other)
  }

  compareMain (other) {
    if (!(other instanceof SemVer)) {
      other = new SemVer(other, this.options)
    }

    return (
      compareIdentifiers(this.major, other.major) ||
      compareIdentifiers(this.minor, other.minor) ||
      compareIdentifiers(this.patch, other.patch)
    )
  }

  comparePre (other) {
    if (!(other instanceof SemVer)) {
      other = new SemVer(other, this.options)
    }

    // NOT having a prerelease is > having one
    if (this.prerelease.length && !other.prerelease.length) {
      return -1
    } else if (!this.prerelease.length && other.prerelease.length) {
      return 1
    } else if (!this.prerelease.length && !other.prerelease.length) {
      return 0
    }

    let i = 0
    do {
      const a = this.prerelease[i]
      const b = other.prerelease[i]
      debug('prerelease compare', i, a, b)
      if (a === undefined && b === undefined) {
        return 0
      } else if (b === undefined) {
        return 1
      } else if (a === undefined) {
        return -1
      } else if (a === b) {
        continue
      } else {
        return compareIdentifiers(a, b)
      }
    } while (++i)
  }

  compareBuild (other) {
    if (!(other instanceof SemVer)) {
      other = new SemVer(other, this.options)
    }

    let i = 0
    do {
      const a = this.build[i]
      const b = other.build[i]
      debug('prerelease compare', i, a, b)
      if (a === undefined && b === undefined) {
        return 0
      } else if (b === undefined) {
        return 1
      } else if (a === undefined) {
        return -1
      } else if (a === b) {
        continue
      } else {
        return compareIdentifiers(a, b)
      }
    } while (++i)
  }

  // preminor will bump the version up to the next minor release, and immediately
  // down to pre-release. premajor and prepatch work the same way.
  inc (release, identifier) {
    switch (release) {
      case 'premajor':
        this.prerelease.length = 0
        this.patch = 0
        this.minor = 0
        this.major++
        this.inc('pre', identifier)
        break
      case 'preminor':
        this.prerelease.length = 0
        this.patch = 0
        this.minor++
        this.inc('pre', identifier)
        break
      case 'prepatch':
        // If this is already a prerelease, it will bump to the next version
        // drop any prereleases that might already exist, since they are not
        // relevant at this point.
        this.prerelease.length = 0
        this.inc('patch', identifier)
        this.inc('pre', identifier)
        break
      // If the input is a non-prerelease version, this acts the same as
      // prepatch.
      case 'prerelease':
        if (this.prerelease.length === 0) {
          this.inc('patch', identifier)
        }
        this.inc('pre', identifier)
        break

      case 'major':
        // If this is a pre-major version, bump up to the same major version.
        // Otherwise increment major.
        // 1.0.0-5 bumps to 1.0.0
        // 1.1.0 bumps to 2.0.0
        if (
          this.minor !== 0 ||
          this.patch !== 0 ||
          this.prerelease.length === 0
        ) {
          this.major++
        }
        this.minor = 0
        this.patch = 0
        this.prerelease = []
        break
      case 'minor':
        // If this is a pre-minor version, bump up to the same minor version.
        // Otherwise increment minor.
        // 1.2.0-5 bumps to 1.2.0
        // 1.2.1 bumps to 1.3.0
        if (this.patch !== 0 || this.prerelease.length === 0) {
          this.minor++
        }
        this.patch = 0
        this.prerelease = []
        break
      case 'patch':
        // If this is not a pre-release version, it will increment the patch.
        // If it is a pre-release it will bump up to the same patch version.
        // 1.2.0-5 patches to 1.2.0
        // 1.2.0 patches to 1.2.1
        if (this.prerelease.length === 0) {
          this.patch++
        }
        this.prerelease = []
        break
      // This probably shouldn't be used publicly.
      // 1.0.0 'pre' would become 1.0.0-0 which is the wrong direction.
      case 'pre':
        if (this.prerelease.length === 0) {
          this.prerelease = [0]
        } else {
          let i = this.prerelease.length
          while (--i >= 0) {
            if (typeof this.prerelease[i] === 'number') {
              this.prerelease[i]++
              i = -2
            }
          }
          if (i === -1) {
            // didn't increment anything
            this.prerelease.push(0)
          }
        }
        if (identifier) {
          // 1.2.0-beta.1 bumps to 1.2.0-beta.2,
          // 1.2.0-beta.fooblz or 1.2.0-beta bumps to 1.2.0-beta.0
          if (this.prerelease[0] === identifier) {
            if (isNaN(this.prerelease[1])) {
              this.prerelease = [identifier, 0]
            }
          } else {
            this.prerelease = [identifier, 0]
          }
        }
        break

      default:
        throw new Error(`invalid increment argument: ${release}`)
    }
    this.format()
    this.raw = this.version
    return this
  }
}

module.exports = SemVer

},{"../internal/constants":33,"../internal/debug":34,"../internal/identifiers":35,"../internal/re":36}],8:[function(require,module,exports){
const parse = require('./parse')
const clean = (version, options) => {
  const s = parse(version.trim().replace(/^[=v]+/, ''), options)
  return s ? s.version : null
}
module.exports = clean

},{"./parse":24}],9:[function(require,module,exports){
const eq = require('./eq')
const neq = require('./neq')
const gt = require('./gt')
const gte = require('./gte')
const lt = require('./lt')
const lte = require('./lte')

const cmp = (a, op, b, loose) => {
  switch (op) {
    case '===':
      if (typeof a === 'object')
        a = a.version
      if (typeof b === 'object')
        b = b.version
      return a === b

    case '!==':
      if (typeof a === 'object')
        a = a.version
      if (typeof b === 'object')
        b = b.version
      return a !== b

    case '':
    case '=':
    case '==':
      return eq(a, b, loose)

    case '!=':
      return neq(a, b, loose)

    case '>':
      return gt(a, b, loose)

    case '>=':
      return gte(a, b, loose)

    case '<':
      return lt(a, b, loose)

    case '<=':
      return lte(a, b, loose)

    default:
      throw new TypeError(`Invalid operator: ${op}`)
  }
}
module.exports = cmp

},{"./eq":15,"./gt":16,"./gte":17,"./lt":19,"./lte":20,"./neq":23}],10:[function(require,module,exports){
const SemVer = require('../classes/semver')
const parse = require('./parse')
const {re, t} = require('../internal/re')

const coerce = (version, options) => {
  if (version instanceof SemVer) {
    return version
  }

  if (typeof version === 'number') {
    version = String(version)
  }

  if (typeof version !== 'string') {
    return null
  }

  options = options || {}

  let match = null
  if (!options.rtl) {
    match = version.match(re[t.COERCE])
  } else {
    // Find the right-most coercible string that does not share
    // a terminus with a more left-ward coercible string.
    // Eg, '1.2.3.4' wants to coerce '2.3.4', not '3.4' or '4'
    //
    // Walk through the string checking with a /g regexp
    // Manually set the index so as to pick up overlapping matches.
    // Stop when we get a match that ends at the string end, since no
    // coercible string can be more right-ward without the same terminus.
    let next
    while ((next = re[t.COERCERTL].exec(version)) &&
        (!match || match.index + match[0].length !== version.length)
    ) {
      if (!match ||
            next.index + next[0].length !== match.index + match[0].length) {
        match = next
      }
      re[t.COERCERTL].lastIndex = next.index + next[1].length + next[2].length
    }
    // leave it in a clean state
    re[t.COERCERTL].lastIndex = -1
  }

  if (match === null)
    return null

  return parse(`${match[2]}.${match[3] || '0'}.${match[4] || '0'}`, options)
}
module.exports = coerce

},{"../classes/semver":7,"../internal/re":36,"./parse":24}],11:[function(require,module,exports){
const SemVer = require('../classes/semver')
const compareBuild = (a, b, loose) => {
  const versionA = new SemVer(a, loose)
  const versionB = new SemVer(b, loose)
  return versionA.compare(versionB) || versionA.compareBuild(versionB)
}
module.exports = compareBuild

},{"../classes/semver":7}],12:[function(require,module,exports){
const compare = require('./compare')
const compareLoose = (a, b) => compare(a, b, true)
module.exports = compareLoose

},{"./compare":13}],13:[function(require,module,exports){
const SemVer = require('../classes/semver')
const compare = (a, b, loose) =>
  new SemVer(a, loose).compare(new SemVer(b, loose))

module.exports = compare

},{"../classes/semver":7}],14:[function(require,module,exports){
const parse = require('./parse')
const eq = require('./eq')

const diff = (version1, version2) => {
  if (eq(version1, version2)) {
    return null
  } else {
    const v1 = parse(version1)
    const v2 = parse(version2)
    const hasPre = v1.prerelease.length || v2.prerelease.length
    const prefix = hasPre ? 'pre' : ''
    const defaultResult = hasPre ? 'prerelease' : ''
    for (const key in v1) {
      if (key === 'major' || key === 'minor' || key === 'patch') {
        if (v1[key] !== v2[key]) {
          return prefix + key
        }
      }
    }
    return defaultResult // may be undefined
  }
}
module.exports = diff

},{"./eq":15,"./parse":24}],15:[function(require,module,exports){
const compare = require('./compare')
const eq = (a, b, loose) => compare(a, b, loose) === 0
module.exports = eq

},{"./compare":13}],16:[function(require,module,exports){
const compare = require('./compare')
const gt = (a, b, loose) => compare(a, b, loose) > 0
module.exports = gt

},{"./compare":13}],17:[function(require,module,exports){
const compare = require('./compare')
const gte = (a, b, loose) => compare(a, b, loose) >= 0
module.exports = gte

},{"./compare":13}],18:[function(require,module,exports){
const SemVer = require('../classes/semver')

const inc = (version, release, options, identifier) => {
  if (typeof (options) === 'string') {
    identifier = options
    options = undefined
  }

  try {
    return new SemVer(version, options).inc(release, identifier).version
  } catch (er) {
    return null
  }
}
module.exports = inc

},{"../classes/semver":7}],19:[function(require,module,exports){
const compare = require('./compare')
const lt = (a, b, loose) => compare(a, b, loose) < 0
module.exports = lt

},{"./compare":13}],20:[function(require,module,exports){
const compare = require('./compare')
const lte = (a, b, loose) => compare(a, b, loose) <= 0
module.exports = lte

},{"./compare":13}],21:[function(require,module,exports){
const SemVer = require('../classes/semver')
const major = (a, loose) => new SemVer(a, loose).major
module.exports = major

},{"../classes/semver":7}],22:[function(require,module,exports){
const SemVer = require('../classes/semver')
const minor = (a, loose) => new SemVer(a, loose).minor
module.exports = minor

},{"../classes/semver":7}],23:[function(require,module,exports){
const compare = require('./compare')
const neq = (a, b, loose) => compare(a, b, loose) !== 0
module.exports = neq

},{"./compare":13}],24:[function(require,module,exports){
const {MAX_LENGTH} = require('../internal/constants')
const { re, t } = require('../internal/re')
const SemVer = require('../classes/semver')

const parse = (version, options) => {
  if (!options || typeof options !== 'object') {
    options = {
      loose: !!options,
      includePrerelease: false
    }
  }

  if (version instanceof SemVer) {
    return version
  }

  if (typeof version !== 'string') {
    return null
  }

  if (version.length > MAX_LENGTH) {
    return null
  }

  const r = options.loose ? re[t.LOOSE] : re[t.FULL]
  if (!r.test(version)) {
    return null
  }

  try {
    return new SemVer(version, options)
  } catch (er) {
    return null
  }
}

module.exports = parse

},{"../classes/semver":7,"../internal/constants":33,"../internal/re":36}],25:[function(require,module,exports){
const SemVer = require('../classes/semver')
const patch = (a, loose) => new SemVer(a, loose).patch
module.exports = patch

},{"../classes/semver":7}],26:[function(require,module,exports){
const parse = require('./parse')
const prerelease = (version, options) => {
  const parsed = parse(version, options)
  return (parsed && parsed.prerelease.length) ? parsed.prerelease : null
}
module.exports = prerelease

},{"./parse":24}],27:[function(require,module,exports){
const compare = require('./compare')
const rcompare = (a, b, loose) => compare(b, a, loose)
module.exports = rcompare

},{"./compare":13}],28:[function(require,module,exports){
const compareBuild = require('./compare-build')
const rsort = (list, loose) => list.sort((a, b) => compareBuild(b, a, loose))
module.exports = rsort

},{"./compare-build":11}],29:[function(require,module,exports){
const Range = require('../classes/range')
const satisfies = (version, range, options) => {
  try {
    range = new Range(range, options)
  } catch (er) {
    return false
  }
  return range.test(version)
}
module.exports = satisfies

},{"../classes/range":6}],30:[function(require,module,exports){
const compareBuild = require('./compare-build')
const sort = (list, loose) => list.sort((a, b) => compareBuild(a, b, loose))
module.exports = sort

},{"./compare-build":11}],31:[function(require,module,exports){
const parse = require('./parse')
const valid = (version, options) => {
  const v = parse(version, options)
  return v ? v.version : null
}
module.exports = valid

},{"./parse":24}],32:[function(require,module,exports){
// just pre-load all the stuff that index.js lazily exports
const internalRe = require('./internal/re')
module.exports = {
  re: internalRe.re,
  src: internalRe.src,
  tokens: internalRe.t,
  SEMVER_SPEC_VERSION: require('./internal/constants').SEMVER_SPEC_VERSION,
  SemVer: require('./classes/semver'),
  compareIdentifiers: require('./internal/identifiers').compareIdentifiers,
  rcompareIdentifiers: require('./internal/identifiers').rcompareIdentifiers,
  parse: require('./functions/parse'),
  valid: require('./functions/valid'),
  clean: require('./functions/clean'),
  inc: require('./functions/inc'),
  diff: require('./functions/diff'),
  major: require('./functions/major'),
  minor: require('./functions/minor'),
  patch: require('./functions/patch'),
  prerelease: require('./functions/prerelease'),
  compare: require('./functions/compare'),
  rcompare: require('./functions/rcompare'),
  compareLoose: require('./functions/compare-loose'),
  compareBuild: require('./functions/compare-build'),
  sort: require('./functions/sort'),
  rsort: require('./functions/rsort'),
  gt: require('./functions/gt'),
  lt: require('./functions/lt'),
  eq: require('./functions/eq'),
  neq: require('./functions/neq'),
  gte: require('./functions/gte'),
  lte: require('./functions/lte'),
  cmp: require('./functions/cmp'),
  coerce: require('./functions/coerce'),
  Comparator: require('./classes/comparator'),
  Range: require('./classes/range'),
  satisfies: require('./functions/satisfies'),
  toComparators: require('./ranges/to-comparators'),
  maxSatisfying: require('./ranges/max-satisfying'),
  minSatisfying: require('./ranges/min-satisfying'),
  minVersion: require('./ranges/min-version'),
  validRange: require('./ranges/valid'),
  outside: require('./ranges/outside'),
  gtr: require('./ranges/gtr'),
  ltr: require('./ranges/ltr'),
  intersects: require('./ranges/intersects'),
  simplifyRange: require('./ranges/simplify'),
  subset: require('./ranges/subset'),
}

},{"./classes/comparator":5,"./classes/range":6,"./classes/semver":7,"./functions/clean":8,"./functions/cmp":9,"./functions/coerce":10,"./functions/compare":13,"./functions/compare-build":11,"./functions/compare-loose":12,"./functions/diff":14,"./functions/eq":15,"./functions/gt":16,"./functions/gte":17,"./functions/inc":18,"./functions/lt":19,"./functions/lte":20,"./functions/major":21,"./functions/minor":22,"./functions/neq":23,"./functions/parse":24,"./functions/patch":25,"./functions/prerelease":26,"./functions/rcompare":27,"./functions/rsort":28,"./functions/satisfies":29,"./functions/sort":30,"./functions/valid":31,"./internal/constants":33,"./internal/identifiers":35,"./internal/re":36,"./ranges/gtr":37,"./ranges/intersects":38,"./ranges/ltr":39,"./ranges/max-satisfying":40,"./ranges/min-satisfying":41,"./ranges/min-version":42,"./ranges/outside":43,"./ranges/simplify":44,"./ranges/subset":45,"./ranges/to-comparators":46,"./ranges/valid":47}],33:[function(require,module,exports){
// Note: this is the semver.org version of the spec that it implements
// Not necessarily the package version of this code.
const SEMVER_SPEC_VERSION = '2.0.0'

const MAX_LENGTH = 256
const MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER ||
  /* istanbul ignore next */ 9007199254740991

// Max safe segment length for coercion.
const MAX_SAFE_COMPONENT_LENGTH = 16

module.exports = {
  SEMVER_SPEC_VERSION,
  MAX_LENGTH,
  MAX_SAFE_INTEGER,
  MAX_SAFE_COMPONENT_LENGTH
}

},{}],34:[function(require,module,exports){
(function (process){
const debug = (
  typeof process === 'object' &&
  process.env &&
  process.env.NODE_DEBUG &&
  /\bsemver\b/i.test(process.env.NODE_DEBUG)
) ? (...args) => console.error('SEMVER', ...args)
  : () => {}

module.exports = debug

}).call(this,require('_process'))
},{"_process":4}],35:[function(require,module,exports){
const numeric = /^[0-9]+$/
const compareIdentifiers = (a, b) => {
  const anum = numeric.test(a)
  const bnum = numeric.test(b)

  if (anum && bnum) {
    a = +a
    b = +b
  }

  return a === b ? 0
    : (anum && !bnum) ? -1
    : (bnum && !anum) ? 1
    : a < b ? -1
    : 1
}

const rcompareIdentifiers = (a, b) => compareIdentifiers(b, a)

module.exports = {
  compareIdentifiers,
  rcompareIdentifiers
}

},{}],36:[function(require,module,exports){
const { MAX_SAFE_COMPONENT_LENGTH } = require('./constants')
const debug = require('./debug')
exports = module.exports = {}

// The actual regexps go on exports.re
const re = exports.re = []
const src = exports.src = []
const t = exports.t = {}
let R = 0

const createToken = (name, value, isGlobal) => {
  const index = R++
  debug(index, value)
  t[name] = index
  src[index] = value
  re[index] = new RegExp(value, isGlobal ? 'g' : undefined)
}

// The following Regular Expressions can be used for tokenizing,
// validating, and parsing SemVer version strings.

// ## Numeric Identifier
// A single `0`, or a non-zero digit followed by zero or more digits.

createToken('NUMERICIDENTIFIER', '0|[1-9]\\d*')
createToken('NUMERICIDENTIFIERLOOSE', '[0-9]+')

// ## Non-numeric Identifier
// Zero or more digits, followed by a letter or hyphen, and then zero or
// more letters, digits, or hyphens.

createToken('NONNUMERICIDENTIFIER', '\\d*[a-zA-Z-][a-zA-Z0-9-]*')

// ## Main Version
// Three dot-separated numeric identifiers.

createToken('MAINVERSION', `(${src[t.NUMERICIDENTIFIER]})\\.` +
                   `(${src[t.NUMERICIDENTIFIER]})\\.` +
                   `(${src[t.NUMERICIDENTIFIER]})`)

createToken('MAINVERSIONLOOSE', `(${src[t.NUMERICIDENTIFIERLOOSE]})\\.` +
                        `(${src[t.NUMERICIDENTIFIERLOOSE]})\\.` +
                        `(${src[t.NUMERICIDENTIFIERLOOSE]})`)

// ## Pre-release Version Identifier
// A numeric identifier, or a non-numeric identifier.

createToken('PRERELEASEIDENTIFIER', `(?:${src[t.NUMERICIDENTIFIER]
}|${src[t.NONNUMERICIDENTIFIER]})`)

createToken('PRERELEASEIDENTIFIERLOOSE', `(?:${src[t.NUMERICIDENTIFIERLOOSE]
}|${src[t.NONNUMERICIDENTIFIER]})`)

// ## Pre-release Version
// Hyphen, followed by one or more dot-separated pre-release version
// identifiers.

createToken('PRERELEASE', `(?:-(${src[t.PRERELEASEIDENTIFIER]
}(?:\\.${src[t.PRERELEASEIDENTIFIER]})*))`)

createToken('PRERELEASELOOSE', `(?:-?(${src[t.PRERELEASEIDENTIFIERLOOSE]
}(?:\\.${src[t.PRERELEASEIDENTIFIERLOOSE]})*))`)

// ## Build Metadata Identifier
// Any combination of digits, letters, or hyphens.

createToken('BUILDIDENTIFIER', '[0-9A-Za-z-]+')

// ## Build Metadata
// Plus sign, followed by one or more period-separated build metadata
// identifiers.

createToken('BUILD', `(?:\\+(${src[t.BUILDIDENTIFIER]
}(?:\\.${src[t.BUILDIDENTIFIER]})*))`)

// ## Full Version String
// A main version, followed optionally by a pre-release version and
// build metadata.

// Note that the only major, minor, patch, and pre-release sections of
// the version string are capturing groups.  The build metadata is not a
// capturing group, because it should not ever be used in version
// comparison.

createToken('FULLPLAIN', `v?${src[t.MAINVERSION]
}${src[t.PRERELEASE]}?${
  src[t.BUILD]}?`)

createToken('FULL', `^${src[t.FULLPLAIN]}$`)

// like full, but allows v1.2.3 and =1.2.3, which people do sometimes.
// also, 1.0.0alpha1 (prerelease without the hyphen) which is pretty
// common in the npm registry.
createToken('LOOSEPLAIN', `[v=\\s]*${src[t.MAINVERSIONLOOSE]
}${src[t.PRERELEASELOOSE]}?${
  src[t.BUILD]}?`)

createToken('LOOSE', `^${src[t.LOOSEPLAIN]}$`)

createToken('GTLT', '((?:<|>)?=?)')

// Something like "2.*" or "1.2.x".
// Note that "x.x" is a valid xRange identifer, meaning "any version"
// Only the first item is strictly required.
createToken('XRANGEIDENTIFIERLOOSE', `${src[t.NUMERICIDENTIFIERLOOSE]}|x|X|\\*`)
createToken('XRANGEIDENTIFIER', `${src[t.NUMERICIDENTIFIER]}|x|X|\\*`)

createToken('XRANGEPLAIN', `[v=\\s]*(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:\\.(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:\\.(${src[t.XRANGEIDENTIFIER]})` +
                   `(?:${src[t.PRERELEASE]})?${
                     src[t.BUILD]}?` +
                   `)?)?`)

createToken('XRANGEPLAINLOOSE', `[v=\\s]*(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:\\.(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:\\.(${src[t.XRANGEIDENTIFIERLOOSE]})` +
                        `(?:${src[t.PRERELEASELOOSE]})?${
                          src[t.BUILD]}?` +
                        `)?)?`)

createToken('XRANGE', `^${src[t.GTLT]}\\s*${src[t.XRANGEPLAIN]}$`)
createToken('XRANGELOOSE', `^${src[t.GTLT]}\\s*${src[t.XRANGEPLAINLOOSE]}$`)

// Coercion.
// Extract anything that could conceivably be a part of a valid semver
createToken('COERCE', `${'(^|[^\\d])' +
              '(\\d{1,'}${MAX_SAFE_COMPONENT_LENGTH}})` +
              `(?:\\.(\\d{1,${MAX_SAFE_COMPONENT_LENGTH}}))?` +
              `(?:\\.(\\d{1,${MAX_SAFE_COMPONENT_LENGTH}}))?` +
              `(?:$|[^\\d])`)
createToken('COERCERTL', src[t.COERCE], true)

// Tilde ranges.
// Meaning is "reasonably at or greater than"
createToken('LONETILDE', '(?:~>?)')

createToken('TILDETRIM', `(\\s*)${src[t.LONETILDE]}\\s+`, true)
exports.tildeTrimReplace = '$1~'

createToken('TILDE', `^${src[t.LONETILDE]}${src[t.XRANGEPLAIN]}$`)
createToken('TILDELOOSE', `^${src[t.LONETILDE]}${src[t.XRANGEPLAINLOOSE]}$`)

// Caret ranges.
// Meaning is "at least and backwards compatible with"
createToken('LONECARET', '(?:\\^)')

createToken('CARETTRIM', `(\\s*)${src[t.LONECARET]}\\s+`, true)
exports.caretTrimReplace = '$1^'

createToken('CARET', `^${src[t.LONECARET]}${src[t.XRANGEPLAIN]}$`)
createToken('CARETLOOSE', `^${src[t.LONECARET]}${src[t.XRANGEPLAINLOOSE]}$`)

// A simple gt/lt/eq thing, or just "" to indicate "any version"
createToken('COMPARATORLOOSE', `^${src[t.GTLT]}\\s*(${src[t.LOOSEPLAIN]})$|^$`)
createToken('COMPARATOR', `^${src[t.GTLT]}\\s*(${src[t.FULLPLAIN]})$|^$`)

// An expression to strip any whitespace between the gtlt and the thing
// it modifies, so that `> 1.2.3` ==> `>1.2.3`
createToken('COMPARATORTRIM', `(\\s*)${src[t.GTLT]
}\\s*(${src[t.LOOSEPLAIN]}|${src[t.XRANGEPLAIN]})`, true)
exports.comparatorTrimReplace = '$1$2$3'

// Something like `1.2.3 - 1.2.4`
// Note that these all use the loose form, because they'll be
// checked against either the strict or loose comparator form
// later.
createToken('HYPHENRANGE', `^\\s*(${src[t.XRANGEPLAIN]})` +
                   `\\s+-\\s+` +
                   `(${src[t.XRANGEPLAIN]})` +
                   `\\s*$`)

createToken('HYPHENRANGELOOSE', `^\\s*(${src[t.XRANGEPLAINLOOSE]})` +
                        `\\s+-\\s+` +
                        `(${src[t.XRANGEPLAINLOOSE]})` +
                        `\\s*$`)

// Star ranges basically just allow anything at all.
createToken('STAR', '(<|>)?=?\\s*\\*')
// >=0.0.0 is like a star
createToken('GTE0', '^\\s*>=\\s*0\.0\.0\\s*$')
createToken('GTE0PRE', '^\\s*>=\\s*0\.0\.0-0\\s*$')

},{"./constants":33,"./debug":34}],37:[function(require,module,exports){
// Determine if version is greater than all the versions possible in the range.
const outside = require('./outside')
const gtr = (version, range, options) => outside(version, range, '>', options)
module.exports = gtr

},{"./outside":43}],38:[function(require,module,exports){
const Range = require('../classes/range')
const intersects = (r1, r2, options) => {
  r1 = new Range(r1, options)
  r2 = new Range(r2, options)
  return r1.intersects(r2)
}
module.exports = intersects

},{"../classes/range":6}],39:[function(require,module,exports){
const outside = require('./outside')
// Determine if version is less than all the versions possible in the range
const ltr = (version, range, options) => outside(version, range, '<', options)
module.exports = ltr

},{"./outside":43}],40:[function(require,module,exports){
const SemVer = require('../classes/semver')
const Range = require('../classes/range')

const maxSatisfying = (versions, range, options) => {
  let max = null
  let maxSV = null
  let rangeObj = null
  try {
    rangeObj = new Range(range, options)
  } catch (er) {
    return null
  }
  versions.forEach((v) => {
    if (rangeObj.test(v)) {
      // satisfies(v, range, options)
      if (!max || maxSV.compare(v) === -1) {
        // compare(max, v, true)
        max = v
        maxSV = new SemVer(max, options)
      }
    }
  })
  return max
}
module.exports = maxSatisfying

},{"../classes/range":6,"../classes/semver":7}],41:[function(require,module,exports){
const SemVer = require('../classes/semver')
const Range = require('../classes/range')
const minSatisfying = (versions, range, options) => {
  let min = null
  let minSV = null
  let rangeObj = null
  try {
    rangeObj = new Range(range, options)
  } catch (er) {
    return null
  }
  versions.forEach((v) => {
    if (rangeObj.test(v)) {
      // satisfies(v, range, options)
      if (!min || minSV.compare(v) === 1) {
        // compare(min, v, true)
        min = v
        minSV = new SemVer(min, options)
      }
    }
  })
  return min
}
module.exports = minSatisfying

},{"../classes/range":6,"../classes/semver":7}],42:[function(require,module,exports){
const SemVer = require('../classes/semver')
const Range = require('../classes/range')
const gt = require('../functions/gt')

const minVersion = (range, loose) => {
  range = new Range(range, loose)

  let minver = new SemVer('0.0.0')
  if (range.test(minver)) {
    return minver
  }

  minver = new SemVer('0.0.0-0')
  if (range.test(minver)) {
    return minver
  }

  minver = null
  for (let i = 0; i < range.set.length; ++i) {
    const comparators = range.set[i]

    comparators.forEach((comparator) => {
      // Clone to avoid manipulating the comparator's semver object.
      const compver = new SemVer(comparator.semver.version)
      switch (comparator.operator) {
        case '>':
          if (compver.prerelease.length === 0) {
            compver.patch++
          } else {
            compver.prerelease.push(0)
          }
          compver.raw = compver.format()
          /* fallthrough */
        case '':
        case '>=':
          if (!minver || gt(minver, compver)) {
            minver = compver
          }
          break
        case '<':
        case '<=':
          /* Ignore maximum versions */
          break
        /* istanbul ignore next */
        default:
          throw new Error(`Unexpected operation: ${comparator.operator}`)
      }
    })
  }

  if (minver && range.test(minver)) {
    return minver
  }

  return null
}
module.exports = minVersion

},{"../classes/range":6,"../classes/semver":7,"../functions/gt":16}],43:[function(require,module,exports){
const SemVer = require('../classes/semver')
const Comparator = require('../classes/comparator')
const {ANY} = Comparator
const Range = require('../classes/range')
const satisfies = require('../functions/satisfies')
const gt = require('../functions/gt')
const lt = require('../functions/lt')
const lte = require('../functions/lte')
const gte = require('../functions/gte')

const outside = (version, range, hilo, options) => {
  version = new SemVer(version, options)
  range = new Range(range, options)

  let gtfn, ltefn, ltfn, comp, ecomp
  switch (hilo) {
    case '>':
      gtfn = gt
      ltefn = lte
      ltfn = lt
      comp = '>'
      ecomp = '>='
      break
    case '<':
      gtfn = lt
      ltefn = gte
      ltfn = gt
      comp = '<'
      ecomp = '<='
      break
    default:
      throw new TypeError('Must provide a hilo val of "<" or ">"')
  }

  // If it satisifes the range it is not outside
  if (satisfies(version, range, options)) {
    return false
  }

  // From now on, variable terms are as if we're in "gtr" mode.
  // but note that everything is flipped for the "ltr" function.

  for (let i = 0; i < range.set.length; ++i) {
    const comparators = range.set[i]

    let high = null
    let low = null

    comparators.forEach((comparator) => {
      if (comparator.semver === ANY) {
        comparator = new Comparator('>=0.0.0')
      }
      high = high || comparator
      low = low || comparator
      if (gtfn(comparator.semver, high.semver, options)) {
        high = comparator
      } else if (ltfn(comparator.semver, low.semver, options)) {
        low = comparator
      }
    })

    // If the edge version comparator has a operator then our version
    // isn't outside it
    if (high.operator === comp || high.operator === ecomp) {
      return false
    }

    // If the lowest version comparator has an operator and our version
    // is less than it then it isn't higher than the range
    if ((!low.operator || low.operator === comp) &&
        ltefn(version, low.semver)) {
      return false
    } else if (low.operator === ecomp && ltfn(version, low.semver)) {
      return false
    }
  }
  return true
}

module.exports = outside

},{"../classes/comparator":5,"../classes/range":6,"../classes/semver":7,"../functions/gt":16,"../functions/gte":17,"../functions/lt":19,"../functions/lte":20,"../functions/satisfies":29}],44:[function(require,module,exports){
// given a set of versions and a range, create a "simplified" range
// that includes the same versions that the original range does
// If the original range is shorter than the simplified one, return that.
const satisfies = require('../functions/satisfies.js')
const compare = require('../functions/compare.js')
module.exports = (versions, range, options) => {
  const set = []
  let min = null
  let prev = null
  const v = versions.sort((a, b) => compare(a, b, options))
  for (const version of v) {
    const included = satisfies(version, range, options)
    if (included) {
      prev = version
      if (!min)
        min = version
    } else {
      if (prev) {
        set.push([min, prev])
      }
      prev = null
      min = null
    }
  }
  if (min)
    set.push([min, null])

  const ranges = []
  for (const [min, max] of set) {
    if (min === max)
      ranges.push(min)
    else if (!max && min === v[0])
      ranges.push('*')
    else if (!max)
      ranges.push(`>=${min}`)
    else if (min === v[0])
      ranges.push(`<=${max}`)
    else
      ranges.push(`${min} - ${max}`)
  }
  const simplified = ranges.join(' || ')
  const original = typeof range.raw === 'string' ? range.raw : String(range)
  return simplified.length < original.length ? simplified : range
}

},{"../functions/compare.js":13,"../functions/satisfies.js":29}],45:[function(require,module,exports){
const Range = require('../classes/range.js')
const { ANY } = require('../classes/comparator.js')
const satisfies = require('../functions/satisfies.js')
const compare = require('../functions/compare.js')

// Complex range `r1 || r2 || ...` is a subset of `R1 || R2 || ...` iff:
// - Every simple range `r1, r2, ...` is a subset of some `R1, R2, ...`
//
// Simple range `c1 c2 ...` is a subset of simple range `C1 C2 ...` iff:
// - If c is only the ANY comparator
//   - If C is only the ANY comparator, return true
//   - Else return false
// - Let EQ be the set of = comparators in c
// - If EQ is more than one, return true (null set)
// - Let GT be the highest > or >= comparator in c
// - Let LT be the lowest < or <= comparator in c
// - If GT and LT, and GT.semver > LT.semver, return true (null set)
// - If EQ
//   - If GT, and EQ does not satisfy GT, return true (null set)
//   - If LT, and EQ does not satisfy LT, return true (null set)
//   - If EQ satisfies every C, return true
//   - Else return false
// - If GT
//   - If GT is lower than any > or >= comp in C, return false
//   - If GT is >=, and GT.semver does not satisfy every C, return false
// - If LT
//   - If LT.semver is greater than that of any > comp in C, return false
//   - If LT is <=, and LT.semver does not satisfy every C, return false
// - If any C is a = range, and GT or LT are set, return false
// - Else return true

const subset = (sub, dom, options) => {
  sub = new Range(sub, options)
  dom = new Range(dom, options)
  let sawNonNull = false

  OUTER: for (const simpleSub of sub.set) {
    for (const simpleDom of dom.set) {
      const isSub = simpleSubset(simpleSub, simpleDom, options)
      sawNonNull = sawNonNull || isSub !== null
      if (isSub)
        continue OUTER
    }
    // the null set is a subset of everything, but null simple ranges in
    // a complex range should be ignored.  so if we saw a non-null range,
    // then we know this isn't a subset, but if EVERY simple range was null,
    // then it is a subset.
    if (sawNonNull)
      return false
  }
  return true
}

const simpleSubset = (sub, dom, options) => {
  if (sub.length === 1 && sub[0].semver === ANY)
    return dom.length === 1 && dom[0].semver === ANY

  const eqSet = new Set()
  let gt, lt
  for (const c of sub) {
    if (c.operator === '>' || c.operator === '>=')
      gt = higherGT(gt, c, options)
    else if (c.operator === '<' || c.operator === '<=')
      lt = lowerLT(lt, c, options)
    else
      eqSet.add(c.semver)
  }

  if (eqSet.size > 1)
    return null

  let gtltComp
  if (gt && lt) {
    gtltComp = compare(gt.semver, lt.semver, options)
    if (gtltComp > 0)
      return null
    else if (gtltComp === 0 && (gt.operator !== '>=' || lt.operator !== '<='))
      return null
  }

  // will iterate one or zero times
  for (const eq of eqSet) {
    if (gt && !satisfies(eq, String(gt), options))
      return null

    if (lt && !satisfies(eq, String(lt), options))
      return null

    for (const c of dom) {
      if (!satisfies(eq, String(c), options))
        return false
    }
    return true
  }

  let higher, lower
  let hasDomLT, hasDomGT
  for (const c of dom) {
    hasDomGT = hasDomGT || c.operator === '>' || c.operator === '>='
    hasDomLT = hasDomLT || c.operator === '<' || c.operator === '<='
    if (gt) {
      if (c.operator === '>' || c.operator === '>=') {
        higher = higherGT(gt, c, options)
        if (higher === c)
          return false
      } else if (gt.operator === '>=' && !satisfies(gt.semver, String(c), options))
        return false
    }
    if (lt) {
      if (c.operator === '<' || c.operator === '<=') {
        lower = lowerLT(lt, c, options)
        if (lower === c)
          return false
      } else if (lt.operator === '<=' && !satisfies(lt.semver, String(c), options))
        return false
    }
    if (!c.operator && (lt || gt) && gtltComp !== 0)
      return false
  }

  // if there was a < or >, and nothing in the dom, then must be false
  // UNLESS it was limited by another range in the other direction.
  // Eg, >1.0.0 <1.0.1 is still a subset of <2.0.0
  if (gt && hasDomLT && !lt && gtltComp !== 0)
    return false

  if (lt && hasDomGT && !gt && gtltComp !== 0)
    return false

  return true
}

// >=1.2.3 is lower than >1.2.3
const higherGT = (a, b, options) => {
  if (!a)
    return b
  const comp = compare(a.semver, b.semver, options)
  return comp > 0 ? a
    : comp < 0 ? b
    : b.operator === '>' && a.operator === '>=' ? b
    : a
}

// <=1.2.3 is higher than <1.2.3
const lowerLT = (a, b, options) => {
  if (!a)
    return b
  const comp = compare(a.semver, b.semver, options)
  return comp < 0 ? a
    : comp > 0 ? b
    : b.operator === '<' && a.operator === '<=' ? b
    : a
}

module.exports = subset

},{"../classes/comparator.js":5,"../classes/range.js":6,"../functions/compare.js":13,"../functions/satisfies.js":29}],46:[function(require,module,exports){
const Range = require('../classes/range')

// Mostly just for testing and legacy API reasons
const toComparators = (range, options) =>
  new Range(range, options).set
    .map(comp => comp.map(c => c.value).join(' ').trim().split(' '))

module.exports = toComparators

},{"../classes/range":6}],47:[function(require,module,exports){
const Range = require('../classes/range')
const validRange = (range, options) => {
  try {
    // Return '*' instead of '' so that truthiness works.
    // This will throw if it's invalid anyway
    return new Range(range, options).range || '*'
  } catch (er) {
    return null
  }
}
module.exports = validRange

},{"../classes/range":6}],48:[function(require,module,exports){
module.exports = {
    name: 'kaleido_scopes',
    plotly: require('./plotly/render'),
    // Additional plugins go here
}

},{"./plotly/render":53}],49:[function(require,module,exports){
module.exports = {
  contentFormat: {
    png: 'image/png',
    jpeg: 'image/jpeg',
    webp: 'image/webp',
    svg: 'image/svg+xml',
    pdf: 'application/pdf',
    eps: 'application/postscript',
    emf: 'image/emf',
    json: 'application/json'
  },

  statusMsg: {
    400: 'invalid or malformed request syntax',
    406: 'requested format is not acceptable',
    525: 'plotly.js error',
    526: 'plotly.js version 1.11.0 or up required',
    527: 'plotly.js version 1.53.0 or up required for exporting to `json`',
    530: 'image conversion error'
  },

  dflt: {
    format: 'png',
    scale: 1,
    width: 700,
    height: 500
  },

  // only used in render for plotly.js < v1.30.0
  imgPrefix: {
    base64: /^data:image\/\w+;base64,/,
    svg: /^data:image\/svg\+xml,/
  },

  mathJaxConfigQuery: '?config=TeX-AMS-MML_SVG',

  // time [in ms] after which printToPDF errors when image isn't loaded
  pdfPageLoadImgTimeout: 20000
}

},{}],50:[function(require,module,exports){
function isNonEmptyString (v) {
  return typeof v === 'string' && v.length > 0
}

module.exports = isNonEmptyString

},{}],51:[function(require,module,exports){
const isNumeric = require('fast-isnumeric')

function isPositiveNumeric (v) {
  return isNumeric(v) && v > 0
}

module.exports = isPositiveNumeric

},{"fast-isnumeric":1}],52:[function(require,module,exports){
const cst = require('./constants')
const isPlainObj = require('is-plain-obj')
const isPositiveNumeric = require('./is-positive-numeric')
const isNonEmptyString = require('./is-non-empty-string')

const contentFormat = cst.contentFormat
const ACCEPT_HEADER = Object.keys(contentFormat).reduce(function (obj, key) {
  obj[ contentFormat[key] ] = key
  return obj
}, {})

/** plotly-graph parse
 *
 * @param {object} body : JSON-parsed request body
 *  - figure
 *  - format
 *  - scale (only for plotly.js v.1.31.0 and up)
 *  - width
 *  - height
 *  - encoded
 *  - fid (figure id)
 * 0r:
 *  - data
 *  - layout
 * @param {object} _opts : component options
 *  - format
 *  - scale (only for plotly.js v.1.31.0 and up)
 *  - width
 *  - height
 *  - safeMode
 * @return {object}
 *  - errorCode
 *  - result
 */
function parse (body, _opts) {
  const result = {}

  const errorOut = (code, extra) => {
    let message = `${cst.statusMsg[code]}`
    if (extra) message = `${message} (${extra})`
    return {code, message, result: null}
  }

  let figure
  let opts

  // to support both 'serve' requests (figure/format/../)
  // and 'run' body (data/layout) structures
  if (body.figure) {
    figure = body.figure
    opts = body
  } else {
    figure = body
    opts = _opts
  }

  result.scale = isPositiveNumeric(opts.scale) ? Number(opts.scale) : cst.dflt.scale
  result.fid = isNonEmptyString(opts.fid) ? opts.fid : null
  result.encoded = !!opts.encoded

  if (isNonEmptyString(opts.format)) {
    if (cst.contentFormat[opts.format]) {
      result.format = opts.format
    } else {
      return errorOut(400, 'wrong format')
    }
  } else {
    result.format = cst.dflt.format;
  }

  if (!isPlainObj(figure)) {
    return errorOut(400, 'non-object figure')
  }

  if (!figure.data && !figure.layout) {
    return errorOut(400, 'no \'data\' and no \'layout\' in figure')
  }

  result.figure = {}

  if ('data' in figure) {
    if (Array.isArray(figure.data)) {
      result.figure.data = figure.data
    } else {
      return errorOut(400, 'non-array figure data')
    }
  } else {
    result.figure.data = []
  }

  if ('layout' in figure) {
    if (isPlainObj(figure.layout)) {
      result.figure.layout = figure.layout
    } else {
      return errorOut(400, 'non-object figure layout')
    }
  } else {
    result.figure.layout = {}
  }

  result.width = parseDim(result, opts, 'width')
  result.height = parseDim(result, opts, 'height')

  if (_opts.safeMode && willFigureHang(result)) {
    return errorOut(400, 'figure data is likely to make exporter hang, rejecting request')
  }

  return {code: 0, message: null, result}
}

function parseDim (result, opts, dim) {
  const layout = result.figure.layout

  if (isPositiveNumeric(opts[dim])) {
    return Number(opts[dim])
  } else if (isPositiveNumeric(layout[dim]) && !layout.autosize) {
    return Number(layout[dim])
  } else {
    return cst.dflt[dim]
  }
}

function willFigureHang (result) {
  const data = result.figure.data

  // cap the number of traces
  if (data.length > 200) return true

  let maxPtBudget = 0

  for (let i = 0; i < data.length; i++) {
    const trace = data[i] || {}

    // cap the number of points using a budget
    maxPtBudget += estimateDataLength(trace) / maxPtsPerTrace(trace)
    if (maxPtBudget > 1) return true
  }
}

// Consider the array of maximum length as a proxy to determine
// the number of points to be drawn. In general, this estimate
// can be (much) smaller than the true number of points plotted
// when it does not match the length of the other coordinate arrays.
function findMaxArrayLength (cont) {
  const arrays = Object.keys(cont)
    .filter(k => Array.isArray(cont[k]))
    .map(k => cont[k])

  const lengths = arrays.map(arr => {
    if (Array.isArray(arr[0])) {
      // 2D array case
      return arr.reduce((a, r) => a + r.length, 0)
    } else {
      return arr.length
    }
  })

  return Math.max(0, ...lengths)
}

function estimateDataLength (trace) {
  const topLevel = findMaxArrayLength(trace)
  let dimLevel = 0
  let cellLevel = 0

  // special case for e.g. parcoords and splom traces
  if (Array.isArray(trace.dimensions)) {
    dimLevel = trace.dimensions
      .map(findMaxArrayLength)
      .reduce((a, v) => a + v)
  }

  // special case for e.g. table traces
  if (isPlainObj(trace.cells)) {
    cellLevel = findMaxArrayLength(trace.cells)
  }

  return Math.max(topLevel, dimLevel, cellLevel)
}

function maxPtsPerTrace (trace) {
  const type = trace.type || 'scatter'

  switch (type) {
    case 'scattergl':
    case 'splom':
    case 'pointcloud':
    case 'table':
      return 1e7

    case 'scatterpolargl':
    case 'heatmap':
    case 'heatmapgl':
      return 1e6

    case 'scatter3d':
    case 'surface':
      return 5e5

    case 'mesh3d':
      if ('alphahull' in trace && Number(trace.alphahull) >= 0) {
        return 1000
      } else {
        return 5e5
      }

    case 'parcoords':
      return 5e5
    case 'scattermapbox':
      return 5e5

    case 'histogram':
    case 'histogram2d':
    case 'histogram2dcontour':
      return 1e6

    case 'box':
      if (trace.boxpoints === 'all') {
        return 5e4
      } else {
        return 1e6
      }
    case 'violin':
      if (trace.points === 'all') {
        return 5e4
      } else {
        return 1e6
      }

    default:
      return 5e4
  }
}

module.exports = parse

},{"./constants":49,"./is-non-empty-string":50,"./is-positive-numeric":51,"is-plain-obj":2}],53:[function(require,module,exports){
/* global Plotly:false */

const semver = require('semver')
const cst = require('./constants')
const parse = require('./parse')

/**
 * @param {object} info : info object
 *  - data
 *  - format
 *  - width
 *  - height
 *  - scale
 *  - encoded
 * @param {string} mapboxAccessToken: mapboxAccessToken
 * @param {string} topojsonURL
 */
function render (info, mapboxAccessToken, topojsonURL) {
  let opts = {};

  if (mapboxAccessToken !== undefined && mapboxAccessToken.length > 0) {
    opts.mapboxAccessToken = mapboxAccessToken;
  }
  if (topojsonURL !== undefined && topojsonURL.length > 0) {
    opts.topojsonURL = topojsonURL;
  }

  // Rename info.data to info.figure
  info.figure = info.data
  delete info.data;

  // Parse request
  let parsed = parse(info, opts);
  if (parsed.code !== 0) {
    // Bad request return promise with error info
    return new Promise((resolve) => {resolve(parsed)})
  }

  // Use parsed export request
  info = parsed.result;
  const figure = info.figure;
  const format = info.format;
  const encoded = info.encoded;

  // Build default config, and let figure.config override it
  const defaultConfig = {
    mapboxAccessToken: opts.mapboxAccessToken || null,
    plotGlPixelRatio: info.scale * 2
  }
  if (opts.topojsonURL) {
    defaultConfig.topojsonURL = opts.topojsonURL
  }

  const config = Object.assign(defaultConfig, figure.config)

  let errorCode = 0
  let result = null
  let errorMsg = null
  let pdfBgColor = null
  const done = () => {
    if (errorCode !== 0 && !errorMsg) {
      errorMsg = cst.statusMsg[errorCode]
    }

    return {
      code: errorCode,
      message: errorMsg,
      pdfBgColor,
      format,
      result,
      width: info.width,
      height: info.height,
      scale: info.scale,
    }
  }

  const PRINT_TO_PDF = (format === 'pdf' || format === 'eps')
  const PRINT_TO_EMF = (format === 'emf')

  let imgOptsFormat
  if (PRINT_TO_PDF || PRINT_TO_EMF) {
    imgOptsFormat = 'svg'
  } else if (format === 'json') {
    imgOptsFormat = 'full-json'
  } else {
    imgOptsFormat = format
  }

  // stash `paper_bgcolor` here in order to set the pdf window bg color
  const pdfBackground = (gd, _bgColor) => {
    if (!pdfBgColor) pdfBgColor = _bgColor
    gd._fullLayout.paper_bgcolor = 'rgba(0,0,0,0)'
  }

  const imgOpts = {
    format: imgOptsFormat,
    width: info.width,
    height: info.height,
    // only works as of plotly.js v1.31.0
    scale: info.scale,
    // return image data w/o the leading 'data:image' spec
    imageDataOnly: PRINT_TO_EMF || (!PRINT_TO_PDF && !encoded),
    // blend (emf|jpeg) background color as (emf|jpeg) does not support transparency
    setBackground: (format === 'jpeg' || format === 'emf') ? 'opaque'
      : PRINT_TO_PDF ? pdfBackground
        : ''
  }

  if (
    // 'full-json' was introduced in plotly.js v1.53.0
    // see: https://github.com/plotly/plotly.js/releases/tag/v1.53.0
    imgOpts.format === 'full-json' && semver.lt(Plotly.version, '1.53.0')
  ) {
    errorCode = 527
    errorMsg = `plotly.js version: ${Plotly.version}`
    return new Promise((resolve) => {resolve(done())})
  }

  let promise

  if (semver.gte(Plotly.version, '1.30.0')) {
    promise = Plotly
      .toImage({ data: figure.data, layout: figure.layout, config: config }, imgOpts)
  } else if (semver.gte(Plotly.version, '1.11.0')) {
    const gd = document.createElement('div')

    promise = Plotly
      .newPlot(gd, figure.data, figure.layout, config)
      .then(() => Plotly.toImage(gd, imgOpts))
      .then((imgData) => {
        Plotly.purge(gd)

        switch (format) {
          case 'png':
          case 'jpeg':
          case 'webp':
            if (encoded) {
              return imgData
            } else {
              return imgData.replace(cst.imgPrefix.base64, '')
            }
          case 'svg':
            if (encoded) {
              return imgData
            } else {
              return decodeSVG(imgData)
            }
          case 'pdf':
          case 'eps':
          case 'emf':
            return imgData
        }
      })
  } else {
    errorCode = 526
    errorMsg = `plotly.js version: ${Plotly.version}`
    return new Promise((resolve) => {resolve(done())})
  }

  const img = document.getElementById("kaleido-image")
  const style = document.getElementById("head-style")

  let exportPromise = promise.then((imgData) => {
    result = imgData
    return done()
  })

  if (PRINT_TO_PDF) {
    exportPromise = exportPromise.then((response) => {
      // Retrun promise that resolves when the image is loaded in the <img> element
      return new Promise((resolve, reject) => {
        style.innerHTML = `
        @page { size: ${info.width * info.scale}px ${info.height * info.scale}px; }
        body { margin: 0; padding: 0; background-color: ${pdfBgColor} }
        `
        img.onload = resolve
        img.onerror = reject
        img.src = response.result
        setTimeout(() => reject(new Error('too long to load image')), cst.pdfPageLoadImgTimeout)
      }).then(() => {
        // We don't need to transport image bytes back to C++ since PDF export will be performed
        result = null;
        return done()
      })
    })
  }

  return exportPromise
      .catch((err) => {
        errorCode = 525
        errorMsg = err.message
        result = null;
        return done()
      })
}

function decodeSVG (imgData) {
  return window.decodeURIComponent(imgData.replace(cst.imgPrefix.svg, ''))
}

module.exports = render

},{"./constants":49,"./parse":52,"semver":32}]},{},[48])(48)
});
