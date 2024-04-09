function hasAllProperties(obj1, obj2) {
    for (var prop in obj1) {
        if (obj1.hasOwnProperty(prop)) {
            if (!obj2.hasOwnProperty(prop)) {
                return false;
            }
        }
    }
    return true;
}
  
  module.exports = hasAllProperties
  