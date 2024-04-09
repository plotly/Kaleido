const cst = require('./constants')
const isPositiveNumeric = require('./is-positive-numeric')
const isNonEmptyString = require('./is-non-empty-string')
const hasAllProperties = require('./has-all-properties')

/** mermaid-graph parse
 *
 * @param {object} body : JSON-parsed request body
 *  - data
 *  - format
 *  - scale
 *  - width
 *  - height
 *  - config
 * @param {object} mermaidConfig : mermaid config
 * @return {object}
 *  - errorCode
 *  - result
 */
function parse (body, mermaidConfig) {

    let result = body;
    result.code = 0;
    
    const errorOut = (code, extra) => {
        let message = `${cst.statusMsg[code]}`
        if (extra) { 
            message = `${message} (${extra})`
        }
        return {code, message, result: null}
    }

    if (!isNonEmptyString(body.data)) {
        return errorOut(400, 'empty markdown')
    }
    
    if (isNonEmptyString(body.format)) {
        if (cst.contentFormat[body.format]) {
            result.format = opts.format
        } else {
            return errorOut(406, 'wrong format')
        }
    } else {
        result.format = cst.dflt.format;
    }

    result.scale = isPositiveNumeric(body.scale) ? Number(body.scale) : cst.dflt.scale
    result.width = isPositiveNumeric(body.width) ? Number(body.width) : cst.dflt.width
    result.height = isPositiveNumeric(body.height) ? Number(body.height) : cst.dflt.height

    if (!hasAllProperties(body.config, mermaid.mermaidAPI.defaultConfig)) {
        return errorOut(400, 'wrong diagram config parameters')
    }

    if (!hasAllProperties(mermaidConfig, mermaid)) {
        return errorOut(400, 'wrong mermaid config parameters')
    }

    return result
 }

 

module.exports = parse