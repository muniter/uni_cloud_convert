const formData = require('form-data');
const fs = require('fs');

function setupMultipartFormData(requestParams, context, ee, next) {
  const form = new formData();
  form.append('fileName', fs.createReadStream('sample.mp3'));
  form.append('newFormat', 'wav');
  requestParams.body = form;
  return next();
}

module.exports = {
  setupMultipartFormData,
}