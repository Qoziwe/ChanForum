function initializeCarousel() {
  const track = document.querySelector("#D-C-C-Track");
  const cards = Array.from(track.children);
  const leftButton = document.querySelector(".D-C-C-Button.left");
  const rightButton = document.querySelector(".D-C-C-Button.right");

  const cardWidthVW = 15 + 2; // Ширина карточки (15vw) + gap (2vw)

  // Клонирование карточек для бесконечной прокрутки
  cards.forEach((card) => {
    const clone = card.cloneNode(true);
    track.appendChild(clone);
  });
  cards.forEach((card) => {
    const clone = card.cloneNode(true);
    track.insertBefore(clone, track.firstChild);
  });

  // Начальный индекс для центрирования карусели
  let currentIndex = cards.length;

  // Перемещение трека к определенному индексу
  const moveToCard = (index) => {
    const translateX = -(index * cardWidthVW);
    track.style.transform = `translateX(${translateX}vw)`;
  };

  // Движение вправо
  const moveRight = () => {
    track.style.transition = "transform 0.5s ease-in-out";
    currentIndex++;
    moveToCard(currentIndex);
    if (currentIndex >= cards.length * 2) {
      setTimeout(() => {
        track.style.transition = "none";
        currentIndex = cards.length;
        moveToCard(currentIndex);
      }, 500);
    }
  };

  // Движение влево
  const moveLeft = () => {
    track.style.transition = "transform 0.5s ease-in-out";
    currentIndex--;
    moveToCard(currentIndex);
    if (currentIndex < cards.length) {
      setTimeout(() => {
        track.style.transition = "none";
        currentIndex = cards.length * 2 - 1;
        moveToCard(currentIndex);
      }, 500);
    }
  };

  // События для кнопок
  rightButton.addEventListener("click", moveRight);
  leftButton.addEventListener("click", moveLeft);

  // Инициализация позиции
  moveToCard(currentIndex);

  // Убедитесь, что у карточек корректная ширина
  cards.forEach((card) => {
    card.style.width = "15vw"; // Ширина карточки
    card.style.height = "18vw"; // Высота карточки
  });
}

// Инициализация карусели при загрузке
initializeCarousel();

const burgerButtons = document.querySelectorAll(".D-C-Card-Front-Button");

burgerButtons.forEach((button) => {
  button.addEventListener("click", () => {
    button.classList.toggle("active");
    const card = button.closest(".D-C-Card");
    if (card) {
      const back = card.querySelector(".D-C-Card-Back");

      if (back) {
        if (back.style.display === "block") {
          back.style.display = "none";
        } else {
          back.style.display = "block";
        }
      }
      card.classList.toggle("flipped");
    }
  });
});

//likes
// Добавляем обработчик на форму лайка
document.addEventListener('DOMContentLoaded', function() {
  // Находим все кнопки лайков на странице
  const likeForms = document.querySelectorAll('.like-form');
  
  likeForms.forEach(form => {
    form.addEventListener('submit', function(event) {
      const postId = form.getAttribute('id').split('-')[2]; // Получаем ID поста из ID формы

      // Сохраняем ID поста в localStorage
      localStorage.setItem('lastLikedPostId', postId);

    });
  });

  // Проверяем, есть ли сохраненный ID поста и прокручиваем до него
  const lastLikedPostId = localStorage.getItem('lastLikedPostId');
  if (lastLikedPostId) {
    const postElement = document.getElementById(`D-C-Card-${lastLikedPostId}`);
    if (postElement) {
      postElement.scrollIntoView({ behavior: 'smooth' });
      localStorage.setItem('lastLikedPostId', 0); 
    }
  }
});