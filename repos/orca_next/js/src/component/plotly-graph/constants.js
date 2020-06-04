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

  // config option passed in render step
  plotGlPixelRatio: 2.5,

  // time [in ms] after which printToPDF errors when image isn't loaded
  pdfPageLoadImgTimeout: 20000
}
