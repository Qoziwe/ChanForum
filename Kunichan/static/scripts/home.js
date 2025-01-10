(function () {
  const carousel = document.getElementById("D-CC-Carousel");
  const cards = Array.from(carousel.children);
  const prevButton = document.getElementById("prev");
  const nextButton = document.getElementById("next");

  let currentIndex = 0;

  function updateCarousel() {
    const cardWidth =
      document.querySelector(".D-CC-C-Card").offsetWidth +
      2 *
        parseFloat(
          getComputedStyle(document.querySelector(".D-CC-C-Card")).marginLeft
        );
    carousel.style.transform = `translateX(-${currentIndex * cardWidth}px)`;
  }

  function cloneCards() {
    cards.forEach((card) => {
      const cloneStart = card.cloneNode(true);
      const cloneEnd = card.cloneNode(true);
      carousel.appendChild(cloneStart);
      carousel.insertBefore(cloneEnd, carousel.firstChild);
    });
  }

  function handleNext() {
    currentIndex++;
    if (currentIndex >= cards.length) {
      currentIndex = 0;
      carousel.style.transition = "none";
      carousel.style.transform = `translateX(-0px)`;
      setTimeout(() => {
        carousel.style.transition = "transform 0.5s ease";
      }, 50);
    }
    updateCarousel();
  }

  function handlePrev() {
    currentIndex--;
    if (currentIndex < 0) {
      currentIndex = cards.length - 1;
      const cardWidth =
        document.querySelector(".D-CC-C-Card").offsetWidth +
        2 *
          parseFloat(
            getComputedStyle(document.querySelector(".D-CC-C-Card")).marginLeft
          );
      carousel.style.transition = "none";
      carousel.style.transform = `translateX(-${currentIndex * cardWidth}px)`;
      setTimeout(() => {
        carousel.style.transition = "transform 0.5s ease";
      }, 50);
    }
    updateCarousel();
  }

  cloneCards();
  updateCarousel();

  nextButton.addEventListener("click", handleNext);
  prevButton.addEventListener("click", handlePrev);
})();

// Находим все кнопки с классом D-C-Card-Front-Button
const burgerButtons = document.querySelectorAll(".D-C-Card-Front-Button");

burgerButtons.forEach((button) => {
  button.addEventListener("click", () => {
    // Тогглим класс "active" для текущей кнопки
    button.classList.toggle("active");

    // Находим родительскую карточку
    const card = button.closest(".D-C-Card");
    if (card) {
      const back = card.querySelector(".D-C-Card-Back");

      if (back) {
        // Если задняя часть видна, скрываем её
        if (back.style.display === "block") {
          back.style.display = "none";
        } else {
          // Иначе делаем видимой
          back.style.display = "block";
        }
      }

      // Тогглим класс для карточки (если нужно дополнительное поведение)
      card.classList.toggle("flipped");
    }
  });
});
