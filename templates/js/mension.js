<script>
  $(document).ready(function () {
const users = [
    {% for user in mention_users  %}
      {
        key: "{{ user.username }}",
        value: "{{ user.username|default:user.username }}",
        html: '<div style="display:flex; align-items:center;"><img src="{{ user.photo.url }}" class="img-avatar rounded-circle " alt="avatar"> <div class="mx-1"> <strong>{{ user.username }}</strong> <div style="font-size:smaller; color:gray;">{{ user.email }}</div></div>'
      }{% if not forloop.last %},{% endif %}
    {% endfor %}
  ];
     const tribute = new Tribute({
    trigger: '@',
    values: users,
    selectTemplate: function (item) {
      return '@' + item.original.key;
    },
    menuItemTemplate: function (item) {
      return item.original.html;
    }
  });
     const contentTriggerList = document.querySelectorAll('[id="content"]')
     const contentList = [...contentTriggerList].map(contentTriggerEl => tribute.attach(contentTriggerEl))
});
</script>