const carousel = document.querySelector(".carousel");
const cards = Array.from(carousel.children);
const prevButton = document.getElementById("prev");
const nextButton = document.getElementById("next");

let currentIndex = 0;

function updateCarousel() {
  const cardWidth =
    document.querySelector(".card").offsetWidth +
    2 *
      parseFloat(getComputedStyle(document.querySelector(".card")).marginLeft);
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
      document.querySelector(".card").offsetWidth +
      2 *
        parseFloat(
          getComputedStyle(document.querySelector(".card")).marginLeft
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
