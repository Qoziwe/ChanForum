const snowContainer = document.querySelector(".snow-container");
const snowflakeCount = 50;

function createSnowflake() {
  if (snowContainer.children.length >= snowflakeCount) {
    return 0;
  }

  const snowflake = document.createElement("div");
  snowflake.classList.add("snowflake");
  const size = Math.random() * 10 + 5;
  snowflake.style.width = `${size - 25}vw`;
  snowflake.style.height = `${size - 25}vw`;
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

  if (window.innerWidth > 700) {
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
    }
  } else {
    if (navigation.classList.contains("collapsed")) {
      localStorage.setItem("NavigationBarStatus", "collapsed");
      document.getElementById("Toggle-btn").style.left = "1vw";
    } else {
      localStorage.setItem("NavigationBarStatus", "decollapsed");
      document.getElementById("Toggle-btn").style.left = "80%";
    }
  }
}

window.onload = function () {
  const navigation = document.getElementById("Navigation");
  const PElements = document.querySelectorAll(".N-Button p");
  const NButtonSVGElemets = document.querySelectorAll(".N-H-Svg");
  const NH1Elements = document.querySelectorAll("#Navigation h1");
  if (
    localStorage.getItem("NavigationBarStatus") == "collapsed" &&
    window.innerWidth > 700
  ) {
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
  var path = window.location.pathname.replace("/", "") || "0";
  path = path.substring(path.lastIndexOf("/") + 1);
  const targetElement = document.getElementById(path);
  if (path == "edit") {
    document.getElementById("userpost").classList.add("NavigationSelectedMenu");
  }
  if (targetElement) {
    targetElement.classList.add("NavigationSelectedMenu");
  } else {
    // Display a message if the element is not found
    // console.warn(`Element with id="${path}" not found.`);
  }
});
