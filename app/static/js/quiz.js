$(document).ready(function() {
  
  $("#gpt-button").click(function () {
    console.log("clicked");
  
    generateQuiz();
  });
  
  $("#chat-input").keydown(function (event) {
    if (event.which === 13) {
      event.preventDefault();
      generateQuiz();
    }
  });
  
  function generateQuiz() {
    $("#gpt-button").prop("disabled", true);
    $("#spinner").removeClass("d-none");
    var question = $("#chat-input").val();
  
    if (question.trim() === "") {
      return; // Don't proceed if the prompt is empty or contains only whitespace
    }
  
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
    var csrfToken = $('input[name="csrf_token"]').val(); // Retrieve the CSRF token
    $.ajax({
      type: "POST",
      url: "/quiz",
      headers: {
        "X-CSRFToken": csrfToken, // Set the CSRF token as a header
      },
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
  
        console.log("Generated Number:of quiz", data.question_text.length);
  
        // Show the "Generate Quiz" button
        $("#quiz-button").removeClass("d-none");
        $("#list-group").removeClass("d-none");
        $("#spinner").addClass("d-none");
        $("#gpt-button").prop("disabled", false);
      },
      error: function () {
        $("#spinner").addClass("d-none");
        alertMsg('Something went wrong')
        $("#gpt-button").prop("disabled", false);
      },
    });
  }
});
