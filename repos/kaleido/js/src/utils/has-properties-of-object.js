/** checks if a given object contains _only_ properties of another object
 *
 * @param {object} containedObject : given object that is checked
 * @param {object} object : another object
 * @return {boolean}
 */
function hasPropertiesOfObject(containedObject, object) {
    for (var prop in containedObject) {
        if (containedObject.hasOwnProperty(prop)) {
            if (!object.hasOwnProperty(prop)) {
                return false
            }
        }
    }
    return true
}
  
  module.exports = hasPropertiesOfObject 
  