{% load i18n %}

$(document).ready(function() {
     AOS.init();
     var tab_url = window.location.pathname.replace(/^((?:[^\/]*\/){3}).*$/, "$1");
     var active_tab = document.querySelectorAll(`a[href='${tab_url}']`);
    active_tab[0].classList.add('active');

  const sessionTimeout = {{ session_timeout }} * 1000;
  const warningBefore = 60 * 1000;       // 1 minute before logout

  let warningTimer, logoutTimer;
  const timeoutModal = new bootstrap.Modal(document.getElementById('sessionTimeoutModal'));

  function startTimers() {
    clearTimeout(warningTimer);
    clearTimeout(logoutTimer);

    warningTimer = setTimeout(() => {
      timeoutModal.show();
      startCountdown(60);
    }, sessionTimeout - warningBefore);

    logoutTimer = setTimeout(() => {
      window.location.href = "{% url 'account_logout' %}";
    }, sessionTimeout);
  }

  function startCountdown(seconds) {
    const countdownElem = document.getElementById('countdown');
    let remaining = seconds;
    countdownElem.innerText = remaining;
    const interval = setInterval(() => {
      remaining--;
      countdownElem.innerText = remaining;
      if (remaining <= 0) clearInterval(interval);
    }, 1000);
  }

  ['click', 'mousemove', 'keydown'].forEach(event =>
    document.addEventListener(event, () => startTimers())
  );

  document.getElementById('stayLoggedInBtn').addEventListener('click', () => {
    timeoutModal.hide();
    startTimers();
  });

  startTimers();
  });

  document.addEventListener("DOMContentLoaded", function () {
        // Request permission for browser notifications
        if ("Notification" in window) {
            Notification.requestPermission().then((result) => {
                console.log("Notification permission:", result);
            });
        }
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
    });
     var socket = new WebSocket("ws://" + window.location.host + "/ws/notifications/");
             var translations = document.getElementById("translations");
        var translatedActions = {
            "created": translations.dataset.created,
            "updated": translations.dataset.updated,
            "deleted": translations.dataset.deleted
        };
                  var models = document.getElementById("models");
          var translatedModels = {
              "administrativeinvestigation": models.dataset.administrativeinvestigation,
              "notation": models.dataset.notation,
              "task": models.dataset.task,
              "hearing": models.dataset.hearing,
              "litigationcases": models.dataset.litigationcases,
              "path": models.dataset.path,
          };
    socket.onmessage = function (event) {
        var notification = JSON.parse(event.data);
            if (notification.type === 'user.status') {
      console.log('User ID:', notification.user_id, 'is now', notification.status);
    }
        console.log(notification);
        var modelTranslated = translatedModels[notification.content_type] || notification.content_type; // Default to action if not found
        var notificationDropdown = document.getElementById("notificationItems");
        var actionTranslated = translatedActions[notification.action] || notification.action; // Default to action if not found
        var newItem = document.createElement("li");
        var liClass = "";
        var pClass = "";
                    if (notification.is_read === true )
                    {
                      liClass = "opacity-75";
                      pClass = "text-muted";
                    }
                    else {
                      pClass = "fw-bolder text-dark";
                    }
        newItem.className = liClass;
        newItem.innerHTML = `<a class="dropdown-item" href="#">
                            <p class="${ pClass }">${actionTranslated} ${ modelTranslated } <i class="text-primary">(${ notification.object_name })</i></p>
                            <small class="text-muted d-block"><strong>${ notification.action_by }</strong> ${ notification.timestamp }</small>
                        </a>`;
        const no_notifications = document.getElementById("no_notifications");
        if(no_notifications) {
          document.getElementById("no_notifications").remove();
        }
        notificationDropdown.insertBefore(newItem, notificationDropdown.firstChild.nextSibling);
        document.getElementById("notificationCount").innerText++;
                if ("Notification" in window && Notification.permission === "granted") {
                  let notificationContent = '';
                  if (notification.type === 'user.status')
                  {
                    notificationContent = `${notification.username} is now ${notification.status}`
                  }
                  else {
                    notificationContent = `${notification.action_by} ${actionTranslated} ${notification.object_name}`
                  }
            new Notification("{% trans 'Legal App - New Notification' %}", {

                body: notificationContent,
                icon: "/static/images/qilogo.svg",  // Optional: Add your own notification icon
                requireInteraction: true,  // Keeps the notification on screen until user dismisses
            });
        }
    };


    socket.onclose = function () {
        console.log("WebSocket closed.");
    };

     var page = 1;  // Track the current page
    var loading = false;  // Prevent multiple requests
    var hasMore = true;  // Indicates if there are more notifications to load

    function loadMoreNotifications() {
        if (!hasMore || loading) return;  // Stop if no more notifications or already loading

        loading = true;
        page += 1;

        fetch(`/load-more-notifications/?page=${page}`)
            .then(response => response.json())
            .then(data => {
                var notificationDropdown = document.getElementById("notificationItems");
                             var translations = document.getElementById("translations");
        var translatedActions = {
            "created": translations.dataset.created,
            "updated": translations.dataset.updated,
            "deleted": translations.dataset.deleted
        };
          var models = document.getElementById("models");
          var translatedModels = {
              "administrativeinvestigation": models.dataset.administrativeinvestigation,
              "notation": models.dataset.notation,
              "task": models.dataset.task,
              "hearing": models.dataset.hearing,
              "litigationcases": models.dataset.litigationcases,
              "path": models.dataset.path,
          };

                data.notifications.forEach(notification => {
                    var actionTranslated = translatedActions[notification.action] || notification.action; // Default to action if not found
                    var modelTranslated = translatedModels[notification.content_type] || notification.content_type; // Default to action if not found
                    var liClass = "";
                    var pClass = "";
                    if (notification.is_read === true )
                    {
                      liClass = "opacity-75";
                      pClass = "text-muted";
                    }
                    else {
                      pClass = "fw-bolder text-dark";
                    }
                    var newItem = document.createElement("li");
                    newItem.className = liClass;
                    newItem.innerHTML = `<a class="dropdown-item" href="#">
                            <p class="${ pClass }">${actionTranslated} ${ modelTranslated } <i class="text-primary">(${ notification.object_name })</i></p>
                            <small class="text-muted d-block"><strong>${ notification.action_by }</strong> ${ notification.timestamp }</small>
                        </a>`;
                    notificationDropdown.appendChild(newItem);
                });

                hasMore = data.has_more;  // Update if more notifications are available
                loading = false;
            })
            .catch(error => {
                console.error("Error loading more notifications:", error);
                loading = false;
            });
    }

    // Listen for scroll event on the notifications dropdown
    document.getElementById("notificationItems").addEventListener("scroll", function () {
        var dropdown = this;
        if (dropdown.scrollTop + dropdown.clientHeight >= dropdown.scrollHeight - 5) {
            loadMoreNotifications();  // Load more notifications when reaching the bottom
        }
    });
  {% if request.not_read_notifications_count > 0 %}
    document.getElementById("read_all_notifications").addEventListener('click', function() {
        if (confirm('{% trans "Are you sure you want to read all notifications?" %}')) {
          fetch("{% url 'read_all_notifications'  %}", {
            method: 'POST',
            headers: {
              'X-CSRFToken': '{{ csrf_token }}',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
          })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              alert(data.message);
              // Option 1: Remove the row from the table
              //this.closest('tr').remove();
              // Option 2: Or, reload the page to reflect changes:
              window.location.reload();
            } else {
              alert('Error: ' + data.message);
            }
          })
          .catch(error => {
            console.error('Error:', error);
            alert('{% trans "An error occurred while read all notifications" %}');
          });
        }
      });
  {% endif %}
{% if request.not_deleted_notifications_count > 0 %}
    document.getElementById("delete_all_notifications").addEventListener('click', function() {
        if (confirm('{% trans "Are you sure you want to delete all notifications?" %}')) {
          fetch("{% url 'delete_all_notifications'  %}", {
            method: 'POST',
            headers: {
              'X-CSRFToken': '{{ csrf_token }}',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
          })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              alert(data.message);
              // Option 1: Remove the row from the table
              //this.closest('tr').remove();
              // Option 2: Or, reload the page to reflect changes:
              window.location.reload();
            } else {
              alert('Error: ' + data.message);
            }
          })
          .catch(error => {
            console.error('Error:', error);
            alert('{% trans "An error occurred while delete all notifications" %}');

          });
        }
      });
  {% endif %}