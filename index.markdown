---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home-page
title: Home
---

# Workshop Venues
{% for workshop in site.workshops %}
  <h2>
    <a href="{{ workshop.url | prepend: site.baseurl }} ">
      {{workshop.conference}} | {{workshop.conference-date}} 
    </a>
  </h2>
{% endfor %}
<br>
