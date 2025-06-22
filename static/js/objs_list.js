
window.addEventListener("load", function() {
      const sessionData = JSON.parse('{{ session | escapejs }}');
      const objDeleteURL = "{% url obj_delete 0 %}";
      const popoverTriggerList = [].slice.call(document.querySelectorAll("[data-bs-toggle=\"popover\"]"));
      const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, { html: true, trigger: "hover click" });
      });
      for (const key in sessionData) {
        if (sessionData.hasOwnProperty(key)) {
          const element = document.getElementById(key);
          if (element) {
            element.value = sessionData[key];
          }
        }
      }


      document.querySelectorAll(".delete-obj").forEach(function(button) {
        button.addEventListener("click", function() {
          const objId = this.getAttribute("data-obj-id");
          if (confirm("{% trans 'Are you sure you want to delete?' %}")) {
            fetch(objDeleteURL.replace("0", objId), {
              method: "POST",
              headers: {
                "X-CSRFToken": '{{ csrf_token }}',
                "Content-Type": "application/json"
              },
              body: JSON.stringify({})
            })
              .then(response => response.json())
              .then(data => {
                if (data.success) {
                  alert(data.message);
                  // Option 1: Remove the row from the table
                  this.closest("tr").remove();
                  // Option 2: Or, reload the page to reflect changes:
                  // window.location.reload();
                } else {
                  alert("Error: " + data.message);
                }
              })
              .catch(error => {
                console.error("Error:", error);
                alert("{% trans 'An error occurred while deleting.' %}");
              });
          }
        });
      });
      });