/* global Mermaid:false */

const semver = require('semver')

/**

 */
function render () {
  
  let errorCode = 0
  let result = null
  let errorMsg = null
  let pdfBgColor = null
  
  const done = () => {
    if (errorCode !== 0 && !errorMsg) {
      errorMsg = cst.statusMsg[errorCode]
    }

    return {
    // TODO this is hardcoded 
      code: errorCode,
      message: errorMsg,
      pdfBgColor,
      format: "svg",
      result,
      width: 200,
      height: 200,
      scale: 1,
    }
  }

  let promise = Promise.resolve("TO DO");

  let exportPromise = promise.then((imgData) => {
    result = imgData
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
