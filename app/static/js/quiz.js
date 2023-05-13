$("#gpt-button").click(function () {
  generateQuiz();
});

$("#chat-input").keydown(function (event) {
  if (event.which === 13) {
    event.preventDefault();
    generateQuiz();
  }
});

function generateQuiz() {
  var question = $("#chat-input").val();

  let html_data = `
  <a href="#" class="list-group-item list-group-item-action d-flex gap-3 py-3">
    <img src="../static/images/user.png" alt="favicon" width="32" height="32" class="rounded-circle flex-shrink-0" />
    <div class="d-flex gap-2 w-100 justify-content-between">
      <div>
        <p class="mb-0 opacity-75">${question}</p>
      </div>
    </div>
  </a>`;

  $("#chat-input").val("");
  $("#list-group").append(html_data);

  // Send AJAX request to generate quiz questions
  $.ajax({
    type: "POST",
    url: "/quiz",
    data: { prompt: question },
    success: function (data) {
      // Add AI response to chat log
      let ai_data = `
      <a href="#" class="list-group-item list-group-item-action d-flex gap-3 py-3">
        <img src="../static/images/ai.png" alt="favicon" width="32" height="32" class="rounded-circle flex-shrink-0" />
        <div class="d-flex gap-2 w-100 justify-content-between">
          <div>
            <p class="mb-0 opacity-75">${data.answer}</p>
          </div>
        </div>
      </a>`;
      $("#list-group").append(ai_data);

      // Access the 'answer' from the response data
      console.log(data.answer);

      // Show the "Generate Quiz" button
      $("#quiz-button").removeClass("d-none");
    },
  });
}

$("#quiz-button").click(function () {
  var prompt = $("#chat-input").val();

  let html_data = `
  <a href="#" class="list-group-item list-group-item-action d-flex gap-3 py-3">
    <img src="../static/images/user.png" alt="favicon" width="32" height="32" class="rounded-circle flex-shrink-0" />
    <div class="d-flex gap-2 w-100 justify-content-between">
      <div>
        <p class="mb-0 opacity-75">${prompt}</p>
      </div>
    </div>
  </a>`;

  $("#chat-input").val("");
  $("#list-group").append(html_data);

  $.ajax({
    type: "POST",
    url: "/generate-quiz",
    data: { prompt: prompt },
    success: function (data) {
      let ai_data = `
      <a href="#" class="list-group-item list-group-item-action d-flex gap-3 py-3">
        <img src="../static/images/ai.png" alt="favicon" width="32" height="32" class="rounded-circle flex-shrink-0" />
        <div class="d-flex gap-2 w-100 justify-content-between">
          <div>
            <p class="mb-0 opacity-75">${data.answer}</p>
          </div>
        </div>
      </a>`;

      $("#list-group").append(ai_data);

      console.log("Generated Quiz Number:", data.quiz_number);

      window.location.href = data.quiz_url;
    },
    error: function () {
      console.log("Failed to generate quiz");
    }
  });
});
