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


document.querySelectorAll('.like-button').forEach(button => {
    button.addEventListener('click', function(event) {
        event.preventDefault();
        fetch(this.getAttribute('data-url'), {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                this.innerHTML = data.liked ? '❤️ Unlike' : '🤍 Like';
                document.querySelector(`#likes-${data.post_id}`).innerText = `${data.likes_count} likes`;
            }
        });
    });
});


