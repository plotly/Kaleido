/* global Mermaid:false */

const semver = require('semver')
const hasOwn = require('object.hasown')
const constants = require('./constants')
const parse = require('./parse')

if (!Object.hasOwn) {
	hasOwn.shim();
}

/**
 * @param {object} info : info object
 *  - data
 *  - format
 *  - width
 *  - height
 *  - scale
 *  - config
 */
function render (info) {

  let parsed = parse(info);
  if (parsed.code !== 0) {
    // Bad request return promise with error info
    return new Promise((resolve) => {resolve(parsed)})
  }

  // Set diagram config
  mermaid.mermaidAPI.setConfig(parsed.config)
  
  let errorCode = 0
  let result = null
  let errorMsg = null
  let pdfBgColor = null
  
  const done = () => {
    if (errorCode !== 0 && !errorMsg) {
      errorMsg = constants.statusMsg[errorCode]
    }

    return {
      code: errorCode,
      message: errorMsg,
      pdfBgColor,
      format: parsed.format,
      result,
      width: parsed.width,
      height: parsed.height,
      scale: parsed.scale,
    }
  }

  let promise 

  // TODO create different rendering call for v<10 and v>=10 of mermaidjs ?

  promise = mermaid.render("graph", info.data)

  let exportPromise = promise.then((imgData) => {
      result = imgData.svg
      return done()
    })

  return exportPromise
      .catch((err) => {
        errorCode = 525
        errorMsg = err.message
        result = null;
        return done()
      })
}

module.exports = render
