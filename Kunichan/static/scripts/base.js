const snowContainer = document.querySelector(".snow-container");
const snowflakeCount = 80;

function createSnowflake() {
  if (snowContainer.children.length >= snowflakeCount) {
    return 0; // Если снежинок уже больше, чем нужно, не создаем новые
  }

  const snowflake = document.createElement("div");
  snowflake.classList.add("snowflake");
  const size = Math.random() * 10 + 5;
  snowflake.style.width = `${size}px`;
  snowflake.style.height = `${size}px`;
  const startX = Math.random() * 100;
  snowflake.style.left = `${startX}vw`;
  const fallDuration = Math.random() * 5 + 5;
  snowflake.style.animationDuration = `${fallDuration}s`;
  const swayDistance = Math.random() * 50 - 25;
  snowflake.style.setProperty("--sway-distance", `${swayDistance}px`);
  const blur = Math.random() * 3;
  snowflake.style.filter = `blur(${blur}px)`;
  const opacity = Math.random() * 0.5 + 0.5;
  snowflake.style.opacity = `${opacity}`;

  snowflake.addEventListener("animationend", () => {
    snowflake.remove();
  });

  snowContainer.appendChild(snowflake);
}

window.addEventListener("load", () => {
  const preloader = document.getElementById("preloader");
  preloader.classList.add("hidden");
});

setInterval(() => {
  if (document.hidden) return;
  createSnowflake();
}, 200);

function urlFor(data) {
  window.location.href = `/${data}`;
}

function toggleNavigation() {
  const navigation = document.getElementById("Navigation");
  const PElements = document.querySelectorAll(".N-Button p");
  const NButtonSVGElemets = document.querySelectorAll(".N-H-Svg");
  const NH1Elements = document.querySelectorAll("#Navigation h1");
  navigation.classList.toggle("collapsed");

  if (navigation.classList.contains("collapsed")) {
    localStorage.setItem("NavigationBarStatus", "collapsed");
    setTimeout(function () {
      PElements.forEach((element) => {
        element.style.display = "none";
      });
      NButtonSVGElemets.forEach((element) => {
        element.style.margin = "0 auto";
      });
      NH1Elements.forEach((element) => {
        element.style.display = "none";
      });
      document.getElementById("Toggle-btn").style.position = "static";
      document.getElementById("Toggle-btn").style.margin = "0 auto";
    }, 300);
  } else {
    localStorage.setItem("NavigationBarStatus", "decollapsed");
    PElements.forEach((element) => {
      element.style.display = "block";
    });
    NButtonSVGElemets.forEach((element) => {
      element.style.margin = "0";
    });
    NH1Elements.forEach((element) => {
      element.style.display = "block";
    });
    document.getElementById("Toggle-btn").style.position = "absolute";
    document.getElementById("Toggle-btn").style.margin = "0 1.8vw 0 0";
  }
}

window.onload = function () {
  const navigation = document.getElementById("Navigation");
  const PElements = document.querySelectorAll(".N-Button p");
  const NButtonSVGElemets = document.querySelectorAll(".N-H-Svg");
  const NH1Elements = document.querySelectorAll("#Navigation h1");
  if (localStorage.getItem("NavigationBarStatus") == "collapsed") {
    PElements.forEach((element) => {
      element.style.display = "none";
    });
    NButtonSVGElemets.forEach((element) => {
      element.style.margin = "0 auto";
    });
    NH1Elements.forEach((element) => {
      element.style.display = "none";
    });
    document.getElementById("Toggle-btn").style.position = "static";
    document.getElementById("Toggle-btn").style.margin = "0 auto";
  }
  navigation.classList.toggle(
    String(localStorage.getItem("NavigationBarStatus"))
  );
};

window.addEventListener("DOMContentLoaded", () => {
  // Получаем текущий путь из URL без начального "/"
  const path = window.location.pathname.replace("/", "") || "0"; // Подставляем "0", если путь пустой

  // Ищем элемент с ID, совпадающим с path
  const targetElement = document.getElementById(path);

  // Проверяем, найден ли элемент
  if (targetElement) {
    // Если найден, добавляем класс
    targetElement.classList.add("NavigationSelectedMenu");
  } else {
    // Выводим сообщение, если элемент не найден
    console.warn(`Элемент с id="${path}" не найден.`);
  }
});
