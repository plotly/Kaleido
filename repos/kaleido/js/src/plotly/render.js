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
  const figure = info.figure
  const format = info.format
  const encoded = info.encoded

  // Build default config, and let figure.config override it
  const defaultConfig = {
    mapboxAccessToken: opts.mapboxAccessToken || null,
    plotGlPixelRatio: opts.plotGlPixelRatio || cst.plotGlPixelRatio
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
