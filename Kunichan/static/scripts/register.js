const errorMessage = "{{ error | safe }}";
if (errorMessage) {
  alert(
    "Ошибка: пользователь с таким email уже существует! Пожалуйста, войдите в систему."
  );
}

window.onload = function () {
  var counter = 90;
  var readmeclearer = setInterval(() => {
    counter -= 0.5;
    document.getElementById(
      "R-Container"
    ).style.transform = `rotateY(${counter.toString()}deg`;
    if (counter <= 0) {
      clearInterval(readmeclearer);
    }
  }, 2.5);
};

const LoginButton = document.getElementById("R-C-LB-A");
LoginButton.onclick = function () {
  var counter = 0;
  var readmeclearer = setInterval(() => {
    counter += 0.5;
    document.getElementById(
      "R-Container"
    ).style.transform = `rotateY(${counter.toString()}deg`;
    if (counter >= 90) {
      clearInterval(readmeclearer);
    }
  }, 2.5);
  setTimeout(function () {
    window.location.href = "./login";
  }, 800);
};
