const isNumeric = require('fast-isnumeric')

function isPositiveNumeric (v) {
  return isNumeric(v) && v > 0
}

module.exports = isPositiveNumeric
