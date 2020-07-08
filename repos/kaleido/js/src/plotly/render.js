/* global Plotly:false */

const semver = require('semver')
const cst = require('./constants')
const parse = require('./parse')
const tinycolor = require('tinycolor2')

const fillUrl = /(^|; )fill: url\('#([^']*)'\);/
const fillRgbaColor = /(^|; )fill: rgba\(([^)]*)\);/
const fillOpacityZero = /(^|\s*)fill-opacity: 0;/
const strokeOpacityZero = /(^|; )stroke-opacity: 0;/
const opacityZero = /(^|; )opacity: 0;/

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

  if (PRINT_TO_EMF) {
    exportPromise = exportPromise.then((response) => {

      // Get background color from figure's definition
      var bgColor;
      var bgColorStr;
      if ((figure.layout || {}).paper_bgcolor) {
        // Get background color from layout, if any
        bgColorStr = figure.layout.paper_bgcolor;
      } else if (((((figure.layout || {}).template) || {}).layout || {}).paper_bgcolor) {
        // Get background color from template, if any
        bgColorStr = figure.layout.template.layout.paper_bgcolor;
      } else {
        // Background color is white
        bgColorStr = "white";
      }


      var color = tinycolor(bgColorStr).toRgb()
      bgColor = [color.r, color.g, color.b]
      // return response;
      return cleanSvg(response, bgColor)
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

function cleanSvg (response, bgColor) {

  const svg = response.result
  // Import svg string into a dom element
  const doc = new DOMParser().parseFromString(svg, 'application/xml');
  const fragment = doc.children[0];

  // Remove path and rectangles that are compleletely transparent
  fragment.querySelectorAll('rect, path').forEach(function (node) {
    var style = node.getAttribute('style')
    if (style && (
        (style.match(fillOpacityZero) && style.match(strokeOpacityZero)) ||
        style.match(opacityZero)
    )) node.remove()
  })

  // Set fill color to background color if its fill-opacity is 0 but stroke-opacity isn't 0
  fragment.querySelectorAll('rect').forEach(function (node) {
    var style = node.getAttribute('style')
    if (!style) return
    var m = style.match(fillOpacityZero)

    if (m) {
      var sep = m[1]
      var rgbFill = `${sep}fill: rgb(${bgColor[0]},${bgColor[1]},${bgColor[2]});`
      style = style.replace(m[0], rgbFill)
      node.setAttribute('style', style)
    }
  })

  // Fix black legends by removing rect.legendtoggle
  // regexp: svg = svg.replace(/<rect class="legendtoggle"[^>]+>/g, '')
  fragment.querySelectorAll('rect.legendtoggle').forEach(node => node.remove())

  // Remove colorbar background if it's transparent
  fragment.querySelectorAll('rect.cbbg').forEach(function (node) {
    var style = node.getAttribute('style')
    if (style && style.match(fillOpacityZero)) node.remove()
  })

  // Fix fill in colorbars
  fragment.querySelectorAll('rect.cbfill').forEach(function (node) {
    var style = node.getAttribute('style')
    if (style && style.match(fillUrl)) {
      var gradientId = style.match(fillUrl)[2]

      var el = fragment.getElementById(gradientId)
      // Inkscape doesn't deal well with gradientUnits="objectBoundingBox"
      el.setAttribute('gradientUnits', 'userSpaceOnUse')
      var height = node.getAttribute('height')
      el.setAttribute('y1', height)
    }
  })



  // Fix path with rgba color for fill
  fragment.querySelectorAll('path').forEach(function (node) {
    var style = node.getAttribute('style')
    if (!style) return
    var m = style.match(fillRgbaColor)
    if (m) {
      var sep = m[1]
      var rgba = m[2].split(',')
      if (rgba[3] === 0) {
        node.remove()
      } else {
        var rgbFill = `${sep}fill: rgb(${rgba.slice(0, 3).join(',')})`
        style = style.replace(m[0], rgbFill)
        node.setAttribute('style', style)
      }
    }
  })

  // Fix black background in rasterized images (WebGL)
  const canvas = document.createElement("canvas");

  const promises = [];
  fragment.querySelectorAll('image').forEach(function (node) {
    var dataType = 'data:image/png;base64'
    var href = node.getAttribute('xlink:href')
    var parts = href.split(',')
    if (parts[0] === dataType) {
      const ctx = canvas.getContext("2d");

      const promise = new Promise((resolve, reject) => {
        const img = new Image();
        img.addEventListener("load", () => resolve(img));
        img.addEventListener("error", err => reject(err));
        img.src = href;
      }).then((img) => {
        ctx.drawImage(img, 0, 0);
        const image = ctx.getImageData(0, 0, img.width, img.height)

        for (var y = 0; y < image.height; y++) {
          for (var x = 0; x < image.width; x++) {
            var idx = (image.width * y + x) << 2

            var alpha = image.data[idx + 3]
            if (alpha < 255) {
              // Manually do alpha composition (https://en.wikipedia.org/wiki/Alpha_compositing)
              image.data[idx] = image.data[idx] * alpha / 255 + bgColor[0] * (1 - alpha / 255)
              image.data[idx + 1] = image.data[idx + 1] * alpha / 255 + bgColor[1] * (1 - alpha / 255)
              image.data[idx + 2] = image.data[idx + 2] * alpha / 255 + bgColor[2] * (1 - alpha / 255)

              image.data[idx + 3] = 255
            }
          }
        }

        ctx.putImageData(image, 0, 0)
        node.setAttribute('xlink:href', canvas.toDataURL())
      });

      promises.push(promise)
    }
  })

  return Promise.all(promises).then(() => {
    response.result = fragment.outerHTML
    return response
  })
}

module.exports = render
