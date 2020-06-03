function isNonEmptyString (v) {
  return typeof v === 'string' && v.length > 0
}

module.exports = isNonEmptyString
