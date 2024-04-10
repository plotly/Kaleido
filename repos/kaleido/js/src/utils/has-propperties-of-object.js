/** checks if a given object contains _only_ properties of another object
 *
 * @param {object} containedObject : given object that is checked
 * @param {object} object : another object
 * @return {boolean}
 */
function hasPropertiesOfObject(containedObject, object) {
    const containedKeys = Object.keys(containedObject);
    const keys = Object.keys(object);
    for (let key of containedKeys) {
        if (!keys.includes(key)) {
            return containedKeys;
        }
    }
    return true;
}
  
  module.exports = hasPropertiesOfObject 
  