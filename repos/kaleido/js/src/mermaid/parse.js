const constants = require('./constants')
const isPositiveNumeric = require('../utils/is-positive-numeric')
const isNonEmptyString = require('../utils/is-non-empty-string')
const hasPropertiesOfObject = require('../utils/has-propperties-of-object')

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
        let message = `${constants.statusMsg[code]}`
        if (extra) { 
            message = `${message} (${extra})`
        }
        return {code, message, result: null}
    }

    if (!isNonEmptyString(body.data)) {
        return errorOut(400, 'empty markdown')
    }
    
    if (isNonEmptyString(body.format)) {
        if (constants.contentFormat[body.format]) {
            result.format = opts.format
        } else {
            return errorOut(406, 'wrong format')
        }
    } else {
        result.format = constants.defaultParams.format;
    }

    result.scale = isPositiveNumeric(body.scale) ? Number(body.scale) : constants.defaultParams.scale
    result.width = isPositiveNumeric(body.width) ? Number(body.width) : constants.defaultParams.width
    result.height = isPositiveNumeric(body.height) ? Number(body.height) : constants.defaultParams.height

    if (!hasPropertiesOfObject(body.config, mermaid.mermaidAPI.defaultConfig)) {
        return errorOut(400, 'wrong diagram config parameters')
    }

    if (!hasPropertiesOfObject(mermaidConfig, mermaid)) {
        return errorOut(400, 'wrong mermaid config parameters')
    }

    return result
 }

module.exports = parse