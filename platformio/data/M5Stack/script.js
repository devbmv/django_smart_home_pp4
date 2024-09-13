//============================================================================

function sendData() {
  var variable1Value = document.getElementById('variable1').value;
  fetch('/update?variable1=' + variable1Value)
    .then(response => response.text())
    .then(data => {
      document.getElementById('response').innerHTML = 'Response: ' + data;
    })
    .catch(error => console.error('Error:', error));
}

//================================================================================

const form = document.getElementById('uploadForm');
const progressBar = document.querySelector('.progress-bar');
const info = document.querySelector('.info');

//============================================================================

form.addEventListener('submit', function (event) {
  event.preventDefault();
  const formData = new FormData(form);
  const request = new XMLHttpRequest();
  request.open('POST', form.action, true);
  request.upload.onprogress = function (e) {
    if (e.lengthComputable) {
      const percentComplete = (e.loaded / e.total) * 100;
      progressBar.style.width = percentComplete + '%';
      info.textContent = 'Uploading ' + percentComplete.toFixed(2) + '%';
    }
  };

  //============================================================================

  request.onload = function () {
    if (request.status == 200) {
      progressBar.style.width = '100%';
      info.textContent = 'Upload complete.';
    } else {
      info.textContent = 'Upload failed. Please try again.';
    }
  };
  request.send(formData);
});

//============================================================================